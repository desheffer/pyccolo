Pyccolo
=======

Small Python application for playing Pandora radio on a Raspberry Pi running
Arch Linux.

The application will be coded to assume the following set of hardware is used:
-   Hacked Keyboard?
-   LCD Screen?

## Installation

### Initial Setup

1. Download Arch Linux.

        wget http://downloads.raspberrypi.org/images/archlinuxarm/archlinux-hf-2012-09-18/archlinux-hf-2012-09-18.zip
        unzip archlinux-hf-2012-09-18.zip

2.  Write it to an SD card.

        dd bs=1M if=archlinux-hf-2012-09-18.img of=/dev/sdX

3.  Boot and SSH into the Raspberry Pi (default password is 'root').

        ssh root@alarmpi

    1.  Fetch updates and upgrade.

            pacman -Syyu

    2.  Change the root password.

            passwd

    3.  Enable sound output.

            echo "snd-bcm2835" > /etc/modules-load.d/snd-bcm2835.conf

### Pyccolo Setup

1.  Install git and clone the Pyccolo repository.

        pacman -S git
        git clone git://github.com/desheffer/pyccolo.git
        cd pyccolo

2.  Install Pyccolo.

        ### TODO ###

3.  Configure Pyccolo to start as a service.

        cp extras/pyccolo.service /usr/lib/systemd/system/pyccolo.service
        systemctl enable pyccolo
