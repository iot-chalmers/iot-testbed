#!/bin/bash

# First reset the node so we get it mounted if it was not
#sleep 1
/home/user/scripts/usb-hub-off.sh
/home/user/scripts/usb-hub-on.sh
sleep 1
/home/user/scripts/nrf52/nrfjprog.sh --reset -f nrf52
# Now program the node
firmware_path=$1
#get script from https://raw.githubusercontent.com/WayneKeenan/nrfjprog.sh/master/nrfjprog.sh
export PATH=$PATH:/home/user/scripts/nrf52/JLink_Linux_arm
#/home/user/scripts/nrf52/nrfjprog.sh -f nrf52 --erase-all
/home/user/scripts/nrf52/nrfjprog.sh --flash $firmware_path -f nrf52
/home/user/scripts/nrf52/nrfjprog.sh --flash $firmware_path -f nrf52
if [ $? -ne 0 ]; then
    /home/user/scripts/nrf52/nrfjprog.sh -f nrf52 --erase-all
    /home/user/scripts/nrf52/nrfjprog.sh --flash $firmware_path -f nrf52
    /home/user/scripts/nrf52/nrfjprog.sh --flash $firmware_path -f nrf52
    if [ $? -ne 0 ]; then exit 1; fi;
fi

# Reboot the node
#/home/user/scripts/usb-hub-off.sh
#/home/user/scripts/usb-hub-on.sh
#sleep 1
/home/user/scripts/nrf52/nrfjprog.sh --reset -f nrf52
#sleep 1

# tty=/dev/serial/by-id/usb-SEGGER_J-Link_000683332328-if00; stty -F $tty 115200 min 1 cs8 -cstopb -parenb -brkint -icrnl -imaxbel -opost -isig -icanon -iexten -echo -echoe -echok -echoctl -echoke; cat $tty
