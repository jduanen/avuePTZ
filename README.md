# avuePTZ
Application for controlling and viewing video from an Avue G50IR-WB36N PTZ (Pan/Tilt/Zoom) camera

![Avue PTZ Camera](AVUE_G50IR-WB36N.jpg)

[Avue Camera Information](docs/avue.md)

[Pelco Control Protocol Information](docs/pelco.md)

## Controller

The controller is responsible for streaming video from the camera to a remote display, and receiving commands to direct the PTZ (pan/tilt/zoom) platform as well as the other camera functions (e.g., zoom in/out, focus near/far/auto, backlight compensation, contrast, IR-mode, wiper, etc.).

It is enclosed in a weatherproof (NEMA) box which connects to the Avue camera via its cable harnass and plugs into the 110VAC power.  Enclosed is the (24 VAC) power supply for the Avue camera and a (USB +5 VDC) power supply for the Raspberry Pi and its peripherals.

![Camera Controller](controller.jpg)

### Hardware

The control unit consists of a (2GB) Raspberry Pi 4B with two USB dongles -- one to digitize the video, and another to send (Pelco) commands to the camera via RS485.
I modified the Raspberry Pi to add a U.FL connector so that I can use an external antenna.

#### NTSC Video Digitizer USB Dongle
* Fushicai USBTV007 Video Grabber (EasyCAP)
  - ID 1b71:3002

![Video Digitizer](images/USBTV007.png)

#### Future Technology Devices USB to RS485 Dongle
* idVendor=0403, idProduct=6001, bcdDevice= 6.00
* FTDI USB Serial Device converter
* /dev/ttyUSB0
* install udev rules for USB dongle and reload udevd
  - sudo cp ./99-dtech-rs422_485.rules /etc/udev/rules.d/
  - sudo udevadm control --reload-rules
  - sudo udevadm trigger
* check dongle
   - 'v4l2-ctl -d /dev/video0 --list-formats-ext'
      * YUYV 4:2:2

![RS485 Converter](images/FTD_RS485.png)

### Software

The Raspi uses it's internal H264 encoder to compress the video from the digitizer and streams it over the WiFi connection. A good WiFi signal (better than ??dBm) is required to ensure good quality video.

Packages to be installed after a fresh install of Raspi OS Lite (Trixie) on the uSD card include:
* git
  - 'sudo apt install git'
* ffmepg
  - 'sudo apt install ffmpeg'
* gstreamer (including v4l2src, v4l2h264enc, rtph264pay, and udpsink)
  - 'sudo apt install -y gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    libgstreamer-plugins-bad1.0-dev'
  - check install
    * 'gst-inspect-1.0 v4l2h264enc'
    * 'gst-inspect-1.0 udpsink'
  - test basic video input
    * 'gst-launch-1.0 v4l2src device=/dev/video0 num-buffers=100 ! videoconvert ! autovideosink'
  - check HW encoding 
    * 'gst-inspect-1.0 | grep h264enc'
      - should report v4l2h264enc (HW encode) and x264enc (SW encode)
  - install streaming support
    * 'sudo apt install libx264-dev libjpeg-dev gstreamer1.0-pulseaudio'
  - test video pipeline
    * 'gst-launch-1.0 v4l2src device=/dev/video0 ! \
      video/x-raw,width=720,height=480,framerate=30/1 ! \
      v4l2h264enc bitrate=2000000 ! \
      h264parse ! \
      udpsink host=<RECEIVER_IPA> port=5000 sync=false'
    --> FIXME doesn't work

Code from this repo is installed as well as the tools from my [linuxTools](https://github.com/jduanen/linuxTools) project for measuring the CPU temperature and WiFi signal quality (i.e., ? and rssi.sh respectively). These metrics are transmitted as MQTT messages by the mqttd service [?], and are continuously monitored by my [SensorNet](https://github.com/jduanen/SensorNet) project.

#### Web-Server
* Flask-based python app
* Using the ???? web server

#### Streaming Video

* Video Capture USB Dongle
  - get all info: 'v4l2-ctl --all'
  - list devices: 'v4l2-ctl --list-devices'
  - test capture: 'v4l2-ctl -d /dev/video0 --set-fmt-video=width=720,height=480,pixelformat=MJPG
ffplay /dev/video0'

* GStreamer
  - server
    * 'gst-launch-1.0 v4l2src device=/dev/video0 ! \
      video/x-raw,width=720,height=480,framerate=30/1 ! \
      v4l2h264enc extra-controls="controls,video_bitrate=2000000" ! \
      h264parse ! rtph264pay config-interval=1 pt=96 ! \
      udpsink host=$RECEIVER_IPA port=5000 sync=false'
  - client
    * 'gst-launch-1.0 udpsrc port=5000 ! \
      application/x-rtp,payload=96,encoding-name=H264 ! \
      rtpH264depay ! h264parse ! avdec_h264 ! \
      autovideosink sync=false'

* FFMPG & VLC
  - server
    * ffmpeg -fflags +genpts+igndts -i /dev/video0 -c:v h264_omx -an -b:v 12M -f mpegts - | cvlc -I dummy - --sout='#std{access=http,mux=ts,dst=:8554}'
  - client
    * vlc http://avue:8554

===================================================================================
**TODO**

* figure out lowest latency method of transmitting the video

sudo apt install x264
cvlc -vvv v4l2:///dev/video0 --sout '#transcode{vcodec=h264,vb=800,acodec=none}:rtp{sdp=rtsp://:8554/}'

cvlc -vvv v4l2:///dev/video0 --sout '#transcode{vcodec=mp2v,vb=800,acodec=none}:rtp{sdp=rtsp://:8554/}'

cvlc -vvv v4l2:///dev/video0:chroma=mp2v --v4l2-width 1280 --v4l2-height 720 --sout '#transcode{vcodec=mp2v,acodec=mpga,fps=30}:rtp{mux=ts,sdp=rtsp://:8888/live.sdp}'

* using HW encode:
  - ffmpeg -i /dev/video0 -c:v h264_v4l2m2m -b:v 8M -f mpegts udp://192.168.166.216:8999
  - options
    * -framerate 25 -fflags +genpts -re
    * -vcodec libx264 -preset veryfast -pix_fmt yuv420p -strict -2 -y -f mpegts -r 25 udp://239.0.0.1:1234?pkt_size=1316

* client side:
  - vlc -vvv --network-caching 200 rtsp://192.168.166.216:8554/
  - vlc -vvv udp://192.168.166.216:8999

* enable port 5000 on gpuServer1
  - sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
  - sudo apt-get install iptables-persistent
  - sudo ufw allow 5000/tcp

* test port access
  - python3 -m http.server 8000

* Local viewing with mplayer:
  - mplayer tv:// -tv device=/dev/video4:input=0:norm=NTSC -vo x11

* Remote serving with vlc:
  - source device: v4l2:///dev/video0

--------------------------------------------------------------------------------------------------
* OpenMAX and MMAL are the only platform APIs available on Raspi
* Video format of capture device
  - 720x480, yuyv422, interlaced
  - packet size: 691,200, stride: 1440
* ffmpeg
  - yuv420p, bicubic, auto-scaler_0

  - ffmpeg -fflags +genpts+igndts -pix_fmt yuv420p -i /dev/video0 -c:v h264_v4l2m2m -b:v 8M -f mpegts - | cvlc -I dummy - --sout='#std{access=http,mux=ts,dst=:8554}'
  - ffmpeg -i /dev/video0 -c:v h264_v4l2m2m -b:v 8M -f mpegts - | cvlc -I dummy - --sout='#std{access=http,mux=ts,dst=:8554}'
  - ffmpeg -i /dev/video0 -c:v h264_omx -b:v 8M -f mpegts - | cvlc -I dummy - --sout='#std{access=http,mux=ts,dst=:8554}'
  - ffmpeg -fflags +genpts+igndts -i /dev/video0 -c:v h264_omx -an -b:v 10M -progress pipe:2 -f mpegts - | cvlc -I dummy - --sout='#std{access=http,mux=ts,dst=:8554,acodec=none}'

===================================================================================
* read temperature
  - alias temp='/opt/vc/bin/vcgencmd measure_temp'

* monitor temp and RSSI
  - while true; do vcgencmd measure_temp; sleep 30; iwlist wlan0 scan | egrep dBm; done

* setup avue services
  - sudo cp avue<svc>.service /lib/systemd/system/avue<svc>.service
  - sudo systemctl daemon-reload
  - sudo systemctl enable avue<svc>
  - sudo systemctl start avue<svc>
  - sudo systemctl status avue<svc>

===================================================================================

## TODO
* make a tool to set the camera's baudrate
* make a tool that allows CLI-based control of the camera
* enable systemd watchdogs to ensure applications are all running
* figure out how to reduce latency of video streaming
* create default startup state for controller
