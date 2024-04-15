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
    def StartAcq(self,AcqMode=str):
        '''Start acquisition in the mode specified by AcqMode, as a safety the int time is set at 100ms for the moment.\n
        AcqMode can take the value Live,Acquire,AI for analog integration,Pc for single photon counting.'''
        self.Sendcommand('AcqStart('+AcqMode+')',1024)
        self.AsyncStatusReady()

    def StartSeq(self,AcqMode,NbrSeq):
        self.Sendcommand('SeqParamSet(AcquisitionMode,'+str(AcqMode)+')',1024)
        self.AsyncStatusReady()
        self.Sendcommand('SeqParamSet(NoOfLoops,'+str(NbrSeq)+')',1024)
        self.AsyncStatusReady()
        self.Sendcommand('SeqStart()',1024)

    def StopAcq(self):
        self.Sendcommand('AcqStop()',1024)
        self.AsyncStatusReady()

    def BckgSubstraction(self):
        self.AcqStatusReady()
        a=self.Sendcommand('CorDoCorrection(Current,Background)',1024)

    def SaveImg(self,Folder):
        self.AcqStatusReady()
        print('Saving')
        self.Sendcommand('ImgSave(Current,IMG,'+Folder+',1)',1024)
        self.AsyncStatusReady()

    def SaveSeq(self,Folder):
        self.AcqStatusReady()
        print('Saving sequence')
        self.Sendcommand('SeqSave(IMG,'+Folder+')',1024)
        self.AsyncStatusReady()

    def Set_NumberIntegration(self,Mode,Nbr):
        a=self.Sendcommand('CamParamSet('+str(Mode)+',NrExposures,'+str(Nbr)+')',1024)
    
    def Set_MCPGain(self,Gain):
        a=self.Sendcommand('DevParamSet(TD,MCP Gain,'+str(Gain)+')',1024)
    
    def Get_Delay1(self):
        a=self.Sendcommand('DevParamGet(Delay1)',1024)
        print(a)

    def Get_Delay2(self):
        a=self.Sendcommand('DevParamGet(Delay2)',1024)
        print(a)
####################################
# Shutter
####################################
    def ShutterOpen(self):
        self.Sendcommand('DevParamSet(TD,Shutter,Open)',1024)
        time.sleep(5)

    def ShutterOpenFast(self):
        self.Sendcommand('DevParamSet(TD,Shutter,Open)',1024)

    def ShutterClose(self):
        self.Sendcommand('DevParamSet(TD,Shutter,Closed)',1024)
        time.sleep(5)
####################################
# Status
####################################
        
    def AcqStatusReady(self):
        '''Return True if a acquisition is taking place.'''
        
        while True:
            a=self.Sendcommand('AcqStatus()',2048)
            if a.split(',')[1]=='AcqStatus' and a.split(',')[2]=='busy':
                continue
            elif a.split(',')[1]=='AcqStatus' and a.split(',')[2]=='idle\r':
                break
            time.sleep(1)
            
    def AsyncStatusReady(self):
        while True:
            try:
                a=self.Sendcommand('AsyncCommandStatus()',1024)
            except TimeoutError:
                print('Timeout Async')
                break
            except TypeError:
                print('Another response was received while async')
                break
            try:
                #if a.split(',')[4]=='1\r' or a.split(',')[2]=='0' :
                if a.split(',')[2]=='0' :
                    break
            except IndexError:
                continue
            time.sleep(0.5)
        

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
        self.AsyncStatusReady()
        self.StopAcq()        
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
    print(sc.Get_Delay1())
    print(sc.Get_Delay2())
    #sc.Set_NumberIntegration('AI',10)
    #sc.ShutterOpen()
    #sc.StartSeq('AI',5)
    #sc.ShutterClose()
    #sc.BckgSubstraction()
    #sc.SaveSeq('C:\\Users\\Hamamatsu\\Documents\\Data\\1.trash\\000001.img')
    #time.sleep(5)
    #print(sc.Sendcommand('AppStart(True)',1024))
    #print(sc.Sendcommand("MainParamGet(GateMode)",1024))
