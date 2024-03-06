# This file allows the control of the EMCCD using the lightfield 

import clr
import sys
import os
import time

try:
    from System.IO import *
    from System import String
    from System.Collections.Generic import List
except:
    sys.exit('Please unistall clr and pythonnet and run py -m pip install -U pythonnet ')


# Add needed dll references
sys.path.append(os.environ['LIGHTFIELD_ROOT'])
sys.path.append(os.environ['LIGHTFIELD_ROOT']+"\\AddInViews")
clr.AddReference('PrincetonInstruments.LightFieldViewV5')
clr.AddReference('PrincetonInstruments.LightField.AutomationV5')
clr.AddReference('PrincetonInstruments.LightFieldAddInSupportServices')

# PI imports
from PrincetonInstruments.LightField.Automation import Automation
from PrincetonInstruments.LightField.AddIns import ExperimentSettings
from PrincetonInstruments.LightField.AddIns import DeviceType
from PrincetonInstruments.LightField.AddIns import CameraSettings

def device_found(experiment):
    # Find connected device
    for device in experiment.ExperimentDevices:
        if (device.Type == DeviceType.Camera):
            return True

    # If connected device is not a camera inform the user
    print("Camera not found. Please add a camera and try again.")
    return False

class LightFieldControl:

    def __init__(self,ExperimentName):
        # Create the LightField Application (true for visible)
        # The 2nd parameter forces LF to load with no experiment
        self.auto = Automation(True, List[String]())

        # Get experiment object
        self.experiment = self.auto.LightFieldApplication.Experiment
    

        if device_found(self.experiment) == True:
            self.LoadExperiment(ExperimentName)
            self.Status=True
            
            #First we check if the temperature is correctly set
            if (self.experiment.IsReadyToRun & self.experiment.IsRunning==False):
                self.experiment.SetValue( CameraSettings.SensorTemperatureSetPoint ,-55)

            # And we wait for the temperature to be settled
            while( self.experiment.GetValue( CameraSettings.SensorTemperatureReading)!= -55):
                time.sleep(3)
                print('Temperature of the camera : {}'.format(self.experiment.GetValue( CameraSettings.SensorTemperatureReading)))  
            self.LoadExperiment(ExperimentName) 
            
        else:
            
            self.Status=False
        

        
    def LoadExperiment(self,Name):
        result= self.experiment.Load(Name)
        if result ==False :
            print('Error loading experiment!')
            sys.exit()

    def Acquire(self):
        # Acquire an image
        if self.experiment.IsRunning==False & self.experiment.IsReadyToRun == True:
            self.experiment.Acquire()

    def SetSavefileName(self,Filename):
        self.experiment.SetValue(ExperimentSettings.FileNameGenerationBaseFileName,Path.GetFileName(Filename))


    def SetSettingValue(self,setting, value):    
        # Check for existence before setting, return true if it exist
        if self.experiment.Exists(setting):        
            self.experiment.SetValue(setting, value)
            return True
        else:
            return False

if __name__ == "__main__":
    emccd=LightFieldControl(ExperimentName='TimeTraceEM')
    if emccd.Status==False:
        print("The experiment couldn't be setup please close all instance of Lightfield, check connection and retry.")
        sys.exit()
    emccd.Acquire()
