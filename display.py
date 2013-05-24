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

from controller import Controller

import pygame
import threading
import time
import urllib2
import StringIO
import gobject

SCREEN_WIDTH = 320
SCREEN_HEIGHT = 240

ART_SIZE = (100, 100)

class Display(gobject.GObject):
    def __init__(self):
        """Initialize graphical user interface."""

        gobject.GObject.__init__(self)
        self.lock = threading.RLock()

        self.queue_draw = True

        self.stations = []
        self.station = None
        self.song = None
        self.art_url = ''
        self.playing = False

        self.mode = None
        self.mode_active = False
        self.mode_timeout_timer = None

        # Intialize screen.
        pygame.init()
        pygame.mouse.set_visible(False)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

        # Load images.
        self.background_img = None
        self.art_img = None
        try:
            self.background_img = pygame.image.load('background.png').convert()
        except:
            pass

    def run(self, mainloop):
        """Render the user interface and poll for events in a loop."""

        while True:
            # Monitor for quit events.
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    mainloop.quit()

            # Get queue status.
            with self.lock:
                queue_draw = self.queue_draw
                self.queue_draw = False

            # If nothing has changed then sleep momentarily.
            if not queue_draw:
                time.sleep(0.01)
                continue

            # Fill background
            surface = pygame.Surface(self.screen.get_size())
            surface = surface.convert()
            surface.fill((0, 0, 0))

            # Render the user interface.
            self.render(surface)
            self.screen.blit(surface, (0, 0))
            pygame.display.flip()

    def render(self, surface):
        """Render user interface elements."""

        # Handle special modes.
        #if self.mode_active:
        #    # Station selection mode.
        #    if self.mode == Controller.MODE_STATION:
        #        self.draw_text(surface, SCREEN_WIDTH / 2, 20, 'SELECT STATION', 20, align=0)

        #        row_range = (4, -4)
        #        row_count = abs(row_range[1] - row_range[0]) + 1
        #        row_height = SCREEN_HEIGHT / (row_count + 1)

        #        for num in range(0, len(self.stations)):
        #            station = self.station + row_range[0] + num
        #            if station >= 0 and station < len(self.stations):
        #                self.draw_text(surface, 10, row_height * (num + 1),
        #                               self.stations[station], 14)
        #    return

        if self.background_img:
            surface.blit(self.background_img, self.background_img.get_rect())

        # Display station information.
        if self.station is not None:
            station = self.stations[self.station]
            self.draw_text(surface, SCREEN_WIDTH / 2, 220,
                           'Station: %s' % station, 16, align=0)

        # Display song information.
        song = self.song
        if not song:
            self.draw_text(surface, SCREEN_WIDTH / 2, 120, 'Loading', 22,
                           align=0, valign=0)
        elif not self.playing:
            self.draw_text(surface, SCREEN_WIDTH / 2, 120, 'PAUSED', 22,
                           align=0, valign=0)
        else:
            self.draw_text(surface, SCREEN_WIDTH / 2, 40, song[2], 22,
                           align=0, valign=0)
            self.draw_text(surface, 130, 120, song[0], 18, bold=True)
            self.draw_text(surface, 130, 150, song[1], 18)

            if self.art_img:
                art_pos = self.art_img.get_rect()
                art_pos.x = 10
                art_pos.y = 80
                surface.blit(self.art_img, art_pos)

    def draw_text(self, surface, x, y, text, size, r=255, g=255, b=255,
                  bold=False, italic=False, face='Ubuntu', align=1, valign=-1):
        """Draw text on the screen."""

        font = pygame.font.SysFont(face, size, bold, italic)
        text_surface = font.render(text, 1, (r, g, b))
        text_pos = text_surface.get_rect()

        # Set horizontal alignment.
        if align == 1:
            text_pos.left = x
        elif align == 0:
            text_pos.centerx = x
        elif align == -1:
            text_pos.right = x

        # Set vertical alignment.
        if valign == 1:
            text_pos.top = y
        elif valign == 0:
            text_pos.centery = y
        elif valign == -1:
            text_pos.bottom = y

        surface.blit(text_surface, text_pos)

    def load_art(self):
        """Load album art for the current song."""

        with self.lock:
            art_url = self.art_url

        try:
            # Load album art image.
            content = urllib2.urlopen(art_url).read()
            buf = StringIO.StringIO(content)
            art_surface = pygame.image.load(buf, art_url)
            art_surface = pygame.transform.smoothscale(art_surface, ART_SIZE)
        except:
            # Create blank album art image.
            art_surface = pygame.Surface(ART_SIZE)
            art_surface = art_surface.convert()
            art_surface.fill((32, 32, 32))

        with self.lock:
            if self.art_url == art_url:
                self.art_img = art_surface.convert()
                self.queue_draw = True

    def change_mode(self, controller, mode):
        """Change the current user interface control mode."""

        with self.lock:
            self.mode = mode
            self.mode_active = False
            self.queue_draw = True

    def mode_timeout(self):
        """Disable the current mode."""

        with self.lock:
            self.mode_timeout_timer = None
            self.mode_active = False
            self.queue_draw = True

    def change_station(self, music, station, stations):
        """Change the station list that is displayed."""

        with self.lock:
            self.stations = stations
            self.station = station
            self.song = None
            self.art_url = None
            self.art_img = None

            if self.mode == Controller.MODE_STATION:
                self.mode_active = True

                if self.mode_timeout_timer:
                    self.mode_timeout_timer.cancel()
                self.mode_timeout_timer = threading.Timer(2, self.mode_timeout)
                self.mode_timeout_timer.start()

            self.queue_draw = True

    def change_song(self, music, artist, album, track, art_url):
        """Change the song name that is displayed."""

        with self.lock:
            self.song = (artist, album, track)
            self.art_url = art_url
            self.art_img = None
            threading.Thread(target=self.load_art).start()
            self.queue_draw = True

    def change_state(self, music, state):
        """Change the playing state that is displayed."""

        with self.lock:
            self.playing = state
            self.queue_draw = True
