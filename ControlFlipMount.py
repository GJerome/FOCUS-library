try:
    from pylablib.devices import Thorlabs 
except:
    print("pls execute pip install pylablib")


class FlipMount:

    def __init__(self,SN):
        # Class allowing for the control of the MFF101/M Flip mount. This is just a wrapper form pylablib inmplementation
        self.Device=Thorlabs.kinesis.MFF(SN)

    def ChangeState(self,state):
        if self.Device.get_state()!=state:
            self.Device.move_to_state(int(state))
        
    def FlipState(self):
        if self.Device.get_state()==0:
            self.Device.move_to_state(1)
        else:
            self.Device.move_to_state(0)
    


if __name__ == "__main__":
    a=FlipMount("37007725")
    a.ChangeState(0)