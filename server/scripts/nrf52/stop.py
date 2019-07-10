#!/usr/bin/env python

# Simon Duquennoy (simonduq@sics.se)

import sys
import os
import subprocess
import sys
#sys.path.append('/usr/testbed/scripts')
#sys.path.append('..')
#import psshlib

REMOTE_LOGS_PATH = "/home/user/logs"
REMOTE_SCRIPTS_PATH = "/home/user/scripts"
REMOTE_JN_SCRIPTS_PATH = os.path.join(REMOTE_SCRIPTS_PATH, "nrf52")
REMOTE_TMP_PATH = "/home/user/tmp"
REMOTE_NULL_FIRMWARE_PATH = os.path.join(REMOTE_JN_SCRIPTS_PATH, "null.nrf52.hex")

def pssh(hosts_path, cmd, message, inline=False):
  print "%s (on all: %s)" %(message, cmd)
  cmdpth = os.path.join(REMOTE_SCRIPTS_PATH, cmd)
  return subprocess.call(["parallel-ssh", "-h", hosts_path, "-o", "pssh-out", "-e", "pssh-err", "-l", "user", "-i" if inline else "", cmdpth])
  
if __name__=="__main__":

  if len(sys.argv)<2:
    print "Job directory parameter not found!"
    sys.exit(1)
    
  # The only parameter contains the job directory
  job_dir = sys.argv[1]
       
  hosts_path = os.path.join(job_dir, "hosts")
  # Kill serialdump
  pssh(hosts_path, "killall -9 picocom", "Stopping picocom")
  pssh(hosts_path, "screen -S nrf52screen -X quit", "Stopping screen")
  pssh(hosts_path, "screen -wipe", "Wiping screens")
  pssh(hosts_path, "killall -9 screen", "Killing screen")

  #pssh(hosts_path, "killall -9 cat; killall -9 contiki*", "Stopping serialdump")

  # Program the nodes with null firmware
  if pssh(hosts_path, "%s %s"%(os.path.join(REMOTE_JN_SCRIPTS_PATH, "install.sh"), REMOTE_NULL_FIRMWARE_PATH), "Uninstalling nrf52 firmware") != 0:
    sys.exit(4)

