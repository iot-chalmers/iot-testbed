#!/bin/bash

log_path=$1
#search for the Korean clone CM5000MSP and the original Moteiv TMote
tty_path1=`ls /dev/serial/by-id/usb-FTDI_MTM-CM5000*`
tty_path2=`ls /dev/serial/by-id/usb-Moteiv_tmote_sky_*`
tty_path="$tty_path1$tty_path2"
killall -9 picocom
killall -9 screen
screen -wipe
screen -dmS skyscreen bash
screen -S skyscreen -X stuff "picocom --noreset -fh -b 115200 --imap lfcrlf $tty_path | ~/scripts/contiki-timestamp > $log_path\n"
sleep 1
ps | grep "$! "
exit $?
