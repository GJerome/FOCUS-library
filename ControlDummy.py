dummy_time = 0

def sleep(t):
    global dummy_time
    dummy_time += t

def time():
    return dummy_time
    
###################################################################

class FlipMount:
    def __init__(self, serial, Name=None):
        self.state = 0
        self.name = Name
        self.parameterDict = {}

    def ChangeState(self, state):
        self.state = state
        print('State: {}'.format(self.state))

    def GetState(self):
        return self.state

###################################################################

class ShutterControl:
    def __init__(self, serial, Name=None):
        self.name = Name
        self.parameterDict = {}

    def SetOpen(self):
        pass
        
    def SetClose(self):
       pass 

###################################################################

class FilterWheel:
    def __init__(self, serial):
        self.name = serial
        self.parameterDict = {}

    def SetOpen(self):
        pass
        
    def SetClose(self):
       pass 


    
###################################################################
    
class LaserControl:
    def __init__(self, str_a, str_b, x):
        self.parameterDict = {}

    def SetStatusShutterTunable(self, status):
        print('StatusShutterTunable: {}'.format(status))

###################################################################

class PulsePicker:
    def __init__(self, serial):
        self.parameterDict = {}

    def SetPower(self, power):
        print('Power: {}'.format(power))

###################################################################

class LightFieldControl:
    def __init__(self, str) -> None:
        self.parameterDict = {}
        self.framenr = 0
        
    def GetFrameTime(self):
        return 1
    
    def GetExposureTime(self):
        return 1
    
    def GetNumberOfFrame(self):
        return self.framenr
    
    def SetNumberOfFrame(self, n):
        self.framenr = n
    
    def Acquire(self):
        pass

    def WaitForAcq(self):
        pass

    def SetEMGain(self, Gain):
        self.EMGain = str(Gain)
    
    def SetSaveDirectory(self, str):
        print('Save directory: {}'.format(str))
    
###################################################################   

class ConexController:
    def __init__(self, str):
        self.parameterDict = {}
        pass
    
    def MoveTo(self, pos):
        print('Position: {}'.format(pos))
    def GetPosition(self):
        return 1

class PiezoControl:
    def __init__(self, str):
        self.parameterDict = {}
        pass

class PiezoAxisControl:
    def __init__(self, piezo, axis,Timeout):
        self.parameterDict = {}
        pass
    
    def MoveTo(self, pos):
        print('Position: {}'.format(pos))