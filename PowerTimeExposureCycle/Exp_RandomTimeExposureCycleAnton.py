USE_DUMMY = False
import os
import sys
os.system('cls')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 

import numpy as np
import pandas as pd
import glob
import random 
import spe_loader as sl

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

import FileControl


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

    def initialize(self, start_x, end_x, start_y, end_y, BeamRadius,FileDir):
        self.initializePiezo(start_x, end_x, start_y, end_y,BeamRadius)
        self.initializeInstruments()
        self.initializeConex()
        self.initializeOutputDirectory(FileDir)

    #############################
    # Piezo parameter
    #############################
    def DistanceTwoPoint(pointA, pointB):
        return np.sqrt(np.sum((pointA - pointB)**2, axis=0))

    def DistanceArray(pointA, pointsB):
        return np.sqrt(np.sum((pointA - pointsB)**2, axis=1))
    
    def initializePiezo(self, start_x, end_x, start_y, end_y,BeamRadius):
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
        self.Pos = np.stack([X.ravel(), Y.ravel()], axis=-1)
        index=random.sample(range(0, self.Pos.shape[0]), self.Pos.shape[0])
        self.Pos=self.Pos[index,:]
        self.GeneralPara['Nb_points']=self.Pos.shape[0]
        self.Nb_Points = self.Pos.shape[0]

        PosFiltered=np.empty(self.Pos.shape)
        for index in range(self.Nb_Points):
            if index==0:
                PosFiltered[index,:]=self.Pos[0,:]
                self.Pos=np.delete(self.Pos,0,0)
            else:
                if self.DistanceTwoPoint(PosFiltered[index-1,:],self.Pos[0,:])<BeamRadius:            
                    a=np.argmax(self.DistanceArray(PosFiltered[index-1,:],self.Pos)>BeamRadius)
                    PosFiltered[index,:]=self.Pos[a,:]
                    self.Pos=np.delete(self.Pos,a,0)
                    if a==0:
                        print('Could not find a point not within the beam avoidance radius.')
                else:
                    PosFiltered[index,:]=self.Pos[0,:]
                    self.Pos=np.delete(self.Pos,0,0)
    
        self.Pos=PosFiltered
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



def evaluateFitnessValues(FileDir,Time_Min,Time_Max):
    # Load experimental data
    DataTot, CycleStore,Nb_pts = LoadDataFromFiles(FileDir)
    # Load experimental settings
    Pos, p_cyc, TimeCycle, TimeSync,t_globalSync,StabilityTime_begin,StabilityTime_reset,StabilityTime_end = loadExperimentInfo(CycleStore, Nb_pts,FileDir)

    M_all=pd.DataFrame(index=range(Nb_pts),columns=['Enhancement','error','S1','S2'])


    # Compute fitnesses
    fitness_values = np.zeros(Nb_pts)
    for i in range(Nb_pts):
        # We first  compute the time at which the stability time begin and end for each cycles
        # The way the timing work is the following. The first timestamp  correspond to the time between the first spectra and the second step in a sequence.
        # So if the StabilityTime_begin=10,StabilityTime_reset=10 and the first step is 1s then the first timestamp will occur at t[0]=21s
        # All other Timestamp occurs at each step of the cycles
        ts_end=np.argmin(np.abs(DataTot.index-t_globalSync-StabilityTime_end))
        ts_begin=np.argmin(np.abs(DataTot.index-StabilityTime_begin))

        #We then cut the data accordingly and put them on the samereference frame i.e time between zero and he end of their associated stability time
        dataFit_End=DataTot.loc[i,:,:].loc[DataTot.loc[i,:,:].index>DataTot.loc[i,:,:].index[ts_end],:]
        dataFit_End=pd.DataFrame(dataFit_End.to_numpy(),index=(dataFit_End.index[-1]-dataFit_End.index)[::-1],columns=dataFit_End.columns)
        dataFit_Begin=DataTot.loc[i,:,:].loc[DataTot.loc[i,:,:].index<DataTot.loc[i,:,:].index[ts_begin],:]

        ##########################
        # Use rolling mean to remove noise 
        ##########################
        print('{}/{} Rolling mean computation'.format(i+1,Nb_pts))
        FitDataResult_End = pd.DataFrame(index=dataFit_End.index,columns=dataFit_End.columns)
        for j in dataFit_End.index:
            FitDataResult_End.loc[j,:]=dataFit_End.loc[j,:].rolling(10,min_periods=1).mean()
        FitDataResult_End['Mes']=i
        FitAll_End=pd.concat([FitAll_End,FitDataResult_End],axis=0)
            

        FitDataResult_Begin = pd.DataFrame(index=dataFit_Begin.index,columns=dataFit_Begin.columns)
        for j in dataFit_Begin.index:
            FitDataResult_Begin.loc[j,:]=dataFit_Begin.loc[j,:].rolling(10,min_periods=1).mean()
        FitDataResult_Begin['Mes']=i
        FitAll_Begin=pd.concat([FitAll_Begin,FitDataResult_Begin],axis=0)
        
        ##########################
        # Interpolate to the same timescale
        ##########################

        print('{}/{} Interpolation to the same timebase'.format(i+1,Nb_pts))
        if (dataFit_End.index[-1]-dataFit_End.index[0])>(dataFit_Begin.index[-1]-dataFit_Begin.index[0]):
            time_int=np.abs(dataFit_Begin.index-dataFit_Begin.index[-1])[::-1]
            dataTemp_Interp=pd.DataFrame(FitDataResult_End.iloc[:,:-2],dtype='float64')
            dataFit_interp2=pd.DataFrame(np.interp(time_int,
                                    dataTemp_Interp.loc[(dataTemp_Interp.index)<=time_int[-1],:].index,
                                    dataTemp_Interp.loc[dataTemp_Interp.index<=time_int[-1],:].max(axis=1)),index=time_int)
            dataFit_interp1=pd.DataFrame(FitDataResult_Begin.max(axis=1).to_numpy(),index=time_int)
        else:
            time_int=np.abs(dataFit_End.index-dataFit_End.index[-1])[::-1]
            dataTemp_Interp=pd.DataFrame(FitDataResult_Begin.iloc[:,:-2],dtype='float64')
            dataFit_interp1=np.interp(time_int,
                                    dataTemp_Interp.loc[dataTemp_Interp.index<=time_int[-1],:].index,
                                    dataTemp_Interp.loc[dataTemp_Interp.index<=time_int[-1],:].max(axis=1))
            dataFit_interp2=pd.DataFrame(FitDataResult_Begin.max(axis=1).to_numpy(),index=time_int)
        
        M_all.loc[i,'EnhancementTime']=[dataFit_interp2.div(dataFit_interp1,axis=0)]
        M_all.loc[i,'S1']=[dataFit_interp1]
        M_all.loc[i,'S2']=[dataFit_interp2]
        M_all.loc[i,'error']=dataFit_interp2.div(dataFit_interp1).std(axis=0).to_numpy()



        fitness_values[i] =(M_all.loc[j,'S2'][0].loc[(M_all.loc[j,'S2'][0].index>Time_Min) & (M_all.loc[j,'S2'][0].index<Time_Max),0]
                            /M_all.loc[j,'S1'][0].loc[(M_all.loc[j,'S1'][0].index>Time_Min) & (M_all.loc[j,'S1'][0].index<Time_Max),0]).mean()
     
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
    
    # We asssume that we probe with a single frequency
    StabilityTime_begin=float(para['Stability time begin '])
    StabilityTime_reset=float(para['Stability time reset'])
    StabilityTime_end=float(para['Stability time end '])
 

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
    print("Dataset loaded")
    return DataTot, CycleStore, len(Folder)

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

    BeamRadius=10 # Minimum distance betweensuccesive point in um

    StabilityTime_Begin=20# Time for which it will probe at the beginning of the cycle
    StabilityTime_Reset=30# The beam will then be block for this amount of time so that the sample 'reset'
    StabilityTime_End = 30# Time for which it will probe at the end of the cycle
    #The total time is then StabilityTime_Begin+ StabilityTime_Reset+ StabilityTime_End+Time of cycle
    PowerProbePulsePicker=500
    EmGainProbe=10

    Spectrograph_slit=10 # This is just for record not actually setting it up
    Spectrograph_Center=750# This is just for record not actually setting it up

    FolderCalibWavelength='//sun/garnett/home-folder/gautier/Femto-setup/Data/0.Calibration/Spectrometer.csv'

    GeneralPara = {'Experiment name': ' ML_Anton', 'Nb_points':Nb_Points,'Beam avoidance radius':BeamRadius,
               'Stability time begin ': StabilityTime_Begin,'Stability time reset':StabilityTime_Reset,'Stability time end ': StabilityTime_End,
               'Power probe ':PowerProbePulsePicker,'Em Gain probe':EmGainProbe,'Spectrograph slit width':Spectrograph_slit,'Spectrograph center Wavelength':Spectrograph_Center,
               'Note': 'The SHG unit from Coherent was used and ND05 for probe'}

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
    runner.initialize(start_x, end_x, start_y, end_y,BeamRadius, FileDir)

    
    
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

