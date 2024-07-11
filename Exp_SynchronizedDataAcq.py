import threading as th
import ControlPiezoStage as Transla
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import ControlLockInAmplifier as lock



#############################
# Data function
#############################
def DataAcq_Lockin(LockInDevice,t,event):
    LockInDevice.AutorangeSource()
    data=LockInDevice.AcquisitionLoop(t)

    event.set()
    print(data)

def MonitorPiezo(x_axis,y_axis,z_axis,event):
    # I think in this specific cas we have to use event as we want to monitor the piezo position
    # as the measurement is actually happening. So the other thread will set an event 

    Data=pd.DataFrame(index=['t','x','y','z'])
    t0=time.time()
    while event.is_set(): 
        x=x_axis.GetPosition()
        y=y_axis.GetPosition()
        z=z_axis.GetPosition()
        t1=time.time()-t0
        Data.append({'t':t1,'x':x,'y':y,'z':z})

if __name__=='__main__':
    
    #############################
    # Global parameter
    #############################
    time_exp=10 # time of experiment in second

    LockInParaFile='ParameterLockIn.txt'

    GeneralPara={'Experiment name':' PL no move','Exposition duration':time_exp}

    InstrumentsPara={}
    #############################
    # Initialisation of lock-in amplifier
    #############################

    LockInDevice=lock.LockInAmplifier(LockInParaFile)

    InstrumentsPara['Lock-in-amplifier']=LockInDevice.parameterDict

    #############################
    # Initialisation of the Piezo
    #############################
    piezo=Transla.PiezoControl('COM15')
    x_axis=Transla.PiezoAxisControl(piezo,'x')
    y_axis=Transla.PiezoAxisControl(piezo,'y')
    z_axis=Transla.PiezoAxisControl(piezo,'z')

    print('Initialised piezo')

    #############################
    # Parallelism stuff
    #############################
    
    event = th.Event()
    th1=th.Thread(target=DataAcq_Lockin,args=(LockInDevice,1,event))
    th2=th.Thread(target=MonitorPiezo,args=(x_axis,y_axis,z_axis,event))

    th1.start()
    th2.start()

    plt.plot()
    