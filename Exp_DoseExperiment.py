import ControlFlipMount as shutter
import ControlLaser as las
import ControlPulsePicker as picker
import FileControl
import ControlPiezoStage as Transla

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
Nb_Points_subgrid=16

#List of Power
P_eff = (15, 200)  # power in uW
P_calib = ( 500, 16.2)  # Power from the pp to reach values of P

#List of time exposure
t_exp = (10, 1000)  

P, T = np.meshgrid(P_calib, t_exp)
PT = np.stack([P.ravel(), T.ravel()], axis=-1)



#############################
# Piezo parameter
#############################

#Definition of small grid

start_x = 0
end_x = 13.6
x = np.linspace(start_x, end_x, int(np.floor(np.sqrt(Nb_Points_subgrid))))

start_y = 0
end_y = 13.6
y = np.linspace(start_y, end_y, int(np.ceil(np.sqrt(Nb_Points_subgrid))))

X, Y = np.meshgrid(x, y)
Pos = np.stack([X.ravel(), Y.ravel()], axis=-1)
index=random.sample(range(0, 16), 16)
SmallGrid=Pos[index,:]

#Definition of big grid


Nb_Points_grid_Power=len(P_eff)
start_x = 0
end_x = 66.4
x = np.linspace(start_x, end_x, Nb_Points_grid_Power)

Nb_Points_grid_time=len(t_exp)
start_y = 0
end_y = 66.4
y = np.linspace(start_y, end_y, Nb_Points_grid_time)

X, Y = np.meshgrid(x, y)
Pos = np.stack([X.ravel(), Y.ravel()], axis=-1)
BigGrid=Pos

GeneralPos=np.zeros([Nb_Points_subgrid*Nb_Points_grid_Power*Nb_Points_grid_time,2])

for j in range(BigGrid.shape[0]):
    GeneralPos[j*Nb_Points_subgrid:(j+1)*Nb_Points_subgrid,:]=SmallGrid+BigGrid[j,:]


print('Number of Points:{}\n'.format(GeneralPos.shape[0]))


GeneralPara = {'Experiment name': ' DosingExperiment', 'Nb points': Nb_Points_subgrid*Nb_Points_grid_Power*Nb_Points_grid_time,
               'Point List': GeneralPos,
               'Power list':P_eff,
               'Power Calib':P_calib,
               'Exposure time':t_exp,
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
    x_axis = Transla.PiezoAxisControl(piezo, 'x')
    y_axis = Transla.PiezoAxisControl(piezo, 'y')
    print('Initialised piezo translation stage')



#############################
# Initialisation of the shutter
#############################

FM = shutter.FlipMount("37007726")
print('Initialised Flip mount')

#############################
# Preparation of the directory
#############################
print('Directory staging, please check other window')
DirectoryPath = FileControl.PrepareDirectory(GeneralPara, InstrumentsPara)
# Saving the list of position
mat.rcParams.update({'font.size': 9, 'font.family': 'sans-serif', 'font.sans-serif': ['Arial'],
                         'xtick.labelsize': 9, 'ytick.labelsize': 9,
                           'figure.dpi': 300, 'savefig.dpi': 300,
                             'figure.figsize': (10/2.5,10/2.5)})

fig1,ax=plt.subplots(1,1)
ax.scatter(GeneralPos[:,0],GeneralPos[:,1])
ax.set_xlabel('x[$\\mu$m]')
ax.set_ylabel('y[$\\mu$m]')
plt.tight_layout()
plt.savefig(DirectoryPath+'/Points.png')
#############################
# TimeTrace loop
#############################
print('')
MesNumber = np.linspace(0, Nb_Points_grid_Power*Nb_Points_grid_time, Nb_Points_grid_Power*Nb_Points_grid_time, endpoint=False,dtype=int)
IteratorMes= np.nditer(MesNumber, flags=['f_index'])

MesSubgrid = np.linspace(0, Nb_Points_subgrid, Nb_Points_subgrid, endpoint=False,dtype=int)
IteratorMesSubgrid= np.nditer(MesSubgrid, flags=['f_index'])

Laser.SetStatusShutterTunable(1)
FM.ChangeState(0)

for k in IteratorMes:
    print('Exposure Time: {}s'.format(PT[k,1]))
    print('Power :{}'.format(PT[k,0]))
    pp.SetPower(PT[k,0])
    print('Progress:{}%'.format(np.round(100*k/(PT.shape[0]),2)))
    Pos=GeneralPos[k*Nb_Points_subgrid:(k+1)*Nb_Points_subgrid,:]

    
    for j in IteratorMesSubgrid:
        if j==0:
            x_axis.MoveTo(Pos[j,0])
            y_axis.MoveTo(Pos[j,1])
            FM.ChangeState(1)
        else:
            x_axis.MoveTo(Pos[j,0])
            y_axis.MoveTo(Pos[j,1])
        time.sleep(PT[k,1])
    IteratorMesSubgrid.reset()
    FM.ChangeState(0)
    print('')

Laser.SetStatusShutterTunable(0)
