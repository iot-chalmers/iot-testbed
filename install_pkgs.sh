#!/bin/bash
########## To sync: rsync -avz -e "ssh -p17122" ./iot-testbed testbed@sunlight.ds.informatik.uni-kiel.de:/home/testbed ######

########## Server side ###########
##### Make a user called testbed that have sudo, and execute thses steps from user tesbed
##### 1. configure the /etc/hosts file to have the raspi IPs and hostnames, for example:
# 192.168.87.228	raspi03
# 192.168.87.229	raspi04
# 192.168.87.230	raspi05

####install packages on server
sudo apt update --fix-missing
sudo apt install -y python-2.7 iptables-persistent dhcpdump rsync default-jre default-jdk pssh putty-tools clusterssh libffi screen at ntp tree

#sudo apt install -y gcc-4.9-arm-linux-gnueabihf-base #you might only find a newer version. install it for the time being
#sudo apt-get install -y g++-arm-linux-gnueabihf
sudo apt install -y gcc-arm-linux-gnueabihf #I use the version 4.9, but you might only find a newer version. Install it for the time being
sudo apt-get install -y binutils-arm-none-eabi build-essential 

sudo pip install --upgrade pip
sudo pip install parallel-ssh
sudo pip install pytz

####Optional: download MAC addresses vendor database, so that the network logs of your Linux server recognize RaspberryPi MAC addresses vendor field
sudo wget https://linuxnet.ca/ieee/oui.txt -O /usr/local/etc/oui.txt

####ping PIs
for ip in $(cat ./server/scripts/all-hosts); do ping -c 1 -t 1 $ip && echo "${ip} is up"; done | grep "is up"

####add user 'testbed' to dialout group
sudo usermod -aG dialout testbed

####add the users that need to use the testbedSW to the group testbed
sudo usermod -aG testbed ban
sudo usermod -aG testbed oha
sudo usermod -aG testbed vpo

####create install folder for testbed SW
sudo mkdir -p /usr/testbed
sudo chown testbed:testbed /usr/testbed

########## RasPIs ##########
####1. Preparation steps:
##### a. Update the file: server/scripts/all-hosts with the PIs hostnames
##### b. please make a user called 'user', and give it sudo access without password over ssh (add it to sudoers)
####### add the following line in /etc/sudoers:
####### user    ALL=(ALL) NOPASSWD: ALL
##### (done automatically in step 2) c. ssh once to every PI, such that you have the key signature in your .ssh folder, and it does not complain later
##### d. if you get the following strange error message on the PIa: 
######(mesg: ttyname failed: Inappropriate ioctl for device), delete the last line in /root/.profile: (mesg n || true)
######The file shall look like this (roughly), without the offending line: mesg n || true:
# /root/.profile
# # ~/.profile: executed by Bourne-compatible login shells.
# if [ "$BASH" ]; then
#   if [ -f ~/.bashrc ]; then
#     . ~/.bashrc
#   fi
# fi

####2. add PIs keys signatures -- execute on every user account on the server
for ip in $(cat /usr/testbed/scripts/all-hosts); do 
  if [ -z `ssh-keygen -F $ip` ]; then
    ssh-keyscan -H $ip >> ~/.ssh/known_hosts
  fi
done

####3. these commands would install the required pkgs on the PIs
parallel-ssh --timeout 0 --hosts ./server/scripts/all-hosts --user user --inline "sudo mkdir -p /usr/testbed && sudo chown user:user /usr/testbed && sudo usermod -aG dialout user && sudo apt update && sudo apt -y --force-yes install picocom ssh python2.7 python-serial screen at ntpdate ntp"

####4. install testbed SW to the server /usr and to PIs
sh /home/testbed/iot-testbed/install.sh

####5. COPY JLINK rules file to allow flashing nrf52 for non-root users
parallel-ssh --timeout 0 --hosts ./server/scripts/all-hosts --user user --inline "sudo cp /home/user/scripts/nrf52/JLink_Linux_V632i_arm/99-jlink.rules /etc/udev/rules.d"

####6. IMPROTANT: login as root or sudo -i to each PI, and flash any file on the nrf52 board to update the JLink firmwarw
parallel-ssh --timeout 0 --hosts ./server/scripts/all-hosts --user user --inline "sudo -i && cd /home/user/scripts/nrf52 && ./install.sh null.nrf52.hex"

####7. test if testbed SW works and connects to the PIs listed under 
python /usr/testbed/scripts/testbed.py status
python /usr/testbed/scripts/testbed.py create --name 'null' --platform 'nrf52' --duration 2 --copy-from /usr/testbed/examples/nrf52-hello-world/hello-world.nrf52.hex --start

####8. Optional, but recommended: check ntp time. SW will break when the PIs time is out of sync.
# parallel-ssh --hosts ./server/scripts/all-hosts --user user  --inline "ntptime"

####9. test making a job from your laptop using your own account on the server: (replace the variables with usseful arguments)
# scp -P17122 $(FNAME).hex ${USER}@sunlight.ds.informatik.uni-kiel.de:/home/${USER}/newjob.nrf52.hex
# ssh -p17122 ${USER}@sunlight.ds.informatik.uni-kiel.de "python /usr/testbed/scripts/testbed.py create --name '${NAME}' --platform 'nrf52' --duration ${DURATION} --copy-from /home/${USER}/newjob.nrf52.hex --start"

####10. if this makes a problem, then disable apt autoupdate. Steps:
# systemctl stop apt-daily.service
# systemctl disable apt-daily.service
# systemctl kill --kill-who=all apt-daily.service
# wait until `apt-get updated` has been killed
# while ! (systemctl list-units --all apt-daily.service | fgrep -q dead)
# do
#   sleep 1;
# done

##### Appendix: Adding a new user to the server
####Note that tsetbed SW is installed under /usr/testbed, and the sources (git hub repo) is under /home/testbed/iot-testbed
####1. add the users that need to use the testbedSW to the group testbed
sudo usermod -aG testbed newuser
####2. add PIs keys signatures -- execute on every user account on the server
for ip in $(cat /usr/testbed/scripts/all-hosts); do 
  if [ -z `ssh-keygen -F $ip` ]; then
    ssh-keyscan -H $ip >> ~/.ssh/known_hosts
  fi
done
