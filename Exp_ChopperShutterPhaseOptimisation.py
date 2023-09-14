import ControlLockInAmplifier as lock
import ControlLaser as las
import ControlChopper as chop

import numpy as np

import FileControl 
import time
#import matplotlib.pyplot as plt

#############################
# Global parameter
#############################
time_exp=1 # time of experiment in second
nb_loop=2

FileNameData='DataChopperOptimisation_'

LockInParaFile='ParameterLockIn.txt'

GeneralPara={'Experiment name':' PL no move','Exposition duration':time_exp,
             'Number of loop':nb_loop}

InstrumentsPara={}
#############################
# Initialisation of lock-in amplifier
#############################

LockInDevice=lock.LockInAmplifier(LockInParaFile)

InstrumentsPara['Lock-in-amplifier']=LockInDevice.parameterDict

#############################
# Initialisation of laser
#############################

Laser= las.LaserControl('COM8',2)

InstrumentsPara['Laser']=Laser.parameterDict

#############################
# Initialisation of Chopper
#############################

Chopper1= chop.OpticalChopper('COM11')
Chopper1.SetInternalFrequency(0)
Chopper1.SetMotorStatus('ON')
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
#angle=range(0,360,0.1)
angle=np.arange(0,3600,5)

IntensityData=np.zeros(len(angle))
IntensityData2=np.zeros(len(angle))
ErrorBar=np.zeros(len(angle))
ErrorBar2=np.zeros(len(angle))
temp_iterator=np.nditer(angle, flags=['f_index'])

print("Everything is ready")

Laser.StatusShutterTunable(1)
for k in  temp_iterator:
    Laser.StatusShutterTunable(1)
    #LockInDevice.AutorangeSource()
    Chopper1.SetPhase(np.round(k, decimals=2))
    Chopper1.WaitForLock(10)
    time.sleep(2)
    

    data_Source1,t1,data_Source2,t2=LockInDevice.AcquisitionLoop(time_exp)
    
    #############################
    # Interpolation to the same timebase
    #############################

    data_Source2_interp=np.interp(t1,t2,data_Source2)
    t1_scaled=(t1-t1[1])/LockInDevice.Timebase
    #plt.scatter(t1_scaled[1:],data_Source1[1:])
    print(np.round(k, decimals=2))
    IntensityData[temp_iterator.index]=np.mean(data_Source1)
    ErrorBar[temp_iterator.index]=np.std(data_Source1)
    IntensityData2[temp_iterator.index]=np.mean(data_Source2_interp)
    ErrorBar2[temp_iterator.index]=np.std(data_Source2_interp)

ExportData=np.array(np.transpose([angle,IntensityData,ErrorBar,IntensityData2,ErrorBar2]))
FileControl.ExportFileChopperOptimisation(DirectoryPath,FileNameData+'loop{}'.format(str(k)),ExportData)
Laser.StatusShutterTunable(0)
#plt.show()

      
