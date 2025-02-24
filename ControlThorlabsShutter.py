# Taken from https://github.com/Thorlabs/Motion_Control_Examples/blob/main/Python/KCube/KSC101/KSC101_pythonnet.py


import os
import time
import sys
import clr

clr.AddReference(
    "C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.DeviceManagerCLI.dll")
clr.AddReference(
    "C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericMotorCLI.dll")
clr.AddReference(
    "C:\\Program Files\\Thorlabs\\Kinesis\\ThorLabs.MotionControl.KCube.SolenoidCLI.dll")

from Thorlabs.MotionControl.KCube.SolenoidCLI import *
from Thorlabs.MotionControl.GenericMotorCLI import *
from Thorlabs.MotionControl.DeviceManagerCLI import *
class ShutterControl:

    def __init__(self,SN,Name):
        try:

            DeviceManagerCLI.BuildDeviceList()

            # create new device
            serial_no = SN  # Replace this line with your device's serial number

            # Connect
            self.device = KCubeSolenoid.CreateKCubeSolenoid(serial_no)
            self.device.Connect(serial_no)

            # Ensure that the device settings have been initialized
            if not self.device.IsSettingsInitialized():
                self.device.WaitForSettingsInitialized(10000)  # 10 second timeout
                assert self.device.IsSettingsInitialized() is True

            # Start polling and enable
            self.device.StartPolling(250)  # 250ms polling rate
            time.sleep(0.25)
            self.device.EnableDevice()
            time.sleep(0.5)  # Wait for device to enable


            self.device.SetOperatingMode(SolenoidStatus.OperatingModes.Manual)
        
        except Exception as e:
            print(e)
        self.parameterDict = {'Name':Name,'{} Serial number'.format(str(Name)):SN,}

    def SetOpen(self):
        self.device.SetOperatingState(SolenoidStatus.OperatingStates.Active)
        
    def SetClose(self):
        self.device.SetOperatingState(SolenoidStatus.OperatingStates.Inactive)




if __name__ == "__main__":
    shutter=ShutterControl("68800883",'Shutter')
    shutter.SetOpen()
    #shutter.SetClose()
    #time.sleep(5)
    #shutter.SetClose()
