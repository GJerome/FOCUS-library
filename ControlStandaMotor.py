from ctypes import *
import os
from math import floor
import platform
import sys

# Load library
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)),"DLL_file"))
import pyximc as pyximx

def Find_Motor(vertabatum=False):
	"""If verbatum is set to true the function will output the COM port name."""
    # number of detected device
	probe_flags = pyximx.EnumerateFlags.ENUMERATE_PROBE + pyximx.EnumerateFlags.ENUMERATE_NETWORK
	enum_hints = b"addr=192.168.0.1,172.16.2.3"

	# List containing all the device , used for passing throught functions
	devenum = pyximx.lib.enumerate_devices(probe_flags, enum_hints)

	dev_count = pyximx.lib.get_device_count(devenum)
	if dev_count==0: 
		sys.exit()

	print("There is currently {} device".format(repr(dev_count)))

    # The following loop will search for the device and put them in the following order in axis[]
    # LB4 Prep ,LB4 ANA, LP ANA 
	axis_id = ["", ""]
	eng = pyximx.engine_settings_t()

	for i in range(0, pyximx.lib.get_device_count(devenum)):
		open_name = pyximx.lib.get_device_name(devenum, i)
		if vertabatum==True:
			print(open_name)
		if repr(open_name).find('COM6') != -1:
			axis_id[0] = pyximx.lib.open_device(pyximx.lib.get_device_name(devenum, i))
		elif repr(open_name).find('COM7') != -1:
			axis_id[1] = pyximx.lib.open_device(pyximx.lib.get_device_name(devenum, i))
		else:
			print('Problem during assignation of COM port for motor')
	return axis_id;


ximc_package_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "Library")
pyximx.lib.set_bindy_key(os.path.join(ximc_package_dir, "keyfile.sqlite").encode("utf-8"))

class RotationMotorStanda:
	def __init__(self,MotorId):
		self.MotorId=MotorId
		self.eng = pyximx.engine_settings_t()
		self.pos= pyximx.get_position_t()
		# conversion factor from step to deg so 80 step =1 deg
		self.convfactor = 80
		print('Created motor')		

	def SetPrecision(self):
		pyximx.lib.get_engine_settings(self.MotorId, byref(self.eng))
		self.eng.MicrostepMode = pyximx.MicrostepMode.MICROSTEP_MODE_FRAC_256
		pyximx.lib.set_engine_settings(self.MotorId, byref(self.eng))

	def MoveAbs(self,AngleAbs):
		moveM = pyximx.lib.command_move(self.MotorId, floor(AngleAbs*self.convfactor), floor(((AngleAbs* self.convfactor)%1)*256))		
		waitM = pyximx.lib.command_wait_for_stop(self.MotorId, 10)
		print(repr(waitM))
		if repr(moveM) != '0' :
			print('Problem during movement to the absolute angle {} deg'.format(AngleAbs))

	def MoveRela(self,AngleRela):
		resultA = pyximx.lib.get_position(self.MotorId, byref(self.pos))
		CurrentAngle=float(self.pos.Position / 80 + self.pos.uPosition/(256*80))
		moveM = pyximx.lib.command_move(self.MotorId, floor((CurrentAngle+AngleRela)*self.convfactor), floor((((CurrentAngle+AngleRela)*self.convfactor)%1)*256))
		waitM = pyximx.lib.command_wait_for_stop(self.MotorId, 10)
        
		if repr(moveM) != '0' :
			print('Problem during movement to the relative angle {} deg'.format(AngleRela))
	
	def GetPos(self):
		resultA = pyximx.lib.get_position(self.MotorId, byref(self.pos))
		CurrentAngle=float(self.pos.Position / 80 + self.pos.uPosition/(256*80))
		return CurrentAngle
	
#MotorIdList=Find_Motor(True)
#Motor1=RotationMotorStanda(MotorIdList[0])
#Motor1.MoveRela(+90)
		

	