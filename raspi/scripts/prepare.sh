/home/user/scripts/usb-hub-on.sh
mkdir -p logs/$1
cp -r /home/user/scripts/sky /home/user/tmp
if pgrep picocom; then killall -9 picocom;fi
if pgrep serial_forwarder; then killall -9 serial_forwarder;fi
if pgrep serialdump; then killall -9 serialdump;fi
if pgrep contiki-timestamp; then killall -9 contiki-timestamp;fi
