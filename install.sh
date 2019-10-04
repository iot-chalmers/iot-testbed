git pull
rsync -azv --delete server/examples /usr/testbed/
rsync -azv --delete server/scripts /usr/testbed/
parallel-rsync -h /usr/testbed/scripts/all-hosts -l user -azv raspi/scripts /home/user
parallel-rsync -h /usr/testbed/scripts/all-hosts -l user -azv raspi/fstab /home/user/fstab
parallel-ssh --timeout 0 --hosts ./server/scripts/all-hosts --user user --inline "if ! grep -q '/home/user/tmp' /etc/fstab; then cat /home/user/fstab >> /etc/fstab; fi; rm -f /home/user/fstab; mkdir -p /home/user/tmp"
parallel-ssh --timeout 0 --hosts ./server/scripts/all-hosts --user user --inline "sudo mount -a"
parallel-rsync -h /usr/testbed/scripts/all-hosts -l user -azv server/scripts /usr/testbed/
