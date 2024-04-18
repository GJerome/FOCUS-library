from ctypes import *
import time
import os
import sys
import platform




def frange(start, stop, step):
    i = start
    result=[];
    while i < stop:
        result.append(i)
        i += step
    return result
#####################################################################################
## ELEMENT TO CHANGE FOR A CALIBRATION
#####################################################################################

# Angle for the different element 
axisLP=238.15   # last calibrated value 238.152
fastLB4prep=97.1    
fastLB4ana=95.1

#Choice of the element to calibrate : LP=2 , LB4P=0, LB4A=1
choice=1

#####################################################################################
#####################################################################################

#creation of a list of angle value that the element will take

deltathetLP=frange((axisLP-0.25),(axisLP+0.25),0.002)
deltathetLB4P=frange((fastLB4prep-0.6),(fastLB4prep+0.6),0.004)
deltathetLB4A=frange((fastLB4ana-0.7),(fastLB4ana+0.7),0.004)

if choice==2:
    deltetha=deltathetLP
elif choice==0:
    deltetha=deltathetLB4P
elif choice==1:
    deltetha=deltathetLB4A
else:
    print('Wrong user input (see the value of choice)')
    
# conversion factor from step to deg so 80 step =1 deg
convfactor = 80




# log file
logfile = open('log_Calib.txt', "w")
logfile.write("Begginning of Calibration\n")

####################
# # Loading library and device
####################
dir_path = os.path.abspath(os.path.dirname(__file__))
ximc_package_dir = os.path.join(dir_path, "Library")
sys.path.append(ximc_package_dir)

if platform.system() == "Windows":
    os.environ["Path"] = ximc_package_dir + ";" + os.environ["Path"]  # add dll

try:
    from pyximc import *
except ImportError as err:
    print(
        "Can't import pyximc module. (look for relative path of library)")
    exit()
except OSError as err:
    print(err, "\n Can't load libximc library. Please add all shared libraries to the appropriate places.")
    exit()
print('Loaded Library pyminxc')
# lib is a shared library defined in pyximp.py (loaded library)

lib.set_bindy_key(os.path.join(ximc_package_dir, "keyfile.sqlite").encode("utf-8"))

# This is device search and enumeration with probing. It gives more information about devices.
probe_flags = EnumerateFlags.ENUMERATE_PROBE + EnumerateFlags.ENUMERATE_NETWORK
enum_hints = b"addr=192.168.0.1,172.16.2.3"

# List containing all the device , used for passing throught functions
devenum = lib.enumerate_devices(probe_flags, enum_hints)

# number of detected device
dev_count = lib.get_device_count(devenum)
controller_name = controller_name_t()

print("Device count: " + repr(dev_count))

# the open_device function return an id that can be used by libminx lib to
# call any  function

# The following loop will search for the device and put them in the following order in axis[]
# LB4 Prep ,LB4 ANA, LP ANA and put them with the right precision for the motor
axis_id = ["", "", ""]
eng = engine_settings_t()

for i in range(0, 4):
    open_name = lib.get_device_name(devenum, i)
    if repr(open_name).find('COM5') != -1:
        axis_id[0] = lib.open_device(lib.get_device_name(devenum, i))
    elif repr(open_name).find('COM6') != -1:
        axis_id[2] = lib.open_device(lib.get_device_name(devenum, i))
    elif repr(open_name).find('COM4') != -1:
        axis_id[1] = lib.open_device(lib.get_device_name(devenum, i))
    else:
        print('Axis not used (unplugged)')

for i in range(0, 3):
    result = lib.get_engine_settings(axis_id[i], byref(eng))
    eng.MicrostepMode = MicrostepMode.MICROSTEP_MODE_FRAC_256
    result = lib.set_engine_settings(axis_id[i], byref(eng))
    if repr(result) != '0':
        logfile.write('Problem of setting the motor precision :' + repr(result))

##Import princeston instrument

try:
    from princeston import *
except ImportError as err:
    print(err,"Can't import princeston  module. (look for relative path of library)")
    exit()
except OSError as err:
    print(err, "\n Can't load libximc library. Please add all shared libraries to the appropriate places.")
    exit()


print("Loaded Princeston module")
result_ini,experiment,auto=init_princeston()
if(result_ini):
    logfile.write('Camera found')
    print('Experiment loaded with success')
else:
    logfile.write('Problem loading exp :Camera not found pls make sure the other instance of Lightfield are closed')
    print('Problem loading exp :Camera not found')
    exit()

result= experiment.Load('Calibration')
if result ==False :
    print('Error loading experiment!')
    exit()
####################
# # Measurement
####################

mv=move_settings_t()
pos=get_position_t()

for i in range(0,len(deltetha)):
#when so for each step the microstep factor must be set to 82 deg
#witch is the equivalent of 0.04 deg
#The second parameter will only give the youy the integer as a number of step
#the third parameter will give you the decimal value rounded to the 3 floating point (precision of the motor 1/256)
#then the adequat number of microstep is found we troncate it
    
    mv=lib.command_move(axis_id[choice], int((deltetha[i] * convfactor)//1), int((round((deltetha[i] * convfactor)%1,3)*256)//1))
    wait = lib.command_wait_for_stop(axis_id[choice], 50)
    
    if repr(mv) != '0' :
         logfile.write('Problem during movement of the motor at the {} movement'.format(i))
         print('Error of the motor motion')
         
    result=lib.get_position(axis_id[choice], byref(pos))
    print('motor at {} deg'.format((pos.Position + (pos.uPosition/256))/80))
    while (wait !=0 ):
        time.sleep(1)
        wait = lib.command_wait_for_stop(axis_id[choice], 50)
    while (experiment.IsRunning and (experiment.IsReadyToRun == False) ):
        time.sleep(1)
    print('Aquisition')
    experiment.Acquire()
    while(experiment.IsRunning):
        time.sleep(1)
#####
        
print('Closing device')
for i in range(0,2):
    result=lib.close_device(axis_id[i])
