import ControlLockInAmplifier as lock
import ControlLaser as las
import ControlPulsePicker as picker
import ControlStreakCamera as StreakCamera
import FileControl 
import ControlConex as Rtransla

import numpy as np
import time as time
import os

os.system('cls')
#############################
# Global parameter
#############################


Nb_points=4
DistancePts=0.1

# Streak camera parameter
Nb_exposure=150
Nb_loop=50
MCP_Gain=35

# Start Rough stage
startx=4.1
starty=8.75


# Misc parameter
FileNameData='DataStreakRepeatPos_'


GeneralPara={'Experiment name':' StreakRepeatDiffPos','Nb points':Nb_points,
             'Distance Between Points ':DistancePts,
             'Note':'The SHG unit from Coherent was used'}

InstrumentsPara={}



#############################
# Initialisation of laser
#############################

Laser= las.LaserControl('COM8',0.5)

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

x_axis=Rtransla.ConexController('COM12')
y_axis=Rtransla.ConexController('COM13')
print('Initialised rough translation stage')
x_axis.MoveTo(startx)
y_axis.MoveTo(starty)
#############################
# Initialisation of the streak camera
#############################

sc=StreakCamera.StreakCamera(PortCmd=1001,PortData=1002,Buffer=1024,IniFile='C:\ProgramData\Hamamatsu\HPDTA\SingleSweepExp.ini')
sc.Set_NumberIntegration('AI',Nb_exposure)
sc.Set_MCPGain(MCP_Gain)
InstrumentsPara['Streak camera']={'Nb_exposure':Nb_exposure,'Nb_loop':Nb_loop,'MCP gain':MCP_Gain}


#############################
# Preparation of the directory
#############################
print('Directory staging, please check other window')
DirectoryPath=FileControl.PrepareDirectory(GeneralPara,InstrumentsPara)


#############################
# Printing loop
#############################
print('')

MesNumber=np.linspace(1,Nb_points,Nb_points)
IteratorMes=np.nditer(MesNumber, flags=['f_index'])

print("Begin acquisition")
Laser.StatusShutterTunable(1)
for k in  IteratorMes:
    print('Measurement number:{}'.format(MesNumber[IteratorMes.index]))
    os.mkdir(DirectoryPath+'\\Mes'+str(MesNumber[IteratorMes.index])) 

    x_axis.MoveTo(x_axis.GetPosition()+(MesNumber[IteratorMes.index]+1)*DistancePts)
    

    # Acquisition loop   
    sc.ShutterOpen()
    sc.StartSeq('Analog Integration',Nb_loop)
    sc.AsyncStatusReady()
    sc.ShutterClose()
    sc.BckgSubstraction()
    # Save the data  
    sc.SaveSeq(DirectoryPath+'\\Mes'+str(MesNumber[IteratorMes.index])+'\\000001.img')

sc.Set_MCPGain(0)
Laser.StatusShutterTunable(0)
print('Experiment finished')