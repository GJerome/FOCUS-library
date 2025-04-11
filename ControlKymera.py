from pyAndorSpectrograph import ATSpectrograph
import time 


class KymeraSpectrograph:

    def __init__(self):
        self.sdk = ATSpectrograph()
        ret = self.sdk.Initialize("") # ini driver for spectro
        if ATSpectrograph.ATSPECTROGRAPH_SUCCESS==ret:
            self.Wavelength=self.GetWavelength()
            self.SlitWidth=self.GetSlitwidth()
        else:
            print(ret)
        self.parameterDict={'Wavelength':self.Wavelength, 'Slit width':self.SlitWidth}   

    ###########
    # Get
    ###########
    def GetWavelength(self):
        try:
            (ret,a)=self.sdk.GetWavelength(0)            
        except:
            print("ControlKymera error: can't get wavelength returning 0")
            return 0
        if ret==20201:
            print("ControlKymera error:can't communicate with the instrument")
            a=0
        return a
    def GetSlitwidth(self):
        try:
            (ret,a)=self.sdk.GetSlitWidth(0,1)
        except:
            print("ControlKymera error: can't get slit width returning default value")
            return 10.
        if ret==20201:
            print("ControlKymera error:can't communicate with the instrument")
            a=10
        return a
    ###########
    # Set
    ###########

    def SetWavelength(self,wave):
        ret=self.sdk.SetWavelength(0,int(wave))

    def SetSlitwidth(self,width):
        ret=self.sdk.SetSlitWidth(0,1,int(width))
    
    def SetFlipMirror(self,Port):
        '''Set output 0 for direct, 1 for side'''
        ret=self.sdk.SetFlipperMirror(0,2,Port)

    ###########
    # MISC
    ###########

    def __del__(self):
        self.sdk.Close()

if __name__ == "__main__":

    spectro=KymeraSpectrograph()
    print('Spectro Wavelength = {} nm'.format(spectro.GetWavelength()))
    print('Slit width= {} um'.format(spectro.GetSlitwidth()))
    spectro.SetSlitwidth(100)
    spectro.SetWavelength(700)
    #spectro.SetFlipMirror(0)
    print('Slit width= {} um'.format(spectro.GetSlitwidth()))
    print('Spectro Wavelength = {} nm'.format(spectro.GetWavelength()))
