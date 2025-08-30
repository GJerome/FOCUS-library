UseBothRoughAndFineTransla=True

import random
import spe_loader as sl
import glob
import pandas as pd
import numpy as np
import sys
import os
import shutil
import time as time
from scipy.integrate import simpson
import scipy.constants as cst
USE_DUMMY = False
os.system('cls')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


if USE_DUMMY:
    import ControlDummy as shutter
    import ControlDummy as ThorlabsShutter
    import ControlDummy as las
    import ControlDummy as picker
    import ControlDummy as EMCCD
    import ControlDummy as Transla
    import ControlDummy as time
    import ControlDummy as FilterWheel
    if UseBothRoughAndFineTransla==True:
        import ControlDummy as RoughTransla
else:
    import ControlFilterWheel as FilterWheel
    import ControlFlipMount as shutter
    import ControlThorlabsShutter as ThorlabsShutter
    import ControlLaser as las
    import ControlPulsePicker as picker
    import ControlEMCCD as EMCCD
    import ControlPiezoStage as Transla
    import ML_Tools
    import ControlKymera as spectrolib
    if UseBothRoughAndFineTransla==True:
        import ControlConex as RoughTransla

import FileControl


#############################
# Custom function
#############################

def ParameterRead(ParameterFile):
    ParameterList = {}
    with open(ParameterFile, 'r') as ParaFile:
        for line in ParaFile:
            if line[0] != '#':
                try:
                    ParameterList[line[0:line.index(
                        '=')]] = line[line.index('=')+1:].strip()
                except ValueError:
                    pass
    return ParameterList


def DistanceTwoPoint(pointA, pointB):
    return np.sqrt(np.sum((pointA - pointB)**2, axis=0))


def DistanceArray(pointA, pointsB):
    return np.sqrt(np.sum((pointA - pointsB)**2, axis=1))

#############################
#
#############################


class timeTraceRunner:
    def __init__(self, **kwargs):
        self.GeneralPara = kwargs
        if 'Nb_points' not in self.GeneralPara:
            raise ValueError(
                'Parameters must contain the number of points [\'Nb_points\']')
        self.Nb_points_Generation=self.GeneralPara['Nb_points_Generation']
        

    def initialize(self, start_x_rough, start_y_rough, BeamRadius,Coeff,SpacingBetweenRough_p,FileDir,PointsCalib):
        self.initializePos(generations_budget,self.Nb_points_Generation,self.GeneralPara['Nb_points_piezo'],
                                     Coeff,PointsCalib,BeamRadius=BeamRadius,
                                     startX_rough=start_x_rough,startY_rough=start_y_rough,
                                     SpacingBetweenRough=SpacingBetweenRough_p)
        self.initializeInstruments()
        self.initializeTranslation()
        self.initializeOutputDirectory(FileDir)

    #############################
    # Position paramter
    #############################

    def initializePos(self,generations_budget,Nb_Points_Generation,Nb_points_Piezo,
                                     Coeff,PointsCalib,BeamRadius,
                                     startX_rough,startY_rough,SpacingBetweenRough):

        self.Pos=ML_Tools.Generate_RandomPositionRoughFine(generations_budget,Nb_Points_Generation,
                                                           Nb_points_Piezo,
                                     Coeff,PointsCalib,BeamRadius,
                                     startX_rough,startY_rough,SpacingBetweenRough)
        
        self.GeneralPara['Nb_points'] = self.Pos.loc[self.Pos['Generation']==0,:].shape[0]
        self.Nb_Points = self.Pos.loc[self.Pos['Generation']==0,:].shape[0]

        try:
            print('Number of Points:{}-{}\n'.format(self.Nb_Points, self.Pos.shape[0]))
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
        self.pp = picker.PulsePicker(
            "USB0::0x0403::0xC434::S09748-10A7::INSTR")
        self.InstrumentsPara['Pulse picker'] = self.pp.parameterDict
        print('Initialised pulse picker')

        #############################
        # Initialisation of the EMCCD
        #############################
        self.camera = EMCCD.LightFieldControl('ML2')
        self.FrameTime = self.camera.GetFrameTime()
        self.ExposureTime = self.camera.GetExposureTime()
        self.NumberOfFrame = self.camera.GetNumberOfFrame()
        # self.camera.SetEMGain(1)
        self.InstrumentsPara['PI EMCCD'] = self.camera.parameterDict
        print('Initialised EMCCD')

        #############################
        # Initialisation of the shutter
        #############################
        self.FM = ThorlabsShutter.ShutterControl("68800883", 'Shutter')
        # state 1 is the one with the ND
        self.FM_ND = shutter.FlipMount("37007725", 'ND1')
        self.InstrumentsPara['FlipMount'] = self.FM.parameterDict | self.FM_ND.parameterDict

        self.FilterWheel = FilterWheel.FilterWheel('COM18',False)
        self.FilterWheel.set_speed_mode('high')
        self.InstrumentsPara['FilterWheel'] = self.FilterWheel.parameterDict

        print('Initialised Flip mount and Filter wheel')

        #############################
        # Initialisation of the spectrometer
        #############################

        self.spectro = spectrolib.KymeraSpectrograph()
        self.InstrumentsPara['Spectrograph'] = self.spectro.parameterDict
        print('Initialised spectro')
        

    #############################
    # Initialisation of the Translation system
    #############################
    def initializeTranslation(self):
        if UseBothRoughAndFineTransla==False:
            if 'ControlConex' in sys.modules:
                self.x_axis = Transla.ConexController('COM12')
                self.y_axis = Transla.ConexController('COM13')
                self.InstrumentsPara['Rough Stage']=self.x_axis.parameterDict | self.y_axis.parameterDict 
                print('Initialised rough translation stage')
            elif 'ControlPiezoStage' in sys.modules or USE_DUMMY:
                piezo = Transla.PiezoControl('COM15')
                self.x_axis = Transla.PiezoAxisControl(piezo, 'y', 3)
                self.y_axis = Transla.PiezoAxisControl(piezo, 'z', 3)
                self.InstrumentsPara['PiezoStage']=piezo.parameterDict
                print('Initialised piezo translation stage')
        else:
            self.x_axis_Rough = RoughTransla.ConexController('COM12')
            self.y_axis_Rough = RoughTransla.ConexController('COM14')
            self.InstrumentsPara['Rough Stage']=self.x_axis_Rough.parameterDict | self.y_axis_Rough.parameterDict 

            piezo = Transla.PiezoControl('COM15')
            self.x_axis = Transla.PiezoAxisControl(piezo, 'y', 3)
            self.y_axis = Transla.PiezoAxisControl(piezo, 'z', 3)
            self.z_axis=Transla.PiezoAxisControl(piezo, 'x', 3)
            self.InstrumentsPara['PiezoStage']=piezo.parameterDict

    #############################
    # Preparation of the directory
    #############################
    def initializeOutputDirectory(self, path):
        print('Directory staging, please check other window')
        # out_dir = path
        # if USE_DUMMY:
        #    out_dir = path + '/output-dummy'
        # if(not os.path.isdir(out_dir)):
        #    os.makedirs(out_dir)
        self.DirectoryPath = FileControl.PrepareDirectory(
            self.GeneralPara, self.InstrumentsPara)
        pd.DataFrame(self.Pos).to_csv(self.DirectoryPath+'/Position.csv')

    #############################
    # TimeTrace loop
    #############################

    def runTimeTrace(self, StabilityTime_Begin, StabilityTime_Reset, StabilityTime_End,
                     PowerProbePulsePicker, EmGainProbe, sample_parameters,Generation,
                       FilterWheelPosCycle=2,TimeTransFilterWheel=1.6):

        if USE_DUMMY:
            return
        Pos_Generation=self.Pos.loc[self.Pos['Generation']==Generation,:]
        MesNumber = range(Pos_Generation.shape[0])
        IteratorMes = np.nditer(MesNumber, flags=['f_index'])

        Nb_Cycle = len(sample_parameters[0]['t_cyc'])
        CycNumber = range(Nb_Cycle)
        IteratorCyc = np.nditer(CycNumber, flags=['f_index'])

        self.Laser.SetStatusShutterTunable(1)
        
        for k in IteratorMes:
            self.FM.SetClose()


            #############
            # Moving 
            #############
            Pos_temp=Pos_Generation.iloc[IteratorMes.index,:]
            self.x_axis_Rough.MoveTo(Pos_temp['x_rough'])
            self.y_axis_Rough.MoveTo(Pos_temp['y_rough'])
            self.x_axis.MoveTo(Pos_temp['x_piezo'])
            self.y_axis.MoveTo(Pos_temp['y_piezo'])
            self.z_axis.MoveTo(Pos_temp['z_piezo'])

            #############
            # Intensity/Power Cycles
            ############# 
            t_cyc = sample_parameters[MesNumber[IteratorMes.index]]['t_cyc']
            p_cyc = sample_parameters[MesNumber[IteratorMes.index]]['p_cyc']
            p_cyc_calib = sample_parameters[k]['p_cyc_calib']

            assert (len(t_cyc) == len(p_cyc) == len(p_cyc_calib) == Nb_Cycle)

            T_tot = np.sum(t_cyc)

            t_sync = np.zeros(len(t_cyc))# Create timing parameter

            #############
            # Generation of the folder and measurement prep
            #############
            print('Measurement number:{}'.format(MesNumber[IteratorMes.index]))

            TempDirPath = self.DirectoryPath+'/Mes'+str(MesNumber[IteratorMes.index])+'x='+str(np.round(self.x_axis_Rough.GetPosition()+0.001* self.x_axis.GetPosition(),3))+'y='+str(np.round(self.y_axis_Rough.GetPosition()+0.001* self.y_axis.GetPosition(),3))

            if (not os.path.isdir(TempDirPath)):
                os.mkdir(TempDirPath)
            self.camera.SetSaveDirectory(TempDirPath.replace('/', "\\"))

            #############
            # Camera setting adjustement
            #############  
            NbFrameCycle =np.ceil(
                (T_tot+StabilityTime_Begin+StabilityTime_End+StabilityTime_Reset+3.6)/self.FrameTime)  # the 3.6s is due to the filter whell moving
            self.camera.SetNumberOfFrame(NbFrameCycle)
            if EmGainProbe != 0:
                # if not in low noise mode apply an EM gain
                self.camera.SetEMGain(EmGainProbe)

            #############
            # ND and FilterWheel placement
            ############# 
            self.FM_ND.ChangeState(1)
            self.FilterWheel.set_position(1)# Here we assume that the filter wheel at position 1 there is no nd
            
            #############
            # Print important info
            ############# 
            print('Pos x={} mm, y={}mm, z={}um'.format(np.round(self.x_axis_Rough.GetPosition()+0.001* self.x_axis.GetPosition(),4),
                                                   np.round(self.y_axis_Rough.GetPosition()+0.001* self.y_axis.GetPosition(),4),
                                                   np.round(self.z_axis.GetPosition(),2)))
            print('Time cycle:{}'.format(t_cyc.tolist()))
            print('Power cycle:{}'.format(p_cyc.tolist()))
            print('Real Power cycle:{}'.format(p_cyc_calib.tolist()))
            print('Total time={}'.format(T_tot+StabilityTime_Begin +
                  StabilityTime_End+StabilityTime_Reset))

            #############
            # Begin cycle
            #############
            self.FM.SetOpen()
            self.camera.Acquire()  # Launch acquisition
            t0 = time.time()

            ###############
            # Stability time beginning
            ###############
            print('\r'+ " " * 40, end='', flush=True)
            print('\r Stability time beginning', end='', flush=True)
            
            self.pp.SetPower(PowerProbePulsePicker)
            time.sleep(StabilityTime_Begin)
            if EmGainProbe != 0:
                self.camera.SetEMGain(EmGainProbe)

            ###############
            # Reset  time
            ###############
            print('\r'+ " " * 40, end='', flush=True)
            print('\r Reset time', end='', flush=True)
        
            self.FM.SetClose()
            self.FM_ND.ChangeState(0)
            time.sleep(StabilityTime_Reset)
            self.FilterWheel.set_position(FilterWheelPosCycle)
            self.FM.SetOpen()

            #############################
            # Power/Time  step iteration
            #############################
            for j in IteratorCyc:
                print('\r'+ " " * 40, end='', flush=True)
                print('\r Cycle {}: P={},t={}'.format(IteratorCyc.index,
                      p_cyc[IteratorCyc.index], t_cyc[IteratorCyc.index]), end='', flush=True)

                if p_cyc[IteratorCyc.index] == 0:
                    self.FM.SetClose()
                elif p_cyc[IteratorCyc.index] != 0:
                    self.FM.SetOpen()
                    self.pp.SetPower(p_cyc_calib[IteratorCyc.index])
                t_sync[IteratorCyc.index] = time.time()-t0
                time.sleep(t_cyc[IteratorCyc.index])
            IteratorCyc.reset()
            self.FM.SetClose()

            #############################
            # Stability time at the end
            #############################
            print('\r'+ " " * 40, end='', flush=True)
            print('\r Stability Time end')

            self.FM_ND.ChangeState(1)
            self.pp.SetPower(PowerProbePulsePicker)            
            self.FilterWheel.set_position(1)
            self.FM.SetOpen()

            if EmGainProbe != 0:
                self.camera.SetEMGain(EmGainProbe)
            self.camera.WaitForAcq()

            #############################
            # Acq finished
            #############################
            self.FM_ND.ChangeState(0)
            self.FM.SetClose()
            if EmGainProbe != 0:
                self.camera.SetEMGain(1)

            # Save all the cycle in the folder
            temp = pd.DataFrame(
                {'Exposure Time': t_cyc.tolist(), 'Power send': p_cyc.tolist(),
                 'Power Pulse-picker': p_cyc_calib.tolist(), 'Sync': t_sync})
            temp.to_csv(TempDirPath+'/Cycle.csv')

        self.Laser.SetStatusShutterTunable(0)


def generateRandomParameters(Nb_Points, Nb_Cycle,P_calib):
    ''''This function generate a point list. Each element of the list contains a dataframe 
    which define the cycle with the time of exposure, the power send to the sample 
    and the power from the pulse picker and a fittness attribute. The parameter are then the number of points and the number
    of step in a cycle.  '''

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
    P = (0, 4.4, 10, 100, 200)  # power in uW
    # Value to reach on the powermeter (0,11,25,240,475)uW
    # Power from the pp to reach values of P #20MHz
    #P_calib = (500, 500, 800, 2000, 2500)
    p1 = [0.3, 0.175, 0.175, 0.175, 0.175]
    ProbaP = p1

    ###################
    # Proba density function Time
    ###################
    t = (0.1, 1, 10, 60)  # time
    p1 = [0.25, 0.25, 0.25, 0.25]
    ProbaT = p1

    population = []

    for k in range(Nb_Points):
        df = pd.DataFrame()
        df.fitness = -1

        # Intensity/Power Cycle generation
        df['t_cyc'] = rng.choice(t, Nb_Cycle, p=ProbaT)
        # First we generate an array of cycle which only contains index for the moment
        temp = rng.choice(np.linspace(0, len(P), len(
            P), endpoint=False, dtype=int), Nb_Cycle, p=ProbaP)
        while temp[0] == 0:  # We assume that the first element of P is the zero power element
            temp = rng.choice(np.linspace(0, len(P), len(
                P), endpoint=False, dtype=int), Nb_Cycle, p=ProbaP)
        df['p_cyc_calib'] = np.array([P_calib[i] for i in temp])
        df['p_cyc'] = np.array([P[i] for i in temp])
        population.append(df)

    return population

def LoadPreviousPop(FileDir,P_calib):
    P = (0, 4.4, 10, 100, 200) 
    GenFolder=glob.glob(FileDir+'/Generation*')
    GenerationNumber=len(GenFolder)

    CycleStore, Nb_pts=LoaCycle(GenFolder[-1])
    Pos, p_cyc, TimeCycle, TimeSync, t_globalSync, StabilityTime_begin, StabilityTime_reset, StabilityTime_end = loadExperimentInfo(
        CycleStore, Nb_pts, FileDir)
    index_map = {val: idx for idx, val in enumerate(P)}
    population = []

    for k in range(Nb_pts):
        df = pd.DataFrame()
        df.fitness = -1
        df['t_cyc'] = TimeCycle.iloc[:,k].to_numpy()
        df['p_cyc'] = p_cyc.iloc[:,k].to_numpy()
        df['p_cyc_calib'] = np.array([P_calib[index_map[i]] for i in p_cyc.iloc[:,k].to_numpy()])
        population.append(df)
    return population,GenerationNumber



def evaluateFitnessValues(population, FileDir, FolderCalibWavelength, Spectrograph_Center, Time_Min, Time_Max, Observable,GenerationNumber):
    #if USE_DUMMY:
    #    for solution in population:
    #        solution.fitness = np.sum(solution['t_cyc'])
            # f = 0
            # for i in range(len(solution['t_cyc'])):
            #    if solution['t_cyc'][i] == 0.1:
            #        f += 1
            #    else:
            #        break
            # solution.fitness = f
    #    return

    # Load experimental data
    DataTot, CycleStore, Nb_pts = LoadDataFromFiles(FileDir, FolderCalibWavelength, Spectrograph_Center,GenerationNumber)
    assert len(population) == Nb_pts

    # Load experimental settings
    Pos, p_cyc, TimeCycle, TimeSync, t_globalSync, StabilityTime_begin, StabilityTime_reset, StabilityTime_end = loadExperimentInfo(
        CycleStore, Nb_pts, FileDir)

    M_all = pd.DataFrame(index=range(Nb_pts), columns=['Enhancement', 'error', 'S1', 'S2'])

    ###################
    # Compute fitnesses
    ###################
    fitness_values = np.zeros(Nb_pts)
    for i in range(Nb_pts):
        # We first  compute the time at which the stability time begin and end for each cycles
        # The first timestamp  correspond to the time between the first spectra and the first spectra of the second step.
        # So if the StabilityTime_begin=10, StabilityTime_reset=10 and the first step is 1s then the first of t_globalSync
        # will occur at t[0]=21s. All other Timestamp occurs at each step of the cycles.
        # The last timestamp correspond to the end of the cycles but there is 1.6s made for the filterwheel to move to its position.

        dataTemp = DataTot.loc[(DataTot['Mes']==i),:] # DataTot is in nm

        ts_end =np.argmin(np.abs(dataTemp['Time']-t_globalSync[i]-3.2))
        ts_begin =np.argmin(np.abs(dataTemp['Time']-StabilityTime_begin))

        # Raw spectra in nm
        dataFit_End = dataTemp.loc[dataTemp['Time']>dataTemp.loc[ts_end,'Time'],:].iloc[:,:-1]
        dataFit_End = dataFit_End.set_index(dataFit_End['Time']-dataFit_End['Time'].min()).iloc[:,:-1]
        
        dataFit_Begin = dataTemp.loc[dataTemp['Time']<dataTemp.loc[ts_begin,'Time'],:].iloc[:,:-1]
        dataFit_Begin = dataFit_Begin.set_index(dataFit_Begin['Time']-dataFit_Begin['Time'].min()).iloc[:,:-1]

        if i==0:
            idx_Energy=(cst.h*cst.c)/(dataFit_End.columns*1E-9*cst.value('electron volt'))
            
            # Raw spectra in eV
            FitAll_End = pd.DataFrame(columns=idx_Energy)
            FitAll_Begin = pd.DataFrame(columns=idx_Energy)

        ##########################
        # Use rolling mean to remove noise
        ##########################
        print('\r {}/{} Rolling mean computation and interpolation to the same timebase'.format(i +1, Nb_pts), end='', flush=True)

        FitDataResult_End = pd.DataFrame(index=dataFit_End.index, columns=idx_Energy)
        NormaFactor=(cst.h*cst.c)/(np.power(FitDataResult_End.columns.to_numpy(),2)*cst.value('electron volt'))

        for j in dataFit_End.index:

            dataFit_End[dataFit_End<0]=0
            FitDataResult_End.loc[j, :] = (dataFit_End.loc[j, :].rolling(5, min_periods=1).mean().to_numpy().astype(np.float64))*NormaFactor
            '''
            Floor=dataFit_End.loc[j,:].rolling(5,min_periods=1).mean().min()
            if Floor<0:
                FitDataResult_End.loc[j, :] = (dataFit_End.loc[j, :].rolling(5, min_periods=1).mean().to_numpy().astype(np.float64)+np.abs(Floor))*NormaFactor
            else:
                FitDataResult_End.loc[j, :] = (dataFit_End.loc[j, :].rolling(5, min_periods=1).mean().to_numpy().astype(np.float64))*NormaFactor
            '''
        FitDataResult_End=FitDataResult_End.loc[:,(FitDataResult_End.columns<3) &(FitDataResult_End.columns>1.45) ]
        
        FitDataResult_End['Mes'] = i
        FitAll_End = pd.concat([FitAll_End, FitDataResult_End], axis=0)

        FitDataResult_Begin = pd.DataFrame(index=dataFit_Begin.index, columns=(cst.h*cst.c)/(dataFit_Begin.columns*1E-9*cst.value('electron volt')))
        NormaFactor=(cst.h*cst.c)/(np.power(FitDataResult_Begin.columns.to_numpy(),2)*cst.value('electron volt'))

        for j in dataFit_Begin.index:
            
            dataFit_Begin[dataFit_Begin<0]=0
            FitDataResult_Begin.loc[j, :] = (dataFit_Begin.loc[j, :].rolling(5, min_periods=1).mean().to_numpy().astype(np.float64))*NormaFactor
            '''
            if Floor<0:
                FitDataResult_Begin.loc[j, :] = (dataFit_Begin.loc[j, :].rolling(5, min_periods=1).mean().to_numpy().astype(np.float64)+np.abs(Floor))*NormaFactor
            else:
        
                FitDataResult_Begin.loc[j, :] = (dataFit_Begin.loc[j, :].rolling(5, min_periods=1).mean().to_numpy().astype(np.float64))*NormaFactor
            '''
        FitDataResult_Begin=FitDataResult_Begin.loc[:,(FitDataResult_Begin.columns<3) &(FitDataResult_Begin.columns>1.45) ]
        FitDataResult_Begin['Mes'] = i
        FitAll_Begin = pd.concat([FitAll_Begin, FitDataResult_Begin], axis=0)

        ##########################
        # Interpolate to the same timescale
        ##########################

        if (dataFit_End.index[-1]-dataFit_End.index[0]) > (dataFit_Begin.index[-1]-dataFit_Begin.index[0]):

            time_int = np.abs(dataFit_Begin.index -dataFit_Begin.index[-1])[::-1]

            # S2
            dataTemp_Interp = pd.DataFrame(FitDataResult_End.iloc[:, :-2], dtype='float64')
            dataTemp_Interp = dataTemp_Interp.loc[dataTemp_Interp.index <=time_int[-1], :]

            try:
                dataFit_interp2 = pd.DataFrame(np.interp(time_int, dataTemp_Interp.index,
                                                     simpson(y=dataTemp_Interp.to_numpy(),
                                                              x=dataTemp_Interp.columns.to_numpy(),
                                                                axis=1)),
                                           index=time_int)
                # S1
                dataTemp = simpson(y=FitDataResult_Begin.iloc[:, :-1].to_numpy(),
                               x=FitDataResult_Begin.iloc[:,:-1].columns.to_numpy(),
                               axis=1)
            except:
                print(dataTemp_Interp.shape)
                print(dataTemp.shape)
                exit()
            dataFit_interp1 = pd.DataFrame(dataTemp, index=time_int)
        else:

            time_int = np.abs(dataFit_End.index-dataFit_End.index[-1])[::-1]

            # S1
            dataTemp_Interp = pd.DataFrame(FitDataResult_Begin.iloc[:, :-2], dtype='float64')
            dataTemp_Interp = dataTemp_Interp.loc[dataTemp_Interp.index <=time_int[-1], :]
            try:
                dataFit_interp1 = pd.DataFrame(np.interp(time_int, dataTemp_Interp.index,
                                                     simpson(y=dataTemp_Interp.to_numpy(), 
                                                             x=dataTemp_Interp.columns.to_numpy(), 
                                                             axis=1)),
                                           index=time_int)
            # S2
                dataTemp = simpson(y=FitDataResult_End.iloc[:, :-1].to_numpy(),
                               x=FitDataResult_End.iloc[:,:-1].columns.to_numpy(),
                               axis=1)
            except:
                print(dataTemp_Interp.shape)
                print(dataTemp.shape)
                exit()

            dataFit_interp2 = pd.DataFrame(dataTemp, index=time_int)

        M_all.loc[i, 'EnhancementTime'] = [dataFit_interp2.div(dataFit_interp1, axis=0)]
        M_all.loc[i, 'S1'] = [dataFit_interp1]
        M_all.loc[i, 'S2'] = [dataFit_interp2]
        M_all.loc[i, 'error'] = dataFit_interp2.div(dataFit_interp1).std(axis=0).to_numpy()

        if Observable == 'M2':
            fitness_values[i] = np.abs((M_all.loc[i, 'S2'][0].loc[(M_all.loc[i, 'S2'][0].index > Time_Min) &
                                                                   (M_all.loc[i, 'S2'][0].index < Time_Max), 0]).mean())
            #fitness_values[i] = (M_all.loc[i, 'S2'][0].loc[(M_all.loc[i, 'S2'][0].index > Time_Min) & (M_all.loc[i, 'S2'][0].index < Time_Max), 0]
            #                     / M_all.loc[i, 'S1'][0].loc[(M_all.loc[i, 'S1'][0].index > Time_Min) & (M_all.loc[i, 'S1'][0].index < Time_Max), 0]).mean()
        elif Observable == 'M1':
            fitness_values[i] = (M_all.loc[i, 'S2'][0].loc[(M_all.loc[i, 'S2'][0].index > Time_Min) & (M_all.loc[i, 'S2'][0].index < Time_Max), 0]
                                 - M_all.loc[i, 'S1'][0].loc[(M_all.loc[i, 'S1'][0].index > Time_Min) & (M_all.loc[i, 'S1'][0].index < Time_Max), 0]).mean()
        population[i].fitness = fitness_values[i]

    print()
    print("# FITNESS VALUES #")
    print(fitness_values)

    ML_Data_Shared=pd.DataFrame(index=range(Nb_pts),
                            columns=['Power step','Time step','S1','S2',
                                     'Script Version','Dataset name','S1 full','S2 full',
                                     'Reset time','fitness'])

    for i in range(Nb_pts):
        ML_Data_Shared.loc[i,'Power step']=[p_cyc.loc[:,i]]
        ML_Data_Shared.loc[i,'Time step']=[TimeCycle.loc[:,i]]
        ML_Data_Shared.loc[i,'S1']=FitAll_Begin.loc[(FitAll_Begin['Mes']==i) & (FitAll_Begin.index>10),:].iloc[:,:-1].max(axis=1).mean()
        ML_Data_Shared.loc[i,'S2']=FitAll_End.loc[(FitAll_End['Mes']==i) & (FitAll_End.index>10),:].iloc[:,:-1].max(axis=1).mean()
        ML_Data_Shared.loc[i,'Script Version']="2025-04-10"
        ML_Data_Shared.loc[i,'Dataset name']=FileDir
        ML_Data_Shared.loc[i,'S1 full']=[M_all.loc[i,'S1'][0]]
        ML_Data_Shared.loc[i,'S2 full']=[M_all.loc[i,'S2'][0]]
        ML_Data_Shared.loc[i,'Reset time']=StabilityTime_reset
        ML_Data_Shared.loc[i,'fitness']=fitness_values[i]


    ML_Data_Shared.to_pickle(FileDir+'/ML_Data_Shared_Gen{}.pkl'.format(GenerationNumber))


def get_best_solution(candidates):
    best_ind = np.argmax([ind.fitness for ind in candidates])
    return candidates[best_ind]


def tournamentSelection(selection_pool, tournament_size=4):
    selected = []
    number_of_rounds = tournament_size//2
    for i in range(number_of_rounds):
        number_of_tournaments = len(selection_pool)//tournament_size
        order = np.random.permutation(len(selection_pool)).tolist()
        for j in range(number_of_tournaments):
            tournament_pool = [selection_pool[i]
                               for i in order[tournament_size*j:tournament_size*(j+1)]]
            best = get_best_solution(tournament_pool)
            selected.append(best)
    return selected


def twoPointCrossOver(parent_a, parent_b):
    l = len(parent_a['t_cyc'])
    offspring_a = pd.DataFrame()
    offspring_b = pd.DataFrame()
    m = (np.arange(l) < np.random.randint(l+1)
         ) ^ (np.arange(l) < np.random.randint(l+1))
    properties = ['t_cyc', 'p_cyc', 'p_cyc_calib']
    for prop in properties:
        offspring_a[prop] = np.where(m, parent_a[prop], parent_b[prop])
        offspring_b[prop] = np.where(~m, parent_a[prop], parent_b[prop])
    return [offspring_a, offspring_b]


def makeOffspring(population):
    offspring = []
    order = np.random.permutation(len(population))
    for i in range(len(order)//2):
        offsprings = twoPointCrossOver(
            population[order[2*i]], population[order[2*i+1]])
        offspring = offspring + offsprings
    return offspring


def loadExperimentInfo(CycleStore, Nb_pts, FileDir):

    #############################
    # Reading global parameters
    #############################

    para = ParameterRead(FileDir+'/ExperimentParameter.txt')
    

    # We asssume that we probe with a single frequency
    StabilityTime_begin = float(para['Stability time begin '])
    StabilityTime_reset = float(para['Stability time reset'])
    StabilityTime_end = float(para['Stability time end '])

    #############################
    # Reading cycle info
    #############################

    p_cyc = pd.DataFrame(index=range(10), columns=range(Nb_pts))
    TimeSync = pd.DataFrame(index=range(10), columns=range(Nb_pts))
    TimeCycle = pd.DataFrame(index=range(10), columns=range(Nb_pts))
    t_globalSync = pd.Series(TimeSync.iloc[-1, :], index=range(Nb_pts))

    for i in range(Nb_pts):
        p_cyc.iloc[:,i]=CycleStore.loc[CycleStore['Mes']==i,'Power send']
        TimeCycle.iloc[:,i]=CycleStore.loc[CycleStore['Mes']==i,'Exposure Time']
        TimeSync.iloc[:,i]=CycleStore.loc[CycleStore['Mes']==i,'Sync']
        t_globalSync[i] = t_globalSync[i]+TimeCycle.iloc[-1, i]

    Pos = pd.read_csv(FileDir+'/Position.csv').iloc[:, 1:].to_numpy()

    return Pos, p_cyc, TimeCycle, TimeSync, t_globalSync, StabilityTime_begin, StabilityTime_reset, StabilityTime_end

def LoaCycle(FileDir):

    Folder = sorted(glob.glob(FileDir+'/Mes*'),key=lambda x: float(x[x.find('Mes')+3:x.find('x')]))
    CycleStore = pd.DataFrame()

    for j in range(len(Folder)):
        print('\r Reading Files:{} %'.format(
            np.round(100*j/len(Folder), 1)), end='', flush=True)    
        FileCycle = pd.read_csv(Folder[j]+'/Cycle.csv')
        FileCycle['Mes']=j
        CycleStore = pd.concat([CycleStore, FileCycle], axis=0)

    try:
        CycleStore=CycleStore.drop(labels='Unnamed: 0', axis=1)
    except:
        pass
    return CycleStore, len(Folder)

def LoadDataFromFiles(FileDir, FolderCalibWavelength, WaveCenter,GenerationNumber):
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
    
    Folder = sorted(glob.glob(FileDir+'/Mes*'),key=lambda x: float(x[x.find('Mes')+3:x.find('x')]))
    CycleStore = pd.DataFrame()
    DataTot = pd.DataFrame(columns=list(Wavelength)+['Time','Mes'])

    for j in range(len(Folder)):
        print('\r Reading Files:{} %'.format(
            np.round(100*j/len(Folder), 1)), end='', flush=True)
        File = glob.glob(Folder[j]+'/*[0-9].spe')
        DataRaw = sl.load_from_files(File)
        MetaData = pd.DataFrame(DataRaw.metadata)
        TimeI = MetaData.loc[:, 0].to_numpy()/(1E6)  # Time in ms
        DataTotTemp=pd.DataFrame(columns=list(Wavelength)+['Time','Mes'])    
        try:
            temp=np.squeeze(DataRaw.data)
            if temp.shape[0]!=2: # if there is multiple ROI
                DataTotTemp[Wavelength]=temp
            else:
                DataTotTemp[Wavelength]=np.squeeze(temp[0,:,:])
        except Exception as e:
            print('\n{}'.format(e))
            exit
        DataTotTemp['Mes'] = j
        DataTotTemp['Time'] = TimeI
        if DataTot.shape[0]==0:
            DataTot=DataTotTemp
        else:
            DataTot=pd.concat([DataTotTemp,DataTot],axis=0)

        FileCycle = pd.read_csv(Folder[j]+'/Cycle.csv')
        FileCycle['Mes']=j
        CycleStore = pd.concat([CycleStore, FileCycle], axis=0)

    try:
        CycleStore=CycleStore.drop(labels='Unnamed: 0', axis=1)
    except:
        pass

    # We loaded all the data so we are going to move them for safe storage
    if os.path.exists(FileDir+'/Generation{}'.format(GenerationNumber))==False:

        os.makedirs(FileDir+'/Generation{}'.format(GenerationNumber), exist_ok=True)
        for f in Folder:
            FolderName=os.path.basename(f)
            NewPath = os.path.join(FileDir+'/Generation{}'.format(GenerationNumber), FolderName)
            shutil.move(f, NewPath)
        try:
            shutil.copy(FileDir+'/Position.csv',FileDir+'/Generation{}/Position.csv'.format(GenerationNumber))
            shutil.copy(FileDir+'/ExperimentParameter.txt',FileDir+'/Generation{}/ExperimentParameter.txt'.format(GenerationNumber))
        except Exception as e:
            print('Warning: problem trying to copy Position.csv and ExperimentParameter.txt')
            print(e)

    return DataTot, CycleStore, len(Folder)

if __name__ != '__main__':
    generations_budget=1

if __name__ == '__main__':

    if not USE_DUMMY:
        os.system('cls')
    PlaneCoefficient=np.array([  6.74074074, -6.32539683, 32.74074074])

    # Value to reach on the powermeter (0,11,25,240,475)uW
    P_calib = (500, 500, 800, 2200, 3100)

    #############################
    # Optimization parameters
    #############################
    generations_budget = 6
    StartFromSeed=False

    #############################
    # Position parameters
    #############################
    Nb_Points_Generation = 100 # Number of cycle per generations
    Nb_points_Piezo=4 # Number of position for the piezo
    BeamRadius = 30  # Minimum distance betweensuccesive point in um
    SpacingRoughFine=0.25

    # Rough stage parameter
    start_x_rough=6
    start_y_rough=6

    #############################
    # Cycles paramters
    #############################
    Nb_Cycle = 10  # Number of cycle during experiment
    StabilityTime_Begin = 60# Time for which it will probe at the beginning of the cycle
    StabilityTime_Reset = 60# The beam will then be block for this amount of time so that the sample 'reset'
    StabilityTime_End = 60  # Time for which it will probe at the end of the cycle
    # The total time is then StabilityTime_Begin+ StabilityTime_Reset+ StabilityTime_End+Time of cycle

    Time_Min = 30
    Time_Max = 60
    
    #############################
    # Detection parameters
    #############################
    PowerProbePulsePicker = 800
    EmGainProbe = 60 # set to zero if low moise mode

    #############################
    # FW parameters
    #############################
    FilterWheelPosCycle=6
    TimeTransFilterWheel=2.76
    
    #############################
    # Misc
    #############################
    Spectrograph_slit = 200  # This is just for record not actually setting it up
    Spectrograph_Center = 700  # This is just for record not actually setting it up

    FolderCalibWavelength = '//sun/garnett/home-folder/gautier/Femto-setup/Data/0.Calibration/Spectrometer.csv'
    GeneralPara = {'Experiment name': ' ML_Anton', 'Nb_points': np.ceil(Nb_Points_Generation/Nb_points_Piezo)*generations_budget*Nb_points_Piezo, 
                    'Nb_points_Generation':Nb_Points_Generation,'Nb_points_piezo':Nb_points_Piezo,
                    'Beam avoidance radius': BeamRadius,'SpacingRoughFine':SpacingRoughFine,
                    'Stability time begin ': StabilityTime_Begin, 'Stability time reset': StabilityTime_Reset, 'Stability time end ': StabilityTime_End,
                    'Power probe ': PowerProbePulsePicker, 'Em Gain probe': EmGainProbe,
                    'Spectrograph slit width': Spectrograph_slit, 'Spectrograph center Wavelength': Spectrograph_Center,
                    'FilterWheel Pos':FilterWheelPosCycle,'Time Transi':TimeTransFilterWheel,
                    'Coefficient Plane':PlaneCoefficient,
                    'Note': 'The SHG unit from Coherent was used and ND3 for probe,beam 1.7um'}

    # FileDir = '/export/scratch2/constellation-data/EnhancePerov/output-dummy/'
    FileDir = 'output-dummy/'


    #############################
    # Initialisation of the Timetrace object
    #############################

    if StartFromSeed==True:
        print('Select seed Directory')
        SeedDirectory=FileControl.AskDirectory()
    print('Select folder for points calibration')
    PointsDirectory=FileControl.AskDirectory()
    try:
        PointsCalib=pd.read_csv(PointsDirectory+'/PointFocusCalib.csv',index_col=0)
    except:
        print('Could not find the file for points calibration')
        sys.exit()
    runner = timeTraceRunner(**GeneralPara)
    runner.initialize(start_x_rough, start_y_rough, BeamRadius,PlaneCoefficient, SpacingRoughFine, FileDir, PointsCalib)

    #############################
    # Generate initial population and calculate fitness values
    #############################
    
    if StartFromSeed==False:
        population = generateRandomParameters(runner.Nb_Points, Nb_Cycle,P_calib)
        runner.runTimeTrace(StabilityTime_Begin, StabilityTime_Reset, StabilityTime_End,
                        PowerProbePulsePicker, EmGainProbe, population,0,FilterWheelPosCycle,TimeTransFilterWheel)
        evaluateFitnessValues(population, runner.DirectoryPath,
                          FolderCalibWavelength, runner.spectro.GetWavelength(), Time_Min, Time_Max, 'M2',0)
    else:
        population,GenNumber=LoadPreviousPop(SeedDirectory,P_calib)
        SeedFolderGen=glob.glob(SeedDirectory+'/Generation*')
        evaluateFitnessValues(population, SeedFolderGen[-1],FolderCalibWavelength, runner.spectro.GetWavelength(), Time_Min, Time_Max, 'M2',0)

    #############################
    # Run succesive generations
    #############################
    number_of_generations = 1
    while number_of_generations < generations_budget:  # generational loop
        print("################")
        print("# GENERATION", number_of_generations, "#")
        print("################")

        offspring = makeOffspring(population)

        # run the experiment
        runner.runTimeTrace(StabilityTime_Begin, StabilityTime_Reset, StabilityTime_End,
                            PowerProbePulsePicker, EmGainProbe, offspring,number_of_generations,FilterWheelPosCycle,TimeTransFilterWheel)
        # calculate fitness values
        evaluateFitnessValues(offspring, runner.DirectoryPath,
                              FolderCalibWavelength, runner.spectro.GetWavelength(), Time_Min, Time_Max, 'M2',number_of_generations)

        # update population
        population = tournamentSelection(population + offspring)

        print("Best solution so far:")
        print(get_best_solution(population).fitness)
        #print(get_best_solution(population)['t_cyc'])

        number_of_generations += 1
