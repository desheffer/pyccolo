#!/usr/bin/env python2

"""
Copyright (C) 2013 Doug Sheffer <desheffer@gmail.com>

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see <http://www.gnu.org/licenses/>.

"""

import pygame
import time
import gobject

try:
    import RPi.GPIO as GPIO
except:
    pass

PIN_RA = 24
PIN_RB = 25
PIN_RC = 23
PIN_B1 = 17
PIN_B2 = 22

class Controller(gobject.GObject):
    __gsignals__ = {
        'change-mode': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                        (gobject.TYPE_INT,)),
        'station-up': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'station-down': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'next-song': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'play-pause': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        }

    # Mode enumeration.
    MODE_STATION = 1
    MODE_VOLUME = 2

    CLOCKWISE = ((False, False), # Home
                 (True, False),
                 (True, True),
                 (False, True),
                 (False, False), # Home
                 (True, False),
                 (True, True),
                 (False, True),
                 (False, False), # Home
                )

    def __init__(self):
        """Setup controller."""

        gobject.GObject.__init__(self)

    def run(self, mainloop):
        """Process GPIO knob and button changes in a loop."""

        mode = Controller.MODE_STATION
        self.emit('change-mode', mode)

        # Read from GPIO.
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(PIN_RA, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(PIN_RB, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(PIN_RC, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(PIN_B1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(PIN_B2, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            dial = 0
            dial_home = int(len(Controller.CLOCKWISE) / 2)

            old_b1 = old_b2 = old_rc = False

            while True:
                new_ra = not GPIO.input(PIN_RA)
                new_rb = not GPIO.input(PIN_RB)
                new_rc = not GPIO.input(PIN_RC)
                new_b1 = not GPIO.input(PIN_B1)
                new_b2 = not GPIO.input(PIN_B2)

                # Button one.
                if new_b1 and not old_b1:
                    self.emit('play-pause')
                old_b1 = new_b1

                # Button two.
                if new_b2 and not old_b2:
                    self.emit('next-song')
                old_b2 = new_b2

                # Rotational knob.
                dial_index = dial_home + dial
                if Controller.CLOCKWISE[dial_index - 1] == (new_ra, new_rb):
                    dial = dial - 1
                    if dial <= -3:
                        self.emit('station-down')
                        dial = 0
                elif Controller.CLOCKWISE[dial_index + 1] == (new_ra, new_rb):
                    dial = dial + 1
                    if dial >= 3:
                        self.emit('station-up')
                        dial = 0

                # Dial click.
                if new_rc and not old_rc:
                    if mode == Controller.MODE_STATION:
                        mode = Controller.MODE_VOLUME
                    elif mode == Controller.MODE_VOLUME:
                        mode = Controller.MODE_STATION
                    self.emit('change-mode', mode)
                old_rc = new_rc

                time.sleep(0.001)

        # Fallback to keyboard mode.
        except:
            print "Falling back to keyboard input mode."

            old_keys = pygame.key.get_pressed()

            while True:
                keys = pygame.key.get_pressed()

                if keys[pygame.K_UP] and not old_keys[pygame.K_UP]:
                    self.emit('station-up')
                if keys[pygame.K_DOWN] and not old_keys[pygame.K_DOWN]:
                    self.emit('station-down')
                if keys[pygame.K_LEFT] and not old_keys[pygame.K_LEFT]:
                    self.emit('play-pause')
                if keys[pygame.K_RIGHT] and not old_keys[pygame.K_RIGHT]:
                    self.emit('next-song')
                if keys[pygame.K_q] and not old_keys[pygame.K_q]:
                    mainloop.quit()

                old_keys = keys

                time.sleep(0.01)
