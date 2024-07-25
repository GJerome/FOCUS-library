import serial
import numpy as np
import time
import pandas as pd

# --------------------------------------------------------


class SHG:

    def __init__(self, COMPortSHG, CalibrationFile=None):
        """This class allows to connect to the HarmoniXX Select SHG from APE.
    You can connect to the device using its comport and it use serial as the backend.
    Everything is already set up  as in the documentation.
    Curently the device only support the following command GST, GID, BRK, MMN, NWLxxxx,
    and SMS+/- which is not listed in the documentation.

    If a calibration file is listed it will automatically go to the specify actuator position when specified
    a wavelength. If the wavelength is not specified in the file then it will go to the actuator position,
    the intensity of the SHG might be lower. 

    Currently this only support the NWL and SMS+/- command to go to a specific wavelength
    and optimize the crystal position."""

        self.device = serial.Serial(
            port=COMPortSHG, baudrate=38400, parity='N', stopbits=1, timeout=3)
        if CalibrationFile != None:
            self.Calibration = pd.read_csv(CalibrationFile)
        else:
            self.Calibration=pd.DataFrame({'Wavelength':[0],'delta':[0]})

#####################
# Getters
#####################
    def GetWavelength(self):
        """Get the current wavelength not the actuator position."""
        while True:
            try:
                return int(self.GetCommand('GWL,')[3:])
            except ValueError:
                pass
#####################
# Setters
#####################

    def SetActuatorPosition(self, delta):
        """Set the the actuator position. The delta parameter is should be between +999 and -999."""
        if np.abs(delta) > 1000:
            print('SHG Warning: Actuator position outside of range, not moving')
        else:
            deltaS = f'{int(delta):+04}'
            self.SetCommand('SMS{},'.format(deltaS))
            time.sleep(1)

    def SetWavelength(self, wave):
        """Set the wavelength for the SHG unit. The wavelength is the one set up by 
        the Coherent Chameleon NX laser."""
        if int(wave) < 1000:
            waveS = '0'+str(wave)
        else:
            waveS = wave
        self.device.write('NWL{},'.format(waveS).encode())
        status = self.device.readline()
        if status[3:-1] != b'\x00\x00\x02':
            print('SHG Warning:Problem setting up the wavelength (return:{},status:{})'.format(
                status, self.GetCommand('GST,')))
            return False

        delta = self.Calibration.loc[self.Calibration['Wavelength']
                                     == wave]['delta']
        if len(delta.index) > 0:
            self.SetActuatorPosition(delta)
            print('Optimizing at {} nm'.format(wave))
        return True

#####################
# Serial backend command
#####################

    def GetCommand(self, cmdSend):

        cmd = cmdSend
        self.device.write(cmd.encode())
        status = self.device.readline()
        return status

    def SetCommand(self, cmdSend):
        cmd = cmdSend
        self.device.write(cmd.encode())

    def __del__(self):
        self.device.close()


if __name__ == "__main__":
    print('Main code')
    SHGDevice = SHG('COM17')
    print(SHGDevice.GetWavelength())
    print(SHGDevice.SetCommand('NWL0850,'))
    print(SHGDevice.GetWavelength())
