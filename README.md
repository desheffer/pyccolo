Pyccolo
=======

Small Python application for playing Pandora radio on a Raspberry Pi running
Arch Linux.

The application will be coded to assume the following set of hardware is used:
-   Hacked Keyboard?
-   LCD Screen?

## Installation

1. Download Raspbian Image by Hexxeh.

        wget http://distribution.hexxeh.net/raspbian/raspbian-r3.zip
        unzip raspbian-r3.zip
        cd raspbian-r3

2. Check the file integrity.

        sha1sum -c raspbian-r3.img.sha1

3.  Write it to an SD card and then boot.

        dd bs=1M if=raspbian-r3.img of=/dev/sdX

4.  Change the root password (default is 'hexxeh').

5.  Check for updates.

        apt-get update && apt-get -y dist-upgrade

        apt-get install -y ntp fake-hwclock &&
        dpkg-reconfigure tzdata

        rpi-update

        reboot

6.  Clone the Pyccolo repository and install.

        git clone git://github.com/desheffer/pyccolo.git

        cd pyccolo
        ./install.sh

        reboot
