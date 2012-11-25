Pyccolo
=======

Small Python application for playing Pandora radio on a Raspberry Pi.

The application will be coded to assume the following set of hardware is used:
-   Small LCD screen connected via analog video out.
-   Rotational encoder and push buttons connected via GPIO pins.

## Installation

1. Download the Raspbian Image by Hexxeh.

        wget http://downloads.raspberrypi.org/images/archlinuxarm/archlinux-hf-2012-09-18/archlinux-hf-2012-09-18.zip
        unzip archlinux-hf-2012-09-18.zip

2.  Write it to an SD card and then boot.

        dd bs=1M if=archlinux-hf-2012-09-18.img of=/dev/sdX

3.  Change the root password (default is 'root').

4.  Check for updates.

        pacman -Syyu

5.  Clone the Pyccolo repository and install.

        pacman -S git
        git clone git://github.com/desheffer/pyccolo.git

        cd pyccolo
        ./install.sh

        reboot
