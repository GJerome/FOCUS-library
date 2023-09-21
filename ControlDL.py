## Add some paths to the workspace
import sys
import os
import time

sys.path.append(os.path.join(os.getcwd(), "DLL_file"))


# import the Newport DLL wrapper to this end we first need to select the runtime then we can load the DLL
import pythonnet
pythonnet.load('coreclr')
import clr
clr.AddReference(os.path.dirname(os.path.abspath(__file__))+"\DLL_file\DLS.CommandInterface.dll")
import CommandInterfaceDLS as DLS

class DelayLineObject:

    def __init__(self,ComPort_u,verbatum_status,wait_time):
        # ComPort is the name of the com port 
        # verbatum_status: if we want console output for debugging
        # wait_time is the time the controller take to respond 

        COMport=ComPort_u
        self.wait=wait_time

        self.StatusBit=''
        self.ErrorBit=''
        self.StatusCode=''

        
        self.DelayLine=DLS.DLS()
        resultCo=self.DelayLine.OpenInstrument(COMport)
        if resultCo!=0:
            sys.exit('Problem while connecting to the delay stage controller - exectution aborted')
        
        # Now that the system is connect we need to check the status of the device
        #   If it was unplugged  then error can occur as before if we can't access the delay line 
        #   we exit the programm with an error code

        resultStatus, self.StatusBit , self.ErrorBit , self.StatusCode =self.DelayLine.TS()[0:4]

        if resultStatus==0 and verbatum_status==1:
            print('\n Status bit : {} \n Error bit: {} \n Controller state:{} \n '.format(self.StatusBit , self.ErrorBit , self.StatusCode))
        elif resultStatus==0 and verbatum_status==0:
            pass
        else:
            sys.exit('Problem while getting the status of the controller - exectution aborted')

        #We now check for different type of status and initialize the device
        #due to the different step it is maybe better to check in a while loop.
        #The time it take for the controller to receve a command a send the 
        # response back is 16 ms (documentation)

        while self.StatusCode != '46' and self.StatusCode != '47' and self.StatusCode != '48' and self.StatusCode != '49' :
            
            #If the delay stage is not initialised
            if self.StatusCode=='0A': 
                self.DelayLine.IE()
                time.sleep(self.wait)

            #If the delay stage is not referenced
            if self.StatusCode=='28': 
                self.DelayLine.OR()
                time.sleep(self.wait)

            resultStatus, self.StatusBit , self.ErrorBit , self.StatusCode =self.DelayLine.TS()[0:4]
            
            if resultStatus!=0:
                sys.exit('Problem while getting the status of the controller during initialisation- exectution aborted')

            time.sleep(self.wait)
                
        print('Delay line ready to use')
        #We can now fetch some value that will be usefull later

        self.NegativeLimit=self.DelayLine.SL_Get()[1]
        self.PositiveLimit=self.DelayLine.SR_Get()[1]
        if verbatum_status==1:
            print("\n Positive limit : {} \n Negative limit {} \n".format(self.NegativeLimit,self.PositiveLimit))

    def MoveAbsolute(self,MoveDistance):
        self.CheckReadyStatus()
        self.DelayLine.PA_Set(MoveDistance)

    def MoveRelative(self,MoveDistance):
        self.CheckReadyStatus()
        self.DelayLine.PR_Set(MoveDistance)

    def GetPosition(self, Dowait):

        Pos=self.DelayLine.TP()[1]
        if Dowait==True: time.sleep(self.wait)
        return Pos

    def GetDelay(self):
        # Get delay time compared to home position 
        a=1

    def CheckReadyStatus(self):
        resultStatus, self.StatusBit , self.ErrorBit , self.StatusCode =self.DelayLine.TS()[0:4]
        while self.StatusCode != '46' and self.StatusCode != '47' and self.StatusCode != '48' and self.StatusCode != '49':
            #If the delay stage is not initialised
            if self.StatusCode=='0A': 
                self.DelayLine.IE()
                time.sleep(self.wait)

            #If the delay stage is not referenced
            if self.StatusCode=='28': 
                self.DelayLine.OR()
                time.sleep(self.wait)

            resultStatus, self.StatusBit , self.ErrorBit , self.StatusCode =self.DelayLine.TS()[0:4]

            if resultStatus!=0:
                sys.exit('Problem while getting the status of the controller during initialisation- exectution aborted')

            time.sleep(self.wait)

    def Close(self):    
        self.DelayLine.CloseInstrument()
    
    def __del__(self):
        self.DelayLine.CloseInstrument()

if __name__ == "__main__":
    DL=DelayLineObject('COM16',1,0.016)

    DL.MoveAbsolute(0)
    Pos=(DL.GetPosition(),)
    DL.MoveRelative(200)
    tpos=0
    while tpos<=200:
        tpos=DL.GetPosition()
        Pos=Pos+ (tpos,)