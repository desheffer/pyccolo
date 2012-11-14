#!/bin/bash

CONFIG=~/.config/pyccolo.ini

echo "Installing required dependencies..."
pacman --needed --no-confirm -S python2 pygtk gstreamer0.10-python

if [ ! -f $CONFIG ]; then
    echo "Please enter your Pandora account information..."
    read -p "Email: " USERNAME
    read -s -p "Password: " PASSWORD

    # Setup configuration file.
    mkdir -p `dirname $CONFIG`
    echo "[User]" >> $CONFIG
    echo "username = $USERNAME" >> $CONFIG
    echo "password = $PASSWORD" >> $CONFIG
    echo "Saved account information to $CONFIG."
fi

# Enable sound module.
echo "snd-bcm2835" > /etc/modules-load.d/snd-bcm2835.conf
echo "Enabled snd-bcm2835 module for sound card."

# Configure application to start as a service.
cp -f extras/pyccolo.service /usr/lib/systemd/system/pyccolo.service
#TODO: systemctl enable pyccolo
echo "Enabled systemd service for Pyccolo."

echo "Done"
echo
echo "Now reboot."
