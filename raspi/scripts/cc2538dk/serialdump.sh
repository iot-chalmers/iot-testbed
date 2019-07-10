#!/bin/bash

log_path=$1
tty_path=`ls /dev/serial/by-id/usb-FTDI_FT231X_USB_UART_*`
killall -9 picocom
killall -9 screen
screen -wipe
screen -dmS cc2538screen bash
screen -S cc2538screen -X stuff "picocom --noreset -fh -b 115200 --imap lfcrlf $tty_path | ~/scripts/contiki-timestamp > $log_path\n"
sleep 1
ps | grep "$! "
exit $?
