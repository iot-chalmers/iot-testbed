#!/bin/bash

# First reset the node so we get it mounted if it was not
#sleep 1
/home/user/scripts/usb-hub-off.sh
/home/user/scripts/usb-hub-on.sh
sleep 1
# Now program the node
firmware_path=$1
#get script from https://raw.githubusercontent.com/WayneKeenan/nrfjprog.sh/master/nrfjprog.sh
export PATH=$PATH:/home/user/scripts/nrf52/JLink_Linux_V632i_arm
/home/user/scripts/nrf52/JLink_Linux_V632i_arm/nrfjprog.sh -f nrf52 --erase-all
/home/user/scripts/nrf52/JLink_Linux_V632i_arm/nrfjprog.sh --flash $firmware_path -f nrf52
if [ $? -ne 0 ]; then
    exit 1
fi
/home/user/scripts/nrf52/JLink_Linux_V632i_arm/nrfjprog.sh --reset -f nrf52
sleep 0.5
# Reboot the node
#/home/user/scripts/usb-hub-off.sh
#/home/user/scripts/usb-hub-on.sh
#sleep 1
