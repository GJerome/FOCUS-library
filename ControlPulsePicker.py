import pyvisa as instco

def FindDevice():
    rm = instco.ResourceManager('@py')
    rm.list_resources()
# --------------------------------------------------------

class PulsePicker:
    """ This class connect to a motor using the Comport aguments. It communicate using Comp portts and CLI command. 
    The function is then just to ensure that the command are send accordigly and that everything is working. """
    

    def __init__(self,Adress):
        """ This class connect to a motor using the pyserial backend. It take as an argument the adress of the instruments.
        """

        # Connexion to the serial port
        self.RessourceManager = instco.ResourceManager('@py')
        self.Instrument=self.RessourceManager.open_resource(Adress)

# Get functions        
    def GetDivRatio(self):
        return self.QueryCommand('DIVR?')    
    def GetPower(self):
        '''Read current pulse power. The value is scaled in mW, 0.1 Wsteps'''
        return self.QueryCommand('POWER?')    
    def GetPulseWidth(self):
        '''Read current pulse width. Value is scaled in 0.1ns.'''
        return self.QueryCommand('PWIDTH?')
    def GetPulseDelay(self):
        '''Read current pulse delay. Value is scaled in 0.1 ns.'''
        return self.QueryCommand('PDELAY?')
    def GetTriggerState(self):
        '''Read the trigger condition. If 0 is returned, internal counter is running, 1 means the external trigger input is used.'''
        return self.QueryCommand('EXTTRIGGER?')
    def GetPowerState(self):
        '''Read the status of RF ouput, 0 is OFF,1 is ON.'''
        return self.QueryCommand('PWR_ON?')
    
#Set functions
    def SetDivRatio(self,DivRatio):
        self.WriteCommand('DIVR{}'.format(str(DivRatio)))
    def SetPower(self,Power):
        '''Set pulse power to xxx. Power value is scaled in mW, 0.1W steps.'''
        self.WriteCommand('POWER{}'.format(str(Power)))    
    def SetPower(self,PWIDTH):
        '''Set pulse width to xxx. Value is scaled in 0.1 ns steps. Range: 40-150(4-15 ns)'''
        self.WriteCommand('PWIDTH{}'.format(str(PWIDTH)))
    def SetPulseDelay(self,PWIDTH):
        '''Set pulse delay to xxx. Value is scaled in 0.1 ns steps. Range: 0-500(0-50 ns).'''
        self.WriteCommand('PDELAY{}'.format(str(PWIDTH)))
    def SetTriggerState(self,TriggerState):
        '''Select the trigger condition, 0 select internal counter, 1 select external trigger input.'''
        return self.QueryCommand('EXTTRIGGER{}'.format(str(TriggerState)))
    def SetPowerState(self,PowerState):
        '''Set the status of RF ouput, 0 is OFF,1 is ON.'''
        return self.QueryCommand('PWR_ON{}'.format(str(PowerState)))                 
    

#Pyvisa backend command

    def QueryCommand(self,command):
        return self.Instrument.query(command) 
    def WriteCommand(self,command):
        return self.Instrument.write(command) 
    
#Pyvisa backend command    
    def __del__(self):
        self.RessourceManager.close()

if __name__ == "__main__":
    FindDevice()
    pp=PulsePicker()
    pp.GetPulseDelay()