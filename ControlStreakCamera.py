import socket as sk

import sys
import os
import time

class StreakCamera:
    """ This class connect to the streak camera device. The constructor takes as a argument both command and data port which are specified 
    in the server windows (HDTPA RemoteX)"""
    def __init__(self,PortCmd=int,PortData=int,Buffer=int,**kwargs):

        self.IPadress='127.0.0.1'
        self.portCMD = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
        self.portCMD.settimeout(10)
        self.portData = sk.socket(sk.AF_INET, sk.SOCK_STREAM)

        try:
            self.portCMD.connect((self.IPadress, PortCmd))
            print(self.portCMD.recv(512).decode('ANSI'))
        except ConnectionRefusedError:
            sys.exit('Could not connect to the streak camera with the specified command port')
        try:
            self.portData.connect((self.IPadress, PortData))
            print(self.portData.recv(512).decode('ANSI'))
        except ConnectionRefusedError:
           sys.exit('Could not connect to the streak camera with the specified data port')

        self.Buffer=Buffer
        IniFile= kwargs.get('IniFile', None)
        if IniFile!=None:
            self.Sendcommand('AppStart(1,'+IniFile+',2)',1024)
        else:
            print('No specific experiment was specified loading default.')
            try:
                self.Sendcommand('AppStart(1,C:\ProgramData\Hamamatsu\HPDTA\HPDTA8.ini,2)',1024)
            except:
                sys.exit('Could not load experiements parameter.')
        self.ReponseReceived(1024)
        print('Finished loading')

####################################
# Acquisition related command
####################################
    def AcqStart(self,AcqMode=str):
        '''Start acquisition in the mode specified by AcqMode, as a safety the int time is set at 100ms for the moment.\n
        AcqMode can take the value Live,Acquire,AI for analog integration,Pc for single photon counting.'''
        self.Sendcommand('AcqStart('+AcqMode+')',1024)

    def AcqStop(self):
        self.Sendcommand('AcqStop()',1024)

    def AcqStatus(self):
        '''Return True if a acquisition is taking place.'''
        a=self.Sendcommand('AcqStatus()',2048)
        print(a.split(','))
        if a.split(',')[2]=='busy':
            print('busy')
            return True
        else:
            return False
    
    def AsyncStatus(self):
        a=self.Sendcommand('AsyncCommandStatus()',1024)
        print(a)
        

####################################
# Raw command related methods
####################################

    def Sendcommand(self,Cmd,BufferCMD):
        try:
            self.portCMD.send(''.join([Cmd,'\r']).encode('utf-8'))
            rep=self.portCMD.recv(BufferCMD).decode('utf-8')
        except TimeoutError:
            sys.exit('Timeout with the following command: {}'.format(Cmd))        
        return rep
    
    def ReponseReceived(self,BufferCMD):
        while True:
            try:
                rep=self.portCMD.recv(BufferCMD).decode('utf-8')
                ResponseType=rep.split(',')[0]
            except TimeoutError:
                print('Timeout while receiving multiple')
                break
            if ResponseType!='4':
                break 
####################################
# Destructor
####################################
        
    def __del__(self):
        
        if self.AcqStatus():
            print('Something took place')
            self.AcqStop()
        self.Sendcommand('AppEnd()',1024)
        self.portCMD.close()
        self.portData.close()
        

def IsPortOpen():
    s = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
    result = s.connect_ex(('127.0.0.1', 1002))

    if result == 0:
        print('socket is open')
    s.close()
     


if __name__ == "__main__":
    os.system('cls')
    print('Main file excecuting code')

    #IsPortOpen()
    sc=StreakCamera(PortCmd=1001,PortData=1002,Buffer=1024,IniFile='C:\ProgramData\Hamamatsu\HPDTA\Test.ini')
    sc.AcqStart('Live')
    time.sleep(5)
    #print(sc.Sendcommand('AppStart(True)',1024))
    #print(sc.Sendcommand("MainParamGet(GateMode)",1024))
