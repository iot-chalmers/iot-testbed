#!/bin/bash
#search for the Korean clone CM5000MSP and the original Moteiv TMote
tty_path1=`ls /dev/serial/by-id/usb-FTDI_MTM-CM5000MSP_*`
tty_path2=`ls /dev/serial/by-id/usb-Moteiv_tmote_sky_*`
tty_path="$tty_path1$tty_path2"
firmware_path=$1
#BSL="/home/user/scripts/sky/skytools/msp430-bsl-linux --telosb"
#reset
/home/user/scripts/sky/skytools/msp430-bsl-linux --telosb -c $tty_path -r
#erase
/home/user/scripts/sky/skytools/msp430-bsl-linux --telosb -c $tty_path -e && sleep 2 ; 
#program
/home/user/scripts/sky/skytools/msp430-bsl-linux --telosb -c $tty_path -p $firmware_path && sleep 2 
if [ $? -ne 0 ]; then
    exit 1
fi
#reset
/home/user/scripts/sky/skytools/msp430-bsl-linux --telosb -c $tty_path -r
# Reboot the node
#usb-hub-off.sh
#usb-hub-on.sh
#sleep 1
#sleep 1
# Reboot the node
/home/user/scripts/usb-hub-off.sh
/home/user/scripts/usb-hub-on.sh
#sleep 1



