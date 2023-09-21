import ControlLaser as las
import ControlChopper as chop
import ControlLockInAmplifier as lock
import ControlPulsePicker as PuPi
import ControlEMCCD as emccd
import ControlDL as dl

import numpy as np

import FileControl 
import time
import matplotlib.pyplot as plt

#############################
# Global parameter
#############################
time_exp=1 # time of experiment in second
nb_loop=2
PhaseChopperProbe=295
PhaseChopperPump=400
MotorId=1 # It can take the value of one or two depanding of which motor we are calibrating

# We define the map dimension in mm
res_xy=0.1;
dx=0.05
dy=0.1

StartingPositionx=5
StartingPositiony=7



FileNameData='DataTransientAbsTwoBeam_'

LockInParaFile='ParameterLockInTA.txt'

GeneralPara={'Experiment name':' PL no move','Exposition duration':time_exp,
             'Number of loop':nb_loop}


InstrumentsPara={}



#############################
# Initialisation of laser
#############################

Laser= las.LaserControl('COM6',2)

InstrumentsPara['Laser']=Laser.parameterDict

#############################
# Initialisation of the Pulse Picker
#############################

PulsePicker=PuPi.PulsePicker("USB0::0x0403::0xC434::S09748-10A7::INSTR")

InstrumentsPara['Pulse picker']=PulsePicker.parameterDict

#############################
# Initialisation of lock-in amplifier
#############################

LockInDevice=lock.LockInAmplifier(LockInParaFile)

# Set output 1 and two
LockInDevice.SetOutputTA()

print('Set up lock-in output 1 and 2')

InstrumentsPara['Lock-in-amplifier']=LockInDevice.parameterDict

#############################
# Initialisation of the EMCCD
#############################

camera=emccd.LightFieldControl('TransientAbs2beam')

#############################
# Initialisation of the delay line
#############################

DelayLine=dl.DelayLineObject('COM3',1,0.016)
PosZero=0 # postion at which both pulse are synchronised
DelayLine.MoveAbsolute(PosZero)

#############################
# Initialisation of Choppers
#############################

# Chopper Probe 
Chopper1= chop.OpticalChopper('COM14')
Chopper1.SetInternalFrequency(0)
Chopper1.SetMotorStatus('ON')
Chopper1.WaitForLock(10)
Chopper1.SetPhase(PhaseChopperProbe)
Chopper1.parameterDict['Phase']=PhaseChopperProbe

InstrumentsPara['ChopperProbe']=Chopper1.parameterDict

# Chopper Pump 
Chopper1= chop.OpticalChopper('COM14')
Chopper1.SetInternalFrequency(0)
Chopper1.SetMotorStatus('ON')
Chopper1.WaitForLock(10)
Chopper1.SetPhase(PhaseChopperPump)
Chopper1.parameterDict['Phase']=PhaseChopperPump

InstrumentsPara['ChopperPump']=Chopper1.parameterDict



#############################
# Preparation of the directory
#############################

DirectoryPath=FileControl.PrepareDirectory(GeneralPara,InstrumentsPara)

#############################
# Acquisition loop
#############################
print('Begin acquisition')

StartingPosition=np.linspace(1,11,50)
Speedx=np.linspace(1,11,50)
lengthLine=3

temp_iterator=np.nditer(StartingPosition, flags=['f_index'])

print("Everything is ready")

Laser.StatusShutterTunable(1)
for k in  temp_iterator:
    Laser.StatusShutterTunable(1)
    time.sleep(2)
    Rtransla.MoveLine1D(x_axis,k,k+lengthLine,Speedx[temp_iterator.index])
    y.Move(k)
    Laser.StatusShutterTunable(0)




      
