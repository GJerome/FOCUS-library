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
if __name__=='__main__':
    b=th.Barrier(2)

def DataAcq_Lockin(LockInDevice,t,event):
    LockInDevice.AutorangeSource()
    global DataLock
    b.wait()
    DataLock=LockInDevice.AcquisitionLoop(t)
    event.set()

def MonitorPiezo(x_axis,y_axis,z_axis,event):
    # I think in this specific cas we have to use event as we want to monitor the piezo position
    # as the measurement is actually happening. So both thread will wait for each other as the measurement is happening 
    # the other thread will set an event that will trigger the end of this thread.    
    x=np.empty(0)
    y=np.empty(0)
    z=np.empty(0)
    t=np.empty(0)
    b.wait()
    while not event.is_set(): 
        x=np.append(x,x_axis.GetPosition())
        y=np.append(y,y_axis.GetPosition())
        z=np.append(z,z_axis.GetPosition())
        t=np.append(t,time.time())
    t=t-np.min(t)    
    global DataPiezo
    DataPiezo=pd.DataFrame({'t':t,'x':x,'y':y,'z':z})

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
    th1.join()

    fig1,ax1=plt.subplots(4,1)
    ax1[0].plot(DataLock.loc[:,'t'],DataLock.loc[:,'R1'])
    ax1[1].scatter(DataPiezo.loc[:,'t'],DataPiezo.loc[:,'x'])
    ax1[2].scatter(DataPiezo.loc[:,'t'],DataPiezo.loc[:,'y'])
    ax1[3].scatter(DataPiezo.loc[:,'t'],DataPiezo.loc[:,'z'])
    plt.show()
    