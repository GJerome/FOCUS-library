import ControlFlipMount as shutter
import ControlLaser as las
import ControlPulsePicker as picker
import ControlEMCCD as EMCCD
import FileControl
import ControlPiezoStage as Transla

import numpy as np
import pandas as pd
import time as time
import os
import sys

os.system('cls')

#############################
# Global parameter
#############################


Nb_Points = 100  # Number of position for the piezo
Nb_Cycle = 10  # Number of cycle during experiment
DistancePts = 10

StabilityTime = 30
OnlyOneConfig=False

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
try:
    print('Number of Points:{}\nDistance between points:\n\t x ={} \n\t y ={}'.format(len(Pos),
                                                                                  x[1]-x[0], y[1]-y[0]))
except IndexError:
    print('Number of Points:{}\n'.format(len(Pos)))

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
P = (0, 4.4, 10, 100, 800)  # power in uW
P_calib = (500, 500, 900, 2500, 9200)  # Power from the pp to reach values of P

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

if OnlyOneConfig==True:
    # Intensity/Power Cycle generation
    T_final = rng.choice(t, Nb_Cycle, p=ProbaT)
    # First we generate an array of cycle which only contains index for the moment
    P_Final = rng.choice(np.linspace(0, len(P), len(
        P), endpoint=False, dtype=int), Nb_Cycle, p=ProbaP)

    while P_Final[0] == 0:  # We assume that the first element of P is the zero power element
        P_Final = rng.choice(np.linspace(0, len(P), len(P), endpoint=False, dtype=int), Nb_Cycle, p=ProbaP)
    

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
InstrumentsPara['PI EMCCD'] = camera.parameterDict
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


#############################
# TimeTrace loop
#############################
print('')
MesNumber = np.linspace(0, Nb_Points, Nb_Points, endpoint=False)
IteratorMes = np.nditer(MesNumber, flags=['f_index'])

CycNumber = np.linspace(0, Nb_Cycle, Nb_Cycle, endpoint=False)
IteratorCyc = np.nditer(CycNumber, flags=['f_index'])

Laser.SetStatusShutterTunable(1)
FM.ChangeState(0)
for k in IteratorMes:
    # Generation of the folder and measurement prep
    print('Measurement number:{}'.format(MesNumber[IteratorMes.index]))
    TempDirPath = DirectoryPath+'/Mes'+str(MesNumber[IteratorMes.index])+'x='+str(np.round(
        Pos[IteratorMes.index, 0], 2))+'y='+str(np.round(Pos[IteratorMes.index, 1], 2))
    os.mkdir(TempDirPath)

    camera.SetSaveDirectory(TempDirPath.replace('/',"\\"))
    
    x_axis.MoveTo(Pos[IteratorMes.index, 0])
    y_axis.MoveTo(Pos[IteratorMes.index, 1])

    # Intensity/Power Cycle generation
    t_cyc = rng.choice(t, Nb_Cycle, p=ProbaT)
    # First we generate an array of cycle which only contains index for the moment
    temp = rng.choice(np.linspace(0, len(P), len(
        P), endpoint=False, dtype=int), Nb_Cycle, p=ProbaP)

    while temp[0] == 0:  # We assume that the first element of P is the zero power element
        temp = rng.choice(np.linspace(0, len(P), len(P), endpoint=False, dtype=int), Nb_Cycle, p=ProbaP)
    if OnlyOneConfig==True:
        temp= P_Final
        t_cyc= T_final
    p_cyc_calib = np.array([P_calib[i] for i in temp])
    p_cyc = np.array([P[i] for i in temp])


    T_tot = np.sum(t_cyc)

    # Camera setting adjustement
    NbFrameCycle = np.ceil((T_tot+StabilityTime)/FrameTime)
    camera.SetNumberOfFrame(NbFrameCycle)
    print('Time cycle:{}'.format(t_cyc))
    print('Power cycle:{}'.format(p_cyc))
    print('Real Power cycle:{}'.format(p_cyc_calib))
    print('Total time={}'.format(T_tot+StabilityTime))

    #Create timing parameter
    t_sync=np.zeros(len(t_cyc))
    FM.ChangeState(0)
    camera.Acquire()  # Launch acquisition
    t0=time.time()
    # Power iteration
    for j in IteratorCyc:
        print('Cycle {}: P={},t={}'.format(IteratorCyc.index,p_cyc[IteratorCyc.index],t_cyc[IteratorCyc.index]))
        if p_cyc[IteratorCyc.index] == 0:
            FM.ChangeState(0)
        elif p_cyc[IteratorCyc.index] != 0:
            FM.ChangeState(1)
            pp.SetPower(p_cyc_calib[IteratorCyc.index])
        t_sync[IteratorCyc.index]=time.time()-t0
        time.sleep(t_cyc[IteratorCyc.index])
    IteratorCyc.reset()
    # once it finished we set the power to the minimum and continue measurement
    print('Stability Time')
    FM.ChangeState(1)
    pp.SetPower(np.min(p_cyc_calib))
    camera.WaitForAcq()
    FM.ChangeState(0)

     # Save all the cycle in the folder
    temp = pd.DataFrame(
        {'Exposure Time': t_cyc, 'Power send': p_cyc, 'Power Pulse-picker': p_cyc_calib,'Sync':t_sync})
    temp.to_csv(TempDirPath+'/Cycle.csv')
    
    


Laser.SetStatusShutterTunable(0)
