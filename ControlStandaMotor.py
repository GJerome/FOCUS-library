from ctypes import *
import os
import platform
import sys

# Load library
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)),"DLL_file"))
import pyximc as pyximx
# use cdecl on unix and stdcall on windows
def ximc_shared_lib():
    if platform.system() == "Linux":
        return CDLL("libximc.so")
    elif platform.system() == "FreeBSD":
        return CDLL("libximc.so")
    elif platform.system() == "Darwin":
        return CDLL("libximc.framework/libximc")
    elif platform.system() == "Windows":
        return WinDLL("libximc.dll")
    else:
        return None

def Find_Motor():
    # number of detected device
	probe_flags = pyximx.EnumerateFlags.ENUMERATE_PROBE + pyximx.EnumerateFlags.ENUMERATE_NETWORK
	enum_hints = b"addr="

	# List containing all the device , used for passing throught functions
	devenum = pyximx.lib.enumerate_devices(probe_flags, enum_hints)

	dev_count = pyximx.lib.get_device_count(devenum)
	if dev_count==0: 
		sys.exit()

	print("There is currently {} device".format(repr(dev_count)))

    # The following loop will search for the device and put them in the following order in axis[]
    # LB4 Prep ,LB4 ANA, LP ANA 
	axis_id_f = ["", "", ""]
	eng = pyximx.engine_settings_t()

	for i in range(0, 4):
		open_name = pyximx.lib.get_device_name(devenum, i)
		if repr(open_name).find('COM5') != -1:
			axis_id_f[0] = pyximx.lib.open_device(pyximx.lib.get_device_name(devenum, i))
		elif repr(open_name).find('COM6') != -1:
			axis_id_f[2] = pyximx.lib.open_device(pyximx.lib.get_device_name(devenum, i))
		elif repr(open_name).find('COM4') != -1:
			axis_id_f[1] = pyximx.lib.open_device(pyximx.lib.get_device_name(devenum, i))
		else:
			print('Axis not used in Muller exp')
	return axis_id_f;


ximc_package_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "Library")
pyximx.lib.set_bindy_key(os.path.join(ximc_package_dir, "keyfile.sqlite").encode("utf-8"))

class RotationMotorStanda:
	def _init_(self,MotorId):
		self.MotorId=MotorId
		self.eng = pyximx.engine_settings_t()
		self.pos= pyximx.get_position_t()
		# conversion factor from step to deg so 80 step =1 deg
		self.convfactor = 80
		print('Created motor')		

	def SetPrecision(self):
		pyximx.lib.get_engine_settings(self.MotorId, byref(self.eng))
		self.eng.MicrostepMode = pyximx.MicrostepMode.MICROSTEP_MODE_FRAC_256
		pyximx.lib.set_engine_settings(self.MotorId, byref(self.MotorId))

	def MoveAbs(self,AngleAbs):
		moveM = lib.command_move(self.MotorId, int((AngleAbs) * self.convfactor//1), int((round((AngleAbs) * self.convfactor)%1,3)*256)//1)
		waitM = lib.command_wait_for_stop(self.MotorId, 50)
        
		if repr(moveM) != '0' :
			print('Problem during movement to the absolute ange {} deg'.format(AngleAbs))

	def MoveRela(self,AngleRela):
		resultA = lib.get_position(self.MotorId, byref(self.pos))

	