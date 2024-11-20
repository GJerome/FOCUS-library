import serial
import time 
import sys
import numpy as np

class PiezoControl:
    """ This class control the piezo. All three axis are bundle in this object and one must use PiezoAxisControl
     for consistency with the conex controller."""   

    def __init__(self,ComPortLaser):        

        try:
            self.SerialPort = serial.Serial(ComPortLaser,baudrate=19200,bytesize=serial.EIGHTBITS,stopbits=serial.STOPBITS_ONE,
                                            timeout=1,parity=serial.PARITY_NONE,xonxoff=True)
        except :
            sys.exit("ControlPiezo error: Can't connect to the piezo.")
        # Put all channel in remote
        self.SetCommand('setk,0,1')
        self.SetCommand('setk,1,1')
        self.SetCommand('setk,2,1')
        # Put all channel in closed loop
        self.SetCommand('cloop,0,1')
        self.SetCommand('cloop,1,1')
        self.SetCommand('cloop,2,1')
        # Put all channel with high frequency polling
        self.SetCommand('fready,0')
        self.SetCommand('enctime,0')
        # Get all position
        self.x=self.GetX()
        self.y=self.GetY()
        self.z=self.GetZ()
        
        self.parameterDict={'Piezo mode':'closed loop','Starting position x:':self.x,'Starting position y:': self.y,'Starting position z:':self.z}

    # Get position on all axis
    def GetX(self):
        return float(self.GetCommand('rk,0').split(',')[2])
    def GetY(self):
        return float(self.GetCommand('rk,1').split(',')[2])
    def GetZ(self):
        return float(self.GetCommand('rk,2').split(',')[2])
    
    
    # Set position on all axis
    def SetX(self,pos):  
        self.SetCommand('set,0,{}'.format(np.round(float(pos),3)))     
    def SetY(self,pos):
        self.SetCommand('set,1,{}'.format(np.round(float(pos),3)))

    def SetZ(self,pos):
        self.SetCommand('set,2,{}'.format(np.round(float(pos),3)))
    
    # Misc command    
    def SetCommand(self,cmd):
        self.SerialPort.write('{}\r\n'.format(cmd).encode())
    def GetCommand(self,cmd):
        self.SerialPort.write('{}\r\n'.format(cmd).encode())
        status = self.SerialPort.read_until(b'\r').decode().rstrip()
        return status
    

class PiezoAxisControl:
    '''This calls is to control individual element of the piezo. The accepted value for the axis variable are  x,y,z. '''
    def __init__(self,piezo,axis,Timeout):

        self.piezo=piezo
        self.axis=axis
        self.Timeout=Timeout

    def MoveTo(self,pos):
        pos=np.round(pos,3)
        t0=time.time()
        t1=time.time()-t0
        while ((self.GetPosition()>pos+0.008) or (self.GetPosition()<pos-0.008)) and (t1< self.Timeout):
            if self.axis=='x':
                self.piezo.SetX(pos)
            elif self.axis=='y':
                self.piezo.SetY(pos)
            elif self.axis=='z':
                self.piezo.SetZ(pos)
            time.sleep(0.005)
            t1=time.time()-t0
            if t1>self.Timeout:
                print('Warning: ControlPiezo, could not reach position \n\t Pos:{}\n\t Wanted Pos: {} '.format(np.round(self.GetPosition(),3),pos))
        #print('\t Pos:{}\n\t Wanted Pos: {} '.format(np.round(self.GetPosition(),3),pos))


    def GetPosition(self):
        if self.axis=='x':
            return self.piezo.GetX()
        elif self.axis=='y':
            return self.piezo.GetY()
        elif self.axis=='z':
            return self.piezo.GetZ()
            
            
if __name__ == "__main__":
    piezo= PiezoControl('COM15')
    x_axis=PiezoAxisControl(piezo,'y',2)
    y_axis=PiezoAxisControl(piezo,'z',2)
    #z_axis=PiezoAxisControl(piezo,'y',2)
    # Sample plane is xz
    t0=time.time()
    x_axis.MoveTo(0.01)
    y_axis.MoveTo(0.01)
    #y_axis.MoveTo(0.1)
    #z_axis.MoveTo(0.1)
    t1=time.time()
    print(t1-t0)
    #z_axis.MoveTo(40)
    #print(y_axis.GetPosition())
    #print(z_axis.GetPosition())