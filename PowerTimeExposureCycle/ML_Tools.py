import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import glob as glob
import pandas as pd
import spe_loader as sl


import ControlPiezoStage as Transla
import ControlLaser as laser
import ControlKymera as spectrolib
import ControlPiezoStage as Transla
import ControlEMCCD as EMCCD
import FileControl



def LoadDataFromFiles(FileDir, FolderCalibWavelength, WaveCenter):
    # Compute wavelength
    try:
        temp = pd.read_csv(FolderCalibWavelength, sep='\t', decimal=',')
        a = temp.loc[:, 'a'].to_numpy()
        b = temp.loc[:, 'b'].to_numpy()
        print('Reading wavelength calibration at : {}'.format(
            FolderCalibWavelength))
    except:
        print('Problem reading wavelength calibraton at : {}\n Taking default value.'.format(
            FolderCalibWavelength))
        a = 2.354381287460651
        b = 490.05901104995587
    PixelNumber = np.linspace(1, 1024, 1024)
    CenterPixel = WaveCenter
    Wavelength = (PixelNumber-b)/a+CenterPixel
    
    File= sorted(glob.glob(FileDir+'/*.spe'),key=lambda x: float(x[x.find('data')+4:x.find('.spe')]))
    DataTot = pd.DataFrame(columns=list(Wavelength)+['Time','Mes'])

    for j in range(len(File)):
        print('\r Reading Files:{} %'.format(
            np.round(100*j/len(File), 1)), end='', flush=True)
        DataRaw = sl.load_from_files([File[j]])
        MetaData = pd.DataFrame(DataRaw.metadata)
        TimeI = MetaData.loc[:, 0].to_numpy()/(1E6)  # Time in ms
        DataTotTemp=pd.DataFrame(columns=list(Wavelength)+['Time','Mes'])
        try:
            DataTotTemp[Wavelength]=np.squeeze(DataRaw.data)
        except Exception as e:
            print('\n{}'.format(e))
            exit
        DataTotTemp['Mes'] = j
        DataTotTemp['Time'] = TimeI
        if DataTot.shape[0]==0:
            DataTot=DataTotTemp
        else:
            DataTot=pd.concat([DataTotTemp,DataTot],axis=0)
    return DataTot

def DoFocusAcqSeries(camera,PiezoAxis):
    Piezo_zPos=np.linspace(start=0.1,stop=79.9,num=50)
    NbFrame=camera.GetNumberOfFrame()
    camera.SetNumberOfFrame(20.)
    for pos in Piezo_zPos:
        print(pos)
        PiezoAxis.MoveTo(pos)
        camera.Acquire()
        camera.WaitForAcq()
    #camera.SetNumberOfFrame(float(NbFrame))
    return Piezo_zPos
    
#def FindPlaneEquation(PosXY,PosZ):

def FindFocus(DataFolder,WaveCalibFolder,WavelengthSpectro,Camera,PiezoAxis,PosRoughAxis):
    ''''This function take as argument will scan to z-axis and mesure the intensity then fit the curve find the maximum position and return it in a single float. The unit is in um.
    The argument are the following:

    -DataFolder: folder in which to save the data  

    -WaveCalibFolder: folder containing the calibration file for the spectrometer

    -WavelengthSpectro: current wavelength of the spectro

    -Camera: an LightFieldControl object from ControlEMCCD

    -PiezoAxis: a PiezoAxisControl from ControlPiezo

    -PosRoughAxis: an array containing the [x,y] position of the rough axis this is only used for saving the data file'''
    zPos=DoFocusAcqSeries(Camera,PiezoAxis)
    Data=LoadDataFromFiles(DataFolder,WaveCalibFolder,WavelengthSpectro)
    Data.to_pickle(DataFolder+"/Datax={}y={}.pkl".format(np.round(PosRoughAxis[0],3),np.round(PosRoughAxis[1],3)))
    pd.DataFrame(zPos).to_csv(DataFolder+"/Zpos_x={}y={}.pkl".format(np.round(PosRoughAxis[0],3),np.round(PosRoughAxis[1],3)))

if __name__ == '__main__':
    
    FolderCalibWavelength = '//sun/garnett/home-folder/gautier/Femto-setup/Data/0.Calibration/Spectrometer.csv'

    Spectrograph_slit=100
    Spectrograph_Center=700

    GeneralPara = {'Experiment name': ' FocusFind'}

               
    GeneralPara.update({'Note': 'The SHG unit from Coherent was used and ND1 for probe'})

    InstrumentsPara = {}

    
    #############################
    # Initialisation of laser
    #############################
    Laser = laser.LaserControl('COM8', 'COM17', 0.5)

    InstrumentsPara['Laser'] = Laser.parameterDict
    print('Initialised Laser')
    
    #############################
    # Initialisation of spectro
    #############################
    spectro = spectrolib.KymeraSpectrograph()

    InstrumentsPara['Kymera'] = spectro.parameterDict
    print('Initialised spectro')
    
    #############################
    # Initialisation of piezo
    #############################

    piezo = Transla.PiezoControl('COM15')
    z_axis = Transla.PiezoAxisControl(piezo, 'x', 3)
    InstrumentsPara['PiezoStage']=piezo.parameterDict

    print('Directory staging, please check other window')

    #############################
    # Preparation of the directory
    #############################
    DirectoryPath = FileControl.PrepareDirectory(GeneralPara, InstrumentsPara)
    
    #############################
    # Initialisation of the EMCCD
    #############################

    camera = EMCCD.LightFieldControl('ML2')
    camera.SetSaveDirectory(DirectoryPath.replace('/', "\\"))
    
    InstrumentsPara['PI EMCCD'] = camera.parameterDict
    print('Initialised EMCCD')
    Laser.SetStatusShutterTunable(1)

    z=FindFocus(DirectoryPath,FolderCalibWavelength,spectro.GetWavelength(),camera,z_axis,[1,1])
    