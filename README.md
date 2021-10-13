# avuePZT
Application for controlling and viewing video from AVUE G50IR-WB36N PZT camera

## Connectors
  - Power
    * Red:    24VAC
    * Yellow: NC
    * Black:  24VAC
  - Video
    * composite (BNC-M)
  - Comm
    * Yellow: RS485-/A
    * Green:  RS485+/B
  - I/O 1
    * Black:  COM
    * Brown:  No Connect
    * White:  NO1 (output)
    * Blue:   NC1 (output)
    * Red:    ALM1 (input)
    * Pink:   ALM2 (input)
    * Yellow: ALM3 (input)
    * Green:  ALM4 (input)
  - I/O 2
    * Aqua:   NC2 (output)
    * Brown:  NO2 (output)
    * Gray:   ALM7 (input)
    * Purple: ALM6 (input)
    * Orange: ALM5 (input)

## Presets
* 62: Call to turn on and Save to turn off the IR light
* 63: wiper on/off
* 95: enter main OSD menu (or 9 twice within three secs)

## Default settings:
* 4800, N, 8, 1
* Protocol: Pelco
* Dome Address: 1

## DTech RS422/RS485 USB Dongle
* idVendor=0403, idProduct=6001, bcdDevice= 6.00
* FTDI USB Serial Device converter
* /dev/ttyUSB0
* install udev rules for USB dongle and reload udevd
  - sudo cp ./99-dtech-rs422_485.rules /etc/udev/rules.d/
  - sudo udevadm control --reload-rules
  - sudo udevadm trigger

## Pelco-D protocol
* seven byte message:
  - Sync: 0xFF
  - Address: 0x??
  - Command1:
    * [7]: Sense bit
    * [6-5]: 0
    * [4]: Auto/manual scan
    * [3]: Camera on/off
    * [2]: Iris close
    * [1]: Iris open
    * [0]: Focus near
  - Command2:
    * [7]: Focus far
    * [6]: Zoom wide
    * [5]: Zoom tele
    * [4]: Down
    * [3]: Up
    * [2]: Left
    * [1]: Right
    * [0]: 0
  - Data1:
    * Pan Speed:
      - 0x00: Stop
      - 0x01-0x3F: High speed
      - 0xFF: Turbo speed
  - Data2:
    * Tilt Speed:
      - 0x00 (stop) - 0x3F (max speed)
  - Checksum: 8b (modulo 256) sum of bytes 2-6
* Extended Commands
  - response is four bytes long:
    * Sync: 0xFF
    * Address: 0x??
    * Alarm Info:
      - [7]: Alarm 8
      - [6]: Alarm 7
      - [5]: Alarm 6
      - [4]: Alarm 5
      - [3]: Alarm 4
      - [2]: Alarm 3
      - [1]: Alarm 2
      - [0]: Alarm 1
    * Checksum: 8b (modulo 256) sum of bytes 2-6
  - Set Preset:       0x00, 0x03, 0x00, 1-20
  - Clear Preset:     0x00, 0x05, 0x00, 1-20
  - Goto Preset:      0x00, 0x07, 0x00, 1-20
  - Flip:             0x00, 0x07, 0x00, 21
  - Goto Zero Pan:    0x00, 0x07, 0x00, 22
  - Set Aux:         0x00, 0x09, 0x00, 1-8
  - Clear Aux:        0x00, 0x0B, 0x00, 1-8
  - Remote Reset:     0x00, 0x0F, 0x00, 0x00
  - Set Zone Start:   0x00, 0x11, 0x00, 1-8
  - Set Zone End:     0x00, 0x13, 0x00, 1-8
  - Write Char:       0x00, 0x15, 0-28 (X pos.), 0x?? (ASCII val.)
  - Clear Screen:     0x00, 0x17, 0x00, 0x00
  - Alarm ACK:        0x00, 0x19, 0x00, 0x?? (alarm #)
  - Zone Scan On:     0x00, 0x1B, 0x00, 0x00
  - Zone Scan Off:    0x00, 0x1D, 0x00, 0x00
  - Pattern Start:    0x00, 0x1F, 0x00, 0x00
  - Pattern Stop:     0x00, 0x21, 0x00, 0x00
  - Run Pattern:      0x00, 0x23, 0x00, 0x00
  - Zoom Speed:       0x00, 0x25, 0x00, 0-3
  - Focus Speed:      0x00, 0x27, 0x00, 0-3
  - Reset Camera:     0x00, 0x29, 0x00, 0x00
  - Auto-Focus:       0x00, 0x2B, 0x00, 0-2 (auto/on/off)
  - Auto-Iris:        0x00, 0x2D, 0x00, 0-2 (auto/on/off)
  - AGC:              0x00, 0x2F, 0x00, 0-2 (auto/on/off)
  - Backlight Comp:   0x00, 0x31, 0x00, 1-2 (on/off)
  - AWB:              0x00, 0x33, 0x00, 1-2 (on/off)
  - Phase Delay Mode: 0x00, 0x35, 0x00, 0x00
  - Shutter Speed:    0x00, 0x37, 0x??, 0x??
  - Line Lock Delay:  0x00-0x01, 0x39, 0x??, 0x??
  - White Balance RB: 0x00-0x01, 0x3B, 0x??, 0x??
  - White Balance MG: 0x00-0x01, 0x3D, 0x??, 0x??
  - Adjust Gain:      0x00-0x01, 0x3F, 0x??, 0x??
  - Auto-Iris Level:  0x00-0x01, 0x41, 0x??, 0x??
  - Auto-Iris Peak:   0x00-0x01, 0x43, 0x??, 0x??
  - Query:            0x00, 0x45, 0x??, 0x?? (point-to-point mode only)
    * Response to Query Command:
      - Sync: 0xFF
      - Address: 0x??
      - Part Number (15 bytes)
      - Checksum 0x??

## Video
  * Local viewing with mplayer:
    - mplayer tv:// -tv device=/dev/video4:input=0:norm=NTSC -vo x11
  * Remote serving with ffmpeg:
    - ????

===================================================================================

## Notes
* 01-80 Preset: auto-tour, each with 24 presets
* can store up to 128x presets
* 4x pattern tours, 4x scan
* On-Screen Indicators: clock, direction, temperature
* 24x masking zones
* Alarms: 7x inputs, 2x outputs
* azimuth: 360deg, elevation: +90deg to -90deg (180deg with auto-flip)
* pan 0.4deg/sec for no image vibration
* auto-focus, auto-brightness, auto-iris, AWB, auto backlight compensation, IR cut filter
* on-screen warning if temperature exceeds limit
* startup will delay and turn on heater until at min temperature
* resettable time running count
* IR LED for 60meter range
  - on/off manual control through keyboard
  - if auto-control enabled, image color will be switched to B&W when in low brightness
* wiper function can be set on/off by 63 Preset or via OSD menu
  - seem like it runs for a fixed time and then shuts off
* two 8b switches in the base
  - SW1: ?
  - SW2: baud rate and protocol
* supported protocols: (Factory), Pelco-D, Pelco-P, Ernitec, VCL, Molynx, Vicon, Santachi, Panasonic, Samsung, Diamond, Kalatel, Lilin, Philips, VIDO B02, AD, etc.
  - Pelco-P is deprecated, Pelco-D is RS-422 @ 2400, 4800, or 9600 baud (others are HW-dependent)
* movement rates limited proportional to zoom
* auto-flip when pointing straight down
* park time and park action can be done automatically some time after last motion input
* power-up action selectable -- can be preset, tour, pattern, scan, etc.
* Tour: list of up to 24 presets
* Scan: move between defined left/right limits at a given speed
* Pattern: can record tracks up to 180s long and replay them
* Alarms:
  - on alarm input, can execute selected Preset action
* can do privacy zone masking -- add black mask to video area
* OSD Menu
  - [OPEN]: enter into next menu or save after setting a value
  - [CLOSE]: exit without saving setting
  - Joystick Up: choose the item above
  - Joystick Down: choose the item below
  - Joystick Left: same as [CLOSE]
  - Joystick Right: same as [OPEN]
* on-board Fan
  - can be turned on automatically when temperature reaches a defined point
  - the default is 40C
* can set password to lock the system
  - default is 000000
  - super-password is 892226
* selectable camera ID (aka Dome Address) -- 001-255
* can have many types of cameras: e.g., Sony, LG, CNB, Hitachi
  - wide-dynamic range (WDR) option, backlight compensation, Electronic Image Stabilization (EIS)
* possible to link IR LEDs with AUX1
* save current AzEl position in a preset number, call that number to return to that position
