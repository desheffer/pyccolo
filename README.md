Pyccolo
=======

Small Python application for playing Pandora radio on a Raspberry Pi running
Arch Linux.

h1. Installation

h2. Initial Setup

- Download Arch Linux.
      wget http://downloads.raspberrypi.org/images/archlinuxarm/archlinux-hf-2012-09-18/archlinux-hf-2012-09-18.zip
      unzip archlinux-hf-2012-09-18.zip

- Write it to an SD card.
      dd bs=1M if=archlinux-hf-2012-09-18.img of=/dev/sdX

- Boot the Raspberry Pi and SSH into it (default password is 'root').
      ssh root@alarmpi

  - Fetch updates and upgrade.
        pacman -Syyu

  - Change the password.
        passwd

h2. Pyccolo Setup

TODO
