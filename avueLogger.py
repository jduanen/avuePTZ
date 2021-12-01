#!/usr/bin/env python3
"""
Application for logging the AVUE camera platform to SensorNet MQTT
"""

import argparse
import json
import logging
import os
import re
import signal
import socket
import subprocess
import sys
from threading import Timer
import time
import yaml
from yaml import Loader

#import paho.mqtt.client as mqtt
from systemd.daemon import notify, Notification
import vcgencmd


DEFAULTS = {
    'logLevel': "INFO",   #"DEBUG"  #"WARNING"
    'sampleInterval': 15, # sample interval (15 secs)
    'mqttBroker': "gpuServer1"
}

MQTT_TOPIC = "/sensors/avue"
APPL_NAME = "AvuePZT"
APPL_VERSION = "1.1.0"
DEV_TYPE = "Rpi3"


vcgen = None


#### TODO put this in a common file
def macAddress(hostname):
    """Return the MAC address and interface name used to reach the given host

      Returns usable strings on error.

      Inputs:
        hostname: string name of the target host
      Returns: string name and string form of MAC address of interface used to
       reach the given host
    """
    ipAddr = socket.gethostbyname(hostname)
    match = re.search(r"^.* dev (.*?) .*$",
                      str(subprocess.check_output(["ip", "route", "get", ipAddr])))
    if not match:
        logging.warning(f"Unable to find interface for {ipAddr}")
        return "n/a", "00:00:00:00:00:00"
    intf = match.group(1)
    try:
        macAddr = subprocess.check_output(["cat", f"/sys/class/net/{intf}/address"]).strip().decode("utf-8")
    except Exception as ex:
        logging.warning("Failed to get MAC address for '{hostname}': {ex}")
        return "n/a", "00:00:00:00:00:00"
    return intf, macAddr


#### TODO put this in a common file
def wifiQuality(interface):
    """Return a quality indicator and RSSI of the given WiFi interface

      Returns usable strings on error.

      Inputs:
        interface: string name of WiFi interface for which to get signal quality

      Returns: float value from 0.0 to 1.0 indicating worst to best signal
       quality, respectively, and the RSSI value in dBm
    """
    match = re.search(r'.* Quality=([0-9]+)/([0-9]+)  Signal level=(.*) dBm .*$',
                      str(subprocess.check_output(["iwlist", interface, "scan"])))
    if not match:
        logging.warning(f"Unable to scan interface '{interface}'")
        return "-0.0", "0"
    vals = match.groups()
    if len(vals) != 3:
        logging.warning(f"Unable to get WiFi quality: {match.groups()}")
        return "-0.0", "0"
    return int(vals[0])/int(vals[1]), vals[2]


#### TODO put this in a common file
def deviceTemperature():
    """Return the temperature of the device in degrees C

      Returns: float value of device temperature in degrees C
    """
    global vcgen

    if not vcgen:
        vcgen = vcgencmd.Vcgencmd()
    return vcgen.measure_temp()


#### TODO put this in a common file
class Watchdog():
    @staticmethod
    def notification(typ):
        print(typ)
        try:
            notify(typ)
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
        return self

    def __exit__(self, exc_type, exc_value, traceback):
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
        Watchdog.notification(Notification.WATCHDOG)
        if self.timer:
            self.reset()


def run(options):
    running = True

    def shutdownHandler(signum, frame):
        logging.debug(f"Caught signal: {signum}")
        running = False

    for s in ('TERM', 'HUP', 'INT'):
        sig = getattr(signal, 'SIG'+s)
        signal.signal(sig, shutdownHandler)

    intfName, macAddr = macAddress(options.mqttBroker)
    TOPIC_BASE = f"{MQTT_TOPIC}/{macAddr}/cmd/"
    quality, rssi = wifiQuality(intfName)

    logging.info("Starting")
    #### FIXME
    print(f"{TOPIC_BASE},Startup,{DEV_TYPE},{APPL_NAME},{APPL_VERSION},temp:.1f,q:.4f,rssi:d,{rssi}")
    while running:
        temperature = deviceTemperature()
        quality, rssi = wifiQuality(intfName)
        #### FIXME
        print(f"{TOPIC_BASE}/data,{temperature},{quality:.4f},{rssi}")
        #### TODO think about decoupling sampling interval and watchdog timer
        time.sleep(options.sampleInterval)
    logging.info("Exiting")
    return(0)


def getOpts():
    usage = f"Usage: {sys.argv[0]} [-v] [-L <logLevel>] [-l <logFile>] " + \
      "[-D] [-m <mqttHost>] [-s <sampleInterval>]"
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-D", "--disableWatchdog", action="store_true", type=bool, default=False,
        help="Disable watchdog function")
    ap.add_argument(
        "-L", "--logLevel", action="store", type=str,
        default=DEFAULTS['logLevel'],
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level")
    ap.add_argument(
        "-l", "--logFile", action="store", type=str,
        help="Path to location of logfile (create it if it doesn't exist)")
    ap.add_argument(
        "-m", "--mqttBroker", action="store", type=str,
        default=DEFAULTS['mqttBroker'],
        help="Hostname for where the MQTT broker is running")
    ap.add_argument(
        "-s", "--sampleInterval", action="store", type=int, default=DEFAULTS['sampleInterval'],
        help="secs between data samples")
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

    if opts.sampleInterval <= 0:
        logging.error(f"Invalid sample interval: '{opts.sampleInterval}' secs")
        sys.exit(1)

    if opts.verbose:
        print(f"    MQTT Broker:     {opts.mqttBroker}")
        print(f"    Sample Interval: {opts.sampleInterval} secs")
        else:
        if opts.disableWatchdog:
            print("    Watchdog not enabled")
    return opts


if __name__ == '__main__':
    opts = getOpts()
    with Watchdog(opts.sampleInterval) as dog:
        r = run(opts)
    sys.exit(r)
