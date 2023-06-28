from datetime import datetime
import numpy as np
import tkinter as tk
from tkinter.filedialog import askdirectory

def ExportFileLockIn(path,FileName,data):
    date=datetime.today().strftime('%Y-%m-%d')
    np.savetxt(path+'/'+date+FileName+'txt',data,header='Timestamps \t S2/S1 \t S2 \t S1')

def AskDirectory():
    path = askdirectory(title='Select Folder')
    return path

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

