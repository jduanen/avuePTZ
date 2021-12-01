#!/bin/bash
#
# Script that runs ffmpeg to serve the video stream and issues watchdog updates
#
# Setup by installing 'avueVideo.service' in /lib/systemd/sysetm and running:
#  sudo systemctl daemon-reload
#  sudo systemctl start avueVideo
#  sudo systemctl status avueVideo
#
# To view video: 'vlc http://avue:8554'


INTERVAL=15

function cleanup()
{
	kill $PID
    /bin/systemd-notify --pid $PID --status=STOPPING
	exit
}

trap cleanup EXIT

ffmpeg -fflags +genpts+igndts -i /dev/video0 -c:v h264_omx -an -b:v 8M -f mpegts - | cvlc -I dummy - --sout='#std{access=http,mux=ts,dst=:8554,acodec=none}' & PID=$!

/bin/systemd-notify --pid $PID --ready
while true; do
	if ps -p $PID > /dev/null
	then
		/bin/systemd-notify --pid $PID WATCHDOG=1
	else
		echo "PID: " $PID " not running"
		break
	fi
	sleep $INTERVAL
done

kill $PID
