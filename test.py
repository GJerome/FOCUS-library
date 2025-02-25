import ControlFlipMount as FlipMount
import ControlLaser as las
import ControlPulsePicker as picker
import FileControl
import ControlPiezoStage as Transla
import ControlEMCCD as EMCCD
import ControlFilterWheel as Filterwheel
import ControlThorlabsShutter as shutter

import matplotlib.pyplot as plt
import matplotlib as mat
import numpy as np
import pandas as pd
import time as time

import random
import os
import sys
#############################
# Initialisation of the EMCCD
#############################

start_x =5
end_x = 80
start_y = 5
end_y = 80


x = np.linspace(start_x, end_x, int(np.floor(np.sqrt(100))))
y = np.linspace(start_y, end_y, int(np.floor(np.sqrt(100))))

X, Y = np.meshgrid(x, y)
Pos = np.stack([X.ravel(), Y.ravel()], axis=-1)
print(Pos)

index=random.sample(range(0, Pos.shape[0]), Pos.shape[0])
SmallGrid=Pos[index,:]
print(SmallGrid)

indexTwoPoints=random.sample(range(0, Pos.shape[0]), 2)
TwoPoints=Pos[indexTwoPoints,:]

Nb_Points=SmallGrid.shape[0]


