'''
Library for Pelco-D Protocol control of a PZT camera mount
'''

import logging
from queue import Queue

from parse import parse
import serial


DEF_PORT = "/dev/ttyUSB0"

DEF_BAUDRATE = 4800

DEF_CAMERA_ADDRESS = 0

DEF_SERIAL_TIMEOUT = 0.1    # serial port timeout (secs)


class Pelco():
    def __init__(self, camAddress=DEF_CAMERA_ADDRESS, port=DEF_PORT, baudrate=DEF_BAUDRATE, timeout=DEF_SERIAL_TIMEOUT):
        self.camAddress = camAddress
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

        self.inQ = Queue()

        self.serial = None
        try:
            # N.B. Defaults to 8-N-1, no (HW or SW) flow control
            self.serial = serial.Serial(port=port, baudrate=baudrate, timeout=self.timeout)
        except Exception as ex:
            logging.error(f"Failed to open serial port '{port}': {ex}")
        assert self.serial and self.serial.isOpen(), f"Serial port '{port}' not open"
        self.open = True
        logging.debug(f"Opened {port} at {baudrate}")


#
# TEST
#
if __name__ == '__main__':
    cam = Pelco()

