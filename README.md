Pyccolo
=======

Small Python application for playing Pandora radio on a Raspberry Pi running
Arch Linux.

## Installation

### Initial Setup

1. Download Arch Linux.

       wget http://downloads.raspberrypi.org/images/archlinuxarm/archlinux-hf-2012-09-18/archlinux-hf-2012-09-18.zip
       unzip archlinux-hf-2012-09-18.zip

2. Write it to an SD card.

       dd bs=1M if=archlinux-hf-2012-09-18.img of=/dev/sdX

3. Boot the Raspberry Pi and SSH into it (default password is 'root').

       ssh root@alarmpi

   1. Fetch updates and upgrade.

          pacman -Syyu

   2. Change the password.

          passwd

### Pyccolo Setup

TODO
