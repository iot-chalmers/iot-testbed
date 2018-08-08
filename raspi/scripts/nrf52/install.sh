#!/bin/bash

# First reset the node so we get it mounted if it was not
#sleep 1
../usb-hub-off.sh
../usb-hub-on.sh
sleep 1
# Now program the node
firmware_path=$1
#get script from https://raw.githubusercontent.com/WayneKeenan/nrfjprog.sh/master/nrfjprog.sh
./JLink_Linux_V632i_arm/nrfjprog.sh -f nrf52 --erase-all
./JLink_Linux_V632i_arm/nrfjprog.sh --flash $firmware_path -f nrf52
if [ $? -ne 0 ]; then
    exit 1
fi
./JLink_Linux_V632i_arm/nrfjprog.sh --reset -f nrf52
sleep 1
# Reboot the node
../usb-hub-off.sh
../usb-hub-on.sh
sleep 1
