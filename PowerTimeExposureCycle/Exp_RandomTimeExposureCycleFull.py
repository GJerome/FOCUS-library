import time as time
import os
import sys
import inspect
os.system('cls')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 



import numpy as np
import pandas as pd
import random
import glob as glob
import spe_loader as sl


import ControlFlipMount as shutter
import ControlLaser as las
import ControlPulsePicker as picker
import ControlEMCCD as EMCCD
import FileControl
import ControlPiezoStage as Transla


#############################
# Global parameter
#############################


Nb_Points =100  # Number of position for the piezo

start_x =7
end_x = 78
start_y = 7
end_y = 75


Nb_Cycle = 10 # Number of cycle during experiment

StabilityTime_Begin=60# Time for which it will probe at the beginning of the cycle
StabilityTime_Reset=60# The beam will then be block for this amount of time so that the sample 'reset'
StabilityTime_End = 60# Time for which it will probe at the end of the cycle
#The total time is then StabilityTime_Begin+ StabilityTime_Reset+ StabilityTime_End+Time of cycle

PowerProbePulsePicker=500
EmGainProbe=50



OnlyOneConfig=True # Set it  to true so that it only probe with one config for Nb_points
OnlyOneConfig_Random=False # Set it  to true so that this config is random
OnlyOneConfig_UseCurentCalib=False #Not implemented yet, Set it  to true if you want it to use the current calibration or False if it should read the power send to the pulse picker from a file

ProbeDiffDivRatio= False #For the probing it set to true The staiblity time can be done at specific rep rate and power
DivRatio=[40,4]# A list containing the different div ratio
PowerProbe=[1800,500]# A list containing the power to use to probe

Spectrograph_slit=10 # This is just for record not actually setting it up
Spectrograph_Center=750# This is just for record not actually setting it up

FolderCalibWavelength='//sun/garnett/home-folder/gautier/Femto-setup/Data/0.Calibration/Spectrometer.csv'
BeamRadius=15

#############################
# Piezo parameter
#############################


if start_x==end_x:
    x = np.array([start_x])
    y = np.linspace(start_y, end_y, int(Nb_Points))
elif start_y==end_y:
    y = np.array([start_y])
    x = np.linspace(start_x, end_x, int(Nb_Points))
else:
    x = np.linspace(start_x, end_x, int(np.floor(np.sqrt(Nb_Points))))
    y = np.linspace(start_y, end_y, int(np.ceil(np.sqrt(Nb_Points))))

X, Y = np.meshgrid(x, y)
Pos = np.stack([X.ravel(), Y.ravel()], axis=-1)
index=random.sample(range(0, Pos.shape[0]), Pos.shape[0])
Pos=Pos[index,:]
Nb_Points=Pos.shape[0]

# Once we randomize a first time we just try to make each next point as far as posible of the other
def DistanceTwoPoint(pointA, pointB):
    return np.sqrt(np.sum((pointA - pointB)**2, axis=0))

def DistanceArray(pointA, pointsB):
    return np.sqrt(np.sum((pointA - pointsB)**2, axis=1))

PosFiltered=np.empty(Pos.shape)
for index in range(Nb_Points):
    if index==0:
        PosFiltered[index,:]=Pos[0,:]
        Pos=np.delete(Pos,0,0)
    else:
        if DistanceTwoPoint(PosFiltered[index-1,:],Pos[0,:])<BeamRadius:            
            a=np.argmax(DistanceArray(PosFiltered[index-1,:],Pos)>BeamRadius)
            PosFiltered[index,:]=Pos[a,:]
            Pos=np.delete(Pos,a,0)
            if a==0:
                print('Could not find a point not within the beam avoidance radius.')
        else:
            PosFiltered[index,:]=Pos[0,:]
            Pos=np.delete(Pos,0,0)
    
Pos=PosFiltered

try:
    print('Number of Points:{}\nDistance between points:\n\t x ={} \n\t y ={}'.format(Pos.shape[0],
                                                                                  x[1]-x[0], y[1]-y[0]))
except IndexError:
    print('Number of Points:{}\n'.format(Pos.shape[0]))

GeneralPara = {'Experiment name': ' ML', 'Nb points':Pos.shape[0],'Beam avoidance radius':BeamRadius,
               'Stability time begin ': StabilityTime_Begin,'Stability time reset':StabilityTime_Reset,'Stability time end ': StabilityTime_End,
               'Probe DiffDivRatio':ProbeDiffDivRatio,'Div ratio probe used':DivRatio,'Power probe div ratio':PowerProbe,
               'Power probe ':PowerProbePulsePicker,'Em Gain probe':EmGainProbe,'Spectrograph slit width':Spectrograph_slit,'Spectrograph center Wavelength':Spectrograph_Center,
               'Note': 'The SHG unit from Coherent was used and ND05 for probe'}

InstrumentsPara = {}
##############################################################
# Parameter space and random choice
##############################################################

###################
# Proba density function Power
###################
P = (0, 4.4, 10, 100, 200)  # power in uW
#Value to reach on the powermeter (0,11,25,240,475)uW
P_calib = (500, 500,900, 2400, 3400)  # Power from the pp to reach values of P #20MHz
#P_calib = (500, 1400,2000, 6100, 9300)  # Power from the pp to reach values of P #5MHz
#P_calib = (500, 1700,2500, 10000, 17500)  # Power from the pp to reach values of P #500kHz

p0 = [0.2, 0.2, 0.2, 0.2, 0.2]
p1 = [0.3, 0.175, 0.175, 0.175, 0.175]
ProbaP = p1

GeneralPara['Power cycle']=P
GeneralPara['Power Calib']=P_calib
GeneralPara['Probability table power']=ProbaP
###################
# Proba density function Time
###################
t = (0.1, 1, 10, 100)  # time

p0 = [0.25, 0.25, 0.25, 0.25]
p1 = [0.25, 0.25, 0.25, 0.25]
ProbaT = p1

GeneralPara['Time cycle']=P
GeneralPara['Probability table time']=ProbaT
###################
# RNG declaration
###################
rng = np.random.default_rng()

if OnlyOneConfig==True:
    if OnlyOneConfig_Random==False:
        FileConfig='./PowerTimeExposureCycle/PowerTimeCycles/Cycle241209-Order2.csv'
        print('Reading file {} for power/time config '.format(FileConfig))
        # For the moment we assume only one config
        Cycle_info=pd.read_csv(FileConfig)
        #nb_config_file=len(Cycle_info.columns)
        T_final=Cycle_info.loc[:,'Exposure Time'].to_numpy()
        P_Final=Cycle_info.loc[:,'Power send'].to_numpy()
        if OnlyOneConfig_UseCurentCalib==False:
            P_Final_calib=Cycle_info.loc[:,'Power Pulse-picker'].to_numpy()
        else:
            P_Final_calib=Cycle_info.loc[:,'Power Pulse-picker'].to_numpy()
        Nb_Cycle=Cycle_info.shape[0]
    else:
        print('One random cycle configuration')
        # Intensity/Power Cycle generation
        T_final = rng.choice(t, Nb_Cycle, p=ProbaT)
        # First we generate an array of cycle which only contains index for the moment
        temp = rng.choice(np.linspace(0, len(P), len(
            P), endpoint=False, dtype=int), Nb_Cycle, p=ProbaP)

        while temp[0] == 0:  # We assume that the first element of P is the zero power element
            temp = rng.choice(np.linspace(0, len(P), len(P), endpoint=False, dtype=int), Nb_Cycle, p=ProbaP)
        P_Final_calib=np.array([P_calib[i] for i in temp])
        P_Final=np.array([P[i] for i in temp])
else:
    print('This experiment will consist of a series of {} random cycles'.format(Pos.shape[0]))   
#############################
# Initialisation of laser
#############################
Laser = las.LaserControl('COM8', 'COM17', 0.5)

InstrumentsPara['Laser'] = Laser.parameterDict
print('Initialised Laser')
#############################
# Initialisation of pulse picker
#############################

pp = picker.PulsePicker("USB0::0x0403::0xC434::S09748-10A7::INSTR")
InstrumentsPara['Pulse picker'] = pp.parameterDict
print('Initialised pulse picker')

#############################
# Initialisation of the Conex Controller
#############################
if 'ControlConex' in sys.modules:
    x_axis = Transla.ConexController('COM12')
    y_axis = Transla.ConexController('COM13')
    print('Initialised rough translation stage')

elif 'ControlPiezoStage' in sys.modules:
    piezo = Transla.PiezoControl('COM15')
    x_axis = Transla.PiezoAxisControl(piezo, 'y',3)
    y_axis = Transla.PiezoAxisControl(piezo, 'z',3)
    print('Initialised piezo translation stage')


#############################
# Initialisation of the EMCCD
#############################

camera = EMCCD.LightFieldControl('ML')
FrameTime = camera.GetFrameTime()
ExposureTime = camera.GetExposureTime()
NumberOfFrame = camera.GetNumberOfFrame()
camera.SetEMGain(1)
InstrumentsPara['PI EMCCD'] = camera.parameterDict
print('Initialised EMCCD')

#############################
# Initialisation of the shutter
#############################

FM = shutter.FlipMount("37007726",'Shutter')
FM_ND = shutter.FlipMount("37007725",'ND05') # state 1 is the one with the ND
InstrumentsPara['FlipMount']=FM.parameterDict | FM_ND.parameterDict
print('Initialised Flip mount')


#############################
# Preparation of the directory
#############################
print('Directory staging, please check other window')
DirectoryPath = FileControl.PrepareDirectory(GeneralPara, InstrumentsPara)
pd.DataFrame(Pos).to_csv(DirectoryPath+'/Position.csv')


#############################
# TimeTrace loop
#############################
print('')
MesNumber = np.linspace(0, Pos.shape[0], Pos.shape[0], endpoint=False)
IteratorMes = np.nditer(MesNumber, flags=['f_index'])

CycNumber = np.linspace(0, Nb_Cycle, Nb_Cycle, endpoint=False)
IteratorCyc = np.nditer(CycNumber, flags=['f_index'])

Laser.SetStatusShutterTunable(1)
FM.ChangeState(0)


for k in IteratorMes:

#############################
# Generation of the folder and measurement prep
#############################
    print('Measurement number:{}'.format(MesNumber[IteratorMes.index]))
    TempDirPath = DirectoryPath+'/Mes'+str(MesNumber[IteratorMes.index])+'x='+str(np.round(
        Pos[IteratorMes.index, 0], 2))+'y='+str(np.round(Pos[IteratorMes.index, 1], 2))
    os.mkdir(TempDirPath)

    camera.SetSaveDirectory(TempDirPath.replace('/',"\\"))
    
    x_axis.MoveTo(Pos[IteratorMes.index, 0])
    y_axis.MoveTo(Pos[IteratorMes.index, 1])

#############################
# Power/Time cycle generation
#############################
    # Intensity/Power Cycle generation
    t_cyc = rng.choice(t, Nb_Cycle, p=ProbaT)
    # First we generate an array of cycle which only contains index for the moment
    temp = rng.choice(np.linspace(0, len(P), len(
        P), endpoint=False, dtype=int), Nb_Cycle, p=ProbaP)

    while temp[0] == 0:  # We assume that the first element of P is the zero power element
        temp = rng.choice(np.linspace(0, len(P), len(P), endpoint=False, dtype=int), Nb_Cycle, p=ProbaP)

    if OnlyOneConfig==True:
        t_cyc= T_final
        p_cyc_calib = P_Final_calib
        p_cyc = P_Final
    else:
        p_cyc_calib = np.array([P_calib[i] for i in temp])
        p_cyc = np.array([P[i] for i in temp])


    T_tot = np.sum(t_cyc)

#############################
# Camera setting adjustement
#############################
    NbFrameCycle = np.ceil((T_tot+StabilityTime_Begin+2*StabilityTime_End+StabilityTime_Reset+5*0.3)/FrameTime)
    camera.SetNumberOfFrame(NbFrameCycle)
    print('Time cycle:{}'.format(t_cyc))
    print('Power cycle:{}'.format(p_cyc))
    print('Real Power cycle:{}'.format(p_cyc_calib))
    print('Total time={}'.format(T_tot+T_tot+StabilityTime_Begin+StabilityTime_End))

    
    t_sync=np.zeros(len(t_cyc)) #Create timing parameter

#############################
# Stability time at the begining 
#############################
    print('Probe begin')
    FM_ND.ChangeState(1)
    camera.SetEMGain(EmGainProbe)
    FM.ChangeState(1) # Launch acquisition
    camera.Acquire() 
    t0=time.time()

    if ProbeDiffDivRatio==False:
        pp.SetPower(PowerProbePulsePicker)
        time.sleep(StabilityTime_Begin)
    elif ProbeDiffDivRatio==True:
        DivRatioTemp=pp.GetDivRatio()
        for idx_DR,val_DR in enumerate(DivRatio) :
            pp.SetPower(PowerProbe[idx_DR])
            pp.SetDivRatio(val_DR)
            time.sleep(np.floor(StabilityTime_Begin*0.5))
        pp.SetDivRatio(DivRatioTemp)

    camera.SetEMGain(1)
#############################
# Reset time
#############################
    print('Reset time')
    FM.ChangeState(0)
    FM_ND.ChangeState(0)
    time.sleep(StabilityTime_Reset)
    FM.ChangeState(1)

#############################
#Power/Time  iteration
############################# 
   
    for j in IteratorCyc:
        print('Cycle {}: P={},t={}'.format(IteratorCyc.index,p_cyc[IteratorCyc.index],t_cyc[IteratorCyc.index]))
        if p_cyc[IteratorCyc.index] == 0:
            FM.ChangeState(0)
        elif p_cyc[IteratorCyc.index] != 0:
            FM.ChangeState(1)
            pp.SetPower(p_cyc_calib[IteratorCyc.index])
        t_sync[IteratorCyc.index]=time.time()-t0
        time.sleep(t_cyc[IteratorCyc.index])
    IteratorCyc.reset()


#############################
# Stability time at the end 
#############################

    FM_ND.ChangeState(1)
    FM.ChangeState(1)
    
    camera.SetEMGain(EmGainProbe)
    if ProbeDiffDivRatio==False:
        pp.SetPower(PowerProbePulsePicker)
    elif ProbeDiffDivRatio==True:
        DivRatioTemp=pp.GetDivRatio()
        for idx_DR,val_DR in enumerate(DivRatio) :
            pp.SetPower(PowerProbe[idx_DR])
            pp.SetDivRatio(val_DR)
            time.sleep(np.floor(StabilityTime_End*0.5))
        pp.SetDivRatio(DivRatioTemp)
    camera.WaitForAcq()

#############################
# Acq finished
#############################

    camera.SetEMGain(1)
    FM.ChangeState(0)
    FM_ND.ChangeState(0)
    # Save all the cycle in the folder
    temp = pd.DataFrame(
        {'Exposure Time': t_cyc, 'Power send': p_cyc, 'Power Pulse-picker': p_cyc_calib,'Sync':t_sync})
    temp.to_csv(TempDirPath+'/Cycle.csv')
    
    
Laser.SetStatusShutterTunable(0)
print('Experiment Done: beginning loading file')

def LoadData(Folder):
    # Compute wavelength
    try:
        temp = pd.read_csv(FolderCalibWavelength, sep='\t', decimal=',')
        print('Reading wavelength calibraton at : {}'.format(FolderCalibWavelength))
        a = temp.loc[:, 'a'].to_numpy()[0]
        b = temp.loc[:, 'b'].to_numpy()[0]
    except:
        print('Problem reading wavelength calibraton at : {}\n Taking default value'.format(FolderCalibWavelength))
        a = 2.339
        b = 470.069 
    PixelNumber = np.linspace(1, 1024, 1024)
    CenterPixel = Spectrograph_Center
    Wavelength = (PixelNumber-b)/a+CenterPixel

    Folder = glob.glob(Folder+'/Mes*')
    CycleStore = pd.DataFrame()
    DataTot = []
    for j in range(len(Folder)):
        
        File = glob.glob(Folder[j]+'/*[0-9].spe')
        if len(File)==0:
            File = glob.glob(Folder[j]+'/*.spe')
        DataRaw = sl.load_from_files(File)
        MetaData = pd.DataFrame(DataRaw.metadata)
        TimeI = MetaData.loc[:, 0].to_numpy()/(1E6)  # Time in ms

        DataTotTemp = pd.DataFrame(np.squeeze(
            DataRaw.data[:][:]), columns=Wavelength)
        DataTotTemp['Mes'] = j
        DataTotTemp['Time'] = TimeI
        DataTot.append(DataTotTemp)

        FileCycle = pd.read_csv(Folder[j]+'\Cycle.csv')
        CycleStore = pd.concat([CycleStore, FileCycle], axis=1)

    DataTot = pd.concat(DataTot).set_index(['Mes', 'Time'])
    return DataTot, CycleStore

Data, CycleStore = LoadData(DirectoryPath)

print('Finished loading, beginning compression')
Data.to_pickle(DirectoryPath+"/TimeTraceFull.pkl", compression='xz')
CycleStore.to_csv(DirectoryPath+'/BatchCycle.csv', index=False)