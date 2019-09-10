#!/usr/bin/env python

# Simon Duquennoy (simonduq@sics.se)

import sys
import os
import subprocess
import sys
# sys.path.append('/usr/testbed/scripts')
# from pssh import *

REMOTE_LOGS_PATH = "/home/user/logs"
REMOTE_SCRIPTS_PATH = "/home/user/scripts"
REMOTE_JN_SCRIPTS_PATH = os.path.join(REMOTE_SCRIPTS_PATH, "../tmp/sky")
REMOTE_TMP_PATH = "/home/user/tmp"
REMOTE_NULL_FIRMWARE_PATH = os.path.join(REMOTE_JN_SCRIPTS_PATH, "null.sky.ihex")

def pssh(hosts_path, cmd, message, inline=False):
  print "%s (on all: %s)" %(message, cmd)
  return subprocess.call(["parallel-ssh", "-h", hosts_path, "-o", "pssh-out", "-e", "pssh-err", "-l", "user", "-i" if inline else "", cmd])
  
if __name__=="__main__":
  
  if len(sys.argv)<2:
    print "Job directory parameter not found!"
    sys.exit(1)
    
  # The only parameter contains the job directory
  job_dir = sys.argv[1]
       
  hosts_path = os.path.join(job_dir, "hosts")
  # Kill serialdump
  #pssh(hosts_path, "killall contiki-serialdump -9", "Stopping serialdump")
  pssh(hosts_path, 'if pgrep picocom; then killall -9 picocom;fi', "Stopping serialdump")
  pssh(hosts_path, 'if pgrep serialdump; then killall -9 serialdump;fi', "Stopping picocom")
  pssh(hosts_path, 'if pgrep contiki-timestamp; then killall -9 contiki-timestamp;fi', "Stopping contiki-timestamp")
  # Program the nodes with null firmware
  if pssh(hosts_path, "%s %s"%(os.path.join(REMOTE_JN_SCRIPTS_PATH, "install.sh"), REMOTE_NULL_FIRMWARE_PATH), "Uninstalling sky firmware") != 0:
    sys.exit(4)

