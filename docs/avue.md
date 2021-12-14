# Avue Camera

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
