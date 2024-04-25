import ControlLockInAmplifier as lock
import ControlLaser as las

import pandas as pd
import numpy as np


def Reflectivity(lockin,laser,wavelength,Inttime):
    Data=pd.DataFrame(0.0,index=wavelength,columns=['R1','ErrR1','Phase1','ErrPhase1','R2','ErrR2','Phase2','ErrPhase2','R','errR'])
    for i,wave in enumerate(wavelength):
        laser.SetWavelengthTunable(wave)
        laser.WaitForTuning()
        print(Laser.GetWavelength())

        DataTemp=lockin.AcquisitionLoop(Inttime)
        Data.loc[wave,'R1']=DataTemp.loc[:,'R1'].mean(0)
        Data.loc[wave,'ErrR1']=DataTemp.loc[:,'R1'].std(axis=0)
        Data.loc[wave,'Phase1']=DataTemp.loc[:,'Phase1'].mean(0)
        Data.loc[wave,'ErrPhase1']=DataTemp.loc[:,'Phase1'].std(axis=0)
        Data.loc[wave,'R2']=DataTemp.loc[:,'R2'].mean(0)
        Data.loc[wave,'ErrR2']=DataTemp.loc[:,'R2'].std(axis=0)
        Data.loc[wave,'Phase2']=DataTemp.loc[:,'Phase2'].mean(0)
        Data.loc[wave,'ErrPhase2']=DataTemp.loc[:,'Phase2'].std(axis=0)
        Data.loc[wave,'R']=DataTemp.loc[:,'R2'].mean(0)/DataTemp.loc[:,'R1'].mean(0)
        Data.loc[wave,'errR']=Data.loc[wave,'R']*np.sqrt((Data.loc[wave,'errR1']/Data.loc[wave,'R1'])**2
                                                         + (Data.loc[wave,'errR2']/Data.loc[wave,'R2'])**2)
        
    return Data

if __name__=='__main__':
    import matplotlib.pyplot as plt

    Time_int=2
    wavelength=[400,450,500]
    FileNameData='CarbonRemoval_'

    LockInParaFile = "ParameterLockIn.txt"


    GeneralPara={'Experiment name':' Reflectivity','Integration time [s]':Time_int}

    InstrumentsPara={}
    #############################
    # Initialisation of lock-in amplifier
    #############################

    LockInDevice=lock.LockInAmplifier(LockInParaFile)

    InstrumentsPara['Lock-in-amplifier']=LockInDevice.parameterDict

    #############################
    # Initialisation of laser
    #############################

    Laser= las.LaserControl('COM8','COM17',2)

    InstrumentsPara['Laser']=Laser.parameterDict


    Data=Reflectivity(LockInDevice,Laser,wavelength,Time_int)
    print(Data)
    plt.plot(Data.loc[:,'R'])
    plt.show()
