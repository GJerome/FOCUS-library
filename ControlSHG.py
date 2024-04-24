import serial

# --------------------------------------------------------

class SHG:
    """ This class connect to a motor using the Comport aguments. It communicate using Comp portts and CLI command. 
    The function is then just to ensure that the command are send accordigly and that everything is working. """
    

    def __init__(self,Adress):
        """ This class connect to a motor using the pyserial backend. It take as an argument the adress of the instruments.
        """
        self.device=serial.Serial(port=Adress,baudrate=38400,parity='N',stopbits=1,timeout=3)

    def GetWavelength(self):
        print('To the best of my knwoledge this is not possible.')

    def SetWavelength(self,wave):
        if wave<1000:
            wave='0'+str(wave)
        else:
            wave=wave
        self.device.write('NWL{},'.format(wave).encode())
        if self.device.readline()[3:-1]!=b'\x00\x00\x02':
            print('Problem setting up the wavelength')

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
    SHGDevice.SetWavelength(800)
