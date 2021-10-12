'''
Library for Pelco-D Protocol control of a PZT camera mount
'''

import logging
from queue import Queue
import struct
import threading

from parse import parse
import serial


DEF_PORT = "/dev/ttyUSB0"

DEF_BAUDRATE = 4800  #### TODO try 9600

DEF_CAMERA_ADDRESS = 1

DEF_SERIAL_TIMEOUT = 1.0    # serial port timeout (secs)

EXTENDED_COMMAND_MAP = {
    'SetPreset': (0x00, 0x03, 0x00, (0, 255)),  # N.B., Spec limits to (1, 0x20)
    'ClearPreset': (0x00, 0x05, 0x00, (0, 255)),  # N.B., Spec limits to (1, 0x20)
    'GotoPreset': (0x00, 0x07, 0x00, (0, 255)),  # N.B., Spec limits to (1, 0x20)
    'Flip': (0x00, 0x07, 0x00, 21),
    'GotoZeroPan': (0x00, 0x07, 0x00, 22),
    'SetAux': (0x00, 0x09, 0x00, (1, 8)),
    'ClearAux': (0x00, 0x0B, 0x00, (1, 8)),
    'RemoteReset': (0x00, 0x0F, 0x00, 0x00),
    'SetZoneStart': (0x00, 0x11, 0x00, (1, 8)),
    'SetZoneEnd': (0x00, 0x13, 0x00, (1, 8)),
    'WriteChar': (0x00, 0x15, (0, 28), (0, 127)),
    'ClearScreen': (0x00, 0x17, 0x00, 0x00),
    'AlarmACK': (0x00, 0x19, 0x00, (1, 8)),
    'ZoneScanOn': (0x00, 0x1B, 0x00, 0x00),
    'ZoneScanOff': (0x00, 0x1D, 0x00, 0x00),
    'PatternStart': (0x00, 0x1F, 0x00, 0x00),
    'PatternStop': (0x00, 0x21, 0x00, 0x00),
    'RunPattern': (0x00, 0x23, 0x00, 0x00),
    'ZoomSpeed': (0x00, 0x25, 0x00, (0, 3)),
    'FocusSpeed': (0x00, 0x27, 0x00, (0, 3)),
    'ResetCamera': (0x00, 0x29, 0x00, 0x00),
    'AutoFocus': (0x00, 0x2B, 0x00, (0, 2)),
    'AutoIris': (0x00, 0x2D, 0x00, (0, 2)),
    'AGC': (0x00, 0x2F, 0x00, (0, 2)),
    'BacklightComp': (0x00, 0x31, 0x00, (0, 2)),
    'AWB': (0x00, 0x33, 0x00, (0, 2)),
    'PhaseDelayMode': (0x00, 0x35, 0x00, 0x00),
    'ShutterSpeed': (0x00, 0x37, (0,255), (0,255)),
    'LineLockDelay_0': (0x00, 0x39, (0,255), (0,255)),
    'LineLockDelay_1': (0x01, 0x39, (0,255), (0,255)),
    'WhiteBalanceRB_0': (0x00, 0x3B, (0,255), (0,255)),
    'WhiteBalanceRB_1': (0x01, 0x3B, (0,255), (0,255)),
    'WhiteBalanceMG_0': (0x00, 0x3D, (0,255), (0,255)),
    'WhiteBalanceMG_1': (0x01, 0x3D, (0,255), (0,255)),
    'AdjustGain_0': (0x00, 0x3F, (0,255), (0,255)),
    'AdjustGain_1': (0x01, 0x3F, (0,255), (0,255)),
    'AutoIrisLevel_0': (0x00, 0x41, (0,255), (0,255)),
    'AutoIrisLevel_1': (0x01, 0x41, (0,255), (0,255)),
    'AutoIrisPeak_0': (0x00, 0x43, (0,255), (0,255)),
    'AutoIrisPeak_1': (0x01, 0x43, (0,255), (0,255))
}


class Speed():
    STOP = 0x00
    LOW = 0x10  #### FIXME
    NORMAL = 0x20  #### FIXME
    HIGH = 0x3F
    TURBO = 0xFF


class PresetCommands():
    SET = 'SetPreset'
    CLEAR = 'ClearPreset'
    CALL = 'GotoPreset'


class Pelco():
    """????
    """
    '''
      scanMode, cameraEnable (mapping): sense, scanCam (case)
        X, X (0,0: 0): x, 00 (nop)
        X, 0 (0,1: 1): 0, 01 (-/off)
        X, 1 (0,2: 2): 1, 01 (-/on)
        0, X (1,0: 3): 0, 10 (manual/-)
        0, 0 (1,1: 4): 0, 11 (manual/off)
        0, 1 (1,2: 5): x, xx (illegal)
        1, X (2,0: 6): 1, 10 (auto/-)
        1, 0 (2,1: 7): x, xx (illegal)
        1, 1 (2,2: 8): 1, 11 (auto/on)
    '''
    TRUTH_TABLE = [(0, 0), (0, 1), (1, 1), (0, 2), (0, 3), None, (1, 2), None, (1, 3)]

    def __init__(self, camAddress=DEF_CAMERA_ADDRESS, port=DEF_PORT, baudrate=DEF_BAUDRATE, timeout=DEF_SERIAL_TIMEOUT):
        self.address = camAddress
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

        self.panSpeed = 0
        self.tiltSpeed = 0
        self.zoomSpeed = 0
        self.focusSpeed = 0

        self.serial = None
        try:
            # N.B. Defaults to 8-N-1, no (HW or SW) flow control
            self.serial = serial.Serial(port=port, baudrate=baudrate, timeout=self.timeout)
        except Exception as ex:
            logging.error(f"Failed to open serial port '{port}': {ex}")
        assert self.serial and self.serial.isOpen(), f"Serial port '{port}' not open"
        self.open = True
        logging.debug(f"Opened {port} at {baudrate}")

        self.cameraOn()
        self.motion(Speed.STOP, Speed.STOP)

    def _makeCommands1_2(self, scanMode=None, cameraEnable=None, iris=None, focus=None, zoom=None, pan=None, tilt=None):
        """Create commands 1 and 2 for the standard command format message

          N.B. Because of bad design choices, scanMode and cameraEnable are not
                independent. It is not possible to enable auto-scan and turn
                camera off, nor is it possible to enable manual scan and turn
                the camera on -- attempts to do these operations will result in
                an exception being thrown

          Inputs:
            scanMode: True means enable auto scan mode, False means enable manual
                       scan mode, and None means leave it as it is
            cameraEnable: True means turn camera on, False means turn camera off,
                           and None means leave it as is
            iris: bool True means close iris, False means open iris, None means leave it as is
            focus: bool True means focus near, False means focus far, None means leave it as is
            zoom: bool True means zoom in (tele), False means zoom out (wide), None means leave it as is
            pan: bool if True pan right, if False pan left, if None don't pan
            tilt: bool if True tilt up, if False tilt down, if None don't tilt

          Returns: tuple of byte-sized integers containing command1 and command2
        """
        indx = 0 if scanMode is None else 4 if scanMode else 2
        indx += 0 if cameraEnable is None else 2 if cameraEnable else 1
        sense, scanCam = Pelco.TRUTH_TABLE[indx]
        assert sense is not None and scanCam is not None, f"Invalid scanMode/cameraEnable combination"
        cmd1 = ((sense << 7) & 0x80) | \
               ((scanCam << 3) & 0x18) | \
               (0 if iris is None else 0x08 if iris else 0x04) | \
               (0 if focus is None else 0x01 if focus else 0)
        cmd2 = (0 if focus is None else 0 if focus else 0x80) | \
               (0 if zoom is None else 0x20 if zoom else 0x40) | \
               (0 if tilt is None else 0x08 if tilt else 0x10) | \
               (0 if pan is None else 0x02 if pan else 0x04)
        return (cmd1, cmd2)

    def _sendStandardCommand(self, cmds1_2, panSpeed=None, tiltSpeed=None):
        """Compose an extended command and send it to the camera

          Command format: sync (0xFF), address, cmd1, cmd2, data1, data2, checksum

          Inputs:
            cmds1_2: a tuple of bytes containing command1 and command2 for standard commands
            panSpeed: optional Speed value that selects pan speed, or leaves as is if None
            tiltSpeed: optional Speed value that selects tilt speed, or leaves as is if None

          Returns: list of bools representing state of alarms where True means
                    the alarm is active -- result[0] == Alarm1, result[7] == Alarm8
        """
        self.serial.reset_input_buffer()
        if panSpeed == None:
            panSpeed = self.panSpeed
        assert panSpeed == Speed.TURBO or (panSpeed >= Speed.STOP and panSpeed <= Speed.HIGH), f"Invalid Pan Speed: {panSpeed}"
        self.panSpeed = panSpeed
        if tiltSpeed == None:
            tiltSpeed = self.tiltSpeed
        assert tiltSpeed == Speed.TURBO or (tiltSpeed >= Speed.STOP and tiltSpeed <= Speed.HIGH), f"Invalid Tilt Speed: {tiltSpeed}"
        self.tiltSpeed = tiltSpeed
        cksm = (self.address + cmds1_2[0] + cmds1_2[1] + panSpeed + tiltSpeed) % 256
        cmd = struct.pack("BBBBBBB", 0xFF, self.address, *cmds1_2, panSpeed, tiltSpeed, cksm)
        self.serial.write(cmd)
        logging.debug(f"Send command: {[hex(x) for x in cmd]}")

        vals = self.serial.read(4)
        logging.debug(f"Response: {[hex(x) for x in vals]}")
        if not vals:  #### TMP TMP TMP
            return None
        sync, addr, alarms, checksum = struct.unpack("BBBB", vals)
        assert (sync == 0xFF) and (checksum == (sum(vals[1:3]) % 256)), f"Invalid packet: {[hex(x) for x in vals]}"
        return [bool(alarms & (1 << i)) for i in range(0, 8)]

    def cameraOn(self):
        """Issue command to turn camera on

          Returns: list of bool alarm indications
        """
        return self._sendStandardCommand(self._makeCommands1_2(cameraEnable=True))

    def cameraOff(self):
        """Issue command to turn camera off

          Returns: list of bool alarm indications
        """
        return self._sendStandardCommand(self._makeCommands1_2(cameraEnable=False))

    def motion(self, pan, tilt, panSpeed=None, tiltSpeed=None):
        """Move camera in indicated direction(s) with the given speed(s)

          Inputs:
            pan: bool if True pan right, if False pan left, if None don't pan
            tilt: bool if True tilt up, if False tilt down, if None don't tilt

          Returns: list of bool alarm indications
        """
        return self._sendStandardCommand(self._makeCommands1_2(scanMode=False, pan=pan, tilt=tilt), panSpeed, tiltSpeed)

    def setZoomSpeed(self, speed):
        """Set zoom speed to given value (between 0 and 3)

          Inputs:
            speed: int between 0 and 3 indicating increasing speed
        """
        assert speed >= 0 and speed <= 3, f"Invalid zoom speed: {speed}"
        self.extendedCommand('ZoomSpeed', arg2=speed)

    def zoom(self, zoomDir, speed=None):
        """Zoom in (tele)/out (wide) at (optional) speed

          Inputs:
            zoom: bool where True means to zoom in (tele) and False is zoom out (wide)
            speed: optional int between 0 and 3 indicating increasing speed, None means leave as is

          Returns: list of bool alarm indications
        """
        if speed:
            self.setZoomSpeed(speed)
            self.zoomSpeed = speed
        return self._sendStandardCommand(self._makeCommands1_2(zoom=zoomDir))

    def setFocusSpeed(self, speed):
        """Set focus speed to given value (between 0 and 3)

          Inputs:
            speed: int between 0 and 3 indicating increasing speed
        """
        assert speed >= 0 and speed <= 3, f"Invalid focus speed: {speed}"
        self.extendedCommand('FocusSpeed', arg2=speed)

    def focus(self, focusDir, speed=None):
        """Switch to manual focus and focus near/far at (optional) speed

          Inputs:
            focusDir: bool where True means to focus near and False is focus far
            speed: optional int between 0 and 3 indicating increasing speed

          Returns: list of bool alarm indications
        """
        if speed:
            self.setFocusSpeed(speed)
            self.focusSpeed = speed
        return self._sendStandardCommand(self._makeCommands1_2(focus=focusDir))

    def iris(self, irisDir):
        """Switch to manual iris and open/close iris

          Inputs:
            focusDir: bool where True means to focus near and False is focus far
            speed: optional int between 0 and 3 indicating increasing speed

          Returns: list of bool alarm indications
        """
        return self._sendStandardCommand(self._makeCommands1_2(iris=irisDir))

    def preset(self, presetID, presetCmd):
        """Issue a preset command that either sets, clears, or calls a given
            preset.

          Inputs:
            presetID: 8b int identifying a preset
            presetCmd: PresetCommands value indicating SET, CLEAR, or CALL
                       command type
        """
        assert isinstance(presetCmd, PresetCommands), "Invalid Present Command"
        assert presetID >= 0 and presetID <= 0xFF, f"Invalid Preset ID: {presetID}"
        self.extendedCommand(presetCmd, arg2=presetID)

    def query(self):
        """Issue Query command and return results

          Returns: device address and part number
        """
        self.serial.reset_input_buffer()
        cksm = (self.address + 0x00 + 0x45) % 256
        cmd = struct.pack("BBBBBBB", 0xFF, self.address, 0x00, 0x45, 0x00, 0x00, cksm)
        self.serial.write(cmd)

        vals = self.serial.read(5)
        sync, address, partNumber, checksum = struct.unpack("BBHB", vals)
        assert (sync == 0xFF) and (checksum == (sum(vals[1:4]) % 256)), f"Invalid packet: {[hex(x) for x in vals]}"
        return address, partNumber

    def _sendExtendedCommand(self, word3, word4, word5, word6):
        """Compose an extended command and send it to the camera

          Command format: sync (0xFF), address, cmd1, cmd2, data1, data2, checksum

          Inputs:
            word3: ?
            word4: ?
            word5: ?
            word6: ?
        """
        self.serial.reset_input_buffer()
        cksm = (self.address + word3 + word4 + word5 + word6) % 256
        cmd = struct.pack("BBBBBBB", 0xFF, self.address, word3, word4, word5, word6, cksm)
        self.serial.write(cmd)
        logging.debug(f"Send extended command: {[hex(x) for x in cmd]}")

        vals = self.serial.read(4)
        logging.debug(f"Response: {[hex(x) for x in vals]}")
        if not vals:  #### TMP TMP TMP
            return None
        sync, addr, alarms, checksum = struct.unpack("BBBB", vals)
        assert (sync == 0xFF) and (checksum == (sum(vals[1:3]) % 256)), f"Invalid packet: {[hex(x) for x in vals]}"
        return [bool(alarms & (1 << i)) for i in range(0, 8)]

    @staticmethod
    def validateExtCmd(spec, arg):
        """????
        """
        if isinstance(spec, int):
            if arg is None or arg == spec:
                return spec
            else:
                raise Exception(f"Invalid Extended Command arg: '{arg}' != {spec}")
        elif isinstance(spec, tuple):
            print("XXXX", type(spec[0]), type(spec[1]), type(arg))
            if arg is None:
                raise Exception(f"Must provide arg for Extended Command -- spec: {spec}")
            elif arg < spec[0] or arg > spec[1]:
                raise Exception(f"arg for Extended Command out of range -- {arg} does not lie in range {spec}")
            else:
                return arg
        else:
            raise Exception(f"Invalid Extended Command spec: {spec} -- must be int or tuple of ints")

    def extendedCommand(self, command, arg1=None, arg2=None):
        """Issue an extended command (with optional args)

          Inputs:
            command: string name of extended command
            arg1: optional first int value to be given with extended command
            arg2: optional second int value to be given with extended command

          Returns: list of bool alarm indications
        """
        assert command in EXTENDED_COMMAND_MAP, f"Invalid Extended Command: {command}"
        specs = EXTENDED_COMMAND_MAP[command]
        return self._sendExtendedCommand(specs[0],
                                         specs[1],
                                         Pelco.validateExtCmd(specs[2], arg1),
                                         Pelco.validateExtCmd(specs[3], arg2))


#
# TEST
#
if __name__ == '__main__':
    import time

    logging.basicConfig(level="DEBUG",
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    cam = Pelco()

    # Extended Command with no args
    cam.extendedCommand('GotoZeroPan')

    # Extended Command with one arg
    cam.extendedCommand('ZoomSpeed', arg2=2)
    time.sleep(3)
    cam.extendedCommand('ResetCamera')  # go back to default setting

    # Extended Command with two args
    xPos = 14
    char = ord('A')
    cam.extendedCommand('WriteChar', xPos, char)
    time.sleep(3)
    cam.extendedCommand('ClearScreen')

    # motion at three speeds
    print("pan and tilt: LOW")
    cam.motion(True, True, Speed.LOW, Speed.LOW)
    time.sleep(3)
    cam.motion(True, True, Speed.STOP, Speed.STOP)

    print("pan and tilt: NORMAL")
    cam.motion(False, False, Speed.NORMAL, Speed.NORMAL)
    time.sleep(2)
    cam.motion(False, False, Speed.STOP, Speed.STOP)

    print("pan and tilt: TURBO")
    cam.motion(True, True, Speed.TURBO, Speed.TURBO)
    time.sleep(1)
    cam.motion(True, True, Speed.STOP, Speed.STOP)

    # zoom at three speeds
    #### TODO

    # preset 62: Call to turn on and Save to turn off the IR light
    #### TODO

    # preset 63: wiper on/off
    #### TODO

    # preset 95: enter main OSD menu (or 9 twice within three secs)
    #### TODO

    cam.motion(True, True, Speed.STOP, Speed.STOP)
