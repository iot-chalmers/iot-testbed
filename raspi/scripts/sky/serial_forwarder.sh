tty=`ls /dev/serial/by-id/usb-FTDI_MTM-CM5000*`
port=54321
if [ -z "$tty" ]
then
        echo "Could not find sky device"
        exit 1
fi
#set baudrate
stty -F $tty 115200 min 1 cs8 -cstopb -parenb -brkint -icrnl -imaxbel -opost -isig -icanon -iexten -echo -echoe -echok -echo$
# start forwarding
nc -lt 0.0.0.0 $port <$tty >$tty
# distant closing will stop netcat
# reset serial config
stty -F $tty 9600 min 0 -brkint -icrnl -imaxbel -opost -isig -icanon -iexten -echo -echoe -echok -echoctl -echoke