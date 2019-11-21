#!/bin/bash

log_path=$1
tty_path=`ls /dev/serial/by-id/usb-SEGGER_J-Link_*`
killall -9 picocom
killall -9 screen
screen -wipe
screen -dmS nrf52screen bash
screen -S nrf52screen -X stuff "picocom -fh -b 115200 --imap lfcrlf $tty_path | ~/scripts/contiki-timestamp > $log_path\n"
sleep 1
ps | grep "$! "
exit $?
