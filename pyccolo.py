#!/usr/bin/python3

import os
import configparser
from pandora import *
import gst
import time

class Pyccolo:

    def __init__(self, username, password):
        self.station = None
        self.playlist = None
        self.song = None

        # Initialize Gstreamer.
        self.player = gst.element_factory_make("playbin2", "player")
        self.player.props.flags |= 0x80 # GST_PLAY_FLAG_DOWNLOAD (progressive download)

        # Initialize Pandora.
        self.pandora = Pandora()
        self.pandora.connect(username, password)

    def get_stations(self):
        self.pandora.get_stations()
        return self.pandora.stations

    def get_current_station(self):
        return self.station

    def set_station(self, station_id):
        self.station = self.pandora.get_station_by_id(station_id)
        self.playlist = self.station.get_playlist()
        self.pause()

    def get_current_song(self):
        return self.song

    def is_playing(self):
        state = self.player.get_state()
        return state
        #return state[1] == gst.STATE_PLAYING

    def play(self):
        self.song = self.playlist[0]
        self.player.set_property("uri", self.song.audioUrl)
        self.player.set_state(gst.STATE_PLAYING)

    def pause(self):
        if self.is_playing():
            self.player.set_state(gst.STATE_PAUSED)

if __name__ == "__main__":
    cp = ConfigParser.ConfigParser()
    cp.read(os.path.expanduser("~/.config/pyccolo.ini"))

    try:
        username = cp.get('User', 'username')
        password = cp.get('User', 'password')
    except:
        print("Failed to load username and password from configuration file.")
        exit(1)

    pyccolo = Pyccolo(username, password)
    stations = pyccolo.get_stations()
    pyccolo.set_station(stations[0].id)
    pyccolo.play()

    while True:
        print("%s - %s by %s", pyccolo.is_playing(),
                               pyccolo.get_current_song().title,
                               pyccolo.get_current_song().artist)
        time.sleep(0.1)
