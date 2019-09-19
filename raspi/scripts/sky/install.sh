#!/bin/bash

if pgrep screen; then screen -X -S skyscreen quit;fi
if pgrep screen; then killall -9 screen;fi
if pgrep picocom; then killall -9 picocom;fi
if pgrep serialdump; then killall -9 serialdump;fi
if pgrep serial_forwarder; then killall -9 serial_forwarder;fi
#search for the Korean clone CM5000MSP and the original Moteiv TMote
tty_path1=`ls /dev/serial/by-id/usb-FTDI_MTM-CM5000*`
tty_path2=`ls /dev/serial/by-id/usb-Moteiv_tmote_sky_*`
tty_path="$tty_path1$tty_path2"
firmware_path=$1
if [ -z "$tty_path" ]
then
    echo "Could not find sky device"
    exit 1
fi

COUNTER=0
while [  $COUNTER -lt 5 ]; do
    echo Sky: Flashing trial $COUNTER
    let COUNTER=COUNTER+1 

    #reset
    /home/user/scripts/sky/skytools/msp430-bsl-linux --telosb -c $tty_path -r
    # erase and program
    ~/scripts/sky/skytools/msp430-bsl-linux --telosb --speed=38400 --framesize=224 -c $tty_path -e --erasecycles=2 -p -I $firmware_path && sleep 2

    if [ $? -eq 0 ]; then
        break
    fi
done
if [ $? -ne 0 ]; then
    exit 1
fi
#reset
/home/user/scripts/sky/skytools/msp430-bsl-linux --telosb -c $tty_path -r
# Reboot the node
/home/user/scripts/usb-hub-off.sh
/home/user/scripts/usb-hub-on.sh
