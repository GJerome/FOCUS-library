import ControlFlipMount as shutter
import ControlLaser as las
import ControlPulsePicker as picker
import FileControl
import ControlPiezoStage as Transla
import ControlStreakCamera as StreakCamera

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

# Streak camera parameter
Nb_exposure = 50 # number of integration
Nb_loop = 120 # number of loop in the sequence
MCP_Gain = 34

#############################
# Piezo parameter
#############################

#Definition of small grid
'''
start_x = 5
end_x = 20
x = np.linspace(start_x, end_x, int(np.floor(np.sqrt(Nb_Points_subgrid))))

start_y = 5
end_y = 20
y = np.linspace(start_y, end_y, int(np.floor(np.sqrt(Nb_Points_subgrid))))'''
x = (40,60)

y = (40,60)

X, Y = np.meshgrid(x, y)
Pos = np.stack([X.ravel(), Y.ravel()], axis=-1)
index=random.sample(range(0, Pos.shape[0]), Pos.shape[0])
SmallGrid=Pos[index,:]


GeneralPos=SmallGrid
Nb_points=GeneralPos.shape[0]

print('Number of Points:{}\n'.format(Nb_points))


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
# Initialisation of the streak camera
#############################

sc = StreakCamera.StreakCamera(PortCmd=1001, PortData=1002, Buffer=1024,
                               IniFile='C:\ProgramData\Hamamatsu\HPDTA\SingleSweepExp.ini')
sc.Set_NumberIntegration('AI', Nb_exposure)
sc.Set_MCPGain(MCP_Gain)
InstrumentsPara['Streak camera'] = {
    'Nb_exposure': Nb_exposure, 'Nb_loop': Nb_loop, 'MCP gain': MCP_Gain}


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
for k in IteratorMes:

    print('Progress:{}%'.format(np.round(100*k/(GeneralPos.shape[0]),2)),end='\r',flush=True)
    os.mkdir(DirectoryPath+'\\Mes'+str(MesNumber[IteratorMes.index])+'x='+str(np.round(
        Pos[MesNumber[IteratorMes.index], 0], 2))+'y='+str(np.round(Pos[MesNumber[IteratorMes.index], 1], 2)))

    if k==0:
            x_axis.MoveTo(GeneralPos[k,0])
            y_axis.MoveTo(GeneralPos[k,1])
            FM.ChangeState(1)
    else:
            x_axis.MoveTo(GeneralPos[k,0])
            y_axis.MoveTo(GeneralPos[k,1])
    sc.ShutterOpen()
    sc.StartSeq('Analog Integration', Nb_loop)
    sc.AsyncStatusReady()
    sc.ShutterClose()
    sc.BckgSubstraction()
    sc.SaveSeq(DirectoryPath+'\\Mes'+str(MesNumber[IteratorMes.index])+'x='+str(np.round(
        Pos[MesNumber[IteratorMes.index], 0], 2))+'y='+str(np.round(Pos[MesNumber[IteratorMes.index], 1], 2))+'\\000001.img')


FM.ChangeState(0)
Laser.SetStatusShutterTunable(0)