#!/usr/bin/env python3
"""
Application for controlling and viewing video from AVUE G50IR-WB36N PZT camera
"""

import argparse
import json
import logging
import os
import signal
import sys
import threading
import time
import yaml
from yaml import Loader

from Pelco import *


DEFAULTS = {
    'logLevel': "INFO",  #"DEBUG"  #"WARNING"
    'address': 1,
    'port': "dev/ttyUSB0",
    'baudrate': 4800
}

BAUD_RATES = (4800, 9600)


class AVUE(Pelco):
    """Specialization of Pelco-D protocol for the AVUE G50IR-WB36N PZT camera
    """
    def __init__(self, address, port, baudrate):
        """????
        """
        #### TODO set camera to 9600 baud

        super().__init__(address, port, baudrate)

        #### TODO consider removing extended commands

    def query(self):
        """Override of a Pelco method that doesn't work with this camera
        """
        raise NotImplementedError("Query command not implemented on AVUE camera")

    #### TODO override other methods

    def pan(self, direction, degrees, speed=Speed.NORMAL):
        """Pan the camera a given number of degrees either CW or CCW

          Inputs:
            direction: bool that turns the camera CW if True and CCW if False
            degrees: int that indicates the number of degrees to pan the camera
            speed: Speed value that defines the speed of the pan operation
        """
        self.motion(True, None, panSpeed=speed)
        time.sleep((SECS_PER_DEGREE_PAN * degrees) - PAN_OVERHEAD_TIME)
        self.stop()

    def tilt(self, direction, degrees, speed=Speed.NORMAL):
        """Pan the camera a given number of degrees either CW or CCW

          Inputs:
            direction: bool that turns the camera CW if True and CCW if False
            degrees: int that indicates the number of degrees to pan the camera
            speed: Speed value that defines the speed of the pan operation
        """
        self.motion(True, None, panSpeed=speed)
        time.sleep((SECS_PER_DEGREE_PAN * degrees) - PAN_OVERHEAD_TIME)
        self.stop()

    def azimuth(self, degrees):
        """Move the camera to the given degrees of azimuth from the zero position

          Inputs:
            degrees: int indicating degrees of azimuth (from 0 to 360)
        """
        assert degrees >= 0 and degrees <= 360, f"Invalid azimuth degrees: {degrees}"
        #### TODO keep track of current azimuth, re-zero whenever other motion happens
        raise NotImplementedError("TBD")

    def elevation(self, degrees):
        """Move the camera to the given degrees of elevation from the zero position

          Inputs:
            degrees: int indicating degrees of elevation (from 0 to 180)
        """
        assert degrees >= 0 and degrees <= 180, f"Invalid elevation degrees: {degrees}"
        #### TODO keep track of current elevation, re-zero whenever other motion happens
        raise NotImplementedError("TBD")

    def irMode(self, onOff):
        """Turn the IR illuminator on or off

          N.B. The camera automatically shifts to IR mode when the illuminator
               is turned on, and back to normal color mode when it's turned off

          Inputs:
            onOff: bool that turn the IR illuminator on if True and off if False
        """
        self.preset("Call" if onOff else "Set", 62)

    def wiper(self):
        """Run the camera's wiper for five cycles
        """
        self.preset("Call", 63)


def run(options):
    '''
    for s in ('TERM', 'HUP', 'INT'):
        sig = getattr(signal, 'SIG'+s)
        signal.signal(sig, shutdownHandler)
    '''
    cam = AVUE(options.address, options.port, options.baudrate)
    cam.motion(True, True, Speed.NORMAL, Speed.NORMAL)
    import time #### TMP TMP TMP
    time.sleep(2)
    cam.stop()
    sys.exit(0)

def getOpts():
    usage = f"Usage: {sys.argv[0]} [-v] [-L <logLevel>] [-l <logFile>] " + \
      "[-a <address>] [-b <baudrate>] [-p <port>]"
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-L", "--logLevel", action="store", type=str,
        default=DEFAULTS['logLevel'],
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level")
    ap.add_argument(
        "-l", "--logFile", action="store", type=str,
        help="Path to location of logfile (create it if it doesn't exist)")
    ap.add_argument(
        "-a", "--address", action="store", type=int, default=DEFAULTS['address'],
        help="Pelco-D device address of AVUE camera")
    ap.add_argument(
        "-b", "--baudrate", action="store", type=int, default=DEFAULTS['baudrate'],
        choices=BAUD_RATES,
        help="baud rate of the RS-485 connection to the AVUE camera")
    ap.add_argument(
        "-p", "--port", action="store", type=str, default=DEFAULTS['port'],
        help="RS-485 port connected to the AVUE camera")
    ap.add_argument(
        "-v", "--verbose", action="count", default=0,
        help="Enable printing of debug info")
    opts = ap.parse_args()

    if opts.logFile:
        logging.basicConfig(filename=opts.logFile,
                            format='%(asctime)s %(levelname)-8s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            level=opts.logLevel)
    else:
        logging.basicConfig(level=opts.logLevel,
                            format='%(asctime)s %(levelname)-8s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

    if opts.address < 0 or opts.address > 255:
        logging.error(f"Invalid camera address '{opts.address}': must be between 0-255")
        sys.exit(1)

    if opts.baudrate not in BAUD_RATES:
        logging.error(f"Invalid baud rate '{opts.baudrate}': must be be in {list(BAUD_RATES)}")
        sys.exit(1)

    if opts.verbose:
        print(f"    Camera Address:  {opts.address}")
        print(f"    RS-485 Port:     {opts.port}")
        print(f"    RS-485 Baudrate: {opts.baudrate}")
    return opts


if __name__ == '__main__':
    opts = getOpts()
    r = run(opts)
    sys.exit(r)

