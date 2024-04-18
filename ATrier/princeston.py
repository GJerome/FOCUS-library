# Import the .NET class library
import clr

# Import python sys module
import sys

# Import os module
import os

# Import System.IO for saving and opening files
from System.IO import *

# Import c compatible List and String
from System import String
from System.Collections.Generic import List

# Add needed dll references
sys.path.append(os.environ['LIGHTFIELD_ROOT'])
sys.path.append(os.environ['LIGHTFIELD_ROOT'] + "\\AddInViews")
clr.AddReference('PrincetonInstruments.LightFieldViewV5')
clr.AddReference('PrincetonInstruments.LightField.AutomationV5')
clr.AddReference('PrincetonInstruments.LightFieldAddInSupportServices')

# PI imports
from PrincetonInstruments.LightField.Automation import Automation
from PrincetonInstruments.LightField.AddIns import ExperimentSettings
from PrincetonInstruments.LightField.AddIns import DeviceType
from PrincetonInstruments.LightField.AddIns import CameraSettings
from PrincetonInstruments.LightField.AddIns import SensorTemperatureStatus
from PrincetonInstruments.LightField.AddIns import SpectrometerSettings

try:
    from PrincetonInstruments.LightField.AddIns import ExportFileType
except ImportError as err:
    print(err)
except OsError as err :
    print(err)
    
import time


def save_file(filename):
    # Set the base file name
    experiment.SetValue(
        ExperimentSettings.FileNameGenerationBaseFileName,
        Path.GetFileName(filename))

    # Option to Increment, set to false will not increment
    experiment.SetValue(
        ExperimentSettings.FileNameGenerationAttachIncrement,
        False)

    # Option to add date
    experiment.SetValue(
        ExperimentSettings.FileNameGenerationAttachDate,
        False)

    # Option to add time
    experiment.SetValue(
        ExperimentSettings.FileNameGenerationAttachTime,
        False)


def device_found(experiment):
    # Find connected device
    for device in experiment.ExperimentDevices:
        if (device.Type == DeviceType.Camera):
            return True

    # If connected device is not a camera inform the user
    print("Camera not found. Please add a camera and try again.")
    return False

    
def init_princeston():
    # Create the LightField Application (true for visible)
    # The 2nd parameter forces LF to load with no experiment
    auto = Automation(True, List[String]())

    # Get experiment object
    experiment = auto.LightFieldApplication.Experiment
    

    if device_found(experiment) == True:

        if (experiment.IsReadyToRun & experiment.IsRunning==False):
            experiment.SetValue( CameraSettings.SensorTemperatureSetPoint ,-70)
        
        current = experiment.GetValue( CameraSettings.SensorTemperatureStatus )

        while( experiment.GetValue( CameraSettings.SensorTemperatureReading)!= -69.0):
            time.sleep(3)
            print('Temperature of the camera : {}'.format(experiment.GetValue( CameraSettings.SensorTemperatureReading)))

        
        return True, experiment,auto
    elif device_found(experiment) == False:
        return False, experiment,auto

def init_princeston_mono():

        auto=Automation(True, List[String]())
        experiment = auto.LightFieldApplication.Experiment
        return auto,experiment
