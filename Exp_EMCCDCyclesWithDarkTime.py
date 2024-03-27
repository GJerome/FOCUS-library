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

DarkTime=1 # time of dark time in seconds
cycles=2 # number of cycles

# We create a test zone define by the  PositionCube variable, on the x_axis we do a frequency sweep and on the y axis a power sweep
PositionCube=[7 ,10,1,1]# [x_start y_start x_length y_length]
Freq=[8E3,8E6] # [starting frequency, end frequency] the actual unit send is the cast int of 80E6/Freq which is the division ratio 
Nb_pts_freq=2
PowerSweep=[500,17500] #[Starting power, end power] in mw
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

Laser= las.LaserControl('COM8',2)

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

x_axis=Rtransla.ConexController('COM13')
y_axis=Rtransla.ConexController('COM12')
print('Initialised rough translation stage')

#############################
# Initialisation of the EMCCD
#############################

camera=EMCCD.LightFieldControl('TimeTraceEM')
print('Initialised EMCCD')

#############################
# Preparation of the directory
#############################
print('Directory staging, please check other window')
#DirectoryPath=FileControl.PrepareDirectory(GeneralPara,InstrumentsPara)


#############################
# Printing loop
#############################
print('')

x_pos=np.linspace(PositionCube[0],PositionCube[0]+PositionCube[2],Nb_pts_freq)
FreqSweep=np.linspace(int(80E6/Freq[0]),int(80E6/Freq[1]),Nb_pts_freq,dtype=np.dtype(int))
IteratorFreq=np.nditer(FreqSweep, flags=['f_index'])

y_pos=np.linspace(PositionCube[1],PositionCube[1]+PositionCube[3],Nb_pts_power)
PowerSweep=np.linspace(PowerSweep[0],PowerSweep[1],Nb_pts_power,dtype=np.dtype(int))
IteratorPower=np.nditer(PowerSweep, flags=['f_index'])

print("Begin acquisition")

for k in  IteratorFreq:
    x_axis.MoveTo(x_pos[IteratorFreq.index])    
    pp.SetDivRatio(k) 

    for j in IteratorPower:
        y_axis.MoveTo(y_pos[IteratorPower.index])
        pp.SetPower(j)
        print('Laser on the sample with a div ratio of {} and a power of {}'.format(pp.GetDivRatio(),pp.GetPower()))
        
        for i in range(cycles):
            if i != 0:
                print('Dark time intiated')
                time.sleep(DarkTime)
      #      Laser.StatusShutterTunable(1)
            camera.Acquire()
     #       Laser.StatusShutterTunable(0)
            

            
    IteratorPower.reset()

print('Experiment finished')