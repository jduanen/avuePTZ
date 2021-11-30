#!/usr/bin/env python3
"""
Application for logging the AVUE camera platform to SensorNet MQTT
"""

import argparse
import json
import logging
import os
import signal
import sys
from threading import Timer
import time
import yaml
from yaml import Loader

from systemd.daemon import notify, Notification


DEFAULTS = {
    'logLevel': "INFO",  #"DEBUG"  #"WARNING"
    'watchdog': 15  # watchdog interval in usecs (15 secs)
}


class Watchdog():
    @staticmethod
    def notification(typ):
        if True:
            print(f"N: {typ}")
            return
        try:
            notify(Notification.STOPPING)
        except Exception as ex:
            logging.warning(f"Systemd notification ({typ}) failed: {ex}")

    def __init__(self, timeout):
        self.timeout = timeout
        self.timer = None
        if timeout:
            self.timer = Timer(self.timeout, self.handler)
            self.timer.start()
            Watchdog.notification(Notification.READY)

    def __enter__(self):
        print("ENTER")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print("EXIT")
        self.stop()
        Watchdog.notification(Notification.STOPPING)

    def stop(self):
        if self.timer:
            self.timer.cancel()
        self.timer = None

    def reset(self):
        self.stop()
        self.timer = Timer(self.timeout, self.handler)
        self.timer.start()

    def handler(self):
        print("WD")
        Watchdog.notification(Notification.WATCHDOG)
        if self.timer:
            self.reset()


def run(options):
    '''
    for s in ('TERM', 'HUP', 'INT'):
        sig = getattr(signal, 'SIG'+s)
        signal.signal(sig, shutdownHandler)
    '''
    with Watchdog(options.watchdog) as dog:
        #### TODO put work here
        pass
    logging.info("Exiting")
    return(0)


def getOpts():
    usage = f"Usage: {sys.argv[0]} [-v] [-L <logLevel>] [-l <logFile>] " + \
      "[-w <watchdog>]"
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
        "-v", "--verbose", action="count", default=0,
        help="Enable printing of debug info")
    ap.add_argument(
        "-w", "--watchdog", action="store", type=int, default=DEFAULTS['watchdog'],
        help="secs between watchdog notifications to systemd (0 means no watchdog)")
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

    opts.watchdog = 0 if opts.watchdog < 1 else opts.watchdog

    if opts.verbose:
        if opts.watchdog:
            print(f"    Watchdog Interval:  {opts.watchdog} secs")
        else:
            print("    Watchdog not enabled")
    return opts


if __name__ == '__main__':
    opts = getOpts()
    r = run(opts)
    sys.exit(r)
