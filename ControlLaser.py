import serial
import time
import sys

class LaserControl:
    """ This class connect to the laser """   

    def __init__(self,ComPort,ShutterWaitTime):        

        try:
        # Connexion to the serial port
            self.SerialPort = serial.Serial(ComPort,baudrate=19200,bytesize=serial.EIGHTBITS,timeout=3,parity=serial.PARITY_NONE)
        #except serial.serialutil.SerialException:
        except :
            sys.exit("Can't connect to the laser. You could try to close Discovery NX.")
            
        self.ShutterFixed=self.GetStatusShutterFixed()
        self.ShutterTunable=self.GetStatusShutterTunable()
        
        self.ShutterWaitTime=ShutterWaitTime
        self.Status=self.GetStatus()
        self.Wavelength=self.GetWavelength()
        #print('Laser status: {}\n Laser wavelength:{} \n Shutter Tunable: {}\n Shutter fixed: {}'.format(self.Status,self.Wavelength,self.ShutterTunable,self.ShutterFixed))

        self.parameterDict={'Tunable output wavelength':self.Wavelength}

    def GetStatus(self):
        self.SerialPort.write("?ST\r\n".encode('utf-8'))
        status = self.SerialPort.readline().decode().rstrip()
        return status[4:]

    ###########################
    # Tunable
    ########################### 
      
    def GetWavelength(self):
        self.SerialPort.write("?WV\r\n".encode())
        status = self.SerialPort.readline().decode().rstrip().split(' ')[-1]
        return status
    
    def GetPowerTunable(self):
        self.SerialPort.write("?UF\r\n".encode())
        status = self.SerialPort.readline().decode().rstrip()
        return int(status[14:])
    
    def GetStatusShutterTunable(self):
        self.SerialPort.write("?S \r\n".encode())
        time.sleep(0.5)
        status = self.SerialPort.readline().decode().rstrip()
        if status.find('?')!=-1:  
            return int(status[15])    
        else:
            return int(status[13])
    
    def StatusShutterTunable(self,status):
        '''The status of the shutter is defined as False(0) for close and True(1) as open '''
        self.SerialPort.write("S={} \r\n".format(status).encode())
        time.sleep(self.ShutterWaitTime)
        self.ShutterTunable=self.GetStatusShutterTunable()
        if self.GetStatusShutterTunable()==0:
            print("The shutter for the tunable output is closed")
        if self.GetStatusShutterTunable()==1:
            print("The shutter for the tunable output is opened")

    ###########################
    # Fixed output
    ###########################

    def GetPowerFixed(self):
        self.SerialPort.write("?PFIXED\r\n".encode())
        status = self.SerialPort.readline().decode().rstrip()
        return int(status[19:])
    
    def GetStatusShutterFixed(self):
        self.SerialPort.write("?SFIXED\r\n".encode())
        status = self.SerialPort.readline().decode().rstrip()
        if status.find('?')!=-1:  
            return int(status[8])    
        else:
            return int(status[17])
    
    def StatusShutterFixed(self,status):
        '''The status of the shutter is defined as 0 close and 1 as open'''
        self.SerialPort.write("SFIXED={}\r\n".format(status).encode())
        time.sleep(self.ShutterWaitTime)
        self.ShutterFixed=self.GetStatusShutterFixed()
        if self.ShutterFixed==0:
            print("The shutter for the fixed output is closed")
        if self.ShutterFixed==1:
            print("The shutter for the fixed output is opened")
    
    ###########################
    # MISC
    ###########################    
    
    def GetParameterDictory(self,path):
        return self.parameterDict


if __name__ == "__main__":
    Laser= LaserControl('COM8',2)
    print(Laser.GetWavelength())
