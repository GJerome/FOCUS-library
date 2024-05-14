import ControlSHG 

import serial
import time
import sys

class LaserControl:
    """ This class connect to the laser """   

    def __init__(self,ComPortLaser,ComportSHG,ShutterWaitTime):        

        try:
        # Connexion to the serial port
            self.SerialPort = serial.Serial(ComPortLaser,baudrate=19200,bytesize=serial.EIGHTBITS,timeout=30,parity=serial.PARITY_NONE)
        #except serial.serialutil.SerialException:
        except :
            sys.exit("ControlLaser error: Can't connect to the laser. You could try to close Discovery NX.")
        self.SerialPort.write('E = 0\r\n'.encode())
        status = self.SerialPort.readline().decode().rstrip() 
        self.ShutterFixed=self.GetStatusShutterFixed()
        self.ShutterTunable=self.GetStatusShutterTunable()
        
        self.ShutterWaitTime=ShutterWaitTime
        self.Status=self.GetStatus()
        self.Wavelength=self.GetWavelength()
        # Set the SHG in accordance to the laser tunable output
        self.SHG=ControlSHG.SHG(ComportSHG)
        self.SHG.SetWavelength(self.Wavelength)

        self.parameterDict={'Tunable output wavelength':self.Wavelength,'SHG Wavelength': self.Wavelength}

    def GetStatus(self):
        self.SerialPort.write("?ST\r\n".encode('utf-8'))
        status = self.SerialPort.readline().decode().rstrip()
        return status[4:]

    ###########################
    # Tunable
    ########################### 
      
    def GetWavelength(self):

        self.SerialPort.write("?WV\r\n".encode())
        # Sometimes the output is not cleared so the laser will just output a empty string
        status = self.SerialPort.readline().decode().rstrip()
        if status=='CHAMELEON>':
            status = self.SerialPort.readline().decode().rstrip()

        return int(status.split('>')[1])
    
    def GetPowerTunable(self):

        self.SerialPort.write("?UF\r\n".encode())
        # Sometimes the output is not cleared so the laser will just output a empty string
        status = self.SerialPort.readline().decode().rstrip()
        if status=='CHAMELEON>':
            status = self.SerialPort.readline().decode().rstrip()

        return int(status.split('>')[1])
    
    def GetStatusShutterTunable(self):
        self.SerialPort.write("?S\r\n".encode())
        # Sometimes the output is not cleared so the laser will just output a empty string
        status = self.SerialPort.readline().decode().rstrip()
        if status=='CHAMELEON>':
            status = self.SerialPort.readline().decode().rstrip()

        try:
            return int(status.split('>')[1])
        except:
            sys.exit('LaserControl error: GetStatusShutterTunable: {}'.format(status))
        
    def GetStatusTuning(self):
        self.SerialPort.write('?TS\r\n'.encode())
        # Sometimes the output is not cleared so the laser will just output a empty string
        status = self.SerialPort.readline().decode().rstrip()
        if status=='CHAMELEON>':
            status = self.SerialPort.readline().decode().rstrip()
        try:
            return int(status.split('>')[1])
        except:
            sys.exit('ControlLaser: Tuning error (status:{})'.format(status))
     
    def SetWavelengthTunable(self,wave):
        if (int(wave)<660) and (int(wave)>329):
            self.SerialPort.write("WAVELENGTH={}\r\n".format(int(2*wave)).encode())
            status = self.SerialPort.readline().decode().rstrip()
            a=self.SHG.SetWavelength(int(2*wave))
            b=self.SHG.GetWavelength()
            if a!= True:
                sys.exit("ControlLaser error: SHG couldn't reach desired wavelength(lamda={}) ".format(b))
        elif (wave>=660) and (wave<1301):
            self.SerialPort.write("WAVELENGTH={}\r\n".format(int(wave)).encode())
            status = self.SerialPort.readline().decode().rstrip()
        else:
            sys.exit('ControlLaser error: Chosen wavelength outside of the range achevable.')

    def SetStatusShutterTunable(self,status):
        '''The status of the shutter is defined as False(0) for close and True(1) as open '''
        self.SerialPort.write("S={} \r\n".format(status).encode())
        time.sleep(self.ShutterWaitTime)
        a=self.GetStatusShutterTunable()
        if a==0:
            print("The shutter for the tunable output is closed")
        if a==1:
            print("The shutter for the tunable output is opened")

    def WaitForTuning(self):
        status=self.GetStatusTuning()
        while status==1:
            status=self.GetStatusTuning()
            time.sleep(0.1)

    ###########################
    # Fixed output
    ###########################

    def GetPowerFixed(self):
        self.SerialPort.write("?PFIXED\r\n".encode())
        status = self.SerialPort.readline().decode().rstrip()
        return int(status[19:])
    
    def GetStatusShutterFixed(self):
        self.SerialPort.write("?SFIXED\r\n".encode())
        status = self.SerialPort.readline().decode().rstrip().split('>')[1]
        return int(status)
    
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
    Laser= LaserControl('COM8','COM17',2)
    print(Laser.GetWavelength())

    Laser.SetStatusShutterTunable(1)
    Laser.SetWavelengthTunable(400)
    Laser.WaitForTuning()
    #Laser.GetStatusShutterTunable()

    #Laser.WaitForTuning()
