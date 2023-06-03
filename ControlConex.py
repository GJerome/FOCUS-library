import serial
import time
import numpy as np

# --------------------------------------------------------
def WaitStatus(cc, val, timeout):       
        #print("WaitStatus : " + val)
        for x in range(timeout):
                time.sleep(0.01)
                cmd = '1TS\r\n'
                cc.write(cmd.encode())
                status = cc.readline().decode().rstrip() 
                #print("Status loop= " + status)      
                #if val in status:
                if (status in val) and (status != ''):
                        cc.Status=status
                        #print(" Status = " + status)
                        return 1
        print("WaitStatus timeout, Status = " + status)
        return -1;

def GoToPositions(x_axis,y_axis,z_axis,Pos):
    """ The Pos is a numpy array that should be strucured in the following way
            x   y   z   t
        where (x,y,z) is the position and t is the time the controller should wait before going to the
        position specified by the next line."""

    for i in range(Pos.shape[0]): 
        print('Moving to position (x,y,z)=({},{},{}) for {} s'.format(Pos[i,0],Pos[i,1],Pos[i,2],Pos[i,3]))
        x_axis.MoveTo(Pos[i,0])
        y_axis.MoveTo(Pos[i,1])
        z_axis.MoveTo(Pos[i,2])
        time.sleep(Pos[i,3])


def MoveLine(x_axis,y_axis,z_axis,Pos_i,Pos_f,z,speed_x,speed_y):
    """ The Pos_i and Pos_f parameter are the initial and final position on the (x,y) plane htey should be store in a 1D array of 
     length 2. We also fix the z axis. The parameter t is the time it should take to go from pos_i to pos_f. If the time is too short
     a warning will be output and the maximum speed will be set."""
    temp=x_axis.GetSpeed()
    index_temp=temp.find('\r')
    v_temp_x=temp[3:index_temp]

    temp=y_axis.GetSpeed()
    index_temp=temp.find('\r')
    v_temp_y=temp[3:index_temp]

    ############
    # Initial position set
    ############
    x_axis.MoveTo(Pos_i[0])
    y_axis.MoveTo(Pos_i[1])
    z_axis.MoveTo(z)

    time.sleep(0.5)

    ############
    # Go to final position
    ############
    x_axis.MoveToInstant(Pos_f[0])
    y_axis.MoveToInstant(Pos_f[1])
    WaitStatus(x_axis.SerialPort, '1TS000033', 1000)
    WaitStatus(y_axis.SerialPort, '1TS000033', 1000)

    ############
    # Reset speed
    ############
    x_axis.SetSpeed(v_temp_x)
    y_axis.SetSpeed(v_temp_y)

# --------------------------------------------------------

class ConexController:
    """ This class connect to a motor using the Comport aguments. It communicate using Comp portts and CLI command. 
    The function is then just to ensure that the command are send accordigly and that everything is working. """
    

    def __init__(self,ComPort):
        """ This class connect to a motor using the Comport aguments. It communicate using Comp portts and CLI command. 
        The function is then just to ensure that the command are send accordigly and that everything is working.
        """

        # Connexion to the serial port
        self.SerialPort = serial.Serial(ComPort,baudrate=921600,timeout=3)
        self.Status=self.GetStatus()
        a=0
        while a!=1:
            if self.CheckNotReferencedStatus!= False:
                # Reset command
                self.SerialPort.write("1RS\r\n".encode())
                WaitStatus(self.SerialPort, '1TS00000A', 10000)
           
            # Execute home search
            self.SerialPort.write("1OR\r\n".encode()) 
            a=WaitStatus(self.SerialPort, '1TS000032', 10000)
            #print(a)
        
        self.Pos=self.GetPosition()
        


    def __del__(self):
        self.SerialPort.close()

    # Move command
    
    def MoveTo(self,Pos):
        
        # First we try to move to the position 
        tempstr="1PA"+str(Pos)+"\r\n"
        self.SerialPort.write(tempstr.encode()) 
        WaitStatus(self.SerialPort, '1TS000033 1TS000032 1TS00000E', 1000)

        # If we are in unreferenced state we try the home position and go to the postion 
        while self.CheckNotReferencedStatus():
            print('OR Command')
            self.SerialPort.write("1OR\r\n".encode()) 
            a=WaitStatus(self.SerialPort, '1TS000032', 10000)
                        
            self.SerialPort.write(tempstr.encode()) 
            WaitStatus(self.SerialPort, '1TS000033 1TS000032 1TS00000E', 1000)


        self.Pos=self.GetPosition()
    
    def MoveToInstant(self,Pos): 
        tempstr="1PA"+str(Pos)+"\r\n"
        self.SerialPort.write(tempstr.encode())
    
    # Set and Get differents properties
    def GetStatus(self):
        cmd = '1TS\r\n'
        self.SerialPort.write(cmd.encode())
        status = self.SerialPort.readline().decode().rstrip()
        return status

    def GetSpeed(self): 
        self.SerialPort.write("1VA?\r\n".encode())
        response =  self.SerialPort.readline()
        response_decoded = response.decode('UTF-8') 
        return response_decoded
    
    def GetPosition(self): 
        self.SerialPort.write("1TP\r\n".encode())
        response =  self.SerialPort.readline()
        response_decoded = response.decode('UTF-8')
        try:
            Pos=float(response_decoded[3:])
        except ValueError :
            
            exit("Problem while getting the position: {}".format(response_decoded)) 
        return Pos
    
    def SetSpeed(self,Speed): 
        tempstr="1VA"+str(Speed)+"\r\n"
        self.SerialPort.write(tempstr.encode()) 
        WaitStatus(self.SerialPort, '1TS000033 1TS000032', 1000)

    # Misc  functions
        
    def PrintAllParameter(self):
        self.SerialPort.write("1ZT\r\n".encode())# Get controller status and error
        response =  self.SerialPort.readlines()
        response_decoded = [i.decode('UTF-8') for i in response]
        [print(i) for i in response_decoded ]   # write a string

    def CheckNotReferencedStatus(self):
        temp=self.GetStatus()
        statusNotReferenced=['0A','0B','0C','0D','0E','0F']
        if any(ext in temp for ext in statusNotReferenced):
            return True

    def CorrectNotReferencedState(self):
        self.SerialPort.write("1OR\r\n".encode()) 
        a=WaitStatus(self.SerialPort, '1TS000032', 10000)
         
    

"""
print('Initialisation of z the axis')
z_axis=ConexController('COM5')
print('Initialisation of x the axis')
x_axis=ConexController('COM3')
print('Initialisation of y the axis')
y_axis=ConexController('COM4')

print('Move To different position')
Pos=np.loadtxt('PostionConex.txt')
#GoToPositions(x_axis,y_axis,z_axis,Pos)
Posi=[1,1]
Posf=[5,5]
z=5
MoveLine(x_axis,y_axis,z_axis,Posi,Posf,z,1.5,1.5)
"""