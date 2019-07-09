#!/bin/bash
########## To sync: rsync -avz -e "ssh -p17122" ./iot-testbed testbed@sunlight.ds.informatik.uni-kiel.de:/home/testbed ######

########## Server side ###########
##### 1. configure the /etc/hosts file to have the raspi IPs and hostnames, for example:
# 192.168.87.228	raspi03
# 192.168.87.229	raspi04
# 192.168.87.230	raspi05

####install packages on server
sudo apt update --fix-missing
sudo apt install -y python-2.7 iptables-persistent dhcpdump rsync default-jre default-jdk pssh putty-tools clusterssh libffi screen at ntp tree
sudo apt install -y gcc-4.9-arm-linux-gnueabihf-base
sudo apt-get install -y g++-arm-linux-gnueabihf
sudo apt-get install -y build-essential

pip install --upgrade pip
pip install parallel-ssh
pip install pytz --user

####download MAC addresses vendor database
sudo wget http://standards.ieee.org/regauth/oui/oui.txt -O /usr/local/etc/oui.txt

####ping PIs
for ip in raspi{03..05}; do ping -c 1 -t 1 $ip && echo "${ip} is up"; done

####add user to dialout group
sudo usermod -aG dialout

####create install folder for testbed SW
sudo mkdir -p /usr/testbed
sudo chown testbed:testbed /usr/testbed

########## RasPIs ##########
####1. please make a user called user, and give it sudo access without password over ssh
####2. these commands would install teh pkgs on the PIs
parallel-ssh --hosts ~/testbed/sshhosts.txt --user user  --inline "sudo apt update && sudo apt -y --force-yes install picocom ssh python2.7 screen at ntpdate ntp"
parallel-ssh --hosts ~/testbed/sshhosts.txt --user user  --inline "ntptime"

####install testbed SW to the server /usr and to PIs
sh /home/testbed/iot-testbed/install.sh

####test if it works
python /usr/testbed/scripts/testbed.py status

#####Update the files: ~/testbed/sshhosts.txt and server/scripts/all-hosts with the PIs hostnames

#### if this makes a problem, then disable apt autoupdate
# systemctl stop apt-daily.service
# systemctl disable apt-daily.service
# systemctl kill --kill-who=all apt-daily.service
# wait until `apt-get updated` has been killed
# while ! (systemctl list-units --all apt-daily.service | fgrep -q dead)
# do
#   sleep 1;
# done