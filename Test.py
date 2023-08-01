import ControlChopper as chop
import time as time 

InstrumentsPara={}
Chopper1= chop.OpticalChopper('COM14')

InstrumentsPara['Chopper']=Chopper1.parameterDict
print(InstrumentsPara)
Chopper1.SetInternalFrequency(0)
Chopper1.SetMotorStatus('ON')
Chopper1.WaitForLock(10)

for x in range(0,10*360,360):
    Chopper1.SetPhase(x)
    Chopper1.WaitForLock(10)


