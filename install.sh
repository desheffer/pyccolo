#!/bin/bash

CONFIG=~/.config/pyccolo.ini

# Install dependencies.
echo "Installing required dependencies..."
apt-get install -y python-gst0.10 \
    gstreamer0.10-plugins-base \
    gstreamer0.10-plugins-good \
    gstreamer0.10-plugins-bad \
    alsa-utils

# Enable sound module.
if [ -z `grep "^snd_bcm2835$" /etc/modules` ]; then
    echo "snd_bcm2835" >> /etc/modules
    echo "Enabled snd_bcm2835 module for sound card."
fi

# Set default sound device.
amixer cset numid=3 1
echo "Set audio jack as default sound device."

# Setup configuration file.
if [ ! -f $CONFIG ]; then
    echo "Please enter your Pandora account information..."
    read -p "Email: " USERNAME
    read -s -p "Password: " PASSWORD

    mkdir -p `dirname $CONFIG`
    echo "[User]" >> $CONFIG
    echo "username = $USERNAME" >> $CONFIG
    echo "password = $PASSWORD" >> $CONFIG
    echo "Saved account information to $CONFIG."
fi

# Configure application to start as a service.
#cp -f extras/pyccolo.service /usr/lib/systemd/system/pyccolo.service
#systemctl --system daemon-reload
#TODO: systemctl enable pyccolo
#echo "Enabled systemd service for Pyccolo."

echo "Done"
echo
echo "Now reboot."
