#!/bin/bash

log_path=$1
tty_path=`ls /dev/serial/by-id/usb-SEGGER_J-Link_*`
#screen -wipe
#screen -dmS nrf52screen bash
#screen -S nrf52screen -X stuff "picocom --noreset -fh -b 230400 --imap lfcrlf $tty_path | ~/scripts/contiki-timestamp > $log_path\n"
#screen -S nrf52screen -X stuff "~/scripts/contiki-serialdump -b230400 $tty_path | ~/scripts/contiki-timestamp > $log_path\n"
nohup ~/scripts/contiki-serialdump -b230400 $tty_path | ~/scripts/contiki-timestamp > $log_path & > /dev/null 2> /dev/null

sleep 1
ps | grep "$! "
exit $?
