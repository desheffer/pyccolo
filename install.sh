#!/bin/bash

# Ensure this is a Raspberry Pi and not something else.
if [ ! -f /usr/bin/rpi-update -o ! -f /boot/config.txt ]; then
    echo "This device does not appear to be a Raspberry Pi."
    read -p "Are you sure you want to continue [y/N]? " CONFIRM
    if [ -z $CONFIRM ]; then
        CONFIRM='n'
    fi
    if [ $CONFIRM != 'y' -a $CONFIRM != 'Y' ]; then
        exit
    fi
fi

cd `dirname $0`

INSTALL=/opt/pyccolo
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

# Copy application directory.
rm -rf $INSTALL
cp -r . $INSTALL

# Copy boot configuration.
rm -f /boot/config.txt
cp ./extras/boot__config.txt /boot/config.txt

# Setup Pyccolo to start at boot.
if [ -z `grep 'pyccolo' /etc/inittab` ]; then
    sed -i 's/^id:.:initdefault:$/id:5:initdefault:/' /etc/inittab
    echo "x:5:wait:/usr/bin/xinit /opt/pyccolo/pyccolo.py" >> /etc/inittab
fi

# Disable screensaver and power saving.
if [ -z `grep '^xset -dpms$' /etc/X11/xinit/xinitrc` ]; then
    echo "xset -dpms" >> /etc/X11/xinit/xinitrc
fi
if [ -z `grep '^xset s off$' /etc/X11/xinit/xinitrc` ]; then
    echo "xset s off" >> /etc/X11/xinit/xinitrc
fi

echo
echo "Done."
echo "Now reboot."
