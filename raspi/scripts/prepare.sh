/home/user/scripts/usb-hub-on.sh
mkdir -p logs/$1
cp -r /home/user/scripts/sky /home/user/tmp/sky
killall -q -9 picocom
killall -q -9 serialdump
killall -q -9 contiki-timestamp
