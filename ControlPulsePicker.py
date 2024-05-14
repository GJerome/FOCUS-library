import pyvisa as instco
import sys

def FindDevice():
    rm = instco.ResourceManager()
    print(rm.list_resources())
    
# --------------------------------------------------------

class PulsePicker:
    """ This class connect to a motor using the Comport aguments. It communicate using Comp portts and CLI command. 
    The function is then just to ensure that the command are send accordigly and that everything is working. """
    

    def __init__(self,Adress):
        """ This class connect to a motor using the pyserial backend. It take as an argument the adress of the instruments.
        """

        # Connexion to the serial port
        self.RessourceManager = instco.ResourceManager()
        try:
            self.Instrument=self.RessourceManager.open_resource(Adress)
            
        except instco.VisaIOError as err:
            print('Could not connect to the instrument')
            self.RessourceManager.close()
            print(err)
            return
        #self.Instrument.baud_rate = 38400
        self.Instrument.timeout = 5
        self.Instrument.write_termination = "\r\x00"
        self.Instrument.read_termination = "\r\x00"
        
        try:
            self.RepRate=80E6/self.GetDivRatio() # If the script stops at this point, the best bet is to reboot the pp
        except TypeError:
            print('The instrument is connected but an unexpected response occured.')
            self.RessourceManager.close()
            sys.exit()
        except instco.errors.VisaIOError:
            print('The best bet is to reboot the pp to fix the error')
            self.RessourceManager.close()
            sys.exit()
            
        self.Power=self.GetPower()
        self.PulseDelay=self.GetPulseDelay()
        self.PulseWidth=self.GetPulseWidth()
        if self.GetTriggerState()==0:
            self.TriggerState='Internal'
        elif self.GetTriggerState()==1:
            self.TriggerState='External'
        
        if self.GetPowerState()==0:
            a=self.SetPowerState(1)
            if a=='0':
                print('Could not set RF on')
                sys.exit()

        self.parameterDict={'Repetition rate':self.RepRate,'Power': self.Power,'Pulse delay':self.PulseDelay,'Pulse width':self.PulseWidth,'Trigger': self.TriggerState}

# Get functions        
    def GetDivRatio(self):
        try:
            return int(self.QueryCommand('DIVR?'))
        except ValueError:
            print('Problem getting Pulse picker division ratio.')
            return 0  
    def GetPower(self):
        '''Read current pulse power. The value is scaled in mW, 0.1 Wsteps'''
        try:
            return int(self.QueryCommand('POWER?'))
        except ValueError:
            print('Problem getting Pulse picker power.')
            return 0    
    def GetPulseWidth(self):
        '''Read current pulse width. Value is scaled in 0.1ns.'''
        return int(self.QueryCommand('PWIDTH?'))
    def GetPulseDelay(self):
        '''Read current pulse delay. Value is scaled in 0.1 ns.'''
        return int(self.QueryCommand('PDELAY?'))
    def GetTriggerState(self):
        '''Read the trigger condition. If 0 is returned, internal counter is running, 1 means the external trigger input is used.'''
        return int(self.QueryCommand('EXTTRIGGER?'))
    def GetPowerState(self):
        '''Read the status of RF ouput, 0 is OFF,1 is ON.'''
        return int(self.QueryCommand('PWR_ON?'))
    
#Set functions
    def SetDivRatio(self,DivRatio):
        self.WriteCommand('DIVR{}'.format(str(DivRatio)))
    def SetPower(self,Power):
        '''Set pulse power to xxx. Power value is scaled in mW, 0.1W steps.'''
        self.WriteCommand('POWER{}'.format(str(Power)))    
    def SetPulseWidth(self,PWIDTH):
        '''Set pulse width to xxx. Value is scaled in 0.1 ns steps. Range: 40-150(4-15 ns)'''
        self.WriteCommand('PWIDTH{}'.format(str(PWIDTH)))
    def SetPulseDelay(self,PWIDTH):
        '''Set pulse delay to xxx. Value is scaled in 0.1 ns steps. Range: 0-500(0-50 ns).'''
        self.WriteCommand('PDELAY{}'.format(str(PWIDTH)))
    def SetTriggerState(self,TriggerState):
        '''Select the trigger condition, 0 select internal counter, 1 select external trigger input.'''
        self.WriteCommand('EXTTRIGGER{}'.format(str(TriggerState)))
        return self.QueryCommand('EXTTRIGGER?')
    
    def SetPowerState(self,PowerState):
        '''Set the status of RF ouput, 0 is OFF,1 is ON.'''
        print(self.GetPowerState())
        if self.GetPowerState()==str(PowerState):
            return PowerState
        else:
            self.WriteCommand('PWR_ON{}'.format(str(PowerState))) 
            return self.GetPowerState()                
    

#Pyvisa backend command

    def QueryCommand(self,command):
        
        self.Instrument.write(command)
        return self.Instrument.read_raw().decode().rstrip()
    
    def QueryCommandDebug(self,command):        
        self.Instrument.write(command)
        data=self.Instrument.read_raw()
        return data
    
    def WriteCommand(self,command):
        return self.Instrument.write(command) 
    
#Pyvisa backend command    
    def __del__(self):
        self.RessourceManager.close()

if __name__ == "__main__":
    #FindDevice()
    pp=PulsePicker("USB0::0x0403::0xC434::S09748-10A7::INSTR")
    #print(type(pp.QueryCommand('PWR_ON?')))
    #pp.SetDivRatio(20)
    #print(pp.Instrument.query_ascii_values('*IDN?'))
    #print(pp.parameterDict)
    pp.SetDivRatio(100)
    #print(pp.SetPowerState(1))
    print(pp.GetDivRatio())