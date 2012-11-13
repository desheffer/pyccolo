Pyccolo
=======

Small Python application for playing Pandora radio on a Raspberry Pi running
Arch Linux.

The application will be coded to assume the following set of hardware is used:
-   Hacked Keyboard?
-   LCD Screen?

## Installation

### Operating System

1. Download Arch Linux.

        wget http://downloads.raspberrypi.org/images/archlinuxarm/archlinux-hf-2012-09-18/archlinux-hf-2012-09-18.zip
        unzip archlinux-hf-2012-09-18.zip

2.  Write it to an SD card.

        dd bs=1M if=archlinux-hf-2012-09-18.img of=/dev/sdX

3.  Boot the Raspberry Pi.

4.  Change the root password (default is 'root').

5.  Check for package updates.

        pacman -Syyu

### Application

1.  Install git and clone the Pyccolo repository.

        pacman -S git
        git clone git://github.com/desheffer/pyccolo.git

2.  Install Pyccolo.

        cd pyccolo
        ./install.sh
