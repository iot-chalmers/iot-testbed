#!/usr/bin/env python

# Simon Duquennoy (simonduq@sics.se)

import sys
import os
import subprocess

TESTBED_PI_PATH = "/home/user/scripts"

def pssh(hosts_path, cmd, message, inline=False, merge_path=False):
  print "%s (on all: %s)" %(message, cmd)
  if merge_path:
    cmdpth = os.path.join(TESTBED_PI_PATH, cmd)
  else:
  	cmdpth = cmd
  return subprocess.call(["parallel-ssh","--timeout", "240", "-h", hosts_path, "-o", "pssh-out", "-e", "pssh-err", "-l", "user", "-i" if inline else "", cmdpth])
  
def pscp(hosts_path, src, dst, message):
  print "%s (on all: %s -> %s)" %(message, src, dst)
  return subprocess.call(["parallel-scp", "-h", hosts_path, "-o", "pssh-out", "-e", "pssh-err", "-l", "user", "-r", src, dst])

def pslurp(hosts_path, src, dst, message):
  print "%s (on all: %s -> %s)" %(message, src, dst)
  return subprocess.call(["parallel-slurp", "-h", hosts_path, "-o", "pssh-out", "-e", "pssh-err", "-l", "user", "-r", "-L", dst, src, "."])

