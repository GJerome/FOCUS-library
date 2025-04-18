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
import ControlThorlabsShutter as ThorlabsShutter
import ControlLaser as las
import ControlPulsePicker as picker
import ControlEMCCD as EMCCD
import FileControl
import ControlPiezoStage as Transla
import ControlFilterWheel as FW


#############################
# Global parameter
#############################


Nb_Points =4  # Number of position for the piezo

start_x =40
end_x = 79.5
start_y = 40
end_y = 79.5


Nb_Cycle = 10# Number of cycle during experiment

StabilityTime_Begin=30# Time for which it will probe at the beginning of the cycle
StabilityTime_Reset=30# The beam will then be block for this amount of time so that the sample 'reset'
StabilityTime_End = 30# Time for which it will probe at the end of the cycle
#The total time is then StabilityTime_Begin+ StabilityTime_Reset+ StabilityTime_End+Time of cycle

PowerProbePulsePicker=500
EmGainProbe=0


EachStepDifferentProbaPower=False
FileProbaPower='./PowerTimeExposureCycle/BestPropaPStep_20MHz_25-02-01-B4P9-ML-20MHz_Time0to10s.csv'

EachStepDifferentProbaTime=False

OnlyOneConfig=True # Set it  to true so that it only probe with one config for Nb_points
OnlyOneConfig_Random=False # Set it  to true so that this config is random
OnlyOneConfig_UseCurentCalib=False #Not implemented yet, Set it  to true if you want it to use the current calibration or False if it should read the power send to the pulse picker from a file

ProbeDiffDivRatio= False #For the probing it set to true The staiblity time can be done at specific rep rate and power
DivRatio=[40,4]# A list containing the different div ratio
PowerProbe=[1800,500]# A list containing the power to use to probe

Spectrograph_slit=50 # This is just for record not actually setting it up
Spectrograph_Center=700# This is just for record not actually setting it up

FolderCalibWavelength='//sun/garnett/home-folder/gautier/Femto-setup/Data/0.Calibration/Spectrometer.csv'
BeamRadius=20

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
               'Power probe ':PowerProbePulsePicker,'Em Gain probe':EmGainProbe,
               'Spectrograph slit width':Spectrograph_slit,'Spectrograph center Wavelength':Spectrograph_Center}
if ProbeDiffDivRatio==True:               
    GeneralPara.update({'Probe DiffDivRatio':ProbeDiffDivRatio,'Div ratio probe used':DivRatio,'Power probe div ratio':PowerProbe})
               
GeneralPara.update({'Note': 'The SHG unit from Coherent was used and ND1 for probe'})

InstrumentsPara = {}
##############################################################
# Parameter space and random choice
##############################################################

###################
# Proba density function Power
###################
P = (0, 4.4, 10, 100, 200)  # power in uW
#Value to reach on the powermeter (0,11,25,240,475)uW
P_calib = (500, 500,700, 1900, 2600)  # Power from the pp to reach values of P #20MHz
#P_calib = (500, 1600,2200, 7900, 15700) # Power from the pp to reach values of P #2.58MHz
#P_calib = (500, 600,1100, 3500, 5200) # Power from the pp to reach values of P #2.58MHz same peak power

#P_calib = (500, 1400,2000, 6100, 9300)  # Power from the pp to reach values of P #5MHz
#P_calib = (500, 1700,2400, 9400, 17500)  # Power from the pp to reach values of P #500kHz

if EachStepDifferentProbaPower==False:
    p0 = [0.2, 0.2, 0.2, 0.2, 0.2]
    p1 = [0.3, 0.12, 0.12, 0.16, 0.3]
    ProbaP = p0

    GeneralPara['Power cycle']=P
    GeneralPara['Power Calib']=P_calib
    GeneralPara['Probability table power']=ProbaP
else: 
    ProbaP_step=pd.read_csv(FileProbaPower,usecols=range(6)[1:6])
    print('Probability for each step: ')
    print(ProbaP_step)
    GeneralPara['Power cycle']=ProbaP_step.columns.astype(np.float64).to_numpy()
    GeneralPara['Power Calib']=P_calib
    GeneralPara['Probability table power']=ProbaP_step

###################
# Proba density function Time
###################
t = (0.1, 1, 10, 100)  # time

p0 = [0.25, 0.25, 0.25, 0.25]
p1 = [0, 0.30, 0.35, 0.35]
ProbaT = p0

GeneralPara['Time cycle']=t
GeneralPara['Probability table time']=ProbaT
###################
# RNG declaration
###################
rng = np.random.default_rng()

if OnlyOneConfig==True:
    if OnlyOneConfig_Random==False:
        FileConfig='./PowerTimeExposureCycle/PowerTimeCycles/BestCycle_Gen3_25-03-01MlAnton.csv'
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

camera = EMCCD.LightFieldControl('ML2')
FrameTime = camera.GetFrameTime()
ExposureTime = camera.GetExposureTime()
NumberOfFrame = camera.GetNumberOfFrame()
camera.SetEMGain(1)
InstrumentsPara['PI EMCCD'] = camera.parameterDict
print('Initialised EMCCD')

#############################
# Initialisation of the shutter
#############################

FM = ThorlabsShutter.ShutterControl("68800883",'Shutter')
FM_ND = shutter.FlipMount("37007725",'ND1') # state 1 is the one with the ND
InstrumentsPara['FlipMount']=FM.parameterDict | FM_ND.parameterDict
print('Initialised Flip mount')

FilterWheel = FW.FilterWheel('COM18')
InstrumentsPara['FilterWheel'] = FilterWheel.parameterDict


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

FM.SetClose()
Laser.SetStatusShutterTunable(1)



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
    if OnlyOneConfig==True:
        t_cyc= T_final
    # First we generate an array of cycle which only contains index for the moment
    if EachStepDifferentProbaPower==False:

        temp = rng.choice(np.linspace(0, len(P), len(
            P), endpoint=False, dtype=int), Nb_Cycle, p=ProbaP)

        while temp[0] == 0:  # We assume that the first element of P is the zero power element
            temp = rng.choice(np.linspace(0, len(P), len(P), endpoint=False, dtype=int), Nb_Cycle, p=ProbaP)
    else:
        print('Generating cycle from user defined probability')
        temp=np.zeros([Nb_Cycle],dtype=int)
        for i in range(Nb_Cycle):
            temp[i] = int(rng.choice(np.linspace(0, len(P), len(P), endpoint=False, dtype=int), 1, p=ProbaP_step.iloc[i,:].to_numpy()))

    if OnlyOneConfig==True:
        p_cyc_calib = P_Final_calib
        p_cyc = P_Final
    else:
        p_cyc_calib = np.array([P_calib[i] for i in temp])
        p_cyc = np.array([P[i] for i in temp])


    T_tot = np.sum(t_cyc)

#############################
# Camera setting adjustement
#############################
    NbFrameCycle = np.ceil((T_tot+StabilityTime_Begin+StabilityTime_End+StabilityTime_Reset+3.6)/FrameTime)
    camera.SetNumberOfFrame(NbFrameCycle)
    print('Time cycle:{}'.format(t_cyc))
    print('Power cycle:{}'.format(p_cyc))
    print('Real Power cycle:{}'.format(p_cyc_calib))
    print('Total time={}'.format(T_tot+StabilityTime_Begin+StabilityTime_End+StabilityTime_Reset))

    
    t_sync=np.zeros(len(t_cyc)) #Create timing parameter

#############################
# Stability time at the begining 
#############################
    print('Probe begin')
    FM_ND.ChangeState(1)
    FilterWheel.set_position(1)
    if EmGainProbe!=0:
        camera.SetEMGain(EmGainProbe)
    FM.SetOpen() # Launch acquisition
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
    if EmGainProbe!=0:
        camera.SetEMGain(1)
#############################
# Reset time
#############################
    print('Reset time')
    FM.SetClose()
    FM_ND.ChangeState(0)
    time.sleep(StabilityTime_Reset)
    FM.SetOpen()
    FilterWheel.set_position(2)
#############################
#Power/Time  iteration
############################# 
   
    for j in IteratorCyc:
        print('Cycle {}: P={},t={}'.format(IteratorCyc.index,p_cyc[IteratorCyc.index],t_cyc[IteratorCyc.index]))
        if p_cyc[IteratorCyc.index] == 0:
            FM.SetClose()
        elif p_cyc[IteratorCyc.index] != 0:
            FM.SetOpen()
            pp.SetPower(p_cyc_calib[IteratorCyc.index])
        t_sync[IteratorCyc.index]=time.time()-t0
        time.sleep(t_cyc[IteratorCyc.index])
    IteratorCyc.reset()

    print('Probe end')
#############################
# Stability time at the end 
#############################

    FM_ND.ChangeState(1)
    FilterWheel.set_position(1)
    FM.SetOpen()
    if EmGainProbe!=0:
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
    if EmGainProbe!=0:
        camera.SetEMGain(1)
    FM.SetClose()
    FM_ND.ChangeState(0)
    # Save all the cycle in the folder
    temp = pd.DataFrame(
        {'Exposure Time': t_cyc, 'Power send': p_cyc, 'Power Pulse-picker': p_cyc_calib,'Sync':t_sync})
    temp.to_csv(TempDirPath+'/Cycle.csv')
    
    
Laser.SetStatusShutterTunable(0)
print('Experiment Done: beginning loading file')

def LoadData(FileDir):
    # Compute wavelength
    try:
        temp = pd.read_csv(FolderCalibWavelength, sep='\t', decimal=',')
        print('Reading wavelength calibraton at : {}'.format(FolderCalibWavelength))
        a = temp.loc[:, 'a'].to_numpy()[0]
        b = temp.loc[:, 'b'].to_numpy()[0]
    except:
        print('Problem reading wavelength calibraton at : {}\n Taking default value'.format(FolderCalibWavelength))
        a = 2.354381287460651
        b = 490.05901104995587
    PixelNumber = np.linspace(1, 1024, 1024)
    CenterPixel = Spectrograph_Center
    Wavelength = (PixelNumber-b)/a+CenterPixel

    Folder = sorted(glob.glob(FileDir+'/Mes*'),key=lambda x: float(x[x.find('Mes')+3:x.find('x')]))
    CycleStore = pd.DataFrame()
    DataTot = pd.DataFrame(columns=list(Wavelength)+['Time','Mes'])
    for j in range(len(Folder)):
        print('\r Reading Files:{} %'.format(
            np.round(100*j/len(Folder), 1)), end='', flush=True)
        File = glob.glob(Folder[j]+'/*.spe')
        DataRaw = sl.load_from_files(File)
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

        FileCycle = pd.read_csv(Folder[j]+'\Cycle.csv')
        FileCycle['Mes']=j
        CycleStore = pd.concat([CycleStore, FileCycle], axis=0)

    CycleStore=CycleStore.drop(labels='Unnamed: 0', axis=1)
    
    return DataTot, CycleStore

Data, CycleStore = LoadData(DirectoryPath)

print('Finished loading, beginning compression')
Data.to_pickle(DirectoryPath+"/TimeTraceFull.pkl", compression='xz')
CycleStore.to_csv(DirectoryPath+'/BatchCycle.csv', index=False)