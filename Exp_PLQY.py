import ControlLockInAmplifier as lock
import ControlLaser as las
import ControlConex as Rtransla

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

    data_Source1,t1,data_Source2,t2=LockInDevice.AcquisitionLoop(time_exp)

    #############################
    # Interpolation to the same timebase
    #############################

    data_Source2_interp=np.interp(t1,t2,data_Source2)
    t1_scaled=(t1-t1[1])/LockInDevice.Timebase

    export_data=(t1_scaled,data_Source2_interp,data_Source1)
    FileControl.ExportFileLockIn(DirectoryPath,FileNameData+'loop{}'.format(str(k)),export_data)

    
    print('The sample is sleeping')
    Laser.StatusShutterTunable(0)
    


Laser.StatusShutterTunable(0)

      
