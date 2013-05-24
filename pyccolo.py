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

from display import Display
from controller import Controller
from music import Music

import threading
import gobject

if __name__ == '__main__':
    gobject.threads_init()

    display = Display()
    controller = Controller()
    music = Music()
    mainloop = gobject.MainLoop()

    # Connect signals between components.
    controller.connect('change-mode', display.change_mode)
    controller.connect('station-up', music.tune_station, 1)
    controller.connect('station-down', music.tune_station, -1)
    controller.connect('play-pause', music.play_pause)
    controller.connect('next-song', music.skip_song)
    music.connect('station-changed', display.change_station)
    music.connect('song-changed', display.change_song)
    music.connect('state-changed', display.change_state)

    # Start user interface loop.
    display_thread = threading.Thread(target=display.run, args=(mainloop,))
    display_thread.daemon = True
    display_thread.start()

    # Start radio streaming thread.
    music_thread = threading.Thread(target=music.run, args=(mainloop,))
    music_thread.daemon = True
    music_thread.start()

    # Start GPIO controller thread.
    controller_thread = threading.Thread(target=controller.run, args=(mainloop,))
    controller_thread.daemon = True
    controller_thread.start()

    mainloop.run()
