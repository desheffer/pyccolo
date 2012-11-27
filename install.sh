#!/bin/bash

# Ensure this is a Raspberry Pi and not something else.
if [ ! -f /boot/config.txt ]; then
    echo "This device does not appear to be a Raspberry Pi."
    read -p "Are you sure you want to continue [y/N]? " CONFIRM
    if [ -z "$CONFIRM" ]; then
        CONFIRM='n'
    fi
    if [ "$CONFIRM" != 'y' -a "$CONFIRM" != 'Y' ]; then
        exit
    fi
fi

cd `dirname $0`

INSTALL=/opt/pyccolo
CONFIG=/etc/pyccolo/pyccolo.conf

# Install dependencies.
echo "Installing required dependencies..."
pacman --needed --noconfirm -S \
    base-devel \
    python2 \
    wiringpi \
    gstreamer0.10-python \
    gstreamer0.10-base-plugins \
    gstreamer0.10-good-plugins \
    gstreamer0.10-bad-plugins \
    alsa-firmware alsa-utils \
    python2-pygame \
    ttf-ubuntu-font-family

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
mkdir -p $INSTALL
cp pyccolo.py $INSTALL
cp start.sh $INSTALL
cp background.png $INSTALL
cp -r pandora $INSTALL

# Copy boot configuration.
rm -f /boot/config.txt
cp ./extras/boot__config.txt /boot/config.txt

# Setp RPi.GPIO library.
GPIO=RPi.GPIO-0.4.1a
if [ ! -d $GPIO ]; then
    wget http://pypi.python.org/packages/source/R/RPi.GPIO/$GPIO.tar.gz
    tar -xf $GPIO.tar.gz
    rm -f $GPIO.tar.gz
    (cd $GPIO && python2 setup.py install)
fi

# Enable sound module.
echo
modprobe snd_bcm2835
echo "snd_bcm2835" > /etc/modules-load.d/snd_bcm2835.conf
echo "Enabled snd_bcm2835 module for sound card."

# Set default sound device.
echo
amixer cset numid=3 1 >/dev/null
amixer set PCM -- 0 >/dev/null
echo "Set headphone jack as the default sound device."

# Configure application to start as a service.
echo
cp -f extras/pyccolo.service /usr/lib/systemd/system/pyccolo.service
systemctl --system daemon-reload
systemctl enable pyccolo
echo "Enabled systemd service for Pyccolo."

echo
echo "Done."
echo "Now reboot."
