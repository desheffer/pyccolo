#!/usr/bin/env python

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

import ConfigParser
import time
import sys
import tty
import termios
import urllib2

import gobject
import pygst
pygst.require('0.10')
import gst
import threading

from pandora import *

class Pyccolo:
    def __init__(self, username, password):
        self.station = None
        self.playlist = None
        self.song = None
        self.playing = False

        # Initialize Pandora.
        self.pandora = Pandora()
        self.pandora.connect(username, password)

        # Initialize Gstreamer.
        self.player = gst.element_factory_make("playbin2", "player")
        self.player.props.flags |= 0x80 # GST_PLAY_FLAG_DOWNLOAD (progressive download)
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message::eos", self.on_gst_eos)
        bus.connect("message::buffering", self.on_gst_buffering)
        bus.connect("message::error", self.on_gst_error)

    def get_stations(self):
        """Get the list of stations."""

        self.pandora.get_stations()
        return self.pandora.stations

    def set_station(self, station_id):
        """Set the current station."""

        self.pause()

        # Change the station and the song.
        self.station = self.pandora.get_station_by_id(station_id)
        self.playlist = None
        threading.Thread(target=self.next_song).start()

        print "Station: %s" % self.station.name

        return True

    def tune_station(self, delta):
        """Change the station in one direction, like a tuning dial."""

        stations = self.pandora.stations
        if not stations:
            return False

        # Tune in the direction given.
        curr = stations.index(self.station) + delta
        if curr < 0:
            curr = len(stations) - 1
        elif curr >= len(stations):
            curr = 0

        return self.set_station(stations[curr].id)

    def is_playing(self):
        """True if music is playing."""

        return self.playing

    def play(self):
        """Play the currently paused music track."""

        self.player.set_state(gst.STATE_PLAYING)
        self.playing = True
        return True

    def pause(self):
        """Pause the currently playing music track."""

        if self.playing:
            self.player.set_state(gst.STATE_PAUSED)
        self.playing = False
        return True

    def next_song(self):
        """Skip the current music track."""

        self.player.set_state(gst.STATE_NULL)

        if not self.playlist:
            station = self.station
            self.playlist = self.station.get_playlist()

            # Break if the station was changed while loading.
            if station != self.station:
                return True

        # Play the next song.
        self.song = self.playlist.pop(0)
        self.player.set_property("uri", self.song.audioUrl)
        self.play()

        print "> '%s' by '%s' from '%s'" % (self.song.title,
                                            self.song.artist,
                                            self.song.album)

        return True

    def on_gst_eos(self, bus, message):
        """Begin the next track after the current track has completed."""

        self.next_song()

    def on_gst_buffering(self, bus, message):
        """Display Gstreamer buffering progress to the user."""

        #percent = message.parse_buffering()
        pass

    def on_gst_error(self, bus, message):
        """Display Gstreamer errors to the user."""

        self.playing = False
        err, debug = message.parse_error()
        print "Gstreamer Error: %s, %s, %s" % (err, debug, err.code)
        self.next_song()

def read_char():
    """Read in a single character from the console."""

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def has_network():
    """Determine if the Pandora website can be reached."""

    try:
        response = urllib2.urlopen('http://pandora.com')
        return True
    except urllib2.URLError as err:
        pass
    return False

if __name__ == "__main__":
    # Read in configuration details.
    cp = ConfigParser.ConfigParser()
    cp.read("/etc/pyccolo/pyccolo.conf")
    try:
        username = cp.get('User', 'username')
        password = cp.get('User', 'password')
    except:
        print "Failed to load username and password from configuration file."
        exit(1)

    # Wait until a network connection is available.
    while not has_network():
        time.sleep(1);

    # Initialize radio.
    pyccolo = Pyccolo(username, password)
    stations = pyccolo.get_stations()
    pyccolo.set_station(stations[0].id)

    # Start main loop in a separate thread.
    gobject.threads_init()
    g_loop = threading.Thread(target=gobject.MainLoop().run)
    g_loop.daemon = True
    g_loop.start()

    # Handle user input.
    while True:
        ch = read_char()
        if ch == 'q':
            exit(0)
        elif ch == 'p':
            if pyccolo.is_playing():
                pyccolo.pause()
            else:
                pyccolo.play()
        elif ch == 'n':
            pyccolo.next_song()
        elif ch == 'u':
            pyccolo.tune_station(1)
        elif ch == 'd':
            pyccolo.tune_station(-1)
