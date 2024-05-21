import serial
import time
import sys

class PiezoControl:
    """ This class control the piezo. """   

    def __init__(self,ComPortLaser):        

        try:
            self.SerialPort = serial.Serial(ComPortLaser,baudrate=19200,bytesize=serial.EIGHTBITS,stopbits=serial.STOPBITS_ONE,
                                            timeout=1,parity=serial.PARITY_NONE,xonxoff=True)
        except :
            sys.exit("ControlLaser error: Can't connect to the laser. You could try to close Discovery NX.")
        # Put all channel in remote
        self.SetCommand('setk,0,1')
        self.SetCommand('setk,1,1')
        self.SetCommand('setk,2,1')
        # Put all channel in closed loop
        self.SetCommand('cloop,0,1')
        self.SetCommand('cloop,1,1')
        self.SetCommand('cloop,2,1')
        # Put all channel with high frequency polling
        self.SetCommand('fready,0')
        self.SetCommand('enctime,0')
        # Get all position
        self.x=self.GetX()
        self.y=self.GetY()
        self.z=self.GetZ()
        
        self.parameterDict={'Piezo mode':'closed loop','Starting position x:':self.x,'Starting position y:': self.y,'Starting position z:':self.z}

    # Get position on all axis
    def GetX(self):
        return float(self.GetCommand('rk,0').split(',')[2])
    def GetY(self):
        return float(self.GetCommand('rk,1').split(',')[2])
    def GetZ(self):
        return float(self.GetCommand('rk,2').split(',')[2])
    
    # Misc command    
    def SetCommand(self,cmd):
        self.SerialPort.write('{}\r\n'.format(cmd).encode())
    def GetCommand(self,cmd):
        self.SerialPort.write('{}\r\n'.format(cmd).encode())
        status = self.SerialPort.read_until(b'\r').decode().rstrip()
        return status
    
if __name__ == "__main__":
    piezo= PiezoControl('COM15')
    print(piezo.parameterDict)
