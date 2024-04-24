import serial
import time

def GetCommand(PortObject, cmdSend):       
         
        cmd = cmdSend+'\r'
        PortObject.write(cmd.encode())
        response = PortObject.readline().decode().rstrip()
        return response

def SetCommand(PortObject, cmdSend):       
         
        cmd = cmdSend+'\r'
        PortObject.write(cmd.encode())

class OpticalChopper:
    
        def __init__(self,COMport):
                """ This class connect to the Chopper with the Comportnumber as arguements aguments. 
                It communicate using serial library."""

                # Connexion to the serial port
                self.Chopper = serial.Serial(port=COMport,baudrate=115200,timeout=3)

                self.SetTokenResponse('0')

                #Get the Source that is currently used,0= internal, 1=VCO, 2=Line, 3 = EXT
                self.Source=GetCommand(self.Chopper,'SRCE?')
                #Get the Source that is currently used
                self.Target=GetCommand(self.Chopper,'CTRL?')
                #Get the frequency 
                self.Freq=self.GetInternalFrequency()
                self.Phase=self.GetPhase()

                self.parameterDict={'Source ':self.Source,'Target ':self.Target,'Frequency used ':self.Freq,'Phase':self.Phase}


        #####################################
        # Setter
        #####################################

        def SetTokenResponse(self,val):
                '''Set the way the chopper will send the response 1/ON is verbal and 0/OFF is numeric. 
                Default behavior is 0/OFF.'''
                if str(val) in ['0','OFF','1','ON']: 
                        SetCommand(self.Chopper,'TOKN '+val)
                else:
                        print('Wrong value, setting up the default value for token.')
                        SetCommand(self.Chopper,'TOKN OFF')

        def SetMotorStatus(self,val):
                '''Set the motor status. Accepted value are 1/ON  and 0/OFF.'''
                if str(val) in ['0','OFF','1','ON']: 
                        SetCommand(self.Chopper,'MOTR '+str(val))
                else:
                        print('Wrong value, setting off the motor.')
                        SetCommand(self.Chopper,'MOTR OFF')

        def SetInternalFrequency(self,Freq):
                '''Set the internal frequnecy of the chopper.'''
                SetCommand(self.Chopper,'IFRQ '+str(Freq))

        def SetTarget(self,Target):
                """ Set the target for the frequenncy so either the shaft, the outer or inner parameter.
                The Target parameter accept the following values: (SHAFT, INNER , OUTER)"""
                if str(Target) in ['SHAFT','INNER','OUTER']:
                        SetCommand(self.Chopper,'CTRL '+Target)
                else:
                        print('Wrong value, setting up the target to outer.')
                        SetCommand(self.Chopper,'CTRL OUTER')

        def SetPhase(self,Phase):
                """ Set the phase in degree."""
                SetCommand(self.Chopper,'PHAS '+str(Phase))
                self.parameterDict['Phase']=Phase
        
        def SetRelPhase(self,Status):
                """ Set the the relative phase home. The correct entry are 0/OFF or 1/ON """
                if str(Status) in ['0','OFF','1','ON']: 
                        SetCommand(self.Chopper,'RELP '+Status)
                else:
                        print('Wrong value, setting up the ralative phase to off state.')
                        SetCommand(self.Chopper,'RELP OFF')

        #####################################
        # Getter
        #####################################

        def GetTarget(self):
                """ Get the target for the frequency so either the shaft, the outer or inner parameter."""
                a=GetCommand(self.Chopper,'CTRL?')
                try:
                        return float(a)
                except:
                        print('An error Occured')

        def GetPhase(self):
                """ Get the relative phase status."""
                a=GetCommand(self.Chopper,'PHAS?')
                try:
                        return float(a)
                except:
                        print('An error occured')
                        print(a)

        def GetRelPhase(self):
                """ Get the relative phase status."""
                a=GetCommand(self.Chopper,'RELP?')
                try:
                        return float(a)
                except:
                        print('An error occured')
                        print(a)
        
        def GetInternalFrequency(self):
                """ Get the the internal frequnecy of the chopper which is measured with respect to the target."""
                a=GetCommand(self.Chopper,'IFRQ?')
                try:
                        return float(a)
                except:
                        print('An error occured')
                        print(a)
        def GetMotorStatus(self):
                """ Get motor status.Possible return value are 0/OFF or 1/ON."""
                a=GetCommand(self.Chopper,'MOTR?')
                try:
                        return float(a)
                except:
                        print('An error occured')
                        print(a)

        #####################################
        # MISC function
        #####################################

        def WaitForLock(self,timeout):
                '''This function is to wait so that the chopper is frequency locked qnd phqse locked. 
                Carefull if the motor is locked then it will never reach the locked status.'''
                x=0
                t0=time.time()
                while x<timeout:
                        time.sleep(0.1)
                        StatusLock=[int(GetCommand(self.Chopper,'CHCR? 2')),int(GetCommand(self.Chopper,'CHCR? 3'))]
                        if StatusLock==[1,1]:
                                return 1
                        x=time.time()-t0
                print('Never reached locked status')
                print(StatusLock)
                return -1






