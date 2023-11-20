import ControlDL as DLB
import ControlLaser as las
import ControlLockInAmplifier as lock
import FileControl 

import time
import numpy as np

#############################
# Global parameter
#############################
time_exp=2 # time of experiment in second


FileNameData='DataBeamSync_'

LockInParaFile='ParameterLockIn.txt'

GeneralPara={'Experiment name':' Synchronisation Beam','Exposition duration':time_exp}

InstrumentsPara={}
#############################
# Initialisation of lock-in amplifier
#############################

LockInDevice=lock.LockInAmplifier(LockInParaFile)

InstrumentsPara['Lock-in-amplifier']=LockInDevice.parameterDict

#############################
# Initialisation delay line
#############################

DL=DLB.DelayLineObject('COM16',0,0.016)
DL.MoveAbsolute(0)


#############################
# Initialisation of laser
#############################

Laser= las.LaserControl('COM8',2)
Laser.StatusShutterTunable(1)
InstrumentsPara['Laser']=Laser.parameterDict

#############################
# Preparation of the directory
#############################

DirectoryPath=FileControl.PrepareDirectory(GeneralPara,InstrumentsPara)

#############################
# Variable creation
#############################
distance=np.linspace(0,225,50)
RecordedPosition=np.zeros(len(distance))
IntensityData=np.zeros(len(distance))
IntensityData2=np.zeros(len(distance))
ErrorBar=np.zeros(len(distance))
ErrorBar2=np.zeros(len(distance))
temp_iterator=np.nditer(distance, flags=['f_index'])

#############################
# Acquisition loop
#############################



for k in  temp_iterator:
    DL.MoveAbsolute(float(k))
    
    

    #LockInDevice.AutorangeSource()
    
    time.sleep(3)
    
    print('Begin acquisiton at distance {}'.format(float(DL.GetPosition())))
    data_Source1,t1,data_Source2,t2=LockInDevice.AcquisitionLoop(time_exp)
    print('End acquisiton')
    #############################
    # Interpolation to the same timebase
    #############################

    data_Source2_interp=np.interp(t1,t2,data_Source2)
    t1_scaled=(t1-t1[1])/LockInDevice.Timebase
    
    
    IntensityData[temp_iterator.index]=np.mean(data_Source1[1:])
    ErrorBar[temp_iterator.index]=np.std(data_Source1[1:])
    IntensityData2[temp_iterator.index]=np.mean(data_Source2_interp[1:])
    ErrorBar2[temp_iterator.index]=np.std(data_Source2_interp[1:])
    RecordedPosition[temp_iterator.index]=float(DL.GetPosition())

ExportData=np.array(np.transpose([RecordedPosition,IntensityData,ErrorBar,IntensityData2,ErrorBar2]))
FileControl.ExportFileChopperOptimisation(DirectoryPath,FileNameData+'loop{}'.format(str(k)),ExportData)
Laser.StatusShutterTunable(0)