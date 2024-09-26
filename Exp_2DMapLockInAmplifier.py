import ControlFlipMount as shutter
import ControlLaser as las
import ControlPulsePicker as picker
import FileControl
import ControlPiezoStage as Transla
import ControlLockInAmplifier as lock


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
Nb_Points_subgrid=1200
time_exp=0.1 # time of experiment in second

#############################
# Piezo parameter
#############################

#Definition of small line

start_x = 1
end_x = 80
y = np.linspace(start_x, end_x,Nb_Points_subgrid )

#start_y = 5
#end_y = 20
x = 12.5

X, Y = np.meshgrid(x, y)
Pos = np.stack([X.ravel(), Y.ravel()], axis=-1)
index=random.sample(range(0, Pos.shape[0]), Pos.shape[0])
SmallGrid=Pos[index,:]


GeneralPos=SmallGrid

print('Number of Points:{}\n'.format(GeneralPos.shape[0]))


GeneralPara = {'Experiment name': ' DosingExperiment', 'Nb points': Nb_Points_subgrid,
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
# Initialisation of lock-in amplifier
#############################
LockInParaFile='ParameterLockIn.txt'
LockInDevice=lock.LockInAmplifier(LockInParaFile)

InstrumentsPara['Lock-in-amplifier']=LockInDevice.parameterDict


#############################
# Preparation of the directory
#############################
print('Directory staging, please check other window')
DirectoryPath = FileControl.PrepareDirectory(GeneralPara, InstrumentsPara)
pd.DataFrame(GeneralPos).to_csv(DirectoryPath+'/Position.csv')


print('')

MesNumber = np.linspace(0, GeneralPos.shape[0], GeneralPos.shape[0], endpoint=False,dtype=int)
IteratorMes= np.nditer(MesNumber, flags=['f_index'])


Laser.SetStatusShutterTunable(1)
Result=pd.DataFrame(index=np.linspace(0,GeneralPos.shape[0],GeneralPos.shape[0],endpoint=False,dtype=int),columns=['x','y','R1','R1std','R2','R2std'])
for k in IteratorMes:

    print('Progress:{}%'.format(np.round(100*k/(GeneralPos.shape[0]),2)),end='\r',flush=True)
    if k==0:
            x_axis.MoveTo(GeneralPos[k,0])
            y_axis.MoveTo(GeneralPos[k,1])
            FM.ChangeState(1)
    else:
            x_axis.MoveTo(GeneralPos[k,0])
            y_axis.MoveTo(GeneralPos[k,1])
    Data=LockInDevice.AcquisitionLoop(time_exp)
    Result.loc[str(k),'x']=GeneralPos[k,0]
    Result.loc[str(k),'y']=GeneralPos[k,1]
    Result.loc[str(k),'R1']=Data.loc[:,'R1'].mean()
    Result.loc[str(k),'R1std']=Data.loc[:,'R1'].std()
    Result.loc[str(k),'R2']=Data.loc[:,'R2'].mean()
    Result.loc[str(k),'R2std']=Data.loc[:,'R2'].std()


Result.to_csv(DirectoryPath+'/Data.csv')



FM.ChangeState(0)
Laser.SetStatusShutterTunable(0)