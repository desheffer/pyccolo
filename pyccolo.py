#!/usr/bin/python2

import os
import sys
import tty
import termios
import gtk
import gobject
import gst
import dbus
import time
import ConfigParser
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
        self.pandora.get_stations()
        return self.pandora.stations

    def set_station(self, station_id):
        self.station = self.pandora.get_station_by_id(station_id)
        self.playlist = None
        self.next_song()

    def is_playing(self):
        return self.playing

    def play(self):
        self.player.set_state(gst.STATE_PLAYING)
        self.playing = True

    def pause(self):
        self.player.set_state(gst.STATE_PAUSED)
        self.playing = False

    def next_song(self):
        self.player.set_state(gst.STATE_NULL)
        if not self.playlist:
            self.playlist = self.station.get_playlist()
        self.song = self.playlist.pop(0)
        self.player.set_property("uri", self.song.audioUrl)
        print "'%s' by '%s' from '%s'" % (self.song.title,
                                          self.song.artist,
                                          self.song.album)
        self.play()

    def on_gst_eos(self, bus, message):
        self.next_song()

    def on_gst_buffering(self, bus, message):
        #percent = message.parse_buffering()
        pass

    def on_gst_error(self, bus, message):
        err, debug = message.parse_error()
        print "Gstreamer error: %s, %s, %s" % (err, debug, err.code)
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

if __name__ == "__main__":
    cp = ConfigParser.ConfigParser()
    cp.read(os.path.expanduser("~/.config/pyccolo.ini"))

    try:
        username = cp.get('User', 'username')
        password = cp.get('User', 'password')
    except:
        print "Failed to load username and password from configuration file."
        exit(1)

    pyccolo = Pyccolo(username, password)
    stations = pyccolo.get_stations()
    pyccolo.set_station(stations[0].id)

    gtk.gdk.threads_init()
    while gtk.main_iteration(False):
        ch = read_char()
        if ch == 'q':
            exit(0)
        elif ch == 'n':
            pyccolo.next_song()
