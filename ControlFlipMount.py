try:
    from pylablib.devices import Thorlabs
except Exception as ex:
    print(ex)
    
import time


class FlipMount:

    def __init__(self, SN,Name=None):
        # Class allowing for the control of the MFF101/M Flip mount. This is just a wrapper form pylablib inmplementation
        self.Device = Thorlabs.kinesis.MFF(SN)
        self.TransTime=0.3
        if Name==None:
            self.parameterDict = {'Serial number':SN,'Transition Time':self.TransTime,}
        else:
            self.parameterDict = {'{} Serial number'.format(str(Name)):SN,'{} Transition Time'.format(str(Name)):self.TransTime,}

    def ChangeState(self, state):
        '''Go to a specific state. If you are using it as a shutter please ensure that
        state 1 is transmitting ans state 0 is blocking. The function
        is blocking while the flip mount is moving '''
        if self.Device.get_state() != state:
            self.Device.move_to_state(int(state))
        
            time.sleep(self.TransTime)

    def GetFlipState(self):
        '''Get flipper state. If you are using it as a shutter please ensure that
        state 1 is transmitting ans state 0 is blocking.'''
        return self.Device.get_state()

    def FlipState(self):
        temp=self.GetFlipState()
        if self.Device.get_state() == 0:
            self.Device.move_to_state(1)     
        else:
            self.Device.move_to_state(0)

        time.sleep(self.TransTime)


if __name__ == "__main__":
    InstrumentsPara = {}
    FM = FlipMount("37007726",'Shutter')
    FM_ND = FlipMount("37007725",'ND0.5')
    #print(FM.parameterDict)
    InstrumentsPara['FlipMount']=FM.parameterDict #| FM_ND.parameterDict
    FM_ND.ChangeState(1)
    FM.ChangeState(1)
    print(FM_ND.GetFlipState())
    #t0=time.time()
    #a.FlipState()
    #print(time.time()-t0)


