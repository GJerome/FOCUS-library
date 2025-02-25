import ControlFlipMount as FlipMount
import ControlLaser as las
import ControlPulsePicker as picker
import FileControl
import ControlPiezoStage as Transla
import ControlEMCCD as EMCCD
import ControlFilterWheel as FilterWheel
import ControlThorlabsShutter as shutter
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

#############################
# Global parameter
#############################



# The way it is set up is so that it will iterate thought Divratio and take the associated element in PowerPulsePicker
#So first element of DivRatio will take the first element of PowerPulsePicker
DivRatio=4
PowerPulsePicker=500
ProbePower=5 # Power of the probe in uW. This will not change anything in the scipt it is just for recording purpose
Spectrograph_slit=100 # This is just for record not actually setting it up
Spectrograph_Center=700 # This is just for record not actually setting it up
BeamRadius=10 

#############################
# Piezo parameter
#############################


FileNameData='DataDoseExperiement_'

LockInParaFile='ParameterLockIn.txt'

GeneralPara = {'Experiment name': ' PLMap', 'Beam avoidance radius':BeamRadius,
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
# Initialisation of the flipmounts
#############################

FM1 = FlipMount.FlipMount("37007725")
FM2 = FlipMount.FlipMount("37007726")

print('Initialised Flip mount')

#############################
# Initialisation of the shutter
#############################

FW = FilterWheel.FilterWheel('COM18')

print('Initialised Filter Wheel')

#############################
# Initialisation of the Shutter
#############################

Shutter = shutter.ShutterControl("68800883",'Shutter')

print('Initialised Shutter')

#############################
# Initialisation of the EMCCD
#############################

camera = EMCCD.LightFieldControl('TimeTraceEMMarcel')
FrameTime = camera.GetFrameTime()
ExposureTime = camera.GetExposureTime()
NumberOfFrame = camera.GetNumberOfFrame()
InstrumentsPara['PI EMCCD'] = camera.parameterDict
print('Initialised EMCCD')


#############################
# Printing loop
#############################
print('Directory staging, please check other window')
DirectoryPath = FileControl.PrepareDirectory(GeneralPara, InstrumentsPara)
#pd.DataFrame(GeneralPos).to_csv(DirectoryPath+'/Position.csv')
camera.SetSaveDirectory(DirectoryPath.replace('/',"\\"))

print('')

print("Begin acquisition")

Shutter.SetClose()
Laser.SetStatusShutterTunable(1)

experimentlist = pd.read_csv('D:/Data/25-02-18-MaPb(Br0.5I0.5)3-timetrace/ParametersTimetraceExperiment.csv') 
for i in range(3):
  for index, row in experimentlist.iterrows():
    print('Measurement {},{}'.format(row['Rep-rate'],row['AvgPower']))
    FW.set_position(row['FilterwheelPos'])
    pp.SetDivRatio(row['Div ratio'])
    pp.SetPower(row['PP power'])

    x_axis.MoveTo(row['PosX'])
    y_axis.MoveTo(row['PosY'])
   # print('Laser on the sample with a div ratio of {} and a power of {}'.format(pp.GetDivRatio(),pp.GetPower()))
    Shutter.SetOpen()
    camera.Acquire()   
    camera.WaitForAcq() 
    Shutter.SetClose()

Laser.SetStatusShutterTunable(0)
print('Experiment finished')
