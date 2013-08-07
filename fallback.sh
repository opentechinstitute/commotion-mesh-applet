#!/bin/bash

echo "hi" > /tmp/logger2
echo $0 >> /tmp/logger2
echo $1 >> /tmp/logger2
echo $2 >> /tmp/logger2
#Reparse settings file into wpa_supplicant form
nmcli nm sleep true
pkill -9 wpa_supplicant
./custom_wpa_supplicant -Dnl80211 -i$2 -c -dd
ifconfig $2 up $3 255.0.0.0
olsrd -i $2 -f $1
#Implement way to kill tihs network
#service network-manager start

