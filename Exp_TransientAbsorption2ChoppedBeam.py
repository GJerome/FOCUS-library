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

def Time2distance(t,NbPath):
    '''This function take delay time t[s] as an argument but also the nomber of path the light make and convert it in a distance usable by the delay line.'''
    return 2.99705*1E8*t*NbPath 

#############################
# Global parameter
#############################
time_exp=1 # time of experiment in second
nb_loop=2
PhaseChopperProbe=295
PhaseChopperPump=400

Delaymax=1E-9

# We define the map dimension in mm


FileNameData='DataTransientAbsTwoBeam_'

LockInParaFile='ParameterLockInTA.txt'

GeneralPara={'Experiment name':' TA 2chopped beam','Exposure duration':time_exp,
             'Number of loop':nb_loop,'Delay max':Delaymax}


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

DelayLine=dl.DelayLineObject('COM16',1,0.016)
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
Total_delay=np.linspace(0,Delaymax,100)

temp_iterator=np.nditer(Total_delay, flags=['f_index'])

print("Everything is ready")

Laser.StatusShutterTunable(1)

t=(time.time(),)
for k in  temp_iterator:
    t=t+(time.time(),)
    DelayLine.MoveRelative(Time2distance(k,2))
    camera.Acquire()
    
Laser.StatusShutterTunable(0)



      
