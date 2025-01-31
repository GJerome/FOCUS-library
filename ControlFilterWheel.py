try:
    from pylablib.devices import Thorlabs
except Exception as ex:
    print(ex)
    
import time

class FilterWheel:
    """
    Thorlabs FW102/212 motorized filter wheels.

    Args:
        conn: serial connection parameters (usually port or a tuple containing port and baudrate)
        respect_bound(bool): if ``True``, avoid crossing the boundary between the first and the last position in the wheel
    """
  
    def __init__(self, conn, respect_bound=True):
        self.device = Thorlabs.serial.FW(conn, respect_bound)
        self.respect_bound = respect_bound

    def get_position(self):
        """Get the wheel position (starting from 1)"""
        return self.device.get_position()

    def set_position(self, pos):
        """Set the wheel position (starting from 1)"""
        if self.respect_bound: # check if the wheel could go through zero; if so, manually go around instead
            cur_pos=self.get_position()
            if abs(pos-cur_pos)>=self.device.pcount//2: # could switch by going through zero
                medp1=(2*cur_pos+pos)//3
                medp2=(cur_pos+2*pos)//3
                self.device.set_position(int(medp1))
                self.device.set_position(int(medp2))
                self.device.set_position(int(pos))
            else:
                self.device.set_position(int(pos))
        else:
            self.device.set_position(int(pos))
        return self.device.get_position()

    def get_pcount(self):
        """Get the number of wheel positions (6 or 12)"""
        return self.device.get_pcount()

    def set_pcount(self, pcount=6):
        """Set the number of wheel positions (6 or 12)"""
        return self.device.set_pcount(pcount)

    def get_speed_mode(self):
        """Get the motion speed mode (``"low"`` or ``"high"``)"""
        return self.device.get_speed_mode()

    def set_speed_mode(self, speed_mode = "high"):
        """Set the motion speed mode (``"low"`` or ``"high"``)"""
        return self.device.set_speed_mode(speed_mode)

    def get_trigger_mode(self):
        """Get the trigger mode (``"in"`` to input external trigger, ``"out"`` to output trigger)"""
        return self.device.get_trigger_mode()

    def set_trigger_mode(self, trigger_mode = "out"):
        """Set the trigger mode (``"in"`` to input external trigger, ``"out"`` to output trigger)"""
        return self.device.set_trigger_mode(trigger_mode)

    def get_sensor_mode(self):
        """Get the sensor mode (``"off"`` to turn off when idle to eliminate stray light, ``"on"`` to remain on)"""
        return self.device.get_sensor_mode()

    def set_sensor_mode(self, sensor_mode = "off"):
        """Set the sensor mode (``"off"`` to turn off when idle to eliminate stray light, ``"on"`` to remain on)"""
        return self.device.set_sensor_mode(sensor_mode)

if __name__ == "__main__":

    FW = FilterWheel('COM18')
  #  FW.get_position()
    FW.set_speed_mode()
    FW.set_position(6)
    print(FW.get_position())