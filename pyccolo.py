#!/usr/bin/env python

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
        self.timer = None

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
        self.pandora.get_stations()
        return self.pandora.stations

    def set_station(self, station_id):
        self.station = self.pandora.get_station_by_id(station_id)
        self.playlist = None
        print "Station: %s" % self.station.name

        self.pause()
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(0.5, self.next_song)
        self.timer.start()

        return True

    def tune_station(self, delta):
        stations = self.pandora.stations
        if not stations:
            return False

        curr = stations.index(self.station) + delta
        if curr < 0:
            curr = len(stations) - 1
        elif curr >= len(stations):
            curr = 0

        return self.set_station(stations[curr].id)

    def is_playing(self):
        return self.playing

    def play(self):
        self.player.set_state(gst.STATE_PLAYING)
        self.playing = True
        return True

    def pause(self):
        self.player.set_state(gst.STATE_PAUSED)
        self.playing = False
        return True

    def next_song(self):
        if self.timer:
            self.timer.cancel()
        self.timer = None

        self.player.set_state(gst.STATE_NULL)
        if not self.playlist:
            self.playlist = self.station.get_playlist()
        self.song = self.playlist.pop(0)
        self.player.set_property("uri", self.song.audioUrl)
        self.play()

        print "'%s' by '%s' from '%s'" % (self.song.title,
                                          self.song.artist,
                                          self.song.album)

        return True

    def on_gst_eos(self, bus, message):
        self.next_song()

    def on_gst_buffering(self, bus, message):
        #percent = message.parse_buffering()
        pass

    def on_gst_error(self, bus, message):
        err, debug = message.parse_error()
        print "Gstreamer Error: %s, %s, %s" % (err, debug, err.code)
        self.playing = False
        self.next_song()

def read_char():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def has_network():
    try:
        response = urllib2.urlopen('http://pandora.com')
        return True
    except urllib2.URLError as err:
        pass
    return False

if __name__ == "__main__":
    cp = ConfigParser.ConfigParser()
    cp.read("/etc/pyccolo/pyccolo.conf")

    try:
        username = cp.get('User', 'username')
        password = cp.get('User', 'password')
    except:
        print "Failed to load username and password from configuration file."
        exit(1)

    # TODO: Something better?
    while has_network() == False:
        time.sleep(1);

    pyccolo = Pyccolo(username, password)
    stations = pyccolo.get_stations()
    pyccolo.set_station(stations[0].id)

    gobject.threads_init()
    g_loop = threading.Thread(target=gobject.MainLoop().run)
    g_loop.daemon = True
    g_loop.start()

    while True:
        ch = read_char()
        if ch == 'q':
            exit(0)
        elif ch == 'n':
            pyccolo.next_song()
        elif ch == 'u':
            pyccolo.tune_station(1)
        elif ch == 'd':
            pyccolo.tune_station(-1)
