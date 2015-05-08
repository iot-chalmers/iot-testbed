#!/bin/bash

log_path=$1
tty_path=`ls /dev/serial/by-id/usb-FTDI_FT231X_USB_UART_*`
nohup ~/scripts/cc2538dk/contiki-serialdump -b115200 $tty_path | ~/scripts/cc2538dk/contiki-timestamp > $log_path & > /dev/null 2> /dev/null
sleep 1
ps | grep "$! "
exit $?
