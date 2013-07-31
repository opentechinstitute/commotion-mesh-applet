#!/bin/bash

echo $0 > /tmp/logger
echo $1 >> /tmp/logger
echo $2 >> /tmp/logger
#Reparse settings file into wpa_supplicant form
#service network-manager stop
#pkill -9 wpa_supplicant
#./custom_wpa_supplicant -Dnl80211 -i$2 -c -dd
#ifconfig wlan0 up $3 255.0.0.0
#olsrd -i $2 -f /etc/nm-dispatcher-olsrd/commotionwireless.net.conf
#Implement way to kill tihs network
#service network-manager start

