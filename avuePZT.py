#!/usr/bin/env python3
"""
Application for controlling and viewing video from AVUE G50IR-WB36N PZT camera
"""

import argparse
import itertools
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
    'port': "/dev/ttyUSB0",
    'baudrate': 4800
}

BAUD_RATES = (4800, 9600)

#### TODO improve these values
PAN_DEGREES_PER_SEC = 18.4  # N.B. measured for NORMAL Speed movement
TILT_DEGREES_PER_SEC = 18.4  #### FIXME


class AVUE(Pelco):
    """Specialization of Pelco-D protocol for the AVUE G50IR-WB36N PZT camera
    """
    def __init__(self, address, port, baudrate):
        """????
        """
        super().__init__(address, port, baudrate)

        #### TODO consider removing extended commands

        MOVE_DURATION = 0.0
        INCR_SPEEDS = (Speed.SLOW, Speed.NORMAL, Speed.HIGH)
        MOVE_METHOD_NAMES = ('nop', 'up', 'down', 'right', 'rightUp', 'rightDown', 'left', 'leftUp', 'rightDown')
        MOVE_METHOD_SPECS = zip(MOVE_METHOD_NAMES, itertools.product([None, True, False], repeat=2))
        def moveMethodClosure(pan, tilt):
            """Closure for generating camera movement methods
              Inputs:
                methodName: str name of movement method
                pan: bool that pans CW if True, CCW if False, and does not pan if None
                tilt: bool that tilts up if True, down if False, and does not tilt if None
            """
            def move(self, incr=0):
                """Raise the position of the camera by a given increment

                  This moves for an amount of time given by 'incr' but moves at slow,
                   normal, or fast speed depending on the value of 'incr'.

                  Inputs:
                    incr: an int indicating the move increment -- 0=small, 1=medium, 2=large
                """
                assert incr in (0, 1, 2), f"Invalid increment '{incr}', must be in (0, 1, 2)"
                self.motion(pan, tilt, INCR_SPEEDS[incr], INCR_SPEEDS[incr])
                time.sleep(MOVE_DURATION)
                self.stop()
            return move

        for methodName, (pan, tilt) in MOVE_METHOD_SPECS:
            setattr(self, methodName, moveMethodClosure(pan, tilt))

    def query(self):
        """Override of a Pelco method that doesn't work with this camera
        """
        raise NotImplementedError("Query command not implemented on AVUE camera")

    #### TODO override other methods

    def home(self):
        """Move camera back to home position -- i.e., 0 deg azimuth and 0 deg elevation
        """
        #### FIXME figure out a good way to home the elevation
        self.extendedCommand('GotoZeroPan')

    def pan(self, direction, degrees, speed=Speed.NORMAL):
        """Pan the camera a given number of degrees either CW or CCW from the
            current position

          N.B. These movements are really rough estimates and not accurate or repeatable

          Inputs:
            direction: bool that turns the camera CW if True and CCW if False
            degrees: int that indicates the number of degrees to pan the camera
            speed: Speed value that defines the speed of the pan operation
        """
        assert degrees >= 0, "Invalid pan degrees '{degrees}', must be positive"
        self.motion(direction, None, panSpeed=speed)
        time.sleep(degrees / PAN_DEGREES_PER_SEC)
        self.stop()

    def tilt(self, direction, degrees, speed=Speed.NORMAL):
        """Pan the camera a given number of degrees either CW or CCW from the
            current position

          N.B. These movements are really rough estimates and not accurate or repeatable

          Inputs:
            direction: bool that tilts the camera up if True and down if False
            degrees: int that indicates the number of degrees to tilt the camera
            speed: Speed value that defines the speed of the tilt operation
        """
        assert degrees >= 0, "Invalid tilt degrees '{degrees}', must be positive"
        self.motion(None, direction, tiltSpeed=speed)
        time.sleep(degrees / TILT_DEGREES_PER_SEC)
        self.stop()

    def azimuth(self, degrees):
        """Move the camera to the given degrees of azimuth from the zero position

          This will first pan to the zero postition and then move to the given
           azimuth.  It will go CW or CCW, whichever distance is shorter.

          N.B. These movements are really rough estimates and not accurate or repeatable

          Inputs:
            degrees: int indicating degrees of azimuth (from 0 to 360)
        """
        assert degrees >= 0 and degrees <= 360, f"Invalid azimuth degrees: {degrees}"
        self.extendedCommand('GotoZeroPan')
        time.sleep(1)
        d = degrees if degrees < 180 else degrees - 180
        self.motion(degrees < 180, None, panSpeed=Speed.NORMAL)
        time.sleep(d / PAN_DEGREES_PER_SEC)
        self.stop()

    def elevation(self, degrees):
        """Move the camera to the given degrees of elevation from the zero position

          N.B. These movements are really rough estimates and not accurate or repeatable

          Inputs:
            degrees: int indicating degrees of elevation (from 0 to 180)
        """
        assert degrees >= 0 and degrees <= 180, f"Invalid elevation degrees: {degrees}"
        #### FIXME figure out a way to home the elevation
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

