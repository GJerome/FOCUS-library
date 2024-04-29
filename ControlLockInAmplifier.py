import zhinst.core
import numpy as np
import pandas as pd
import time
import sys

def ParameterRead(ParameterFile):
    ParameterList={}
    with open(ParameterFile,'r') as ParaFile:
        for line in ParaFile:
            if line[0]!= '#':
                try:
                    ParameterList[line[0:line.index('=')-1]]=line[line.index('=')+1:].strip()
                except ValueError:
                    print('Problem reading the following parameter line: {}'.format(line))
    return ParameterList

class LockInAmplifier:

    def __init__(self,parafile):
        
        self.parameterDict=ParameterRead(parafile)
        d=zhinst.core.ziDiscovery()
        
        props = d.get(d.find(self.parameterDict['ServerName']))
        self.api_session = zhinst.core.ziDAQServer(props['serveraddress'], props['serverport'], props['apilevel'])
        try:
            self.api_session.connectDevice(self.parameterDict['ServerName'], props['interfaces'][0])
        except zhinst.core.errors.TimeoutError:    
            sys.exit("Can't connect to the lock-in amplifier. You could try to reboot the system.")
        
        # Name of node for each demodulators
        self.S1_name='/{}/demods/{}/'.format(self.parameterDict['ServerName'],self.parameterDict['Demodulator1'])
        self.S2_name='/{}/demods/{}/'.format(self.parameterDict['ServerName'],self.parameterDict['Demodulator2'])

        #############################
        # Lock-in amplifier parameters
        #############################

        # First output
        self.api_session.setInt(self.S1_name+'enable', 1)
        self.api_session.setDouble(self.S1_name+'rate', float(self.parameterDict['SamplingRate']))
        try:
            self.api_session.setInt(self.S1_name+'order', int(self.parameterDict['FilterOrder']))
            self.api_session.setDouble(self.S1_name+'TimeConstant', float(self.parameterDict['TimeConstant']))
        except KeyError:
            print('Problem setting one of the experiment parameter')

        # Second output
        self.api_session.setInt(self.S2_name+'enable', 1)
        self.api_session.setDouble(self.S2_name+'rate', float(self.parameterDict['SamplingRate']))

        try:
            self.api_session.setInt(self.S2_name+'order', int(self.parameterDict['FilterOrder']))
            self.api_session.setDouble(self.S2_name+'TimeConstant', float(self.parameterDict['TimeConstant']))
        except KeyError:
            print('Problem setting one of the experiment parameter')

        # Global parameter
        self.Timebase=float(self.api_session.getInt("/{}/clockbase".format(self.parameterDict['ServerName'])))

        self.api_session.subscribe(self.S1_name+"sample")
        self.api_session.subscribe(self.S2_name+"sample")



        print("Initialised lock-in and subscribed to the node {} and {} at a samping rate of {} S/s".format(self.S1_name+"sample",
                                                                                                            self.S2_name+"sample",float(self.parameterDict['SamplingRate'])))

    def AcquisitionLoop(self,time_exp):

        #############################
        # Creation of data vector
        #############################

        data_Source1R=np.empty(1)
        data_Source1T=np.empty(1)
        data_Source2R=np.empty(1)
        data_Source2T=np.empty(1)
        t1=np.empty(1)
        t2=np.empty(1)

        t0=time.time()
        time_run=0

        self.api_session.sync()

        while True:
            temp=self.api_session.poll(1, 500,0x0001,True)
            try:

            #############################
            # Data stream
            #############################
                R1=np.sqrt(np.square(temp[self.S1_name+'sample']['x'])+np.square(temp[self.S1_name+'sample']['y']))
                theta1=np.arctan2(temp[self.S1_name+'sample']['x'],temp[self.S1_name+'sample']['y'])
                R2=np.sqrt(np.square(temp[self.S2_name+'sample']['x'])+np.square(temp[self.S2_name+'sample']['y']))
                theta2=np.arctan2(temp[self.S2_name+'sample']['x'],temp[self.S2_name+'sample']['y'])

            #############################
            # Timestamps stream
            #############################
                t1=np.append(t1,temp[self.S1_name+"sample"]['timestamp'])
                t2=np.append(t2,temp[self.S2_name+"sample"]['timestamp'])

            except:
                print("It seems that the field didn't exist, loop didn't finish \n The dictonary had the following data keys:\n {} ".format(temp.keys()))
                break

            data_Source1R=np.append(data_Source1R,R1)
            data_Source1T=np.append(data_Source1T,theta1)
            data_Source2R=np.append(data_Source2R,R2)
            data_Source2T=np.append(data_Source2T,theta2)

            time_run=time.time()-t0
            if time_run>time_exp:
                break
        t1=(t1-t1[1])/self.Timebase
        return pd.DataFrame({'t':t1[1:],'R1':data_Source1R[1:],'Phase1':data_Source1T[1:],
                             'R2':np.interp(t1[1:],t2[1:],data_Source2R[1:]),'Phase2':np.interp(t1[1:],t2[1:],data_Source2T[1:])})
    
    def AcquisitionLoopLegacy(self,time_exp):
        #############################
        # Creation of data vector
        #############################

        data_Source1=np.empty(1)
        data_Source2=np.empty(1)
        t1=np.empty(1)
        t2=np.empty(1)

        t0=time.time()
        time_run=0

        self.api_session.sync()

        while True:
            temp=self.api_session.poll(1, 500,0x0001,True)
            try:

            #############################
            # Data stream
            #############################
                R1=np.sqrt(np.square(temp[self.S1_name+'sample']['x'])+np.square(temp[self.S1_name+'sample']['y']))
                R2=np.sqrt(np.square(temp[self.S2_name+'sample']['x'])+np.square(temp[self.S2_name+'sample']['y']))

            #############################
            # Timestamps stream
            #############################
                t1=np.append(t1,temp[self.S1_name+"sample"]['timestamp'])
                t2=np.append(t2,temp[self.S2_name+"sample"]['timestamp'])

            except:
                print("It seems that the field didn't exist, loop didn't finish \n The dictonary had the following data keys:\n {} ".format(temp.keys()))
                break

            data_Source1=np.append(data_Source1,R1)
            data_Source2=np.append(data_Source2,R2)

            time_run=time.time()-t0
            if time_run>time_exp:
                break
        return data_Source1,t1,data_Source2,t2
    
    
    def SetPathValue(self,path,value):
        #DEMODS/n/ORDER
        try:
            if type(value) is int:
                self.api_session.setInt(path, value)
            elif type(value) is float:
                self.api_session.setDouble(path, value)
            else:
                print('Problem with the value: {} which type is {}'.format(value,type(value)))
        except Exception as e: 
            print('Zhinst error:')
            print(e)
            
    def GetPathValue(self,path):
        try:
            a=self.api_session.get(path)
        except Exception as e: 
            print('Zhinst error:')
            print(e)
            a='Error'
        return a
    
    def GetParameterDictory(self,path):
        return self.parameterDict

    def AutorangeSource(self):
        #Beware there is already a time sleep 
        a=self.SetPathValue('/dev2940/sigins/1/autorange', 1)
        time.sleep(5.5)
        a=self.SetPathValue('/dev2940/sigins/0/autorange', 1)
        time.sleep(5.5)
        

    def SetOutputTA(self,TriggerInput):
        ''' Prepare output depanding on the source that is used for trigger.
        '''
        #Output 1
        self.SetPathValue('/dev2940/sigouts/0/on', 1)
        self.SetPathValue('/dev2940/sigouts/0/range', 1.5)
        self.SetPathValue('/dev2940/sigouts/0/offset', 0.75)
        self.SetPathValue('/dev2940/sigouts/0/amplitudes/3', 0.75)
        self.SetPathValue('/dev2940/sigouts/0/enables/3', 1)

        #Output 2
        self.SetPathValue('/dev2940/sigouts/1/on', 1)
        self.SetPathValue('/dev2940/sigouts/1/range', 1.5)
        self.SetPathValue('/dev2940/sigouts/1/offset', 0.75)
        self.SetPathValue('/dev2940/sigouts/1/amplitudes/7', 0.75)
        self.SetPathValue('/dev2940/sigouts/0/enables/7', 1)

        # Ensure extref lock in
        self.SetPathValue('/dev2940/extrefs/0/enable', 1)
        self.SetPathValue('/dev2940/extrefs/1/enable', 1)
        # Ensure that the trigger is selected
        if TriggerInput=='Trigger1':
            self.SetPathValue('/dev2940/demods/3/adcselect', 2)
            self.SetPathValue('/dev2940/demods/7/adcselect', 2)
        elif TriggerInput=='Trigger2':
            self.SetPathValue('/dev2940/demods/3/adcselect', 3)
            self.SetPathValue('/dev2940/demods/7/adcselect', 3)

if __name__ == "__main__":
    LockInParaFile='ParameterLockInTA.txt'

    lock=LockInAmplifier(LockInParaFile)
    print(lock.AcquisitionLoop(0.5))