import ControlLockInAmplifier as lock
import ControlLaser as las
import ControlPiezoStage as Transla
import ControlFlipMount as FlipMount
import ControlThorlabsShutter as ThorlabsShutter

import numpy as np

import FileControl 
import sys
from os import mkdir
import random
import time

#############################
# Global parameter
#############################

# For each measurement necessary to compute PLQY the thing will stop on each points for a given amount of time and record the data to average it
time_exp=5# time of experiment in second
Nb_Points =4  # Number of position for the piezo

BeamRadius=15
FilterRelaxTime=5


start_x =1
end_x = 79
start_y = 1
end_y = 79
#############################
# Piezo parameter
#############################


if start_x==end_x:
    x = np.array([start_x])
    y = np.linspace(start_y, end_y, int(Nb_Points))
elif start_y==end_y:
    y = np.array([start_y])
    x = np.linspace(start_x, end_x, int(Nb_Points))
else:
    x = np.linspace(start_x, end_x, int(np.floor(np.sqrt(Nb_Points))))
    y = np.linspace(start_y, end_y, int(np.ceil(np.sqrt(Nb_Points))))

X, Y = np.meshgrid(x, y)
Pos = np.stack([X.ravel(), Y.ravel()], axis=-1)
index=random.sample(range(0, Pos.shape[0]), Pos.shape[0])
Pos=Pos[index,:]
Nb_Points=Pos.shape[0]

# Once we randomize a first time we just try to make each next point as far as posible of the other
def DistanceTwoPoint(pointA, pointB):
    return np.sqrt(np.sum((pointA - pointB)**2, axis=0))

def DistanceArray(pointA, pointsB):
    return np.sqrt(np.sum((pointA - pointsB)**2, axis=1))

PosFiltered=np.empty(Pos.shape)
for index in range(Nb_Points):
    if index==0:
        PosFiltered[index,:]=Pos[0,:]
        Pos=np.delete(Pos,0,0)
    else:
        if DistanceTwoPoint(PosFiltered[index-1,:],Pos[0,:])<BeamRadius:            
            a=np.argmax(DistanceArray(PosFiltered[index-1,:],Pos)>BeamRadius)
            PosFiltered[index,:]=Pos[a,:]
            Pos=np.delete(Pos,a,0)
            if a==0:
                print('Could not find a point not within the beam avoidance radius.')
        else:
            PosFiltered[index,:]=Pos[0,:]
            Pos=np.delete(Pos,0,0)
    
Pos=PosFiltered


#############################
# Stable variable
#############################
FileNameData='DataPLQY_'

LockInParaFile='ParameterLockIn.txt'

GeneralPara={'Experiment name':' PLQY','Exposition duration':time_exp,
             'Number of points':Nb_Points}

InstrumentsPara={}
#############################
# Initialisation of lock-in amplifier
#############################

LockInDevice=lock.LockInAmplifier(LockInParaFile)
InstrumentsPara['Lock-in-amplifier']=LockInDevice.parameterDict

#############################
# Initialisation of laser
#############################

Laser = las.LaserControl('COM8', 'COM17', 2)

InstrumentsPara['Laser'] = Laser.parameterDict
print('Initialised Laser')

#############################
# Initialisation of Piezo
#############################
if 'ControlConex' in sys.modules:
    x_axis = Transla.ConexController('COM12')
    y_axis = Transla.ConexController('COM13')
    print('Initialised rough translation stage')

elif 'ControlPiezoStage' in sys.modules:
    piezo = Transla.PiezoControl('COM15')
    x_axis = Transla.PiezoAxisControl(piezo, 'y',3)
    y_axis = Transla.PiezoAxisControl(piezo, 'z',3)
    print('Initialised piezo translation stage')


#############################
# Initialisation of the Flip mount
#############################


FM_Ref = FlipMount.FlipMount("37007725",'Reflexion')#State 1 is longpass filter
FM_IS = FlipMount.FlipMount("37007726",'IS') #State 1 is longpass filter
InstrumentsPara['FlipMount']=FM_IS.parameterDict | FM_Ref.parameterDict
FM_Ref.ChangeState(1)
FM_IS.ChangeState(1)

Shutter = ThorlabsShutter.ShutterControl("68800883",'Shutter')
Shutter.SetClose()
print('Initialised  shutter and Flip mount')

#############################
# Preparation of the directory
#############################

DirectoryPath=FileControl.PrepareDirectory(GeneralPara,InstrumentsPara)

#############################
# Acquisition loop
#############################
print('Begin acquisition')
MesNumber=np.linspace(1,Nb_Points,Nb_Points)
IteratorMes=np.nditer(MesNumber, flags=['f_index'])

Laser.SetStatusShutterTunable(1)

for k in  IteratorMes:

    x_axis.MoveTo(Pos[IteratorMes.index, 0])
    y_axis.MoveTo(Pos[IteratorMes.index, 1])

    TempDirPath = DirectoryPath+'/Mes'+str(MesNumber[IteratorMes.index])+'_Longpass'
    mkdir(TempDirPath)

    FM_Ref.ChangeState(1)
    FM_IS.ChangeState(1)
    Shutter.SetOpen()
    LockInDevice.AutorangeSource()
    time.sleep(FilterRelaxTime)


    DataMes=LockInDevice.AcquisitionLoop3W(time_exp)
    Shutter.SetClose()
    FileControl.ExportFileLockIn(TempDirPath,FileNameData+'loop{}'.format(str(k)),DataMes)

    TempDirPath = DirectoryPath+'/Mes'+str(MesNumber[IteratorMes.index])+'_Shortpass'
    mkdir(TempDirPath)

    FM_Ref.ChangeState(0)
    FM_IS.ChangeState(0)
    Shutter.SetOpen()
    LockInDevice.AutorangeSource()
    time.sleep(FilterRelaxTime)

    DataMes=LockInDevice.AcquisitionLoop3W(time_exp)
    Shutter.SetClose()
    FileControl.ExportFileLockIn(TempDirPath,FileNameData+'loop{}'.format(str(k)),DataMes)


Laser.StatusShutterTunable(0)


      
