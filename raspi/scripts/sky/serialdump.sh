#!/bin/bash

log_path=$1
#search for the Korean clone CM5000MSP and the original Moteiv TMote
tty_path1=`ls /dev/serial/by-id/usb-FTDI_MTM-CM5000MSP_*`
tty_path2=`ls /dev/serial/by-id/usb-Moteiv_tmote_sky_*`
tty_path=$(tty_path1)$(tty_path2)
nohup ~/scripts/contiki-serialdump -b115200 $tty_path | ~/scripts/contiki-timestamp > $log_path & > /dev/null 2> /dev/null
sleep 1
ps | grep "$! "
exit $?
