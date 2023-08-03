import ControlLockInAmplifier as lock
import ControlLaser as las
import ControlChopper as chop

import numpy as np

import FileControl 
import time

#############################
# Global parameter
#############################
time_exp=60*30 # time of experiment in second
time_sleep=6
nb_loop=2
PhaseCalib=200

FileNameData='DataPerformTinPerov_'

LockInParaFile='ParameterLockIn.txt'

GeneralPara={'Experiment name':' PL no move','Exposition duration':time_exp,
             'Time between run':time_sleep,'Number of loop':nb_loop}

InstrumentsPara={}
#############################
# Initialisation of lock-in amplifier
#############################

LockInDevice=lock.LockInAmplifier(LockInParaFile)

InstrumentsPara['Lock-in-amplifier']=LockInDevice.parameterDict

#############################
# Initialisation of laser
#############################

Laser= las.LaserControl('COM6',2)

InstrumentsPara['Laser']=Laser.parameterDict

#############################
# Initialisation of Chopper
#############################

Chopper1= chop.OpticalChopper('COM14')
Chopper1.SetInternalFrequency(0)
Chopper1.SetMotorStatus('ON')
Chopper1.SetPhase(PhaseCalib)
Chopper1.WaitForLock(10)

InstrumentsPara['Chopper']=Chopper1.parameterDict


#############################
# Preparation of the directory
#############################

DirectoryPath=FileControl.PrepareDirectory(GeneralPara,InstrumentsPara)

#############################
# Acquisition loop
#############################
print('Begin acquisition')

for k in range(nb_loop) :
    Laser.StatusShutterTunable(1)
    LockInDevice.AutorangeSource()
    time.sleep(5)

    data_Source1,t1,data_Source2,t2=LockInDevice.AcquisitionLoop(time_exp)

    #############################
    # Interpolation to the same timebase
    #############################

    data_Source2_interp=np.interp(t1,t2,data_Source2)
    Reflectivity=np.divide(data_Source2_interp,data_Source1)
    t1_scaled=(t1-t1[1])/LockInDevice.Timebase

    export_data=(t1_scaled,Reflectivity,data_Source2_interp,data_Source1)
    FileControl.ExportFileLockIn(DirectoryPath,FileNameData+'loop{}'.format(str(k)),export_data)

    
    print('The sample is sleeping')
    Laser.StatusShutterTunable(0)
    time.sleep(time_sleep)


Laser.StatusShutterTunable(0)

      
