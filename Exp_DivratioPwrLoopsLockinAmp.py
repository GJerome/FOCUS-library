import ControlLockInAmplifier as lock
import ControlLaser as las
import ControlPulsePicker as picker
import ControlChopper as chop
import ControlEMCCD as EMCCD
import ControlConex as Rtransla

import FileControl 

import numpy as np
import time
import pandas as pd

#############################
# Global parameter
#############################


# We create a test zone define by the  PositionCube variable, on the x_axis we do a frequency sweep and on the y axis a power sweep
PositionCube=[6.25 ,9,1,1]# [x_start y_start x_length y_length]

#Frequency tuning
Freq=[80E3,4E6] # [starting frequency, end frequency] the actual unit send is the cast int of 80E6/Freq which is the division ratio 
Nb_pts_freq=5

# Power tuning
PowerSweep=[500,17500] #[Starting power, end power] in mw
Nb_pts_power=5

#Measurement 
time_exp=3*60 # time of experiment in second
time_sleep=0
nb_loop=1 # number of on/off cycles

FileNameData='CarbonRemoval_'

LockInParaFile = "ParameterLockIn.txt"


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

Laser= las.LaserControl('COM8',2)

InstrumentsPara['Laser']=Laser.parameterDict

#############################
# Initialisation of the Pulse Picker
#############################

pp=picker.PulsePicker("USB0::0x0403::0xC434::S09748-10A7::INSTR")

InstrumentsPara['Pulse picker']=pp.parameterDict

#############################
# Initialisation of the Conex Controller
#############################

x_axis=Rtransla.ConexController('COM12')
y_axis=Rtransla.ConexController('COM13')
print('Initialised rough translation stage')


#############################
# Preparation of the directory
#############################
print('Directory staging, please check other window')
DirectoryPath=FileControl.PrepareDirectory(GeneralPara,InstrumentsPara)

#############################
# Acquisition loop
#############################
print('Begin acquisition')

x_pos=np.linspace(PositionCube[0],PositionCube[0]+PositionCube[2],Nb_pts_freq)
y_pos=np.linspace(PositionCube[1],PositionCube[1]+PositionCube[3],Nb_pts_power)

FreqSweep=np.linspace(int(80E6/Freq[0]),int(80E6/Freq[1]),Nb_pts_freq,dtype=np.dtype(int))
IteratorFreq=np.nditer(FreqSweep, flags=['f_index'])

PowerSweep=np.linspace(PowerSweep[0],PowerSweep[1],Nb_pts_power,dtype=np.dtype(int))
IteratorPower=np.nditer(PowerSweep, flags=['f_index'])

for i in IteratorFreq:
    x_axis.MoveTo(x_pos[IteratorFreq.index])    
    pp.SetDivRatio(i) 

    for j in IteratorPower:
        y_axis.MoveTo(y_pos[IteratorPower.index])
        pp.SetPower(j)
        print('Laser on the sample with a div ratio of {} and a power of {}'.format(pp.GetDivRatio(),pp.GetPower()))
        
        for k in range(nb_loop):
            Laser.StatusShutterTunable(1)
            LockInDevice.AutorangeSource()
            print('Acquisition {}'.format(k))

            Data=LockInDevice.AcquisitionLoop(time_exp)
            FileControl.ExportFileLockIn(DirectoryPath,
                                         FileNameData+'divrat{}pwr{}loop{}'.format(pp.GetDivRatio(),pp.GetPower(),str(k)),
                                         Data)
            Laser.StatusShutterTunable(0)


            if k != range(nb_loop)[-1] and time_sleep!=0:
                print('The sample is sleeping')
                time.sleep(time_sleep)

    IteratorPower.reset()
    



Laser.StatusShutterTunable(0)

      