# Avue Camera

## Camera

* Sony FCB-EX1010 Color Block Camera (circa 2007)
* 1/4" ExView HAD CCD, 36x Wide-D zoom lens (432x digital zoom)
* 30FPS, 530H, color, interlaced, 1Vp-p analog output, NTSC
* high-sensitivity: 1.4 lux @ 1/60 sec NTSC, ICR Off
* SNR: >50 dB
* IR Cut Filter can be removed from image path
  - ICR automatic depending on ambient light
* spherical privacy zone masking with mosaic effect
  - up to 24x blocks
* VISCA communications protocol
  - description of commands in manual
* slow AE Response Function
  - slows rate at which exposure level changes
  - can be set up to 32x slower than Full Auto or Privacy mode is selected
* up to 11 lines for OSD, up to 20x characters
  - multi-lines for title
* E-FLIP function
* alarm function with adjustable detection zones
* electronic/slow shutter
* internal/external sync (V-lock)
* wide dynamic range
* minimum object distance: 320mm (wide) to 1500mm (tele)
* <5 W

## G50IR-WB36N Outdoor Video Surveillance Camera, DAY & NIGHT, Pan/Tilt/Zoom
* IR Range up to 60m
* Pan/Tilt Speed Automatically Adjusted According to Zoom
* Auto Focus/Iris
* BLC Function
* 128 Preset Positions
* Multi-protocol Communication
* Wiper Function
* High Resolution (530TVL)
* 360° Pan Range, 180° Tilt Range
* Weather-proof (IP 66)
* Die-cast Aluminum Construction
* Programmable Camera Settings
* Built-in Receiver
* OSD Function
* Operational at -40°C to 60°C
* DC 12V/ AC 24V Power Supply
* Image Sensor:  1/4" Ex-View HAD CCD, 530TVL
* Optical Lens & Zoom: 36x (1.7° - 57.8° / 3.4- 122mm); F1.6-F4.5, 12x Digital
* Min. Illumination: 1.4lux (COLOR)
* Lens control:  G50: 0.01 Lux (Night Mode); Zoom, Focus (auto/manual)
* Camera functions:  White Balance (ATW, AWB, manual)
* PTZ Characteristics
  - BLC (Backlight Compensation)
  - Wide Dynamic Range
  - Slow Shutter
  - AGC (Auto Gain Control)
  - AE (Auto Exposure)
  - Gain Limiter
  - Image Flip & Mirror
  - Day-Night ICR Filter (Auto/Manual /Scheduled)
  - Tracking zone selection
  - 360° Pan (0.4° ~ 80° per sec)endless
  - 180° Tilt (0.4° ~ 60° per sec) with Auto-Flip
  - Vario-Speed control
  - Proportional & constant PT speed
* Automation
  - Preset positions (128x)
  - Preset tours (4x)
  - Scan tours (4x)
  - Pattern tracks (4 x 100 sec)
* On-Screen Display
  - Idle protection
  - Scheduled automation
  - Start-up assignment
  - Date/Time/Zoom ratio/Temperature/Zones/Camera name
* OSD menu: Setup / Automation programming, password protection
* External I/O: RS485 / BNCvideo output / 7 sensor inputs / 2 alarm outputs
* Telemetric: Rs485 (2400 - 19200bps), optional with Coax-Control; 16 Multiple Protocol supported
* Power Consumption: DC 24V, 45W (IR Version)
* Environment
  - IP66 weather protection
  - temperature range -40° ~ 60°C
  - humidity up to 95%
* Dimension
  - G50IR/VL: 473 (W)x250 (L)x260 (H)mm, 8.55Kg

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
