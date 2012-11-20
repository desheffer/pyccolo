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
import urllib2

import gobject
import pygst
pygst.require("0.10")
import gst
import threading

import RPi.GPIO as GPIO

from pandora import *

import pygtk
pygtk.require("2.0")
import gtk
import cairo

CONF_FILE = "/etc/pyccolo/pyccolo.conf"
PIN_CCW = 23
PIN_CW = 24
PIN_CLICK = 25

class Display(gtk.Window):
    def __init__(self):
        super(Display, self).__init__()

    def do_realize(self):
        """Initialize a place to draw the GUI."""

        self.set_flags(self.flags() | gtk.REALIZED)
        self.connect("delete-event", gtk.main_quit)

        self.window = gtk.gdk.Window(
            self.get_parent_window(),
            width = self.get_screen().get_width(),
            height = self.get_screen().get_height(),
            window_type = gtk.gdk.WINDOW_TOPLEVEL,
            wclass = gtk.gdk.INPUT_OUTPUT,
            event_mask = self.get_events() | gtk.gdk.EXPOSURE_MASK
        )

        (x, y, w, h, depth) = self.window.get_geometry()
        self.size_allocate(gtk.gdk.Rectangle(x = x, y = y, width = w, height = h))
        self.set_default_size(w, h)

        self.style.attach(self.window)
        self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("red"))
        self.style.set_background(self.window, gtk.STATE_NORMAL)
        self.window.set_user_data(self)

class Pyccolo:
    def __init__(self, display):
        self.station = None
        self.playlists = dict()
        self.song = None
        self.playing = False
        self.timer = None

        # Read in configuration details.
        self.config = ConfigParser.ConfigParser()
        self.config.read(CONF_FILE)
        try:
            username = self.config.get("User", "username")
            password = self.config.get("User", "password")
        except:
            print "Failed to load username and password from configuration file."
            exit(1)

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

        # Attempt to restore last station.
        self.pandora.get_stations()
        try:
            last_station_id = self.config.get("Station", "station_id")
        except:
            last_station_id = stations[0].id
        self.set_station(last_station_id)

    def get_station_id(self):
        """Get the id of the current station."""

        if not self.station:
            return None
        return self.station.id

    def set_station(self, station_id):
        """Set the current station."""

        self.pause()

        # Change the station and the song.
        self.station = self.pandora.get_station_by_id(station_id)

        # Trigger next song.
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(0.25, self.next_song)
        self.timer.start()

        # Save the new station into the configuration file.
        try:
            if not self.config.has_section("Station"):
                self.config.add_section("Station")
            self.config.set("Station", "station_id", station_id)
            with open(CONF_FILE, "wb") as config:
                self.config.write(config)
        except:
            pass

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

        if self.timer:
            self.timer.cancel()
            self.timer = None

        # Get current station settings.
        station = self.station
        playlist = None
        if station.id in self.playlists:
            playlist = self.playlists[station.id]

        self.player.set_state(gst.STATE_NULL)

        # Fill the playlist.
        if not playlist:
            playlist = station.get_playlist()

        # Play the next song in the playlist.
        if station == self.station:
            self.song = playlist.pop(0)
            self.player.set_property("uri", self.song.audioUrl)
            self.play()

            print "> '%s' by '%s' from '%s'" % (self.song.title,
                                                self.song.artist,
                                                self.song.album)

        self.playlists[station.id] = playlist

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

class Controller:
    def __init__(self, pyccolo):
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(PIN_CCW, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        self.ccw = False

        GPIO.setup(PIN_CW, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        self.cw = False

        GPIO.setup(PIN_CLICK, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        self.click_time = None

    def detect_events(self):
        """Process user interface events."""

        # Counterclockwise rotation.
        new_ccw = GPIO.input(PIN_CCW)
        if new_ccw and not self.ccw:
            pyccolo.tune_station(-1)
        self.ccw = new_ccw

        # Clockwise rotation.
        new_cw = GPIO.input(PIN_CW)
        if new_cw and not self.cw:
            pyccolo.tune_station(1)
        self.cw = new_cw

        # Button pressed.
        new_click = GPIO.input(PIN_CLICK)
        if new_click and not self.click_time:
            self.click_time = time.time()

        # Button release.
        if not new_click and self.click_time:
            click_duration = time.time() - self.click_time
            self.click_time = None

            if pyccolo.is_playing():
                pyccolo.pause()
            else:
                pyccolo.play()

        return True

def has_network():
    """Determine if the Pandora website can be reached."""

    try:
        response = urllib2.urlopen("http://pandora.com")
        return True
    except urllib2.URLError as err:
        pass
    return False

if __name__ == "__main__":
    gobject.type_register(Display)

    display = Display()
    display.show_all()

    while not has_network():
        time.sleep(1);

    pyccolo = Pyccolo(display)
    controller = Controller(pyccolo)

    # Start main loop in a separate thread.
    gtk.gdk.threads_init()
    g_loop = threading.Thread(target=gtk.main)
    g_loop.daemon = True
    g_loop.start()

    while controller.detect_events():
        pass
