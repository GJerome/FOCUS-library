import sys
import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scipy.optimize import minimize_scalar

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    import ControlLaser as laser

    import ControlLockInAmplifier as lock
    import FileControl
except:
    print('Problem loading the parent folder please check that the file exist!')

#############################
# Global parameter
#############################
WavelengthRange = np.arrange(400, 410, 1)

LockInParaFile = 'ParameterLockIn.txt'

GeneralPara = {'Experiment name': ' CalibrationSHG',
               'Wavelength range': '{}-{}'.format(WavelengthRange[0], WavelengthRange[-1])}

InstrumentsPara = {}
#############################
# Initialisation of lock-in amplifier
#############################

LockInDevice = lock.LockInAmplifier(LockInParaFile)

InstrumentsPara['Lock-in-amplifier'] = LockInDevice.parameterDict

#############################
# Initialisation of laser
#############################

Laser = laser.LaserControl('COM8', 'COM17', 2)

InstrumentsPara['Laser'] = Laser.parameterDict


#############################
# Preparation of the directory
#############################

DirectoryPath = FileControl.PrepareDirectory(GeneralPara, InstrumentsPara)

#############################
# Declare function
#############################


def OptimizeCompensator(x):
    step = int(np.round(x))
    Laser.SHG.SetActuatorPosition(step)
    data = LockInDevice.AcquisitionLoop(0.5)
    return 1/data.loc['R1'].mean()  # higher R1 means lower value


#############################
# Optimisation loop
#############################
Result = pd.DataFrame({'Wavelength': WavelengthRange,
                      'delta': np.zeros(np.size(WavelengthRange))})
Laser.SetStatusShutterTunable(1)
for i in WavelengthRange:
    Laser.SetWavelengthTunable(i)
    res = minimize_scalar(OptimizeCompensator,
                          bounds=(-200, 200), method='bounded')
    Result.loc[Result['Wavelength'] == i, 'delta'] = int(np.round(res.x))
Laser.SetStatusShutterTunable(0)
Result.to_csv('./ResultSHGCalibration.csv')
fig1, ax1 = plt.subplots(1, 1)
ax1[0].plot(Result.loc[:, 'Wavelength'], Result.loc[:, 'delta'])
plt.show()
