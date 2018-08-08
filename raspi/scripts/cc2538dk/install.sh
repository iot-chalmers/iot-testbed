#!/bin/bash
 
tty_path=`ls /dev/serial/by-id/usb-FTDI_FT231X_USB_UART_*`
firmware_path=$1
# Now reset and program the node
#~/scripts/cc2538dk/setupCC2538.py
# Reboot the node
/home/user/scripts/usb-hub-off.sh
/home/user/scripts/usb-hub-on.sh
sleep 1
~/scripts/cc2538dk/cc2538-bsl/cc2538-bsl.py -b 250000 -p $tty_path -e -v -w $firmware_path
if [ $? -ne 0 ]; then
    exit 1
fi
sleep 1
# Reboot the node
/home/user/scripts/usb-hub-off.sh
/home/user/scripts/usb-hub-on.sh
sleep 1
