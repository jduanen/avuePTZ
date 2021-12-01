#!/bin/bash
#
# ????

INTERVAL=15
CMD="ffmpeg -fflags +genpts+igndts -i /dev/video0 -c:v h264_omx -an -b:v 8M -f mpegts - | cvlc -I dummy - --sout='#std{access=http,mux=ts,dst=:8554,acodec=none}'"

function cleanup()
{
	kill $PID
    /bin/systemd-notify --pid $PID --status=STOPPING
	exit
}

trap cleanup EXIT

$CMD & PID=$!

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
