from datetime import datetime
import numpy as np
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mat

import tkinter as tk
from tkinter.filedialog import askdirectory

def AskDirectory():
    path = askdirectory(title='Select Folder')
    return path


def ExportFileLockIn(path,FileName,data):
    date=datetime.today().strftime('%Y-%m-%d')
    data.to_pickle(path+'/'+date+FileName+'.pkl')

def ExportFileLockInLegacy(path,FileName,data):
    date=datetime.today().strftime('%Y-%m-%d')
    np.savetxt(path+'/'+date+FileName+'.txt',data,header='Timestamps \t S2/S1 \t S2 \t S1')

def ExportFileBeamSpotSize(path,FileName,data):
    print(path)
    date=datetime.today().strftime('%Y-%m-%d')
    np.savetxt(path+'/'+date+FileName+'.txt',data,header='S1 \t Std S1 \t S2 \t Std S2 \t ypos')

def ExportFileChopperOptimisation(path,FileName,data):
    date=datetime.today().strftime('%Y-%m-%d')
    np.savetxt(path+'/'+date+FileName+'.txt',data,header='Angle \t S1 \t Std S1 \t S2 \t Std S2')

def ImportIMGFile(path,FileName,verbatum,graphs):
    """ This methods load the binarry .img file created by the streak camera software and return the data and other information stored 
    in it as a dictionary.    
    This  dictionary has the following structure:
        -Data :2D numpy array
        -TimeRange :1D numpy array
        -TimeUnit: string
        -SpaceRange: a  numpy 1D array 
        -SpaceUnit:string
    The verbatum parameter will print all the parameters of the file is set to True.
    The graphs parameter will make a graphical representation of the data if set to true.
    """
    cm = 1/2.54


    ########################
    #Load and parse the file
    ########################
    file=open(path+'/'+FileName,mode='rb')
    data_raw=file.read()
    IndexDataStart=data_raw[64:].index(b'\x00\x00\x00\x00\x00\x00\x00\x00')+64

    if verbatum==True:
        print(data_raw[64:IndexDataStart].decode())

    ########################
    #Recover image basic parameter
    ########################
    #BitDepth=np.frombuffer(data_raw[12:13], dtype=np.dtype('u1'))
    BytesPerPixel=int(data_raw[data_raw.find(b'BytesPerPixel')+14: \
                                        data_raw.find(b'BytesPerPixel')+15].decode())

    #It can't be that there is more than 2048 pixel which should then show as as 4 char
    #so we split to only slect the right amount of character
    ImgWidth=int(data_raw[data_raw.find(b'HWidth')+8: \
                                        data_raw.find(b'HWidth')+13].decode().split('"')[0])
    ImgHeight=int(data_raw[data_raw.find(b'VWidth')+8: \
                                        data_raw.find(b'VWidth')+13].decode().split('"')[0])

    IndexDataEnd=ImgWidth*ImgHeight*BytesPerPixel+IndexDataStart

    if verbatum==True:
        print('Shape of image (widht x height): {}x{} px'.format(ImgWidth,ImgHeight))


    ########################
    #Recover the unit for the different axis
    ########################

    TimeUnit=data_raw[data_raw.find(b'ScalingYUnit'): \
                                        data_raw.find(b'ScalingYUnit')+18].decode().split('"')
    XUnit=data_raw[data_raw.find(b'ScalingXUnit'): \
                                        data_raw.find(b'ScalingXUnit')+18].decode().split('"')

    if TimeUnit[1]=='' :
        Time=np.linspace(-1,1,ImgHeight)
        TimeUnit[1]=='a.u'
    elif TimeUnit[1]!='':
        try:
            Time=np.frombuffer(data_raw[IndexDataEnd:], dtype=np.dtype('<f4'))
            print('Single sweep data')
        except ValueError:
            Time=np.frombuffer(data_raw[IndexDataEnd-13:], dtype=np.dtype('<f4'))
            print('Synchroscan data')

    if XUnit[1]=='':
        x=np.linspace(-1,1,ImgWidth)
        XUnit[1]='a.u'
    elif TimeUnit[1]!='' and XUnit[1]!='':
        temp=np.frombuffer(data_raw[IndexDataEnd-13:], dtype=np.dtype('<f4'))
        x=temp[0:ImgWidth]
        Time=temp[ImgWidth:]

    ########################
    #Load the data
    ########################

    if BytesPerPixel==4:
        Data= np.reshape(np.frombuffer(data_raw[IndexDataStart:IndexDataEnd], dtype=np.dtype('>u4')), newshape=(ImgHeight, ImgWidth))
    elif BytesPerPixel==2:
        Data= np.reshape(np.frombuffer(data_raw[IndexDataStart:IndexDataEnd], dtype=np.dtype('>u2')), newshape=(ImgHeight, ImgWidth))

    ########################
    #Finally we plot the data
    ########################
    if graphs==True:
        fig=plt.figure(figsize=(5*cm,5*cm))
        ax0 =plt.subplot(1,1,1)

        mat.rcParams.update({'font.size':12,'font.family':'sans-serif','font.sans-serif':['Arial'],
                            'xtick.labelsize':9,'ytick.labelsize':9,'figure.dpi':300,'savefig.dpi':300})
        im=ax0.pcolormesh(x,Time-np.min(Time),Data)
        ax0.set_ylabel('Time [{}]'.format(TimeUnit[1]))
        ax0.set_xlabel('x[{}]'.format(XUnit[1]))
        ax0.invert_yaxis()
        fig.colorbar(im)
    
    ########################
    #Create and return the dictionnary
    ########################
    
    Final={'Data':Data,'TimeRange':Time,'TimeUnit':TimeUnit[1],'SpaceRange':x,'SpaceUnit':XUnit[1]}
    return Final



def PrepareDirectory(GeneralExperimentParameter,Intruments):
    """ This methods create and save all the parameter of the intruments. 
    It will first save the general experiments parameters and then create section for each instruments\n 
    Instruments= Nested dictionary. Each dictionary should contains all the relevant parameters.\n
    GeneralExperimentParameter= Dictionnary containning all the experiment parameter
    """
    path=AskDirectory()
    file=open(path+'/ExperimentParameter.txt','w')
    SectionHeader="############\n"
    InstrumentsHeader="#####\n"
    file.write(SectionHeader+"# General experiment parameter \n"+SectionHeader)

    for para in GeneralExperimentParameter:
        file.write(para+'='+str(GeneralExperimentParameter[para])+'\n')

    file.write('\n\n'+SectionHeader+"# Instruments parameter \n"+SectionHeader)

    for inst in Intruments:
        file.write('\n'+InstrumentsHeader+"#"+str(inst)+"\n"+InstrumentsHeader)
        Instrudict=Intruments[inst]
        for instrupara in Instrudict:
            file.write(instrupara+'='+str(Instrudict[instrupara])+'\n')
    file.close()

    return path

# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()

if __name__ == "__main__":
    GeneralPara={}
    InstrumentsPara={}
    print(PrepareDirectory(GeneralPara,InstrumentsPara))
