import ControlLockInAmplifier as lock
import ControlLaser as las
import ControlPulsePicker as picker
import ControlEMCCD as EMCCD
import FileControl 
import ControlConex as Rtransla

import numpy as np
import time as time
import os

os.system('cls')
#############################
# Global parameter
#############################

DarkTime=300 # time of dark time in seconds
cycles=1 # number of cycles

# We create a test zone define by the  PositionCube variable, on the x_axis we do a frequency sweep and on the y axis a power sweep
PositionCube=[8.8,6.1,0.1,0.1]# [x_start y_start x_length y_length]
Freq=[300E3,100E3] # [starting frequency, end frequency] the actual unit send is the cast int of 80E6/Freq which is the division ratio 

Nb_pts_freq=3

PowerSweep=[17500,17500] #[Starting power, end power] in mw

Nb_pts_power=3


FileNameData='DataDoseExperiement_'

LockInParaFile='ParameterLockIn.txt'

GeneralPara={'Experiment name':' Dose experiment','Dark time':DarkTime,
             'Frequency sweep':Freq,'Number points frequency sweep':Nb_pts_freq,
             'Power sweep':PowerSweep,'Number points power sweep':Nb_pts_power,
             'Note':'The SHG unit from Coherent was used'}

InstrumentsPara={}

x_pos=np.linspace(PositionCube[0],PositionCube[0]+PositionCube[2],Nb_pts_freq)
FreqSweep=np.linspace(int(80E6/Freq[0]),int(80E6/Freq[1]),Nb_pts_freq,dtype=np.dtype(int))
#FreqSweep=np.array([2,20,200],dtype=np.dtype(int))
IteratorFreq=np.nditer(FreqSweep, flags=['f_index'])
print(FreqSweep)
print(IteratorFreq)

y_pos=np.linspace(PositionCube[1],PositionCube[1]+PositionCube[3],Nb_pts_power)
PowerSweep=np.linspace(PowerSweep[0],PowerSweep[1],Nb_pts_power,dtype=np.dtype(int))
#PowerSweep=np.array([1000,1400,1600,2200,3000,3600,7100,11900,17500],dtype=np.dtype(int)) #900,1300,1500,
IteratorPower=np.nditer(PowerSweep, flags=['f_index'])
print(PowerSweep)
print(IteratorPower)

for k in IteratorFreq: #IteratorFreq
    print(k)
    #pp.SetDivRatio(k)  #k


    for j in IteratorPower:

        pp.SetPower(j) #PowerSweep[int(IteratorFreq.index*3+j)]
