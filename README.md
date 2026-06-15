# avuePTZ
Application for controlling and viewing video from an Avue G50IR-WB36N PTZ (Pan/Tilt/Zoom) camera

![Avue PTZ Camera](AVUE_G50IR-WB36N.jpg)

[Avue Camera Information](docs/avue.md)

[Pelco Control Protocol Information](docs/pelco.md)

## Controller

The controller streams live video from the camera to any browser and accepts commands to control
the PTZ platform and camera functions (zoom, focus, IR illuminator, wiper, backlight compensation, etc.).

It is enclosed in a weatherproof (NEMA) box which connects to the Avue camera via its cable harness
and plugs into 110VAC power. Enclosed is a 24VAC supply for the camera and a USB 5VDC supply for
the Raspberry Pi and its peripherals.

![Camera Controller](controller.jpg)

## Hardware

The control unit is a Raspberry Pi 4B (2GB) with two USB dongles — one to digitize the analog video,
one to send Pelco-D commands to the camera over RS485.
The Pi has been modified with a U.FL connector for an external WiFi antenna.

### NTSC Video Digitizer — Fushicai USBTV007 (EasyCAP)

* USB ID: 1b71:3002
* Captures 720x480 YUYV 4:2:2, interlaced (NTSC 480i)
* Device node: typically **`/dev/video0`**, but can shift to `/dev/video1`
  - The Pi 4's bcm2835 codec and ISP kernel drivers claim `/dev/video10`–`/dev/video23`.
    Depending on which modules are loaded at boot, the USB grabber may land at `/dev/video0`
    or `/dev/video1`. Verify after every kernel or driver change.
  - Pass `-i <index>` to `avuePTZ.py` to select the correct device; update the service
    `ExecStart` line if it changes.
* Verify after boot:
  ```bash
  v4l2-ctl --list-devices          # find the usbtv entry and note its /dev/videoN path
  ```

![Video Digitizer](images/USBTV007.png)

### RS485 Serial Interface — FTDI USB-to-RS485 Dongle

* USB ID: 0403:6001
* Device node: `/dev/ttyUSB0`
* Sends Pelco-D commands to the camera (4800 baud, 8-N-1)
* Install udev rules so the device gets a stable name:
  ```bash
  sudo cp ./99-dtech-rs422_485.rules /etc/udev/rules.d/
  sudo udevadm control --reload-rules
  sudo udevadm trigger
  ```

![RS485 Converter](images/FTD_RS485.png)

## Software

### Architecture

`avuePTZ.py` is a Flask application that handles both video and PTZ control:

* **Video**: A background thread runs FFmpeg continuously, capturing from the configured
  video device (default `/dev/video0`, selected via `-i` flag),
  deinterlacing the 480i NTSC source with `yadif`, and encoding JPEG frames in software.
  The latest frame is stored in a shared memory buffer. The `/snapshot` endpoint returns
  the current frame as `image/jpeg`. The browser polls `/snapshot` in a tight loop and
  draws frames to a `<canvas>` element using `createImageBitmap`. This approach works
  in all browsers including Chrome on Android, which does not support MJPEG in `<img>` tags
  and does not reliably stream HTTP responses via `fetch()`.

* **PTZ control**: HTTP endpoints (`/move`, `/zoom`, `/focus`, `/IR`, `/wiper`, `/home`,
  `/zoomWide`, etc.) send Pelco-D commands over RS485 via `pyserial`. The browser sends
  commands on `mousedown`/`touchstart` and stops on `mouseup`/`touchend`, giving
  hold-to-move behavior with minimal latency.

* **Pelco-D protocol**: Implemented in `Pelco.py`. The `AVUE` class in `avuePTZ.py`
  extends it with camera-specific commands (IR preset 62, wiper preset 63, `GotoZeroPan`
  for home).

### Installation (Raspberry Pi OS Lite, Trixie / Debian 13)

#### 1. System packages

```bash
sudo apt install git ffmpeg python3-systemd python3-serial
```

`python3-systemd` and `python3-serial` **must** come from apt. They cannot be
pip-installed on Trixie (PEP 668 / externally-managed-environment). The `systemd`
Python package on PyPI does not include the `Notification` class present in older
versions; the apt package is used instead, with a local shim defined in `avuePTZ.py`.

#### 2. Python environment

```bash
cd ~/Code/avuePTZ
python3 -m venv --system-site-packages venv
source venv/bin/activate
pip install -r requirements.txt      # flask, parse, pyyaml
```

`--system-site-packages` lets the venv see the apt-installed `systemd` and `serial` modules.

#### 3. Udev rules

```bash
sudo cp ./99-dtech-rs422_485.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
```

#### 4. Systemd service

```bash
sudo cp etc/systemd/system/avuePTZ.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable avuePTZ
sudo systemctl start avuePTZ
sudo systemctl status avuePTZ
```

The service runs as user `jdn` and uses the venv at `/home/jdn/Code/avuePTZ/venv`.
The `-i` flag in `ExecStart` selects the video device index; verify with
`v4l2-ctl --list-devices` and update if it differs from the current setting.

`avueVideo.service` and `avueLogger.service` are **permanently deprecated** (see `DEPRECATED/`).
The Flask app owns `/dev/video1` directly via its background capture thread.

### Web Interface

Navigate to `http://avue.lan:8080` in any browser — redirects automatically to `/camera`.

Works on desktop (Brave, Firefox, Chrome) and mobile (Chrome on Android).

**Controls on `/camera`:**

| Control | Behavior |
|---|---|
| D-pad (8 directions) | Hold to move, release to stop |
| ⌂ center button | Home: `GotoZeroPan` Pelco command |
| Speed slider | Pan/tilt speed 0–63 |
| Zoom +/− | Hold to zoom in/out |
| Zoom Wide | Zooms out for 5 s (reaches full wide from any position) |
| Focus Near/Far | Hold to adjust; AF toggle disables manual buttons |
| IR | Toggle IR illuminator and ICR filter |
| Wiper | Triggers one wiper cycle; button locks for 30 s |

Additional legacy pages: `/motion` (desktop, no video), `/mobile` (mobile, no video).

### REST API

All endpoints are under `/api/`. State reads use `GET`, mode changes use `PUT` with a
JSON body, and actions use `POST` with a JSON body. All responses are JSON.

The Pelco-D protocol is write-only — there is no way to query the camera directly.
Reads return the locally-tracked state that was last written.

**State snapshot**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/state` | All tracked state as a single JSON object |

Example response:
```json
{
  "camOn": true, "autoFocus": true, "autoIris": true,
  "AGC": true, "AWB": true, "BLC": true, "IR": false, "wiper": false,
  "panSpeed": 32, "tiltSpeed": 32, "zoomSpeed": 2, "focusSpeed": 2
}
```

**Readable/writable modes** — `GET` returns `{"enabled": bool}`, `PUT` accepts `{"enabled": bool}`

| Endpoint | Controls |
|----------|----------|
| `/api/ir` | IR illuminator + ICR filter |
| `/api/autofocus` | Auto-focus on/off |
| `/api/autoiris` | Auto-iris on/off |
| `/api/agc` | Automatic gain control on/off |
| `/api/awb` | Auto white balance on/off |
| `/api/blc` | Backlight compensation on/off |

**Actions** — `POST` with JSON body, returns `{"ok": true}`

| Endpoint | Body | Description |
|----------|------|-------------|
| `/api/move` | `{"direction": "Up\|Down\|Left\|Right\|LeftUp\|LeftDown\|RightUp\|RightDown\|Stop", "speed": 0-63}` | Pan/tilt; Stop halts all motion |
| `/api/zoom` | `{"direction": "In\|Out\|Stop"}` | Zoom |
| `/api/zoomwide` | _(none)_ | Zoom full-wide over 5 s then stop |
| `/api/focus` | `{"direction": "Near\|Far\|Stop"}` | Manual focus |
| `/api/iris` | `{"direction": "Open\|Close\|Stop"}` | Manual iris |
| `/api/home` | _(none)_ | `GotoZeroPan` — return to home position |
| `/api/wiper` | _(none)_ | Run one wiper cycle |
| `/api/preset` | `{"command": "Set\|Clear\|Call", "id": 0-255}` | Pelco-D preset |

Examples:
```bash
# Read all state
curl http://avue.lan:8080/api/state

# Enable IR
curl -X PUT http://avue.lan:8080/api/ir -H 'Content-Type: application/json' -d '{"enabled": true}'

# Pan right at speed 32
curl -X POST http://avue.lan:8080/api/move -H 'Content-Type: application/json' -d '{"direction": "Right", "speed": 32}'

# Stop movement
curl -X POST http://avue.lan:8080/api/move -H 'Content-Type: application/json' -d '{"direction": "Stop"}'

# Call preset 1
curl -X POST http://avue.lan:8080/api/preset -H 'Content-Type: application/json' -d '{"command": "Call", "id": 1}'
```

### Monitoring

```bash
# CPU temperature (Trixie — vcgencmd is in PATH, not /opt/vc/bin)
vcgencmd measure_temp

# WiFi RSSI
iwlist wlan0 scan | grep dBm

# Continuous
while true; do vcgencmd measure_temp; iwlist wlan0 scan | grep dBm; sleep 30; done
```

CPU temperature and WiFi RSSI are also published via MQTT to the
[SensorNet](https://github.com/jduanen/SensorNet) project by `avueLogger.service`.

### Troubleshooting

**No video / black canvas:**
1. Confirm the video device index: `v4l2-ctl --list-devices` — find the usbtv entry
2. Check the usbtv kernel module: `lsmod | grep usbtv` — load with `sudo modprobe usbtv` if missing
3. Check Flask log for `FFmpeg:` error lines — the capture loop logs FFmpeg stderr on failure
4. Verify the USB dongle is recognized: `lsusb | grep 1b71`

**Movement commands return 500:**
* Pan/tilt speed must be in range 0–63 or exactly 255 (Pelco-D limit). Values 64–254 are invalid
  and will raise an assertion error. The speed slider is clamped to 0–63.

**`from systemd.daemon import Notification` ImportError:**
* The Debian `python3-systemd` package does not export `Notification`. A local shim class
  is defined in `avuePTZ.py` — do not add `systemd-python` from PyPI.

## TODO
* Make a tool to set the camera's baudrate
* Make a tool for CLI-based camera control
* Enable systemd watchdog integration in `avueControl.service`
* Create a defined startup state for the camera (position, zoom, focus, IR)
