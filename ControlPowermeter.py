import win32com.client 
import time
import pandas as pd
import matplotlib.pyplot as plt

class CentauryPowermeter:
    def __init__(self):
        self.UsbDevice = win32com.client.Dispatch("OphirLMMeasurement.CoLMMeasurement")
         # Stop & Close all devices
        self.UsbDevice.StopAllStreams() 
        self.UsbDevice.CloseAll()
        self.SN=self.UsbDevice.ScanUSB()
        self.Handle=self.UsbDevice.OpenUSBDevice(self.SN[0])
        self.Wavelength= self.GetWavelength()
        self.RangeList=self.GetRanges()[1]

    ############
    # MISC functions
    ############
    def AcquireData(self,timeAcq):

        self.UsbDevice.StartStream(self.Handle, 0)		# start measuring
        t0=time.time()
        Data=[]
        TimeStamp=[]
        while (time.time()-t0)<=timeAcq:		
            data = self.UsbDevice.GetData(self.Handle,0)
            if len(data[0]) > 0:		# if any data available, print the first one from the batch
                Data.append(data[0][0])
                TimeStamp.append(data[1][0])
            time.sleep(.1)
        DataPd=pd.DataFrame({'Data':Data,'Time':TimeStamp})
        DataPd['Time']=(DataPd['Time']-DataPd.loc[0,'Time'])/1000
        self.UsbDevice.StopStream(self.Handle, 0)
        return DataPd
    ############
    # Get
    ############
    def GetWavelength(self):
        Index,WaveList=self.UsbDevice.GetWavelengths(self.Handle,0)
        return WaveList[Index]
    
    def GetRanges(self):
        return self.UsbDevice.GetRanges(self.Handle,0)

    ############
    # Set
    ############
    def SetWavelengthIndex(self,Wave):
        temp,WaveList=self.UsbDevice.GetWavelengths(self.Handle,0)
        IsPresent=any(int(x)==Wave for x in WaveList)
        if IsPresent==False:
            self.UsbDevice.AddWavelength(self.Handle,0,Wave)
            temp,WaveList=self.UsbDevice.GetWavelengths(self.Handle,0)
        self.UsbDevice.SetWavelength(self.Handle,0,WaveList.index(str(Wave)))

    
    def SetRange(self,index):
        '''Set the index in rangeList to set the range to. Usually it is best to 
        set it to auto so the index 0.''' 
        self.UsbDevice.SetRange(self.Handle,0,index)

    def __del__(self):
        self.UsbDevice.CloseAll()

if __name__ == "__main__":
    Power=CentauryPowermeter()

    print(Power.GetWavelength())
    print(Power.GetRanges())
    
    Data=Power.AcquireData(5)

    fig,ax=plt.subplots(1,1)
    ax.scatter(Data['Time'],Data['Data'])
    ax.set_xlabel('Time[s]')
    ax.set_ylabel('Power [W]')
    plt.show()


