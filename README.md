# avuePTZ
Application for controlling and viewing video from an Avue G50IR-WB36N PTZ (Pan/Tilt/Zoom) camera

![Avue PTZ Camera](AVUE_G50IR-WB36N.jpg)

[Avue Camera Information](docs/avue.md)

[Pelco Control Protocol Information](docs/pelco.md)

## Controller

The controller streams MJPEG video from the camera to any browser and accepts commands to control
the PTZ platform and camera functions (zoom, focus, IR illuminator, wiper, backlight compensation, etc.).

It is enclosed in a weatherproof (NEMA) box which connects to the Avue camera via its cable harness
and plugs into 110VAC power. Enclosed is a 24VAC supply for the camera and a USB 5VDC supply for
the Raspberry Pi and its peripherals.

![Camera Controller](controller.jpg)

### Hardware

The control unit is a Raspberry Pi 4B (2GB) with two USB dongles — one to digitize the analog video,
one to send Pelco-D commands to the camera over RS485.
The Pi has been modified with a U.FL connector for an external WiFi antenna.

#### NTSC Video Digitizer USB Dongle
* Fushicai USBTV007 Video Grabber (EasyCAP)
  - ID 1b71:3002
  - Captures 720x480 YUYV 4:2:2, interlaced (NTSC 480i), at `/dev/video1`

![Video Digitizer](images/USBTV007.png)

#### Future Technology Devices USB to RS485 Dongle
* idVendor=0403, idProduct=6001
* FTDI USB Serial Device converter at `/dev/ttyUSB0`
* Install udev rules and reload:
  ```
  sudo cp ./99-dtech-rs422_485.rules /etc/udev/rules.d/
  sudo udevadm control --reload-rules
  sudo udevadm trigger
  ```
* Verify video device:
  ```
  v4l2-ctl -d /dev/video1 --list-formats-ext
  ```

![RS485 Converter](images/FTD_RS485.png)

### Software

The Flask app (`avuePTZ.py`) manages both video streaming and PTZ control. FFmpeg captures from
`/dev/video0`, deinterlaces the 480i NTSC source (`yadif`), and encodes JPEG frames which Flask
serves as a `multipart/x-mixed-replace` MJPEG stream. The Pi 4 handles this in software at ~25 fps
without hardware acceleration. A good WiFi signal is required for smooth video.

#### System Packages (Raspberry Pi OS Lite, Trixie)

```bash
sudo apt install git ffmpeg python3-systemd python3-serial
```

`python3-systemd` and `python3-serial` must come from apt — they cannot be pip-installed on Trixie.
GStreamer and VLC are no longer required.

#### Python Environment

```bash
cd /home/pi/avuePTZ
python3 -m venv --system-site-packages venv
source venv/bin/activate
pip install -r requirements.txt
```

`--system-site-packages` allows the venv to use the apt-installed `systemd` and `serial` modules.

#### Web Interface

Navigate to `http://avue:8080/camera` in any browser (desktop or mobile). The page shows the live
video stream with integrated PTZ controls — no VLC or plugins required.

Controls available on the camera page:
* D-pad for pan/tilt (8 directions, hold to move)
* Speed slider
* Zoom in/out (hold)
* Focus near/far with autofocus toggle
* IR illuminator on/off
* Wiper (runs one cycle, button locks for 30 s)

Additional pages:
* `/motion` — original desktop control UI (no video)
* `/mobile` — original mobile control UI (no video)

#### Systemd Services

Two services run on startup:

```bash
# Install
sudo cp avueControl.service avueLogger.service /lib/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable avueControl avueLogger
sudo systemctl start avueControl avueLogger
sudo systemctl status avueControl avueLogger
```

| Service | Description |
|---|---|
| `avueControl` | Flask PTZ controller + MJPEG video stream (port 8080) |
| `avueLogger` | MQTT telemetry (temperature, WiFi RSSI) to SensorNet |

`avueVideo.service` is **permanently disabled** — the Flask app manages `/dev/video0` directly.

#### Monitoring

```bash
# CPU temperature
vcgencmd measure_temp

# WiFi signal
iwlist wlan0 scan | grep dBm

# Continuous monitor
while true; do vcgencmd measure_temp; iwlist wlan0 scan | grep dBm; sleep 30; done
```

System metrics (temperature, WiFi RSSI) are also published via MQTT to the
[SensorNet](https://github.com/jduanen/SensorNet) project by `avueLogger.service`.

## TODO
* Make a tool to set the camera's baudrate
* Make a tool for CLI-based camera control
* Enable systemd watchdog integration in avueControl.service
* Create a defined startup state for the camera (position, zoom, focus, IR)
