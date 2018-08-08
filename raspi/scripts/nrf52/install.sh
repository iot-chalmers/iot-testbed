#!/bin/bash
 
# First reset the node so we get it mounted if it was not
#sleep 1
usb-hub-off.sh
usb-hub-on.sh
sleep 1
# Now program the node
firmware_path=$1
nrfjprog.sh -f nrf52 --erase-all
nrfjprog.sh --flash $firmware_path -f nrf52
if [ $? -ne 0 ]; then
    exit 1
fi
nrfjprog.sh --reset -f nrf52
sleep 1
# Reboot the node
usb-hub-off.sh
usb-hub-on.sh
sleep 1
