from datetime import datetime
import numpy as np

def ExportFileLockIn(FileName,data):
    date=datetime.today().strftime('%Y-%m-%d')
    np.savetxt(date+FileName+'txt',data,header='Timestamps \t S2/S1 \t S2 \t S1')