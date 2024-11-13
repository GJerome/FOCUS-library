USE_DUMMY = False

if USE_DUMMY:
    import ControlDummy as shutter
    import ControlDummy as las
    import ControlDummy as picker
    import ControlDummy as EMCCD
    import ControlDummy as Transla
    import ControlDummy as time
else:
    import ControlFlipMount as shutter
    import ControlLaser as las
    import ControlPulsePicker as picker
    import ControlEMCCD as EMCCD
    import ControlPiezoStage as Transla
    import time as time

import numpy as np
import pandas as pd
import os
import sys
import FileControl
import glob
import spe_loader as sl
import random 

def ParameterRead(ParameterFile):
    ParameterList={}
    with open(ParameterFile,'r') as ParaFile:
        for line in ParaFile:
            if line[0]!= '#':
                try:
                    ParameterList[line[0:line.index('=')]]=line[line.index('=')+1:].strip()
                except ValueError:
                    pass
    return ParameterList

class timeTraceRunner:
    def __init__(self, **kwargs):
        self.GeneralPara = kwargs
        if 'Nb_points' not in self.GeneralPara:
            raise ValueError('Parameters must contain the number of points [\'Nb_points\']')
        self.Nb_Points = GeneralPara['Nb_points']

    def initialize(self, start_x, end_x, start_y, end_y, FileDir):
        self.initializePiezo(start_x, end_x, start_y, end_y)
        self.initializeInstruments()
        self.initializeConex()
        self.initializeOutputDirectory(FileDir)

    #############################
    # Piezo parameter
    #############################
    def initializePiezo(self, start_x, end_x, start_y, end_y):
        x = np.linspace(start_x, end_x, int(np.floor(np.sqrt(self.Nb_Points))))
        y = np.linspace(start_y, end_y, int(np.ceil(np.sqrt(self.Nb_Points))))
        X, Y = np.meshgrid(x, y)
        self.Pos = np.stack([X.ravel(), Y.ravel()], axis=-1)
        index=random.sample(range(0, self.Pos.shape[0]), self.Pos.shape[0])
        self.Pos=self.Pos[index,:]
        self.GeneralPara['Nb_points']=self.Pos.shape[0]
        self.Nb_Points = self.Pos.shape[0]
        try:
            print('Number of Points:{}-{}\nDistance between points:\n\t x ={} \n\t y ={}'.format(self.Nb_Points,self.Pos.shape[0],x[1]-x[0], y[1]-y[0]))
        except IndexError:
            print('Number of Points:{}\n'.format(self.Pos.shape[0]))


    def initializeInstruments(self):
        self.InstrumentsPara = {}

        #############################
        # Initialisation of laser
        #############################
        self.Laser = las.LaserControl('COM8', 'COM17', 0.5)
        self.InstrumentsPara['Laser'] = self.Laser.parameterDict
        print('Initialised Laser')

        #############################
        # Initialisation of pulse picker
        #############################
        self.pp = picker.PulsePicker("USB0::0x0403::0xC434::S09748-10A7::INSTR")
        self.InstrumentsPara['Pulse picker'] = self.pp.parameterDict
        print('Initialised pulse picker')

        #############################
        # Initialisation of the EMCCD
        #############################
        self.camera = EMCCD.LightFieldControl('ML')
        self.FrameTime = self.camera.GetFrameTime()
        self.ExposureTime = self.camera.GetExposureTime()
        self.NumberOfFrame = self.camera.GetNumberOfFrame()
        self.camera.SetEMGain(1)
        self.InstrumentsPara['PI EMCCD'] = self.camera.parameterDict
        print('Initialised EMCCD')

        #############################
        # Initialisation of the shutter
        #############################
        self.FM = shutter.FlipMount("37007726")
        self.InstrumentsPara['FlipMount']=self.FM.parameterDict
        print('Initialised Flip mount')

    #############################
    # Initialisation of the Conex Controller
    #############################
    def initializeConex(self):
        if 'ControlConex' in sys.modules:
            self.x_axis = Transla.ConexController('COM12')
            self.y_axis = Transla.ConexController('COM13')
            print('Initialised rough translation stage')
        elif 'ControlPiezoStage' in sys.modules or USE_DUMMY:
            piezo = Transla.PiezoControl('COM15')
            self.x_axis = Transla.PiezoAxisControl(piezo, 'y',3)
            self.y_axis = Transla.PiezoAxisControl(piezo, 'z',3)
            print('Initialised piezo translation stage')

    #############################
    # Preparation of the directory
    #############################
    def initializeOutputDirectory(self, path):
        print('Directory staging, please check other window')
        out_dir = path
        #if USE_DUMMY:
        #    out_dir = path + '/output-dummy'
        if(not os.path.isdir(out_dir)):
            os.makedirs(out_dir)
        self.DirectoryPath = FileControl.PrepareDirectory(self.GeneralPara, self.InstrumentsPara)
        pd.DataFrame(self.Pos).to_csv(self.DirectoryPath+'/Position.csv')
        #self.camera.SetSaveDirectory(self.DirectoryPath.replace('/',"\\"))

    #############################
    # TimeTrace loop
    #############################
    def runTimeTrace(self,StabilityTime_Begin,StabilityTime_Reset,StabilityTime_End,
                            PowerProbePulsePicker,EmGainProbe, df_t_cyc, df_p_cyc, df_p_cyc_calib):
        '''The parameters are the following: 
        -df_t_cyc: list of the random time selected for one cycle
        -df_p_cyc: list of the random power selected for one cycle
        -df_p_cyc_calib: list of the random power selected for one cycle send to the pulse picker.'''

        MesNumber = np.linspace(0, self.Nb_Points, self.Nb_Points, endpoint=False)
        IteratorMes = np.nditer(MesNumber, flags=['f_index'])

        Nb_Cycle = len(df_t_cyc[0])
        CycNumber = np.linspace(0, Nb_Cycle, Nb_Cycle, endpoint=False)
        IteratorCyc = np.nditer(CycNumber, flags=['f_index'])

        self.Laser.SetStatusShutterTunable(1)
        self.FM.ChangeState(0)
        for k in IteratorMes:
            # Generation of the folder and measurement prep
            print('Measurement number:{}'.format(MesNumber[IteratorMes.index]))
            TempDirPath = self.DirectoryPath+'/Mes'+str(MesNumber[IteratorMes.index])+'x='+str(np.round(
                self.Pos[IteratorMes.index, 0], 2))+'y='+str(np.round(self.Pos[IteratorMes.index, 1], 2))
            
            if(not os.path.isdir(TempDirPath)):
                os.mkdir(TempDirPath)

            self.camera.SetSaveDirectory(TempDirPath.replace('/',"\\"))
            
            self.x_axis.MoveTo(self.Pos[IteratorMes.index, 0])
            self.y_axis.MoveTo(self.Pos[IteratorMes.index, 1])

            # Intensity/Power Cycles
            t_cyc = df_t_cyc[k]
            p_cyc = df_p_cyc[k]
            p_cyc_calib = df_p_cyc_calib[k]
            assert(len(t_cyc) == len(p_cyc) == len(p_cyc_calib) == Nb_Cycle)

            T_tot = np.sum(t_cyc)

            # Camera setting adjustement
            NbFrameCycle = NbFrameCycle = np.ceil((T_tot+StabilityTime_Begin+StabilityTime_End+StabilityTime_Reset)/self.FrameTime)
            self.camera.SetNumberOfFrame(NbFrameCycle)
            print('Time cycle:{}'.format(t_cyc.tolist()))
            print('Power cycle:{}'.format(p_cyc.tolist()))
            print('Real Power cycle:{}'.format(p_cyc_calib.tolist()))
            print('Total time={}'.format(T_tot+StabilityTime_Begin+StabilityTime_End+StabilityTime_Reset))

            #Create timing parameter
            t_sync=np.zeros(len(t_cyc))
            self.camera.SetEMGain(EmGainProbe)
            self.camera.Acquire()# Launch acquisition
            self.FM.ChangeState(1)  
            t0=time.time()

            ###############
            # Stability time beginning
            ###############
            print('Stability time beginning')
            self.pp.SetPower(PowerProbePulsePicker)
            time.sleep(StabilityTime_Begin)
            self.camera.SetEMGain(EmGainProbe)

            ###############
            # Reset  time
            ###############
            print('Reset time')
            self.FM.ChangeState(0)
            time.sleep(StabilityTime_Reset)
            self.FM.ChangeState(1)

            #############################
            #Power/Time  iteration
            #############################
                
            for j in IteratorCyc:
                print('Cycle {}: P={},t={}'.format(IteratorCyc.index,p_cyc[IteratorCyc.index],t_cyc[IteratorCyc.index]))
                if p_cyc[IteratorCyc.index] == 0:
                    self.FM.ChangeState(0)
                elif p_cyc[IteratorCyc.index] != 0:
                    self.FM.ChangeState(1)
                    self.pp.SetPower(p_cyc_calib[IteratorCyc.index])
                t_sync[IteratorCyc.index]=time.time()-t0
                time.sleep(t_cyc[IteratorCyc.index])
            IteratorCyc.reset()

            
            #############################
            # Stability time at the end 
            #############################

            
            print('Stability Time')
            self.FM.ChangeState(1)
            self.pp.SetPower(PowerProbePulsePicker)
            self.camera.SetEMGain(EmGainProbe)
            self.camera.WaitForAcq()

            #############################
            # Acq finished
            #############################

            self.FM.ChangeState(0)
            self.camera.SetEMGain(1)

            # Save all the cycle in the folder
            temp = pd.DataFrame(
                {'Exposure Time': t_cyc.tolist(), 'Power send': p_cyc.tolist(), 'Power Pulse-picker': p_cyc_calib.tolist(),'Sync':t_sync})
            temp.to_csv(TempDirPath+'/Cycle.csv')

        self.Laser.SetStatusShutterTunable(0)


def generateRandomParameters(Nb_Points, Nb_Cycle):
    ##############################################################
    # Parameter space and random choice
    ##############################################################

    ###################
    # RNG declaration
    ###################
    rng = np.random.default_rng()

    ###################
    # Proba density function Power
    ###################
    P = (0, 4.4, 10, 100, 800)  # power in uW
    P_calib = (500, 500,800, 2300, 6800)  # Power from the pp to reach values of P
    p1 = [0.3, 0.175, 0.175, 0.175, 0.175]
    ProbaP = p1

    ###################
    # Proba density function Time
    ###################
    t = (0.1, 1, 10, 100)  # time
    p1 = [0.3, 0.23, 0.23, 0.24]
    ProbaT = p1

    df_t_cyc = pd.DataFrame()
    df_p_cyc = pd.DataFrame()
    df_p_cyc_calib = pd.DataFrame()

    for k in range(Nb_Points):
        # Intensity/Power Cycle generation
        df_t_cyc[k] = rng.choice(t, Nb_Cycle, p=ProbaT)
        # First we generate an array of cycle which only contains index for the moment
        temp = rng.choice(np.linspace(0, len(P), len(P), endpoint=False, dtype=int), Nb_Cycle, p=ProbaP)
        while temp[0] == 0:  # We assume that the first element of P is the zero power element
            temp = rng.choice(np.linspace(0, len(P), len(P), endpoint=False, dtype=int), Nb_Cycle, p=ProbaP)
        df_p_cyc_calib[k] = np.array([P_calib[i] for i in temp])
        df_p_cyc[k] = np.array([P[i] for i in temp])

    return df_t_cyc, df_p_cyc, df_p_cyc_calib

def evaluateFitnessValues(FileDir):
    # Load experimental data
    DataTot, CycleStore = LoadDataFromFiles(FileDir)

    # Wavelength filter
    WavelengthFilter= [col for col in DataTot.columns if 600 <= col <= 900]
    TimeTraceU=DataTot[WavelengthFilter].sum(axis=1).unstack(level=0)
    Nb_pts=int(TimeTraceU.shape[1])

    Pos, p_cyc, TimeCycle, TimeSync,t_globalSync,StabilityTime_begin,StabilityTime_reset,StabilityTime_end = loadExperimentInfo(CycleStore, Nb_pts,FileDir)

    ts=np.zeros(Nb_pts,dtype=int)
    ts_b=np.zeros(Nb_pts,dtype=int)

    # Compute fitnesses
    fitness_values = np.zeros(Nb_pts)
    for i in range(Nb_pts):
        temp_df=TimeTraceU.iloc[:,i].dropna()
        #integrated_int=temp_df.sum()
        ts[i]=np.argmin(np.abs(temp_df.index-t_globalSync[i]))
        ts_b[i]=np.argmin(np.abs(temp_df.index-StabilityTime_begin))

        fitness_values[i] = temp_df.iloc[ts[i]+10:-10].mean(axis=0)/temp_df.iloc[10:ts_b[i]-10].mean(axis=0) # insert mean intensity of stability region as fitness value of measurement i
    print("# FITNESS VALUES #")
    print(fitness_values)
    return fitness_values

def generateNewSolutions(df_t_cyc, df_p_cyc, df_p_cyc_calib, fitness_values):
    # TODO - implement selection and variation step of evolutionary algorithm
    return df_t_cyc, df_p_cyc, df_p_cyc_calib

def loadExperimentInfo(CycleStore, Nb_pts,FileDir):

    #############################
    # Reading global parameters
    #############################
    para=ParameterRead(FileDir+'/ExperimentParameter.txt')
    try:
        StabilityTime_begin=float(para['Stability time begin '])
        StabilityTime_reset=float(para['Stability time reset'])
        StabilityTime_end=float(para['Stability time end '])
        if para['Probe DiffDivRatio']=='True':
            FrequencyProbe=80/pd.DataFrame((para['Div ratio probe used'][1:-1].split(',')),dtype=float)
        elif para['Probe DiffDivRatio']=='False':
            FrequencyProbe=pd.Series((para['Repetition rate'].split('.')[0]),dtype=float)/1E6
        Nb_ProbeFreq=len(FrequencyProbe)
    except:
        print('Could not read parameters, please check parameter file')
        StabilityTime_begin=10
        StabilityTime_reset=30
        StabilityTime_end=30

    #############################
    # Reading cycle info
    #############################

    p_cyc=pd.DataFrame(index=range(10), columns=range(Nb_pts))
    TimeSync=pd.DataFrame(index=range(10), columns=range(Nb_pts))
    TimeCycle=pd.DataFrame(index=range(10), columns=range(Nb_pts))
    t_globalSync=pd.Series(TimeSync.iloc[-1,:],index=range(Nb_pts))

    for i in range(Nb_pts):
        if i==0:
            p_cyc.iloc[:,i]=CycleStore.loc[:,'Power send']
            TimeCycle.iloc[:,i]=CycleStore.loc[:,'Exposure Time']
            TimeSync.iloc[:,i]=CycleStore.loc[:,'Sync']

        else:
            p_cyc.iloc[:,i]=CycleStore.loc[:,'Power send.{}'.format(i)]
            TimeCycle.iloc[:,i]=CycleStore.loc[:,'Exposure Time.{}'.format(i)]
            TimeSync.iloc[:,i]=CycleStore.loc[:,'Sync.{}'.format(i)]
        t_globalSync[i]=t_globalSync[i]+TimeCycle.iloc[-1,i]

    Pos=pd.read_csv(FileDir+'/Position.csv').iloc[:,1:].to_numpy()

    return Pos, p_cyc, TimeCycle, TimeSync,t_globalSync,StabilityTime_begin,StabilityTime_reset,StabilityTime_end
    
def LoadDataFromFiles(FileDir,FolderCalibWavelength,WaveCenter):
    ## We first need to generate the datafile 
        # Compute wavelength
    try:
        temp = pd.read_csv(FolderCalibWavelength, sep='\t', decimal=',')
        print('Reading wavelength calibraton at : {}'.format(FolderCalibWavelength))
        a = temp.loc[:, 'a'].to_numpy()
        b = temp.loc[:, 'b'].to_numpy()
    except:
        print('Problem reading wavelength calibraton at : {}\n Taking default value'.format(FolderCalibWavelength))
        a = 2.354381287460651
        b = 490.05901104995587
    PixelNumber = np.linspace(1, 1024, 1024)
    CenterPixel = WaveCenter
    Wavelength = (PixelNumber-b)/a+CenterPixel

    Folder = glob.glob(FileDir+'/Mes*')
    CycleStore = pd.DataFrame()
    DataTot = []
    for j in range(len(Folder)):
        print('\r Reading Files:{} %'.format(
            np.round(100*j/len(Folder), 1)), end='', flush=True)
        File = glob.glob(Folder[j]+'/*[0-9].spe')
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
    print('Finished loading, beginning compression')

    DataTot.to_pickle("./TimeTraceFull.pkl", compression='xz')
    CycleStore.to_csv('./BatchCycle.csv', index=False)
    
  
    FileNameTimeTraceFull=FileDir+'/TimeTraceFull.pkl'
    FileNameCycle=FileDir+'/BatchCycle.csv'
    #print("Loading data from", FileNameTimeTraceFull, "and", FileNameCycle)
    #TimeTraceFull=pd.read_pickle(FileNameTimeTraceFull,compression='xz')
    #Cycle_info=pd.read_csv(FileNameCycle)
    print("Data loaded")
    return DataTot, CycleStore

# from DataScrapperV2
def LoadDataFromMeasurements():
    # Compute wavelength
    a=2.339373103584057
    b=470.06854115746376
    PixelNumber = np.linspace(1, 1024, 1024)
    CenterPixel = 700
    Wavelength = (PixelNumber-b)/a+CenterPixel

    Folder = glob.glob('./Mes*')
    CycleStore = pd.DataFrame()
    DataTot = []
    for j in range(len(Folder)):
        File = glob.glob(Folder[j]+'/*spe')
        DataRaw = sl.load_from_files(File)
        MetaData = pd.DataFrame(DataRaw.metadata)
        TimeI = MetaData.loc[:, 0].to_numpy()/(1E6)  # Time in ms

        DataTotTemp = pd.DataFrame(np.squeeze(
            DataRaw.data[:][:]), columns=Wavelength)
        DataTotTemp['Mes'] = j
        DataTotTemp['Time'] = TimeI
        DataTot.append(DataTotTemp)

        FileCycle = pd.read_csv(Folder[j]+'/Cycle.csv')
        CycleStore = pd.concat([CycleStore, FileCycle], axis=1)

    DataTot = pd.concat(DataTot).set_index(['Mes', 'Time'])

    #Data.to_pickle("./TimeTraceFull.pkl", compression='xz')
    #CycleStore.to_csv('./BatchCycle.csv', index=False)

    return DataTot, CycleStore


if __name__ == '__main__':

    if not USE_DUMMY:
        os.system('cls')

    #############################
    # Optimization parameters
    #############################
    generations_budget = 10

    #############################
    # TimeTrace parameters
    #############################
    Nb_Points = 50  # Number of position for the piezo
    Nb_Cycle = 10  # Number of cycle during experiment
    DistancePts = 10

    StabilityTime_Begin=20# Time for which it will probe at the beginning of the cycle
    StabilityTime_Reset=30# The beam will then be block for this amount of time so that the sample 'reset'
    StabilityTime_End = 30# Time for which it will probe at the end of the cycle
    #The total time is then StabilityTime_Begin+ StabilityTime_Reset+ StabilityTime_End+Time of cycle
    PowerProbePulsePicker=500
    EmGainProbe=10

    Spectrograph_slit=10 # This is just for record not actually setting it up
    Spectrograph_Center=750# This is just for record not actually setting it up

    FolderCalibWavelength='//sun/garnett/home-folder/gautier/Femto-setup/Data/0.Calibration/Spectrometer.csv'

    GeneralPara = {'Experiment name': ' ML_Anton', 'Nb_points':Nb_Points,
               'Stability time begin ': StabilityTime_Begin,'Stability time reset':StabilityTime_Reset,
               'Stability time end ': StabilityTime_End,
               'Power probe ':PowerProbePulsePicker,'Em Gain probe':EmGainProbe,'Spectrograph slit width':Spectrograph_slit,'Spectrograph center Wavelength':Spectrograph_Center,
               'Note': 'The SHG unit from Coherent was used'}

    FileDir = '/export/scratch2/constellation-data/EnhancePerov/output-dummy/'

    df_t_cyc, df_p_cyc, df_p_cyc_calib = generateRandomParameters(Nb_Points, Nb_Cycle) #generate random initial population
    
    
    start_x = 5
    end_x = 80
    start_y = 5
    end_y = 80    

    ####
    #Initialisation of the Timetrace object
    ####
    runner = timeTraceRunner(**GeneralPara) # This object allow to run the timetrace, load the data, ...
    runner.initialize(start_x, end_x, start_y, end_y, FileDir)

    
    
    number_of_generations = 0 
    while number_of_generations < generations_budget:  # generational loop
        print("################")
        print("# GENERATION",number_of_generations,"#")
        print("################")

        # run the experiment
        runner.runTimeTrace(StabilityTime_Begin,StabilityTime_Reset,StabilityTime_End,
                            PowerProbePulsePicker,EmGainProbe, df_t_cyc, df_p_cyc, df_p_cyc_calib)
        
        # calculate fitness values
        FolderCalibWavelength='//sun/garnett/home-folder/gautier/Femto-setup/Data/0.Calibration/Spectrometer.csv'
        fitness_values = evaluateFitnessValues(runner.DirectoryPath,FolderCalibWavelength,Spectrograph_Center)
       
        # update population
        df_t_cyc, df_p_cyc, df_p_cyc_calib = generateNewSolutions(df_t_cyc, df_p_cyc, df_p_cyc_calib, fitness_values)

        number_of_generations += 1

