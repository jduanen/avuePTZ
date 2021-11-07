#!/usr/bin/env python3
"""
Application for controlling and viewing video from AVUE G50IR-WB36N PZT camera
"""

import argparse
import functools
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

from flask import (Flask, Blueprint, flash, g, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from Pelco import *


#### FIXME add web server port to defaults

DEFAULTS = {
    'logLevel': "INFO",  #"DEBUG"  #"WARNING"
    'address': 1,
    'port': "/dev/ttyUSB0",  ##"/dev/ttyAMA0",
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
        MOVE_METHOD_NAMES = ('nop', 'up', 'down', 'right', 'rightUp', 'rightDown', 'left', 'leftUp', 'leftDown')
        MOVE_METHOD_SPECS = zip(MOVE_METHOD_NAMES, itertools.product([None, True, False], repeat=2))

        def moveMethodClosure(pan, tilt):
            """Closure for generating continuous camera movement methods
              Inputs:
                pan: bool that pans CW if True, CCW if False, and does not pan if None
                tilt: bool that tilts up if True, down if False, and does not tilt if None
            """
            def move(speed=Speed.NORMAL):
                """Move the camera in the given direction(s) at the given speed

                  N.B.  This starts the camera in motion and it must be stopped at some point

                  Inputs:
                    speed: Speeed value indicating the movement speed in each of the selected directions
                """
                self.motion(pan, tilt, speed, speed)
            return move

        def moveIncrMethodClosure(pan, tilt):
            """Closure for generating incremental camera movement methods
              Inputs:
                self: ?
                pan: bool that pans CW if True, CCW if False, and does not pan if None
                tilt: bool that tilts up if True, down if False, and does not tilt if None
            """
            def moveIncr(duration=MOVE_DURATION, incr=0):
                """Move the camera in the selected direction(s) by a given increment

                  This moves for a fixed amount of time given at a speed given by the
                   value of 'incr'

                  Inputs:
                    duration: a float indicating the number of msecs to move in each axis
                    incr: an int indicating the move increment -- 0=small, 1=medium, 2=large
                """
                assert duration >= 0.0, f"Invalid duration: {duration}"
                assert incr in (0, 1, 2), f"Invalid increment '{incr}', must be in (0, 1, 2)"
                self.motion(pan, tilt, INCR_SPEEDS[incr], INCR_SPEEDS[incr])
                time.sleep(duration)
                self.stop()
            return moveIncr

        for methodName, (pan, tilt) in MOVE_METHOD_SPECS:
            setattr(self, methodName, moveMethodClosure(pan, tilt))
            setattr(self, f"{methodName}Incr", moveIncrMethodClosure(pan, tilt))

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
        assert 0 <= degrees <= 360, f"Invalid azimuth degrees: {degrees}"
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
        assert 0 <= degrees <= 180, f"Invalid elevation degrees: {degrees}"
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
    app = Flask(__name__) ## , instance_relative_config=True)
    cam = AVUE(options.address, options.port, options.baudrate)

    MOVE_FUNCS = {
        'Up': cam.up,
        'Down': cam.down,
        'Left': cam.left,
        'LeftUp': cam.leftUp,
        'LeftDown': cam.leftDown,
        'Right': cam.right,
        'RightUp': cam.rightUp,
        'RightDown': cam.rightDown
     }

    @app.route('/hello/<name>')
    def hello(name):
        return f"Hello, World: {name}"

    @app.route('/')
    def index():
        return render_template('./index.html')

    @app.route('/motion')
    def motion():
        return render_template('./motion.html')

    @app.route('/move')
    def move():
        direction = request.args.get('direction')
        s = request.args.get('speed')
        speed = int(s) if s else 0
        logging.debug(f"MOVE: {direction} @ {speed}")
        if direction == 'Stop':
            cam.stop()
        else:
            if direction:
                MOVE_FUNCS[direction](speed)
        return("nothing")
        '''
        j = {'foo': 1}
        return(j)
        '''

    @app.route('/wiper')
    def wiper():
        cam.wiper()
        return("nothing")

    @app.route('/zoom')
    def zoom():
        d = request.args.get('direction')
        speed = 2  #### FIXME
        if d == 'Stop':
            logging.debug("ZOOM: Stop")
            cam.stop()
        else:
            direction = d == "In"
            logging.debug(f"ZOOM: {direction} @ {speed}")
            cam.zoom(direction, speed)
        return("nothing")

    @app.route('/focus')
    def focus():
        d = request.args.get('direction')
        speed = 2  #### FIXME
        if d == 'Stop':
            logging.debug("FOCUS: Stop")
            cam.stop()
        else:
            direction = d == "Near"
            logging.debug(f"FOCUS: {direction} @ {speed}")
            cam.focus(direction, speed)
        return("nothing")

    app.run(host="0.0.0.0", port="8080")
    logging.debug("Exiting")
    return(0)

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
