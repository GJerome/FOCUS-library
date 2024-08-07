import ControlLockInAmplifier as lock
import ControlLaser as las
import ControlPulsePicker as picker
import ControlEMCCD as EMCCD
import FileControl 
#import ControlConex as Rtransla
import ControlPiezoStage as Ftransla

import numpy as np
import time as time
import os
import sys

os.system('cls')
#############################
# Global parameter
#############################

# Carefull now using piezo 
Nb_points=5

DistancePts=10

# Start piezo stage
startx=0
starty=0



GeneralPara={'Experiment name':' EMCCDRepeatDiffPos','Nb points':Nb_points,
             'Distance Between Points ':DistancePts,
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
    x_axis=Ftransla.PiezoAxisControl(piezo,'x')
    y_axis=Ftransla.PiezoAxisControl(piezo,'y')
    print('Initialised piezo translation stage')

x_axis.MoveTo(startx)
y_axis.MoveTo(starty)
#############################
# Initialisation of the EMCCD
#############################

camera=EMCCD.LightFieldControl('TimeTraceEM')
print('Initialised EMCCD')




#############################
# Printing loop
#############################
print('')

MesNumber=np.linspace(1,Nb_points,Nb_points)
IteratorMes=np.nditer(MesNumber, flags=['f_index'])

print("Begin acquisition")
Laser.SetStatusShutterTunable(0)
for k in  IteratorMes:
    print('Measurement number:{}'.format(MesNumber[IteratorMes.index]))
    #os.mkdir(DirectoryPath+'\\Mes'+str(MesNumber[IteratorMes.index])) 

    x_axis.MoveTo(startx+(MesNumber[IteratorMes.index]+1)*DistancePts)
    camera.Acquire()
    time.sleep(1)# This is just to wait for the exp to begin
    Laser.SetStatusShutterTunable(1)
    camera.WaitForAcq()    
    Laser.SetStatusShutterTunable(0)
    #time.sleep(10)

time.sleep(5)
print('Experiment finished')