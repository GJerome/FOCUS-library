import ControlLaser as las
import ControlPulsePicker as picker
import ControlEMCCD as EMCCD
import FileControl 
import ControlFlipMount as shutter
#import ControlConex as Rtransla
import ControlPiezoStage as Ftransla

import numpy as np
import time as time
import os
import sys
import pandas as pd
import random

os.system('cls')
#############################
# Global parameter
#############################
TimeTimeTrace=10*60
#Position Stage

x = (40,50,60)

y = (40,50,60)

X, Y = np.meshgrid(x, y)
Pos = np.stack([X.ravel(), Y.ravel()], axis=-1)
index=random.sample(range(0, Pos.shape[0]), Pos.shape[0])
Pos=Pos[index,:]

print('Pos: {}'.format(Pos))
Nb_points=Pos.shape[0]

GeneralPara={'Experiment name':' EMCCDRepeatDiffPos','Nb points':Nb_points,
             'Note':'The SHG unit from Coherent was used'}

InstrumentsPara={}



#############################
# Initialisation of laser
#############################

Laser= las.LaserControl('COM8','COM17',0.5)

InstrumentsPara['Laser']=Laser.parameterDict
print('Initialised Laser')
#############################
# Initialisation of pulse picker
#############################

pp=picker.PulsePicker("USB0::0x0403::0xC434::S09748-10A7::INSTR")
InstrumentsPara['Pulse picker']=pp.parameterDict
print('Initialised pulse picker')

#############################
# Initialisation of the Conex Controller
#############################
if 'ControlConex' in sys.modules:
    x_axis=Rtransla.ConexController('COM12')
    y_axis=Rtransla.ConexController('COM13')
    print('Initialised rough translation stage')

elif 'ControlPiezoStage' in sys.modules:
    piezo= Ftransla.PiezoControl('COM15')
    x_axis=Ftransla.PiezoAxisControl(piezo,'y',3)
    y_axis=Ftransla.PiezoAxisControl(piezo,'z',3)
    print('Initialised piezo translation stage')

x_axis.MoveTo(0.1)
y_axis.MoveTo(0.1)
#############################
# Initialisation of the EMCCD
#############################

camera=EMCCD.LightFieldControl('TimeTraceEM')
FrameTime = camera.GetFrameTime()
ExposureTime = camera.GetExposureTime()
NumberOfFrame = camera.GetNumberOfFrame()
InstrumentsPara['PI EMCCD'] = camera.parameterDict
NbFrameCycle = np.ceil((TimeTimeTrace)/FrameTime)
camera.SetNumberOfFrame(NbFrameCycle)
print('Initialised EMCCD')


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
pd.DataFrame(Pos).to_csv(DirectoryPath+'/Position.csv')
camera.SetSaveDirectory(DirectoryPath.replace('/',"\\"))

MesNumber = np.linspace(0, Pos.shape[0], Pos.shape[0], endpoint=False,dtype=int)
IteratorMes= np.nditer(MesNumber, flags=['f_index'])

print("Begin acquisition")
Laser.SetStatusShutterTunable(1)
for k in  IteratorMes:
    print('Measurement number:{}'.format(MesNumber[IteratorMes.index]))
    x_axis.MoveTo(Pos[k,0])
    y_axis.MoveTo(Pos[k,1])
    
    #FM.ChangeState(1)
    print('\t x:{}um \n\t y:{} um'.format(x_axis.GetPosition(),y_axis.GetPosition()))
    camera.Acquire()
    camera.WaitForAcq()    
    #FM.ChangeState(0)
Laser.SetStatusShutterTunable(0)
print('Experiment finished')