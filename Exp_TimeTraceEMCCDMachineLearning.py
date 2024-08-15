import ControlFlipMount as shutter
import ControlLaser as las
import ControlPulsePicker as picker
import ControlEMCCD as EMCCD
import FileControl
# import ControlConex as Rtransla
import ControlPiezoStage as Transla

import numpy as np
import time as time
import os
import sys

os.system('cls')

#############################
# Global parameter
#############################


Nb_Points = 10  # Number of position for the piezo
Nb_Cycle = 10  # Number of cycle during experiment
DistancePts = 10

StabilityTime = 100

#############################
# Piezo parameter
#############################

start_x = 20
end_x = 80
x = np.linspace(start_x, end_x, int(np.floor(np.sqrt(Nb_Points))))

start_y = 20
end_y = 80
y = np.linspace(start_y, end_y, int(np.ceil(np.sqrt(Nb_Points))))

X, Y = np.meshgrid(x, y)
Pos = np.stack([X.ravel(), Y.ravel()], axis=-1)
print('Number of Points:{}\nDistance between points:\n\t x ={} \n\t y ={}'.format(len(Pos),
                                                                                  x[1]-x[0], y[1]-y[0]))


GeneralPara = {'Experiment name': ' EMCCDRepeatDiffPos', 'Nb points': Nb_Points,
               'Distance Between Points ': DistancePts,
               'Note': 'The SHG unit from Coherent was used'}

InstrumentsPara = {}
##############################################################
# Parameter space and random choice
##############################################################

###################
# Proba density function Power
###################
P = (0, 1, 10, 100, 1000)  # power

p0 = [0.2, 0.2, 0.2, 0.2, 0.2]
p1 = [0.3, 0.175, 0.175, 0.175, 0.175]
ProbaP = p1

###################
# Proba density function Time
###################
t = (0.1, 1, 10, 100)  # time

p0 = [0.25, 0.25, 0.25, 0.25]
p1 = [0.3, 0.23, 0.23, 0.24]
ProbaT = p1

###################
# RNG declaration
###################
rng = np.random.default_rng()

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
# Initialisation of the Conex Controller
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
# Initialisation of the EMCCD
#############################

camera = EMCCD.LightFieldControl('TimeTraceEM')
FrameTime = camera.GetFrameTime()
ExposureTime = camera.GetExposureTime()
NumberOfFrame = camera.GetNumberOfFrame()

print('Initialised EMCCD')

#############################
# Initialisation of the shutter
#############################

FM = shutter.FlipMount("37007725")
print('Initialised Flip mount')

#############################
# Preparation of the directory
#############################
print('Directory staging, please check other window')
DirectoryPath = FileControl.PrepareDirectory(GeneralPara, InstrumentsPara)


#############################
# TimeTrace loop
#############################
print('')
MesNumber = np.linspace(1, Nb_Points, Nb_Points, endpoint=False)
IteratorMes = np.nditer(MesNumber, flags=['f_index'])

CycNumber = np.linspace(1, Nb_Cycle, Nb_Cycle, endpoint=False)
IteratorCyc = np.nditer(MesNumber, flags=['f_index'])

Laser.SetStatusShutterTunable(1)

for k in IteratorMes:
    # Generation of the folder and measurement prep
    print('Measurement number:{}'.format(MesNumber[IteratorMes.index]))
    TempDirPath = DirectoryPath+'\\Mes'+str(MesNumber[IteratorMes.index])+'x='+np.round(
        Pos[MesNumber[IteratorMes.index], 0], 2)+'y='+np.round(Pos[MesNumber[IteratorMes.index], 1], 2)
    os.mkdir(TempDirPath)
    x_axis.MoveTo(Pos[MesNumber[IteratorMes.index], 0])
    y_axis.MoveTo(Pos[MesNumber[IteratorMes.index], 1])

    # Intensity/Power Cycle generation
    p_cyc = rng.choice(P, Nb_Cycle, p=ProbaP)
    t_cyc = rng.choice(t, Nb_Cycle, p=ProbaT)

    if p_cyc[0] == 0:
        p_cyc[0] = rng.choice(P[1:], 1, p=ProbaP[1:]/np.sum(ProbaP))

    T_tot = np.sum(t_cyc)

    # Camera setting adjustement
    NbFrameCycle = np.ceil((T_tot+StabilityTime)/FrameTime)
    camera.SetNumberOfFrame(NbFrameCycle)
    # Acquire loop
    camera.Acquire()
    for j in IteratorCyc:

    camera.WaitForAcq()


Laser.SetStatusShutterTunable(0)
