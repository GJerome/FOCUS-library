import ControlLockInAmplifier as lock
import ControlLaser as las
import ControlChopper as chop
import ControlStandaMotor as pola

import numpy as np

import FileControl 
import time
import matplotlib.pyplot as plt

#############################
# Global parameter
#############################
time_exp=2 # time of experiment in second
nb_loop=2
PhaseChopper=295
MotorId=1 # It can take the value of one or two depanding of which motor we are calibrating

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
'''
Chopper1= chop.OpticalChopper('COM11')
Chopper1.SetInternalFrequency(0)
Chopper1.SetMotorStatus('ON')
Chopper1.WaitForLock(10)
Chopper1.SetPhase(PhaseChopper)
Chopper1.parameterDict['Phase']=PhaseChopper

InstrumentsPara['Chopper']=Chopper1.parameterDict
'''

#############################
# Initialisation of the polariser
#############################
MotorList=pola.Find_Motor(False)
Motor=pola.RotationMotorStanda(MotorList[MotorId])
Motor.MoveAbs(0)


#############################
# Preparation of the directory
#############################

DirectoryPath=FileControl.PrepareDirectory(GeneralPara,InstrumentsPara)

#############################
# Acquisition loop
#############################
print('Begin acquisition')

angle=np.linspace(0,360,360)+Motor.GetPos()

IntensityData=np.zeros(len(angle))
IntensityData2=np.zeros(len(angle))
ErrorBar=np.zeros(len(angle))
ErrorBar2=np.zeros(len(angle))
AngleReel=np.zeros(len(angle))
temp_iterator=np.nditer(angle, flags=['f_index'])

print("Everything is ready")
ax0=plt.subplot(1,3,1)
ax1=plt.subplot(1,3,2)
ax2=plt.subplot(1,3,3)
color = iter(plt.cm.rainbow(np.linspace(0, 1, len(angle)+1)))
c = next(color)

Laser.StatusShutterTunable(1)
for k in  temp_iterator:
    c = next(color)
    Laser.StatusShutterTunable(1)
    Motor.MoveAbs(k)

    LockInDevice.AutorangeSource()
    
    time.sleep(3)
    
    print('Begin acquisiton at the angle : {}'.format(k))
    data_Source1,t1,data_Source2,t2=LockInDevice.AcquisitionLoop(time_exp)
    print('End acquisiton')
    #############################
    # Interpolation to the same timebase
    #############################

    data_Source2_interp=np.interp(t1,t2,data_Source2)
    t1_scaled=(t1-t1[1])/LockInDevice.Timebase
    ax0.scatter(t1_scaled[1:],data_Source1[1:],color=c)
    
    IntensityData[temp_iterator.index]=np.mean(data_Source1[1:])
    ErrorBar[temp_iterator.index]=np.std(data_Source1[1:])
    IntensityData2[temp_iterator.index]=np.mean(data_Source2_interp[1:])
    ErrorBar2[temp_iterator.index]=np.std(data_Source2_interp[1:])
    AngleReel[temp_iterator.index]=Motor.GetPos()

ax0.set_xlabel('Time [s]')
ax0.set_xlabel('Intensity[V]')
ax1.plot(angle,IntensityData)
ax1.set_xlabel('Angle[deg]')
ax1.set_ylabel('Intensity[V]')
ax2.plot(angle,AngleReel)
ax2.set_xlabel('Asked angle[deg]')
ax2.set_ylabel('Real angle[deg]')

ExportData=np.array(np.transpose([angle,IntensityData,ErrorBar,IntensityData2,ErrorBar2]))
FileControl.ExportFileChopperOptimisation(DirectoryPath,FileNameData+'loop{}'.format(str(k)),ExportData)
Laser.StatusShutterTunable(0)
plt.show()

      
