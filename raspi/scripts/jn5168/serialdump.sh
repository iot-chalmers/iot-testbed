#!/bin/bash

log_path=$1
tty_path=`ls /dev/serial/by-id/*NXP_JN5168_USB_Dongle*`
nohup ~/scripts/contiki-serialdump -b1000000 $tty_path | ~/scripts/contiki-timestamp > $log_path & > /dev/null 2> /dev/null
sleep 1
ps | grep "$! "
exit $?
