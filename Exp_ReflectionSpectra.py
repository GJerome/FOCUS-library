import ControlLockInAmplifier as lock
import ControlLaser as las
import FileControl

import pandas as pd
import numpy as np


def Reflectivity(lockin,laser,wavelength,Inttime,ScalingFactorS1,ScalingFactorS2):
    ''' This function compute the reflectivity of the sample over a range specified by the wavelength factor.It require a already initialised laser and lock-in amplifier.
    The value R1,R2,Phase1 and Phase 2 are not scaled when sended back but the reflectivity can be scaled so that the value is more accurate. 
    The scaling factor depends on the optical path and wavelength but if a scalar is given it will scale the signal using the same scalar.'''
    
    Data=pd.DataFrame(0.0,index=wavelength,columns=['R1','ErrR1','Phase1','ErrPhase1','R2','ErrR2','Phase2','ErrPhase2','R','ErrR'])
    
    if type(ScalingFactorS1)==int:
        ScaleS1=np.ones(len(wavelength))*ScalingFactorS1
        print('Scaling factor contant across wavelength')
    else:
        ScaleS1=ScalingFactorS1

    if type(ScalingFactorS2)==int:
        ScaleS2=np.ones(len(wavelength))*ScalingFactorS2
    else:
        ScaleS2=ScalingFactorS2

    for i,wave in enumerate(wavelength):
        laser.SetWavelengthTunable(wave)
        laser.WaitForTuning()
        lockin.AutorangeSource()
        FileControl.printProgressBar(i + 1, len(wavelength), prefix = 'Scan at {}nm:'.format(np.round(wave,0)), suffix = 'Complete', length = 50)
        #print('Wavelength: {}nm'.format(Laser.GetWavelength()))
        DataTemp=lockin.AcquisitionLoop(Inttime)
        Data.loc[wave,'R1']=DataTemp.loc[:,'R1'].mean(0)
        Data.loc[wave,'ErrR1']=DataTemp.loc[:,'R1'].std(axis=0)
        Data.loc[wave,'Phase1']=DataTemp.loc[:,'Phase1'].mean(0)
        Data.loc[wave,'ErrPhase1']=DataTemp.loc[:,'Phase1'].std(axis=0)

        Data.loc[wave,'R2']=DataTemp.loc[:,'R2'].mean(0)
        Data.loc[wave,'ErrR2']=DataTemp.loc[:,'R2'].std(axis=0)
        Data.loc[wave,'Phase2']=DataTemp.loc[:,'Phase2'].mean(0)
        Data.loc[wave,'ErrPhase2']=DataTemp.loc[:,'Phase2'].std(axis=0)

        Data.loc[wave,'R']=(ScaleS2[i]/ScaleS1[i])*DataTemp.loc[:,'R2'].mean(0)/DataTemp.loc[:,'R1'].mean(0)
        Data.loc[wave,'ErrR']=Data.loc[wave,'R']*np.sqrt((Data.loc[wave,'ErrR1']/Data.loc[wave,'R1'])**2
                                                         + (Data.loc[wave,'ErrR2']/Data.loc[wave,'R2'])**2)
        
    return Data

if __name__=='__main__':
    import matplotlib.pyplot as plt

    Time_int=1
    wavelength=np.linspace(400,500,100)    
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

    Laser.SetStatusShutterTunable(1)
    Data=Reflectivity(LockInDevice,Laser,wavelength,Time_int,1,1)
    Laser.SetStatusShutterTunable(0)
    FileControl.ExportFileLockIn('./','dataReflectivityMirror',Data)
    plt.errorbar(Data.index,Data.loc[:,'R'],Data.loc[:,'ErrR'])
    plt.show()
