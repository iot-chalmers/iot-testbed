#!/bin/bash

log_path=$1
tty_path=`ls /dev/serial/by-id/usb-SEGGER_J-Link_*`
if pgrep picocom; then killall -9 picocom; fi; 
if pgrep screen; then killall -9 screen; fi; 
if pgrep contiki-timestamp; then killall -9 contiki-timestamp; fi;
screen -wipe
screen -dmS nrf52screen bash
screen -S nrf52screen -X stuff "picocom -fh -b 115200 --imap lfcrlf $tty_path | ~/scripts/contiki-timestamp > $log_path\n"
sleep 1
ps | grep "$! "
exit $?
