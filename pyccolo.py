#!/usr/bin/env python

import os
import sys
import time
import tty
import termios
import gst
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

    def main_iteration(self):
        bus = self.player.get_bus()
        if bus.have_pending():
            bus.pop() #TODO

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

    while True:
        pyccolo.main_iteration()
        time.sleep(0.1)
