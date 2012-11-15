#!/bin/bash

cd `dirname $0`

CONFIG=/etc/pyccolo/pyccolo.conf

# Install dependencies.
echo "Installing required dependencies..."
apt-get install -y console-tools \
    alsa-utils \
    python-gst0.10 \
    gstreamer0.10-plugins-base \
    gstreamer0.10-plugins-good \
    gstreamer0.10-plugins-bad

# Enable sound module.
if [ -z `grep "^snd_bcm2835$" /etc/modules` ]; then
    echo
    echo "snd_bcm2835" >> /etc/modules
    echo "Enabled snd_bcm2835 module for sound card."
fi

# Set default sound device.
echo
amixer cset numid=3 1 >/dev/null
amixer set PCM -- 0 >/dev/null
echo "Set headphone jack as the default sound device."

# Setup configuration file.
if [ ! -f $CONFIG ]; then
    echo
    echo "Please enter your Pandora account information..."
    read -p "Email: " USERNAME
    read -s -p "Password: " PASSWORD
    echo

    mkdir -p `dirname $CONFIG`
    echo "[User]" >> $CONFIG
    echo "username = $USERNAME" >> $CONFIG
    echo "password = $PASSWORD" >> $CONFIG
    echo "Saved account information to $CONFIG."
fi

# Configure application to start on boot.
echo
rm -f /etc/init.d/pyccolo
cp extras/etc__init.d__pyccolo /etc/init.d/pyccolo
rm -f /etc/rcS.d/*pyccolo
ln -s /etc/init.d/pyccolo /etc/rcS.d/S99pyccolo
echo "Installed pyccolo service."

echo
echo "Done."
echo "Now reboot."
