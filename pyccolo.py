#!/usr/bin/env python2

"""
Copyright (C) 2012 Doug Sheffer <desheffer@gmail.com>

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

import sys
import pygame
import pandora
import threading
import ConfigParser
import time
import urllib2
import StringIO
import gobject
import pygst
pygst.require('0.10')
import gst

try:
    import RPi.GPIO as GPIO
except:
    pass

CONF_FILE = '/etc/pyccolo/pyccolo.conf'

PIN_RA = 24
PIN_RB = 25
PIN_RC = 23
PIN_B1 = 17
PIN_B2 = 22

SCREEN_WIDTH = 320
SCREEN_HEIGHT = 240
ART_SIZE = (100, 100)

#  ____  _           _
# |  _ \(_)___ _ __ | | __ _ _   _
# | | | | / __| '_ \| |/ _` | | | |
# | |_| | \__ \ |_) | | (_| | |_| |
# |____/|_|___/ .__/|_|\__,_|\__, |
#             |_|            |___/

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

#  __  __           _
# |  \/  |_   _ ___(_) ___
# | |\/| | | | / __| |/ __|
# | |  | | |_| \__ \ | (__
# |_|  |_|\__,_|___/_|\___|
#

class Music(gobject.GObject):
    __gsignals__ = {
        'station-changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                            (gobject.TYPE_INT, gobject.TYPE_PYOBJECT,)),
        'song-changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                         (gobject.TYPE_STRING, gobject.TYPE_STRING,
                          gobject.TYPE_STRING, gobject.TYPE_STRING,)),
        'state-changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                          (gobject.TYPE_BOOLEAN,)),
        }

    def __init__(self):
        """Initialize audio functionality."""

        gobject.GObject.__init__(self)
        self.lock = threading.RLock()

        self.station = None
        self.playlists = dict()
        self.last_position = dict()
        self.song = None
        self.playing = False
        self.next_song_timer = None
        self.save_timer = None

        # Initialize Pandora.
        self.pandora = pandora.Pandora()
        #self.pandora.set_audio_format('mp3')

        # Initialize Gstreamer.
        self.player = gst.element_factory_make('playbin2', 'player')
        self.player.props.flags |= 0x80 # GST_PLAY_FLAG_DOWNLOAD (progressive download)
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect('message::eos', self.on_gst_eos)
        bus.connect('message::error', self.on_gst_error)

    def run(self, mainloop):
        self.config = ConfigParser.ConfigParser()
        self.config.read(CONF_FILE)

        # Read in configuration details.
        try:
            username = self.config.get('User', 'username')
            password = self.config.get('User', 'password')
        except:
            print 'Failed to load username and password from configuration file.'
            mainloop.quit()
            return False

        # Try to initiate a connection.
        try:
            while not self.init(username, password):
                time.sleep(1)
        except:
            print 'Radio connection failed:', sys.exc_info()
            mainloop.quit()
            return False

    def init(self, username, password):
        """Connect to radio and begin playing music."""

        try:
            self.pandora.connect(username, password)
        except (PandoraTimeout, PandoraNetError) as e:
            return False

        # Attempt to restore last station.
        self.pandora.get_stations()
        try:
            last_station_id = self.config.get('Station', 'station_id')
        except:
            last_station_id = self.pandora.stations[0].id
        self.set_station(last_station_id)

        return True

    def set_station(self, station_id):
        """Set the current station."""

        with self.lock:
            # Find the new station.
            new_station = self.pandora.get_station_by_id(station_id)
            if not new_station:
                return False

            # Store player position.
            if self.station and self.player.get_state()[1] != gst.STATE_NULL:
                try:
                    position = self.player.query_position(gst.FORMAT_TIME)
                    self.last_position[self.station.id] = position[0]
                except:
                    pass

            stations = self.pandora.stations
            self.station = new_station

        # Emit the changed signal.
        stations_indexed = []
        station_index = None
        for station in stations:
            if station.id == station_id:
                station_index = len(stations_indexed)
            stations_indexed.append(station.name)
        self.emit('station-changed', station_index, stations_indexed)

        with self.lock:
            # Trigger next song.
            if self.next_song_timer:
                self.next_song_timer.cancel()
            self.next_song_timer = threading.Timer(0.5, self.queue_song)
            self.next_song_timer.start()

            # Save the new station into the configuration file.
            if self.save_timer:
                self.save_timer.cancel()
            self.save_timer = threading.Timer(10, self.save_station)
            self.save_timer.start()

        return True

    def save_station(self):
        """Save the currently tuned station."""

        with self.lock:
            self.save_timer = None
            station_id = self.station.id

        # Save configuration.
        try:
            if not self.config.has_section('Station'):
                self.config.add_section('Station')
            self.config.set('Station', 'station_id', station_id)
            with open(CONF_FILE, 'wb') as config:
                self.config.write(config)
        except:
            pass

    def play(self):
        """Play the currently paused music track."""

        with self.lock:
            self.player.set_state(gst.STATE_PLAYING)
            if not self.playing:
                self.playing = True
                self.emit('state-changed', self.playing)

        return True

    def pause(self):
        """Pause the currently playing music track."""

        with self.lock:
            if self.playing:
                self.player.set_state(gst.STATE_PAUSED)
                self.playing = False
                self.emit('state-changed', self.playing)

        return True

    def tune_station(self, controller, delta):
        """Change the station in one direction, like a tuning dial."""

        with self.lock:
            if not self.station or not self.pandora.stations:
                return False

            # Tune in the direction given.
            curr = self.pandora.stations.index(self.station) + delta
            if curr < 0:
                curr = len(self.pandora.stations) - 1
            elif curr >= len(self.pandora.stations):
                curr = 0

            new_station_id = self.pandora.stations[curr].id

        return self.set_station(new_station_id)

    def play_pause(self, controller):
        """Toggle between playing and paused."""

        with self.lock:
            if self.playing:
                self.pause()
            else:
                self.play()

    def skip_song(self, controller=None):
        """Skip the current music track."""

        threading.Thread(target=self.queue_song, kwargs={'skip': True}).start()

    def queue_song(self, skip=False):
        """Queue the next music track."""

        with self.lock:
            self.next_song_timer = None

            self.player.set_state(gst.STATE_NULL)

            station = self.station
            if not station:
                return False

            # Get current station settings.
            playlist = None
            if station.id in self.playlists:
                playlist = self.playlists[station.id]

            # Lock playlist.
            if playlist == True:
                return False
            elif not playlist:
                self.playlists[station.id] = True

        # Skip most recent song.
        if playlist and skip:
            playlist.pop(0)

        # Fill the playlist.
        if not playlist:
            playlist = station.get_playlist()

        changed = False
        with self.lock:
            self.playlists[station.id] = playlist

            if station == self.station:
                # Play the next song in the playlist.
                self.song = playlist[0]
                self.player.set_property('uri', self.song.audioUrl)
                changed = True

        if changed:
            self.play()
            #threading.Thread(target=self.play).start()

            # Restore last player position.
            # TODO
            #if station.id in self.last_position:
            #    # Block until the player has changed state.
            #    self.player.get_state()

            #    self.player.seek_simple(gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH,
            #                            self.last_position[station.id])
            #    del(self.last_position[station.id])

            self.emit('song-changed', self.song.artist, self.song.album,
                      self.song.title, self.song.artRadio)

        return True

    def on_gst_eos(self, bus, message):
        """Begin the next track after the current track has completed."""

        self.skip_song()

    def on_gst_error(self, bus, message):
        """Report Gstreamer errors."""

        with self.lock:
            self.playing = False
        err, debug = message.parse_error()
        print 'Gstreamer Error: %s, %s, %s' % (err, debug, err.code)
        self.skip_song()

#   ____            _             _ _
#  / ___|___  _ __ | |_ _ __ ___ | | | ___ _ __
# | |   / _ \| '_ \| __| '__/ _ \| | |/ _ \ '__|
# | |__| (_) | | | | |_| | | (_) | | |  __/ |
#  \____\___/|_| |_|\__|_|  \___/|_|_|\___|_|
#

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

gobject.type_register(Display)
gobject.type_register(Controller)
gobject.type_register(Music)

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
