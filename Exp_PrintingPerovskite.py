import ControlLaser as las
import ControlChopper as chop
import ControlConex as Rtransla

import numpy as np

import FileControl 
import time
import matplotlib.pyplot as plt

#############################
# Global parameter
#############################
time_exp=1 # time of experiment in second
nb_loop=2
PhaseChopper=400
MotorId=1 # It can take the value of one or two depanding of which motor we are calibrating




GeneralPara={'Experiment name':' PL no move','Exposition duration':time_exp,
             'Number of loop':nb_loop}

InstrumentsPara={}


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
Chopper1.SetPhase(PhaseChopper)
Chopper1.parameterDict['Phase']=PhaseChopper

InstrumentsPara['Chopper']=Chopper1.parameterDict


#############################
# Conex Controller initialisation
#############################

# We then initalize the axis
#print('Initialisation of z the axis')
#z_axis=ControlConex.ConexController('COM5')
print('Initialisation of x the axis')
x_axis=Rtransla.ConexController('COM13')
print('Initialisation of y the axis')
y_axis=Rtransla.ConexController('COM12')


#############################
# Preparation of the directory
#############################

DirectoryPath=FileControl.PrepareDirectory(GeneralPara,InstrumentsPara)

#############################
# Printing loop
#############################
print('Begin acquisition')

StartingPosition=np.linspace(5,11,50)
Speedx=np.linspace(0.1,11,50)
lengthLine=3

temp_iterator=np.nditer(StartingPosition, flags=['f_index'])

print("Everything is ready")

for k in  temp_iterator:
    Laser.StatusShutterTunable(1)
    time.sleep(2)
    Rtransla.MoveLine1D(y_axis,2,2+lengthLine,Speedx[temp_iterator.index])
    x_axis.MoveTo(k)
    Laser.StatusShutterTunable(0)




      
