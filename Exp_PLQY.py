import ControlLockInAmplifier as lock
import ControlLaser as las
import ControlConex as Rtransla
import ControlFlipMount as FlipMount

import numpy as np

import FileControl 
import time

#############################
# Global parameter
#############################

# For each measurement necessary to compute PLQY the thing will stop on each points for a given amount of time and record the data to average it
time_exp=1# time of experiment in second
nb_points=2 # Number of position to do , by default it will move along the x axis

# Start Rough stage
startx=8.12
DistPoints=0.1


#############################
# Stable variable
#############################
FileNameData='DataPLQY_'

LockInParaFile='ParameterLockIn.txt'

GeneralPara={'Experiment name':' PLQY','Exposition duration':time_exp,
             'Number of points':nb_points,'Distance between points:':DistPoints}

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
# Initialisation of the Conex Controller
#############################

x_axis=Rtransla.ConexController('COM13')
x_axis.MoveTo(startx)
print('Initialised rough translation stage')

#############################
# Initialisation of the Flip mount
#############################

FlipIS=FlipMount.FlipMount("37007725")
FlipIS.ChangeState(0)
FlipR=FlipMount.FlipMount("37007725")
FlipR.ChangeState(0)
#############################
# Preparation of the directory
#############################

DirectoryPath=FileControl.PrepareDirectory(GeneralPara,InstrumentsPara)

#############################
# Acquisition loop
#############################
print('Begin acquisition')
MesNumber=np.linspace(1,nb_points,nb_points)
IteratorMes=np.nditer(MesNumber, flags=['f_index'])

Laser.StatusShutterTunable(1)

for k in  IteratorMes:
    
    LockInDevice.AutorangeSource()
    DataMes=LockInDevice.AcquisitionLoop(time_exp)

    FileControl.ExportFileLockIn(DirectoryPath,FileNameData+'loop{}'.format(str(k)),DataMes)

Laser.StatusShutterTunable(0)


      
