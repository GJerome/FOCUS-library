import ControlFlipMount as FlipMount
import ControlLaser as las
import ControlPulsePicker as picker
import FileControl
import ControlPiezoStage as Transla
import ControlEMCCD as EMCCD

import matplotlib.pyplot as plt
import matplotlib as mat
import numpy as np
import pandas as pd
import time as time

import random
import os
import sys


os.system('cls')

#############################
# Global parameter
#############################
Nb_Points_subgrid=600

DarkTime = 300 # time of dark time in seconds
cycles = 1 # number of cycles

#############################
# Piezo parameter
#############################

#Definition of small grid

start_x = 5
end_x = 80
x = np.linspace(start_x, end_x, int(np.floor(np.sqrt(Nb_Points_subgrid))))

start_y = 5
end_y = 80
y = np.linspace(start_y, end_y, int(np.floor(np.sqrt(Nb_Points_subgrid))))

X, Y = np.meshgrid(x, y)
Pos = np.stack([X.ravel(), Y.ravel()], axis=-1)
index=random.sample(range(0, Pos.shape[0]), Pos.shape[0])
SmallGrid=Pos[index,:]


GeneralPos=SmallGrid

print('Number of Points:{}\n'.format(GeneralPos.shape[0]))


GeneralPara = {'Experiment name': ' DosingExperiment', 'Nb points': Nb_Points_subgrid,
               'Note': 'The SHG unit from Coherent was used'}

InstrumentsPara = {}


# We create a test zone define by the  PositionCube variable, on the x_axis we do a frequency sweep and on the y axis a power sweep
PositionCube=[5,6,75,20]# [x_start y_start x_length y_length] x = y and y = x
#Freq=[40E6,10E6] # [starting frequency, end frequency] the actual unit send is the cast int of 80E6/Freq which is the division ratio 
#PowerSweep=[1300,1300] #[Starting power, end power] in mw


Nb_pts_freq=5
Nb_pts_power=3





FileNameData='DataDoseExperiement_'

LockInParaFile='ParameterLockIn.txt'

GeneralPara = {'Experiment name': ' DosingExperiment', 'Nb points': Nb_Points_subgrid,
               'Note': 'The SHG unit from Coherent was used'}

InstrumentsPara={}



#############################
# Initialisation of laser
#############################

Laser = las.LaserControl('COM8', 'COM17', 0.5)

InstrumentsPara['Laser'] = Laser.parameterDict
print('Initialised Laser')

#############################
# Initialisation of pulse picker
#############################

pp = picker.PulsePicker("USB0::0x0403::0xC434::S09748-10A7::INSTR")
InstrumentsPara['Pulse picker'] = pp.parameterDict
print('Initialised pulse picker')

#############################
# Initialisation of the motorised controller
#############################
if 'ControlConex' in sys.modules:
    x_axis = Transla.ConexController('COM12')
    y_axis = Transla.ConexController('COM13')
    print('Initialised rough translation stage')

elif 'ControlPiezoStage' in sys.modules:
    piezo = Transla.PiezoControl('COM15')
    x_axis = Transla.PiezoAxisControl(piezo, 'x',3)
    y_axis = Transla.PiezoAxisControl(piezo, 'y',3)
    print('Initialised piezo translation stage')

#############################
# Initialisation of the EMCCD
#############################

camera = EMCCD.LightFieldControl('TimeTraceEMMarcel')
FrameTime = camera.GetFrameTime()
ExposureTime = camera.GetExposureTime()
NumberOfFrame = camera.GetNumberOfFrame()
InstrumentsPara['PI EMCCD'] = camera.parameterDict
print('Initialised EMCCD')

#############################
# Initialisation of the shutter
#############################

FM = FlipMount.FlipMount("37007726")
print('Initialised Flip mount')

#############################
# Printing loop
#############################
print('')

x_pos=np.linspace(PositionCube[0],PositionCube[0]+PositionCube[2],Nb_pts_freq)
#FreqSweep=np.linspace(int(80E6/Freq[0]),int(80E6/Freq[1]),Nb_pts_freq,dtype=np.dtype(int))
FreqSweep=np.array([8,10,13,20,40],dtype=np.dtype(int)) #
IteratorFreq=np.nditer(FreqSweep, flags=['f_index'])
print(IteratorFreq)

y_pos=np.linspace(PositionCube[1],PositionCube[1]+PositionCube[3],Nb_pts_power)
#PowerSweep=np.linspace(PowerSweep[0],PowerSweep[1],Nb_pts_power,dtype=np.dtype(int))
PowerSweep=np.array([5300,5300,5300],dtype=np.dtype(int)) #[2600,2600,2600,3200,3200,3200,4600,4600,4600,13100,13100,13100,17500,17500,17500]
IteratorPower=np.nditer(PowerSweep, flags=['f_index'])

#y_axis.MoveTo(y_pos[0])

print("Begin acquisition")

#for k in IteratorFreq: #IteratorFreq
#    x_axis.MoveTo(x_pos[IteratorFreq.index])   #IteratorFreq.index
#    pp.SetDivRatio(k)  #k
#    print(PowerSweeps[IteratorFreq.index])
#    pp.SetPower(int(PowerSweep[IteratorFreq.index])) #IteratorFreq.index
#
#    for j in range(3):
#        y_axis.MoveTo(y_pos[int(j)]) #IteratorPower.index
#        pp.SetPower(PowerSweep[int(IteratorFreq.index*3+j)]) #PowerSweep[int(IteratorFreq.index*3+j)]
#        print('Laser on the sample with a div ratio of {} and a power of {}'.format(pp.GetDivRatio(),pp.GetPower()))
#    
#        for i in range(cycles):
#            if i != 0:
#                print('Dark time intiated')
#
#                time.sleep(DarkTime)
#
#            Laser.SetStatusShutterTunable(1)
#            camera.Acquire()
#            camera.WaitForAcq() 
#            Laser.SetStatusShutterTunable(0)
            

            
#    IteratorPower.reset()

for k in IteratorFreq: 
    x_axis.MoveTo(x_pos[IteratorFreq.index])  
    pp.SetDivRatio(k) 
 #   print(PowerSweep[IteratorFreq.index])
 #   pp.SetPower(int(PowerSweep[IteratorFreq.index]))

    for j in IteratorPower:
        y_axis.MoveTo(y_pos[IteratorPower.index]) 
        pp.SetPower(j) 
        print('Laser on the sample with a div ratio of {} and a power of {}'.format(pp.GetDivRatio(),pp.GetPower()))
    
        for i in range(cycles):
            if i != 0:
                print('Dark time intiated')

                time.sleep(DarkTime)

            Laser.SetStatusShutterTunable(1)
            camera.Acquire()
            camera.WaitForAcq() 
            Laser.SetStatusShutterTunable(0)

    if k == 16:
        time.sleep(60)

    IteratorPower.reset()

print('Experiment finished')