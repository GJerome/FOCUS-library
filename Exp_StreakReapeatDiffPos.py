import ControlLockInAmplifier as lock
import ControlLaser as las
import ControlPulsePicker as picker
import ControlStreakCamera as StreakCamera
import FileControl
import ControlPiezoStage as Transla

import numpy as np
import time as time
import os

os.system('cls')

#############################
# Global parameter
#############################


# Streak camera parameter
Nb_exposure = 20
Nb_loop = 200
MCP_Gain = 25

#############################
# Piezo parameter
#############################
Nb_points = 10

start_x = 0
end_x = 100
x = np.linspace(start_x, end_x, int(np.floor(np.sqrt(Nb_points))))

start_y = 0
end_y = 100
y = np.linspace(start_y, end_y, int(np.ceil(np.sqrt(Nb_points))))

X, Y = np.meshgrid(x, y)
Pos = np.stack([X.ravel(), Y.ravel()], axis=-1)
print('Distance between points:\n\t x ={} \n\t y={}'.format(
    x[1]-x[0], y[1]-y[0]))
# Misc parameter
FileNameData = 'DataStreakRepeatPos_'


GeneralPara = {'Experiment name': ' StreakRepeatDiffPos', 'Nb points': Nb_points,
               'Distance Between Points ': x[1]-x[0],
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
# Initialisation of the Conex Controller
#############################
piezo = Transla.PiezoControl('COM15')
x_axis = Transla.PiezoAxisControl(piezo, 'x')
y_axis = Transla.PiezoAxisControl(piezo, 'y')
z_axis = Transla.PiezoAxisControl(piezo, 'z')
# x_axis=Rtransla.ConexController('COM12')
# y_axis=Rtransla.ConexController('COM13')
print('Initialised translation stage')

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


#############################
# Printing loop
#############################
print('')

MesNumber = np.linspace(1, Nb_points, Nb_points)
IteratorMes = np.nditer(MesNumber, flags=['f_index'])

print("Begin acquisition")

for k in IteratorMes:
    print('Measurement number:{}'.format(MesNumber[IteratorMes.index]))
    os.mkdir(DirectoryPath+'\\Mes'+str(MesNumber[IteratorMes.index]))
    x_axis.MoveTo(Pos[MesNumber[IteratorMes.index], 0])
    y_axis.MoveTo(Pos[MesNumber[IteratorMes.index], 1])
    sc.ShutterOpen()
    sc.StartSeq('Analog Integration', Nb_loop)
    Laser.SetStatusShutterTunable(1)
    sc.AsyncStatusReady()
    sc.ShutterClose()
    Laser.SetStatusShutterTunable(0)
    sc.BckgSubstraction()
    # Save the data
    sc.SaveSeq(DirectoryPath+'\\Mes' +
               str(MesNumber[IteratorMes.index])+'\\000001.img')

sc.Set_MCPGain(0)
Laser.SetStatusShutterTunable(0)
print('Experiment finished')
