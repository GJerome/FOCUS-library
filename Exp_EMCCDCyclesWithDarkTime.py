import ControlLockInAmplifier as lock
import ControlLaser as las
import ControlPulsePicker as picker
import ControlEMCCD as EMCCD
import ControlPiezoStage as piezoC
import FileControl 
import ControlConex as Rtransla

import numpy as np
import time as time
import os
import sys

os.system('cls')
#############################
# Global parameter
#############################

DarkTime = 300 # time of dark time in seconds
cycles = 2 # number of cycles

# We create a test zone define by the  PositionCube variable, on the x_axis we do a frequency sweep and on the y axis a power sweep
PositionCube=[500,500,100,100]# [x_start y_start x_length y_length] x = y and y = x
Freq=[40E6,10E6] # [starting frequency, end frequency] the actual unit send is the cast int of 80E6/Freq which is the division ratio 

Nb_pts_freq=5

PowerSweep=[1300,1300] #[Starting power, end power] in mw

Nb_pts_power=2


FileNameData='DataDoseExperiement_'

LockInParaFile='ParameterLockIn.txt'

GeneralPara={'Experiment name':' Dose experiment','Dark time':DarkTime,
             'Frequency sweep':Freq,'Number points frequency sweep':Nb_pts_freq,
             'Power sweep':PowerSweep,'Number points power sweep':Nb_pts_power,
             'Note':'The SHG unit from Coherent was used'}

InstrumentsPara={}



#############################
# Initialisation of laser
#############################

Laser= las.LaserControl('COM8','COM17',0.5)

InstrumentsPara['Laser']=Laser.parameterDict

#############################
# Initialisation of pulse picker
#############################

pp=picker.PulsePicker("USB0::0x0403::0xC434::S09748-10A7::INSTR")
InstrumentsPara['Pulse picker']=pp.parameterDict
print('Initialised pulse picker')

#############################
# Initialisation of the Conex Controller
#############################
piezo= piezoC.PiezoControl('COM15')
x_axis=piezoC.PiezoAxisControl(piezo,'x')
y_axis=piezoC.PiezoAxisControl(piezo,'y')
z_axis=piezoC.PiezoAxisControl(piezo,'z')
#x_axis=Rtransla.ConexController('COM12')
#y_axis=Rtransla.ConexController('COM13')
print('Initialised rough translation stage')
#x_axis.MoveTo(startx)
#y_axis.MoveTo(starty)

#############################
# Initialisation of the streak camera
#############################

#############################
# Initialisation of the EMCCD
#############################

camera=EMCCD.LightFieldControl('TimeTraceEMMarcel')
print('Initialised EMCCD')



#############################
# Printing loop
#############################
print('')

x_pos=np.linspace(PositionCube[0],PositionCube[0]+PositionCube[2],Nb_pts_freq)
#FreqSweep=np.linspace(int(80E6/Freq[0]),int(80E6/Freq[1]),Nb_pts_freq,dtype=np.dtype(int))
FreqSweep=np.array([8,16,80,160,800],dtype=np.dtype(int)) #
IteratorFreq=np.nditer(FreqSweep, flags=['f_index'])
print(IteratorFreq)

y_pos=np.linspace(PositionCube[1],PositionCube[1]+PositionCube[3],Nb_pts_power)
#PowerSweep=np.linspace(PowerSweep[0],PowerSweep[1],Nb_pts_power,dtype=np.dtype(int))
PowerSweep=np.array([4000,4000],dtype=np.dtype(int)) #[2600,2600,2600,3200,3200,3200,4600,4600,4600,13100,13100,13100,17500,17500,17500]
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
    y_axis.MoveTo(x_pos[IteratorFreq.index])  
    pp.SetDivRatio(k) 
 #   print(PowerSweep[IteratorFreq.index])
 #   pp.SetPower(int(PowerSweep[IteratorFreq.index]))

    for j in IteratorPower:
        z_axis.MoveTo(y_pos[IteratorPower.index]) 
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