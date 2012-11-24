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

from pandora import Pandora
import pygst
pygst.require('0.10')
import gst
import threading

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import cairo

import RPi.GPIO as GPIO
import ConfigParser
import time
import urllib2

CONF_FILE = '/etc/pyccolo/pyccolo.conf'
PIN_A = 24
PIN_B = 25
PIN_C = 23

ALBUM_ART_SIZE = 192

# __        ___           _
# \ \      / (_)_ __   __| | _____      __
#  \ \ /\ / /| | '_ \ / _` |/ _ \ \ /\ / /
#   \ V  V / | | | | | (_| | (_) \ V  V /
#    \_/\_/  |_|_| |_|\__,_|\___/ \_/\_/
#

class Window(gtk.Window):
    def __init__(self):
        """Initialize graphics."""

        gtk.Window.__init__(self)

    def do_realize(self):
        """Initialize a place to draw the GUI."""

        self.set_flags(self.flags() | gtk.REALIZED)
        self.connect('delete-event', gtk.main_quit)

        self.window = gtk.gdk.Window(
            self.get_parent_window(),
            width=self.get_screen().get_width(),
            height=self.get_screen().get_height(),
            window_type=gtk.gdk.WINDOW_TOPLEVEL,
            wclass=gtk.gdk.INPUT_OUTPUT,
            event_mask=self.get_events() | gtk.gdk.EXPOSURE_MASK
        )

        (x, y, w, h, depth) = self.window.get_geometry()
        self.size_allocate(gtk.gdk.Rectangle(x=x, y=y, width=w, height=h))
        self.set_default_size(w, h)

        self.style.attach(self.window)
        self.window.set_user_data(self)

#  ____  _           _
# |  _ \(_)___ _ __ | | __ _ _   _
# | | | | / __| '_ \| |/ _` | | | |
# | |_| | \__ \ |_) | | (_| | |_| |
# |____/|_|___/ .__/|_|\__,_|\__, |
#             |_|            |___/

class Display(gtk.DrawingArea):
    def __init__(self):
        """Initialize graphical user interface."""

        gtk.DrawingArea.__init__(self)

        self.mode = None
        self.stations = []
        self.station = None
        self.artist = ''
        self.album = ''
        self.track = ''
        self.art_url = ''
        self.art = None
        self.playing = False

        self.bg = None
        try:
            self.bg = gtk.gdk.pixbuf_new_from_file('/opt/pyccolo/background.png')
        except:
            pass

        # Create a container window.
        window = Window()
        window.add(self)
        window.show_all()

        self.connect('expose-event', self.expose)

    def expose(self, widget, event):
        cr = widget.window.cairo_create()
        w = self.allocation.width
        h = self.allocation.height

        cr.set_source_rgb(0, 0, 0)
        cr.paint()

        if self.bg:
            widget.window.draw_pixbuf(None, self.bg, src_x=0, src_y=0,
                                      dest_x=0, dest_y=0)

        if not self.playing:
            self.draw_text(cr, 360, 100, 'PAUSED', 28, align=0)

        if self.mode == Controller.MODE_STATION:
            self.draw_text(cr, 360, 425, '<- Station ->', 20, align=0)

        if self.station:
            station = self.stations[self.station]
            self.draw_text(cr, 360, 385, station, 24, align=0)

        if self.track:
            self.draw_text(cr, 360, 80, self.track, 28, align=0)
            self.draw_text(cr, 340, 175, 'by', 14, align=-1)
            self.draw_text(cr, 350, 175, self.artist, 20,
                           weight=cairo.FONT_WEIGHT_BOLD)
            self.draw_text(cr, 340, 225, 'from', 14, align=-1)
            self.draw_text(cr, 350, 225, self.album, 18)

        if self.art:
            widget.window.draw_pixbuf(None, self.art, src_x=0, src_y=0,
                                      dest_x=75, dest_y=125)

    def draw_text(self, cr, x, y, text, size, r=1, g=1, b=1, a=1,
                  face='Ubuntu', align=1,
                  slant=cairo.FONT_SLANT_NORMAL,
                  weight=cairo.FONT_WEIGHT_NORMAL):
        cr.save()
        cr.select_font_face(face, slant, weight)
        cr.set_font_size(size)
        cr.set_source_rgba(r, g, b, a)
        if align == 0:
            x = x - cr.text_extents(text)[2] / 2
        elif align == -1:
            x = x - cr.text_extents(text)[2]
        cr.move_to(x, y)
        cr.text_path(text)
        cr.clip()
        cr.paint()
        cr.restore()

    def load_art(self):
        self.art = None

        art_url = self.art_url

        content = urllib2.urlopen(art_url).read()
        loader = gtk.gdk.PixbufLoader()
        loader.set_size(ALBUM_ART_SIZE, ALBUM_ART_SIZE)
        loader.write(content)
        loader.close()

        if self.art_url == art_url:
            self.art = loader.get_pixbuf()
        self.queue_draw()

    def change_mode(self, controller, mode):
        """Change the current user interface control mode."""

        self.mode = mode
        self.queue_draw()

    def change_station(self, music, station, stations):
        """Change the station list that is displayed."""

        self.stations = stations
        self.station = station
        self.queue_draw()

    def change_song(self, music, artist, album, track, art):
        """Change the song name that is displayed."""

        self.artist = artist
        self.album = album
        self.track = track
        self.art_url = art
        threading.Thread(target=self.load_art).start()
        self.queue_draw()

    def change_state(self, music, state):
        """Change the playing state that is displayed."""

        self.playing = state
        self.queue_draw()

#  __  __           _
# |  \/  |_   _ ___(_) ___
# | |\/| | | | / __| |/ __|
# | |  | | |_| \__ \ | (__
# |_|  |_|\__,_|___/_|\___|
#

class Music(gobject.GObject):
    __gsignals__ = {
        'station-changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                            (gobject.TYPE_STRING, gobject.TYPE_PYOBJECT,)),
        'song-changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                         (gobject.TYPE_STRING, gobject.TYPE_STRING,
                          gobject.TYPE_STRING, gobject.TYPE_STRING,)),
        'state-changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                          (gobject.TYPE_BOOLEAN,)),
        }

    def __init__(self):
        """Initialize and play Pandora radio stations."""

        gobject.GObject.__init__(self)

        self.station = None
        self.playlists = dict()
        self.song = None
        self.playing = False
        self.timer = None

        # Initialize Pandora.
        self.pandora = Pandora()

        # Initialize Gstreamer.
        self.player = gst.element_factory_make('playbin2', 'player')
        self.player.props.flags |= 0x80 # GST_PLAY_FLAG_DOWNLOAD (progressive download)
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect('message::eos', self.on_gst_eos)
        bus.connect('message::error', self.on_gst_error)

    def init(self, username=None, password=None):
        self.config = ConfigParser.ConfigParser()
        self.config.read(CONF_FILE)

        if not username or not password:
            # Read in configuration details.
            try:
                username = self.config.get('User', 'username')
                password = self.config.get('User', 'password')
            except:
                print 'Failed to load username and password from configuration file.'
                exit(1)

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

        # Change the station and the song.
        self.station = self.pandora.get_station_by_id(station_id)

        # Trigger next song.
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(0.25, self.next_song)
        self.timer.start()

        # Save the new station into the configuration file.
        try:
            if not self.config.has_section('Station'):
                self.config.add_section('Station')
            self.config.set('Station', 'station_id', station_id)
            with open(CONF_FILE, 'wb') as config:
                self.config.write(config)
        except:
            pass

        stations = {}
        for station in self.pandora.stations:
            stations[station.id] = station.name
        self.emit('station-changed', station_id, stations)

        return True

    def play(self):
        """Play the currently paused music track."""

        self.player.set_state(gst.STATE_PLAYING)
        if not self.playing:
            self.playing = True
            self.emit('state-changed', self.playing)

        return True

    def pause(self):
        """Pause the currently playing music track."""

        if self.playing:
            self.player.set_state(gst.STATE_PAUSED)
            self.playing = False
            self.emit('state-changed', self.playing)
        return True

    def tune_station(self, controller, delta):
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

    def play_pause(self, controller):
        """Toggle between playing and paused."""

        if self.playing:
            self.pause()
        else:
            self.play()

    def next_song(self, controller=None):
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
            self.player.set_property('uri', self.song.audioUrl)
            self.play()

            self.emit('song-changed', self.song.artist, self.song.album,
                      self.song.title, self.song.artRadio)

        self.playlists[station.id] = playlist

        return True

    def on_gst_eos(self, bus, message):
        """Begin the next track after the current track has completed."""

        self.next_song()

    def on_gst_error(self, bus, message):
        """Report Gstreamer errors."""

        self.playing = False
        err, debug = message.parse_error()
        print 'Gstreamer Error: %s, %s, %s' % (err, debug, err.code)
        self.next_song()

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

    def __init__(self):
        """Setup GPIO pins for input."""

        gobject.GObject.__init__(self)

        self.mode = Controller.MODE_STATION
        self.click_time = None

        self.ccw_step = 0
        self.cw_step = 0
        self.clockwise = ((False, True),
                          (False, False),
                          (True, False),
                          (True, True))

    def main(self):
        """Process user interface events."""

        self.emit('change-mode', self.mode)

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PIN_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(PIN_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        while True:
            new_a = GPIO.input(PIN_A)
            new_b = GPIO.input(PIN_B)

            if self.clockwise[self.cw_step] == (new_a, new_b):
                self.cw_step = self.cw_step + 1
                if self.cw_step == 4:
                    self.cw_step = self.ccw_step = 0
                    self.emit('station-up')

            if self.clockwise[3 - self.ccw_step] == (new_a, new_b):
                self.ccw_step = self.ccw_step + 1
                if self.ccw_step == 4:
                    self.cw_step = self.ccw_step = 0
                    self.emit('station-down')

            ## Button pressed.
            ## TODO: needs work
            #new_click = GPIO.input(PIN_CLICK)
            #if new_click:
            #    if not self.click_time:
            #        self.click_time = time.time()
            #    click_duration = time.time() - self.click_time
            #    if click_duration > 1:
            #        self.emit('next-song')
            ## Button released.
            #elif not new_click and self.click_time:
            #    click_duration = time.time() - self.click_time
            #    if self.click_time < 1:
            #        self.emit('play-pause')
            #    self.click_time = None

gobject.type_register(Window)
gobject.type_register(Display)
gobject.type_register(Controller)
gobject.type_register(Music)

if __name__ == '__main__':
    display = Display()
    controller = Controller()
    music = Music()

    # Connect signals between components.
    controller.connect('change-mode', display.change_mode)
    controller.connect('station-up', music.tune_station, 1)
    controller.connect('station-down', music.tune_station, -1)
    controller.connect('play-pause', music.play_pause)
    controller.connect('next-song', music.next_song)
    music.connect('station-changed', display.change_station)
    music.connect('song-changed', display.change_song)
    music.connect('state-changed', display.change_state)

    while not music.init():
        time.sleep(1);

    # Start controller in its own thread.
    threading.Thread(target=controller.main).start()
    gtk.gdk.threads_init()

    gtk.main()
