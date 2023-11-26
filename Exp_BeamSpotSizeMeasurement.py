import ControlLockInAmplifier as lock
import ControlLaser as las
import ControlPulsePicker as picker
import FileControl 
import ControlConex as Rtransla

import numpy as np
import time as time
import os
import matplotlib.pyplot as plt

os.system('cls')
#############################
# Global parameter
#############################

Dwell_Time=0.1 # timefor each point in second
# We create a test zone define by the  PositionCube variable, on the x_axis we do a frequency sweep and on the y axis a power sweep
PositionCube=[1.5 ,4,1,0.2]# [x_start y_start x_length y_length]
Nb_pts_x=1# Maximum resolution is 0.1um and bi repedability is 2um 
Nb_pts_y=100# Maximum resolution is 0.1um and bi repedability is 2um 
AffineTiltCorrection=0.05760828305799448



FileNameData='DataSpotSize_'

LockInParaFile='ParameterLockIn.txt'

try:
    res_x=PositionCube[2]/Nb_pts_x
    print('Res x={}'.format(res_x))
except ZeroDivisionError:
    res_x=0
try:
    res_y=PositionCube[3]/Nb_pts_y
    print('Res y={}'.format(res_y))
except ZeroDivisionError:
    res_y=0

GeneralPara={'Experiment name':' Dose experiment','Dwelling time':Dwell_Time,
             'Distance between two points y':res_x,
             'Distance between two points x':res_y,
             'Tilt correction':AffineTiltCorrection,
             'Note':'The SHG unit from Coherent was used'}
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
# Initialisation of pulse picker
#############################

pp=picker.PulsePicker("USB0::0x0403::0xC434::S09748-10A7::INSTR")
InstrumentsPara['Pulse picker']=pp.parameterDict
pp.SetDivRatio(20)
pp.SetPower(17500)
print('Initialised pulse picker')

#############################
# Initialisation of the Conex Controller
#############################


x_axis=Rtransla.ConexController('COM13')
y_axis=Rtransla.ConexController('COM12')
z_axis=Rtransla.ConexController('COM14')
z_axis.MoveTo(5)
print('Initialised rough translation stage')

#############################
# Preparation of the directory
#############################
print('Directory staging, please check other window')
DirectoryPath=FileControl.PrepareDirectory(GeneralPara,InstrumentsPara)


#############################
# Printing loop
#############################
print('')

x_pos=np.linspace(PositionCube[0],PositionCube[0]+PositionCube[2],Nb_pts_x)
y_pos=np.linspace(PositionCube[1],PositionCube[1]+PositionCube[3],Nb_pts_y)
z_pos=np.linspace(z_axis.GetPosition(),z_axis.GetPosition()+AffineTiltCorrection*PositionCube[3],Nb_pts_y)


IteratorX=np.nditer(x_pos, flags=['f_index'])
IteratorY=np.nditer(y_pos, flags=['f_index'])


IntensityData=np.zeros(len(y_pos))
IntensityData2=np.zeros(len(y_pos))
ErrorBar=np.zeros(len(y_pos))
ErrorBar2=np.zeros(len(y_pos))
x_pos_real=np.zeros(len(y_pos))
y_pos_real=np.zeros(len(y_pos))

print("Begin acquisition")
Laser.StatusShutterTunable(1)
time.sleep(3)
for k in  IteratorX:
    x_axis.MoveTo(x_pos[IteratorX.index])    
    
    for j in IteratorY:      
        y_axis.MoveTo(y_pos[IteratorY.index])
        z_axis.MoveTo(z_pos[IteratorY.index])
        #LockInDevice.AutorangeSource()
        data_Source1,t1,data_Source2,t2=LockInDevice.AcquisitionLoop(Dwell_Time)

        #############################
        # Interpolation to the same timebase
        #############################

        data_Source2_interp=np.interp(t1,t2,data_Source2)
        t1_scaled=(t1-t1[1])/LockInDevice.Timebase

        IntensityData[IteratorY.index]=np.mean(data_Source1[1:])
        ErrorBar[IteratorY.index]=np.std(data_Source1[1:])
        IntensityData2[IteratorY.index]=np.mean(data_Source2_interp[1:])
        ErrorBar2[IteratorY.index]=np.std(data_Source2_interp[1:])
        y_pos_real[IteratorY.index]=y_axis.GetPosition()
        FileControl.printProgressBar(IteratorY.index + 1, len(y_pos), prefix = 'Progress:', suffix = 'Complete', length = 50)        
        
      
    ExportData=np.array(np.transpose([IntensityData,ErrorBar,IntensityData2,ErrorBar2,y_pos_real]))
    FileControl.ExportFileChopperOptimisation(DirectoryPath,FileNameData+'x={}'.format(str(x_axis.GetPosition())),ExportData)    
    IteratorY.reset()
Laser.StatusShutterTunable(0)
z_axis.MoveTo(z_pos[0])
cm=1/2.54

fig=plt.figure(figsize=(6*cm, 5*cm))
ax0=plt.subplot(1,1,1)
ax0.set_xlabel('y [mm]')
ax0.set_ylabel('Intensity[V]')
ax0.plot(y_pos_real,IntensityData2)
ax0.fill_between(y_pos_real, IntensityData2-ErrorBar2,IntensityData2+ErrorBar2, alpha=0.5)

plt.tight_layout()
plt.show()