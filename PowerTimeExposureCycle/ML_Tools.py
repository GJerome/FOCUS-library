import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import glob as glob
import pandas as pd
import spe_loader as sl
import matplotlib.pyplot as plt
import random

import ControlPiezoStage as Transla
import ControlLaser as laser

import ControlPiezoStage as Transla
import ControlConex as RoughTransla

import FileControl
from scipy.optimize import curve_fit


#############################
# Position generation
#############################
def DistanceTwoPoint(pointA, pointB):
    return np.sqrt(np.sum((pointA - pointB)**2, axis=0))


def DistanceArray(pointA, pointsB):
    return np.sqrt(np.sum((pointA - pointsB)**2, axis=1))

def Generate_RandomPositionRoughFine(generations_budget,Nb_Points_Generation,Nb_points_Piezo,
                                     Coeff,BeamRadius=30,
                                     startX_rough=10,startY_rough=10,SpacingBetweenRough=0.150):
    GeneralPosition=pd.DataFrame(columns=['x_rough','y_rough','x_piezo','y_piezo','z_piezo','Cluster','Generation'])


    NbPts_RoughAxis=np.ceil(Nb_Points_Generation/Nb_points_Piezo)*generations_budget

    x = np.linspace(startX_rough, startX_rough+SpacingBetweenRough*np.ceil(np.sqrt(NbPts_RoughAxis)),
                     int(np.ceil(np.sqrt(NbPts_RoughAxis))))
    y = np.linspace(startY_rough, startY_rough+SpacingBetweenRough*np.ceil(np.sqrt(NbPts_RoughAxis)),
                     int(np.ceil(np.sqrt(NbPts_RoughAxis))))

    X, Y = np.meshgrid(x, y)

    Pos_rough = np.stack([X.ravel(), Y.ravel()], axis=-1)

    i=0
    for j in range(generations_budget):
        k=0
        while k<Nb_Points_Generation:
            Pos_df=pd.DataFrame(columns=['x_rough','y_rough','x_piezo','y_piezo','z_piezo','Cluster','Generation'])
            x = np.linspace(0.5, 79.5, int(np.floor(np.sqrt(Nb_points_Piezo))))
            y = np.linspace(0.5, 79.5, int(np.ceil(np.sqrt(Nb_points_Piezo))))

            X, Y = np.meshgrid(x, y)

            Pos = np.stack([X.ravel(), Y.ravel()], axis=-1)

            # Randomly shuffle position
            index = random.sample(range(0, Pos.shape[0]), Pos.shape[0])
            Pos = Pos[index, :]

            # Avoid point which are too close too each other
            PosFiltered = np.empty(Pos.shape)
            for index in range(Nb_points_Piezo):
                if index == 0:
                    PosFiltered[index, :] = Pos[0, :]
                    Pos = np.delete(Pos, 0, 0)
                else:
                    if DistanceTwoPoint(PosFiltered[index-1, :], Pos[0, :]) < BeamRadius:
                        a = np.argmax(DistanceArray(
                        PosFiltered[index-1, :], Pos) > BeamRadius)
                        PosFiltered[index, :] = Pos[a, :]
                        Pos = np.delete(Pos, a, 0)
                        if a == 0:
                            print(
                            'Could not find a point not within the beam avoidance radius.')
                    else:
                        PosFiltered[index, :] = Pos[0, :]
                        Pos = np.delete(Pos, 0, 0)

            Pos = PosFiltered
            Pos_df['x_piezo']=Pos[:,0]
            Pos_df['y_piezo']=Pos[:,1]
            Pos_df['z_piezo']=Find_zFromEq(Pos_rough[i,0]+0.001*Pos[:,0],Pos_rough[i,1]+0.001*Pos[:,1],Coeff)
            Pos_df['x_rough']=Pos_rough[i,0]
            Pos_df['y_rough']=Pos_rough[i,1]
            Pos_df['Cluster']=i
            Pos_df['Generation']=j
            #GeneralPosition=pd.concat([GeneralPosition,Pos_df],axis=0,ignore_index=True)
            if i==0:
                GeneralPosition=Pos_df
            else:
                GeneralPosition=pd.concat([GeneralPosition,Pos_df],axis=0,ignore_index=True)
            k=k+len(Pos[:,0])
            i=i+1
        
    return GeneralPosition

#############################
# Loading spe file
#############################
   

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


#############################
# Focus related functions
#############################

def DoFocusAcqSeries(camera,PiezoAxis):
    Piezo_zPos=np.linspace(start=0.1,stop=79.9,num=100)
    NbFrame=camera.GetNumberOfFrame()
    camera.SetNumberOfFrame(3.)
    for pos in Piezo_zPos:
        print('\r Focus finding :{} %'.format(np.round(100*pos/Piezo_zPos[-1], 1)), end='', flush=True)
        PiezoAxis.MoveTo(pos)
        camera.Acquire()
        camera.WaitForAcq()
    #camera.SetNumberOfFrame(float(NbFrame))
    return Piezo_zPos

   
def intensity_z(z, I0, z0, zR, I_background=0):
    """
    Calculate the intensity profile along the z-axis.

    Parameters:
    - z: position along the z-axis (scalar or array)
    - I0: peak intensity at the focus
    - z0: position of the focus along the z-axis
    - zR: Rayleigh length
    - I_background: background intensity (default = 0)

    Returns:
    - Intensity I(z) at position z
    """
    return I0 / (1 + ((z - z0)/zR)**2) + I_background


def Find_zFromEq(x,y,Coeff):
    '''x,y represent the position in which we want to find the z and Coeff should be a numpy array for which
      ax+by+cz=d => Coeff[0]*x+Coeff[1]*y+Coeff[2]*z=Coeff[3]'''
    z=Coeff[0]*x+Coeff[1]*y+Coeff[2]
    return z

def best_fit_plane(x, y, z):
    """Computes the best-fit plane equation z = Ax + By + C for given x, y, z data points
    using the least squares method."""

    X = np.column_stack((x, y, np.ones_like(x)))
    coefficients, _, _, _ = np.linalg.lstsq(X, z,rcond=None)
    return coefficients  # A, B, C

def FindFocus(DataFolder,WaveCalibFolder,WavelengthSpectro,Camera,PiezoAxis,PosRoughAxis):
    ''''This function take as argument will scan to z-axis and mesure the intensity then fit the curve find the maximum position and return it in a single float. The unit is in um.
    The argument are the following:

    -DataFolder: folder in which to save the data  

    -WaveCalibFolder: folder containing the calibration file for the spectrometer

    -WavelengthSpectro: current wavelength of the spectro

    -Camera: an LightFieldControl object from ControlEMCCD

    -PiezoAxis: a PiezoAxisControl from ControlPiezo

    -PosRoughAxis: an array containing the [x,y] position of the rough axis this is only used for saving the data file'''
    DataFolderRaw=DataFolder+'/RawDataFocusFind/Datax={}y={}'.format(np.round(PosRoughAxis[0],3),np.round(PosRoughAxis[1],3))
    os.makedirs(DataFolderRaw, exist_ok=True)

    # Acquisition
    camera.SetSaveDirectory(DataFolderRaw.replace('/', "\\"))    
    zPos=DoFocusAcqSeries(Camera,PiezoAxis)

    # Load data
    Data=LoadDataFromFiles(DataFolderRaw,WaveCalibFolder,WavelengthSpectro)
    Data.to_pickle(DataFolder+"/RawDataFocusFind/Datax={}y={}.pkl".format(np.round(PosRoughAxis[0],3),np.round(PosRoughAxis[1],3)))
    pd.DataFrame(zPos,columns=['z']).to_csv(DataFolder+"/RawDataFocusFind/Zpos_x={}y={}.csv".format(np.round(PosRoughAxis[0],3),np.round(PosRoughAxis[1],3)))
    # Here the focus is assumed just to be the point in which there is a maximum. With a fit 
    # it sometimes doesnt fit well because of a reflection which create a sholder in the peak.
    Mes_posz=Data.loc[:,'Mes'].unique()
    DataAgg=pd.DataFrame(columns=['z','Mean of max','std'])

    for ztemp in Mes_posz:
        DataTemp=Data.loc[ Data['Mes']==ztemp,:].iloc[:,:-2]
        temp=pd.DataFrame({'z':zPos[int(ztemp)],'Mean of max':DataTemp.max(axis=1).mean(),'std':DataTemp.max(axis=1).std()},index=[0])
        DataAgg=pd.concat([DataAgg,temp],axis=0,ignore_index=True)
    DataAgg=DataAgg.dropna()
    p_opt,p_cov=curve_fit(intensity_z,xdata=DataAgg.loc[:,'z'],ydata=DataAgg.loc[:,'Mean of max'])
    
    z_fit=np.linspace(start=0.1,stop=79.9,num=500)
    Data_fit=intensity_z(z_fit,p_opt[0],p_opt[1],p_opt[2],p_opt[3])
    FocusPos=DataAgg.loc[DataAgg['Mean of max'].idxmax(axis=0),'z']

    fig,ax=plt.subplots(1,1)
    ax.errorbar(DataAgg['z'],DataAgg['Mean of max'],yerr=DataAgg['std'],label=str(np.round(FocusPos,3)))
    ax.plot(z_fit,Data_fit)
    ax.plot([FocusPos,FocusPos],ax.get_ylim())
    ax.set_xlabel('z[$\mu$m]')
    plt.legend()
    plt.savefig(DataFolderRaw+'/MaxIntZ.png')
    plt.close(fig)

    return FocusPos

def FindPlaneEquation(DataFolder,WaveCalibFolder,WavelengthSpectro,Camera,PiezoAxis,PosRoughAxis,x_rough,y_rough):
    ''''This function will find the plane equation that can be used to correct for sample tilt.
    The argument are the following:

    -DataFolder: folder in which to save the data  

    -WaveCalibFolder: folder containing the calibration file for the spectrometer

    -WavelengthSpectro: current wavelength of the spectro

    -Camera: an LightFieldControl object from ControlEMCCD

    -PiezoAxis: a PiezoAxisControl from ControlPiezo

    -PosRoughAxis: an 2D array containing the [x,y] position of the rough axis, each line correspond to a given point. 
    -x_rough,y_rough the conex controller axis'''

    

    Nb_points=PosRoughAxis.shape[0]
    if Nb_points<3:
        print('FindPlaneEquation error: system undefined please provide more points')
        sys.exit()
    Points=pd.DataFrame(index=range(Nb_points),columns=['x[mm]','y[mm]','z[um]'])

    for i in range(Nb_points):
        x_rough.MoveTo(PosRoughAxis[i,0])
        y_rough.MoveTo(PosRoughAxis[i,1])
        Points.loc[i,'x[mm]']=PosRoughAxis[i,0]
        Points.loc[i,'y[mm]']=PosRoughAxis[i,1]
        Points.loc[i,'z[um]']=FindFocus(DataFolder,WaveCalibFolder,WavelengthSpectro,Camera,PiezoAxis,PosRoughAxis[i,:])
        print(Points)
    Coeff=best_fit_plane(Points.loc[:,'x[mm]'].astype('float'),Points.loc[:,'y[mm]'].astype('float'),Points.loc[:,'z[um]'].astype('float'))
    return Coeff




#############################
# Main script
#############################
if __name__ == '__main__':
    import ControlKymera as spectrolib
    import ControlEMCCD as EMCCD

    
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
    x_axis = Transla.PiezoAxisControl(piezo, 'y', 3)
    y_axis = Transla.PiezoAxisControl(piezo, 'z', 3)
    z_axis = Transla.PiezoAxisControl(piezo, 'x', 3)
    x_axis.MoveTo(0.05)
    y_axis.MoveTo(0.05)
    InstrumentsPara['PiezoStage']=piezo.parameterDict

    x_axis_Rough = RoughTransla.ConexController('COM12')
    y_axis_Rough = RoughTransla.ConexController('COM13')
    InstrumentsPara['Rough Stage']=x_axis_Rough.parameterDict | y_axis_Rough.parameterDict 
    print('Initialised rough translation stage')

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
    x_begin=9.6
    y_begin=10
    x=[x_begin,x_begin+1,x_begin,x_begin+1,x_begin-1,x_begin-1]
    y=[y_begin,y_begin,y_begin+1,y_begin+1,y_begin,y_begin-1]
    Pos=np.transpose(np.array([x,y]))
    Laser.SetStatusShutterTunable(0)

    Coeff=FindPlaneEquation(DirectoryPath,FolderCalibWavelength,spectro.GetWavelength(),camera,z_axis,Pos,x_axis_Rough,y_axis_Rough)
    print(Coeff)
    