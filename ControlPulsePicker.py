import serial

# --------------------------------------------------------

class PulsePicker:
    """ This class connect to a motor using the Comport aguments. It communicate using Comp portts and CLI command. 
    The function is then just to ensure that the command are send accordigly and that everything is working. """
    

    def __init__(self,ComPort):
        """ This class connect to a motor using the Comport aguments. It communicate using Comp portts and CLI command. 
        The function is then just to ensure that the command are send accordigly and that everything is working.
        """

        # Connexion to the serial port
        self.SerialPort = serial.Serial(ComPort,baudrate=921600,timeout=3)
        self.Status=self.GetStatus()
    
        self.Pos=self.GetPosition()
# Get functions        
    def GetDivRatio(self):
        cmd = 'DIVR?\r\n'
        self.SerialPort.write(cmd.encode())
        rep = self.SerialPort.readline().decode().rstrip()
        return rep
#Set functions

#Misc command

    def SendCommand(self,command):
        self.SerialPort.write(command.encode()) 

    def __del__(self):
        self.SerialPort.close()

PulsePickerO=PulsePicker('COM14')
print(PulsePickerO.GetDivRatio())