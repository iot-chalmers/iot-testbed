#!/bin/bash

log_path=$1
tty_path="/dev/ttyBLENANO"
killall -9 picocom
killall -9 screen
screen -wipe
screen -dmS blenanoscreen bash
screen -S blenanoscreen -X stuff "picocom --noreset -fh -b 115200 --imap lfcrlf $tty_path | ~/scripts/contiki-timestamp > $log_path\n"
sleep 1
ps | grep "$! "
exit $?
