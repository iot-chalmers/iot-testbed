tty=`ls /dev/serial/by-id/usb-FTDI_MTM-CM5000*`
port=50000
if [ -z "$tty" ]
then
        echo "Could not find sky device"
        exit 1
fi

# avoid serial port being blocked
if pgrep picocom; then killall -9 picocom;fi
if pgrep serialdump; then killall -9 serialdump;fi
if pgrep serial_forwarder; then killall -9 serial_forwarder;fi
# kill previous screen
if pgrep screen; then killall -9 screen;fi
#set baudrate
stty -F $tty 115200 min 1 cs8 -cstopb -parenb -brkint -icrnl -imaxbel -opost -isig -icanon -iexten -echo -echoe -echok -echoctl -echoke

screen -wipe
screen -dmS skyscreen bash
screen -S skyscreen -X stuff "netcat -lt 0.0.0.0 $port <$tty >$tty\n"
sleep 1

ps | grep "$! "
exit $?
