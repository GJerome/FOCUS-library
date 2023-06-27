import ControlLockInAmplifier as lock
import ControlLaser as las

import matplotlib.pyplot as plt
import numpy as np

import pandas as pd
import ExportFile 
import time

#############################
# Global parameter
#############################
time_exp=60*60 # time of experiment in second
time_sleep=10*60
nb_loop=3

FileNameData='2023-06-20-DataTinMeltingPerov_'
LockInParaFile='ParameterLockIn.txt'


#############################
# Initialisation of lock-in amplifier
#############################

LockInDevice=lock.LockInAmplifier(LockInParaFile)

#############################
# Initialisation of laser
#############################

Laser= las.LaserControl('COM6',2)


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
    ExportFile.ExportFileLockIn(FileNameData+'loop{}'.format(str(k)),export_data)

    
    print('The sample is sleeping')
    Laser.StatusShutterTunable(0)
    time.sleep(time_sleep)


Laser.StatusShutterTunable(0)

      
