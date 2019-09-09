/home/user/scripts/usb-hub-on.sh
mkdir -p logs/$1
cp -r /home/user/scripts/sky /home/user/tmp/sky
killall -9 -q picocom
killall -9 -q serialdump
