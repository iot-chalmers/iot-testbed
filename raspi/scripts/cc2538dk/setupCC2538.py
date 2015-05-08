#!/usr/bin/env python

# Put the openmote in bootloader mode by polling the BOOT_LOADER_PIN that is 
# connected via a 1.5KOhm protection resistor to the bootlaoder pin on openmote
#
# Beshr Al Nahas <beshr@chalmers.se>

import os
import time

BOOT_LOADER_PIN = 17 #GPIO17 MCU == GPIO11 BOARD == GPIO0 Header
BOOT_LOADER_LEVEL = 0

if __name__ == "__main__":
	# turn off the usb hub
    os.system("hub-ctrl -h 0 -P 2 -p 0; hub-ctrl -h 0 -P 3 -p 0; hub-ctrl -h 0 -P 4 -p 0; hub-ctrl -h 0 -P 5 -p 0;")
	
	## Setup the RaspberryPi pin connected to the bootloader pin on openmote
    os.system("gpio -g mode %d out" % (BOOT_LOADER_PIN))
    os.system("gpio -g write %d %d" % (BOOT_LOADER_PIN, BOOT_LOADER_LEVEL))
    time.sleep(0.5)  

    # turn on the usb hub
    os.system("hub-ctrl -h 0 -P 2 -p 1; hub-ctrl -h 0 -P 3 -p 1; hub-ctrl -h 0 -P 4 -p 1; hub-ctrl -h 0 -P 5 -p 1;")
    time.sleep(0.1)
    os.system("gpio -g write %d %d" % (BOOT_LOADER_PIN, not BOOT_LOADER_LEVEL))
