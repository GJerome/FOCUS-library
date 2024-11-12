try:
    from pylablib.devices import Thorlabs
except Exception as ex:
    print(ex)
    
import time


class FlipMount:

    def __init__(self, SN):
        # Class allowing for the control of the MFF101/M Flip mount. This is just a wrapper form pylablib inmplementation
        self.Device = Thorlabs.kinesis.MFF(SN)
        self.TransTime=0.3
        self.parameterDict = {'Serial number':SN,'Transition Time':self.TransTime}

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
    a = FlipMount("37007726")
    print(a.GetFlipState())
    #t0=time.time()
    a.FlipState()
    #print(time.time()-t0)


