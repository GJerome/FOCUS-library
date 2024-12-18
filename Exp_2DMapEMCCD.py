import ControlFlipMount as shutter
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
Nb_Points_subgrid=2500
EMGain=20

# The way it is set up is so that it will iterate thought Divratio and take the associated element in PowerPulsePicker
#So first element of DivRatio will take the first element of PowerPulsePicker
DivRatio=4
PowerPulsePicker=500
ProbePower=5# Power of the probe in uW. This will not change anything in the scipt it is just for recording purpose
Spectrograph_slit=10 # This is just for record not actually setting it up
Spectrograph_Center=750# This is just for record not actually setting it up
BeamRadius=10
#############################
# Piezo parameter
#############################

#Definition of small grid

start_x =5
end_x = 80
start_y = 5
end_y = 80


x = np.linspace(start_x, end_x, int(np.floor(np.sqrt(Nb_Points_subgrid))))
y = np.linspace(start_y, end_y, int(np.floor(np.sqrt(Nb_Points_subgrid))))

X, Y = np.meshgrid(x, y)
Pos = np.stack([X.ravel(), Y.ravel()], axis=-1)
index=random.sample(range(0, Pos.shape[0]), Pos.shape[0])
SmallGrid=Pos[index,:]

Nb_Points=SmallGrid.shape[0]

# Once we randomize a first time we just try to make each next point as far as posible of the other
def DistanceTwoPoint(pointA, pointB):
    return np.sqrt(np.sum((pointA - pointB)**2, axis=0))

def DistanceArray(pointA, pointsB):
    return np.sqrt(np.sum((pointA - pointsB)**2, axis=1))

PosFiltered=np.empty(SmallGrid.shape)
for index in range(Nb_Points):
    if index==0:
        PosFiltered[index,:]=SmallGrid[0,:]
        SmallGrid=np.delete(SmallGrid,0,0)
    else:
        if DistanceTwoPoint(PosFiltered[index-1,:],SmallGrid[0,:])<BeamRadius:
            temp=pd.Series(DistanceArray(PosFiltered[index-1,:],SmallGrid))
            try:            
                a=temp.loc[temp>BeamRadius].index[0]
            except:
                 print('Could not find a point not within the beam avoidance radius.')
                 a=0
            PosFiltered[index,:]=SmallGrid[a,:]
            SmallGrid=np.delete(SmallGrid,a,0)

        else:
            PosFiltered[index,:]=SmallGrid[0,:]
            SmallGrid=np.delete(SmallGrid,0,0)
    
GeneralPos=PosFiltered


print('Number of Points:{}\n'.format(GeneralPos.shape[0]))


GeneralPara = {'Experiment name': ' PLMap', 'Nb points': Nb_Points_subgrid,'Beam avoidance radius':BeamRadius,
               'Power pulse picker':PowerPulsePicker,'Div ratio':DivRatio,'Probe recorded power before BS [uW]':ProbePower,
               'Spectro center wavelength':Spectrograph_Center,'spectro slit width':Spectrograph_slit,
               'Note': 'The SHG unit from Coherent was used'}

InstrumentsPara = {}

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
pp.SetPower(PowerPulsePicker)
pp.SetDivRatio(DivRatio)
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
    x_axis = Transla.PiezoAxisControl(piezo, 'y',3)
    y_axis = Transla.PiezoAxisControl(piezo, 'z',3)
    print('Initialised piezo translation stage')



#############################
# Initialisation of the shutter
#############################

FM = shutter.FlipMount("37007726")
print('Initialised Flip mount')

#############################
# Initialisation of the EMCCD
#############################

camera = EMCCD.LightFieldControl('ML')
FrameTime = camera.GetFrameTime()
ExposureTime = camera.GetExposureTime()
camera.SetNumberOfFrame(1.0)
camera.SetEMGain(EMGain)
NumberOfFrame = camera.GetNumberOfFrame()
InstrumentsPara['PI EMCCD'] = camera.parameterDict
print('Initialised EMCCD')

#############################
# Preparation of the directory
#############################
print('Directory staging, please check other window')
DirectoryPath = FileControl.PrepareDirectory(GeneralPara, InstrumentsPara)
pd.DataFrame(GeneralPos).to_csv(DirectoryPath+'/Position.csv')
camera.SetSaveDirectory(DirectoryPath.replace('/',"\\"))

print('')

MesNumber = np.linspace(0, GeneralPos.shape[0], GeneralPos.shape[0], endpoint=False,dtype=int)
IteratorMes= np.nditer(MesNumber, flags=['f_index'])


Laser.SetStatusShutterTunable(1)
for k in IteratorMes:

    print('Progress:{}%'.format(np.round(100*k/(GeneralPos.shape[0]),2)),end='\r',flush=True)
    if k==0:
            x_axis.MoveTo(GeneralPos[k,0])
            y_axis.MoveTo(GeneralPos[k,1])
            FM.ChangeState(1)
    else:
            x_axis.MoveTo(GeneralPos[k,0])
            y_axis.MoveTo(GeneralPos[k,1])
    camera.Acquire()
    camera.WaitForAcq()



FM.ChangeState(0)
Laser.SetStatusShutterTunable(0)