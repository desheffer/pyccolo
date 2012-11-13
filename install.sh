#!/bin/bash

CONFIG=~/.config/pyccolo.ini

echo "Please enter your Pandora account information..."
read -p "Email: " USERNAME
read -s -p "Password: " PASSWORD

# Setup configuration file.
echo "" > $CONFIG
echo "[User]" >> $CONFIG
echo "username = $USERNAME" >> $CONFIG
echo "password = $PASSWORD" >> $CONFIG
echo "Saved account information to $CONFIG."

# Enable sound module.
echo "snd-bcm2835" > /etc/modules-load.d/snd-bcm2835.conf
echo "Enabled snd-bcm2835 module for sound card."

# Configure application to start as a service.
cp extras/pyccolo.service /usr/lib/systemd/system/pyccolo.service
#TODO: systemctl enable pyccolo
echo "Enabled systemd service for Pyccolo."
