#!/usr/bin/env python

# Simon Duquennoy (simonduq@sics.se)

import sys
import os
import subprocess
sys.path.insert(1,'/usr/testbed/scripts')
from psshlib import *

REMOTE_LOGS_PATH = "/home/user/logs"
REMOTE_SCRIPTS_PATH = "/home/user/scripts"
REMOTE_JN_SCRIPTS_PATH = os.path.join(REMOTE_SCRIPTS_PATH, "nrf52")
REMOTE_TMP_PATH = "/home/user/tmp"
REMOTE_FIRMWARE_PATH = os.path.join(REMOTE_TMP_PATH, "firmware.nrf52.hex")


if __name__=="__main__":

  if len(sys.argv)<2:
    print "Job directory parameter not found!"
    sys.exit(1)
    
  # The only parameter contains the job directory
  job_dir = sys.argv[1]

  # Look for the firmware
  firmware_path = None
  if os.path.isdir(job_dir):
   for f in os.listdir(job_dir):
    if f.endswith(".nrf52.hex"):
      firmware_path = os.path.join(job_dir, f)
      break
       
  if firmware_path == None:
    print "No nrf52 firmware found!"
    sys.exit(2)
      
  hosts_path = os.path.join(job_dir, "hosts")
  # Copy firmware to the nodes
  if pscp(hosts_path, firmware_path, REMOTE_FIRMWARE_PATH, "Copying nrf52 firmware to the PI nodes") != 0:
    sys.exit(3)
  # Program the nodes and start serialdump
  remote_log_dir = os.path.join(REMOTE_LOGS_PATH, os.path.basename(job_dir), "log.txt")
  if pssh(hosts_path, "%s %s %s"%(os.path.join(REMOTE_JN_SCRIPTS_PATH, "install-serialdump.sh"), REMOTE_FIRMWARE_PATH, remote_log_dir), "Installing nrf52 firmware and starting serialdump") != 0:
    sys.exit(4)
  # # Program the nodes
  # if pssh(hosts_path, "%s %s"%(os.path.join(REMOTE_JN_SCRIPTS_PATH, "install.sh"), REMOTE_FIRMWARE_PATH), "Installing nrf52 firmware") != 0:
  #   sys.exit(4)
  # # Start serialdump
  # remote_log_dir = os.path.join(REMOTE_LOGS_PATH, os.path.basename(job_dir), "log.txt")
  # if pssh(hosts_path, "%s %s"%(os.path.join(REMOTE_JN_SCRIPTS_PATH, "serialdump.sh"), remote_log_dir), "Starting serialdump") != 0:
  #   sys.exit(5)

