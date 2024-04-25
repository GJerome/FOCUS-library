import serial

# --------------------------------------------------------

class SHG:
    """ This class connect to a motor using the Comport aguments. It communicate using Comp portts and CLI command. 
    The function is then just to ensure that the command are send accordigly and that everything is working. """
    

    def __init__(self,COMPortSHG):
        """ This class connect to a motor using the pyserial backend. It take as an argument the adress of the instruments.
        """
        self.device=serial.Serial(port=COMPortSHG,baudrate=38400,parity='N',stopbits=1,timeout=3)

    def GetWavelength(self):
         while True:
            try:
                return int(self.GetCommand('GWL,')[3:])
            except ValueError:
                pass

    def SetWavelength(self,wave):
        if int(wave)<1000:
            wave='0'+str(wave)
        else:
            wave=wave
        self.device.write('NWL{},'.format(wave).encode())
        status=self.device.readline()
        if status[3:-1]!=b'\x00\x00\x02':
            print('SHG Warning:Problem setting up the wavelength (status:{})'.format(self.GetCommand('GST,')))
            return False
        else:
            return True

    #Serial backend command  
    def GetCommand(self, cmdSend):       
         
        cmd = cmdSend+'\r'
        self.device.write(cmd.encode())
        return self.device.readline().decode().rstrip()

    def SetCommand(self, cmdSend):       
         
        cmd = cmdSend+'\r'
        self.device.write(cmd.encode())

    def __del__(self):
        self.device.close()

if __name__ == "__main__":

    SHGDevice = SHG('COM17')
    print(SHGDevice.GetWavelength())
    SHGDevice.SetWavelength(1289)
    print(SHGDevice.GetWavelength())
