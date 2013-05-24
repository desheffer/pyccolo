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

import sys
import pandora
import threading
import ConfigParser
import time
import gobject
import pygst
pygst.require('0.10')
import gst

CONF_FILE = '/etc/pyccolo/pyccolo.conf'

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

