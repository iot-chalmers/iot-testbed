#!/bin/bash

log_path=$1
tty_path=`ls /dev/serial/by-id/usb-SEGGER_J-Link_*`
#gtimeout -s ABRT --kill-after=$(($(DURATION)+2)) --foreground $(DURATION) picocom --noreset -fh -b 230400 --imap lfcrlf $tty_path --logfile $log_path
#nohup ~/scripts/contiki-serialdump -b115200 $tty_path | ~/scripts/contiki-timestamp > $log_path & > /dev/null 2> /dev/null
nohup picocom --noreset -fh -b 230400 --imap lfcrlf $tty_path --logfile $log_path & > /dev/null 2> /dev/null

sleep 1
ps | grep "$! "
exit $?
