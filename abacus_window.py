# -*- coding: utf-8 -*-
#Copyright (c) 2010, Walter Bender

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

from constants import *

import pygtk
pygtk.require('2.0')
import gtk
from gettext import gettext as _
from math import pow
import os

try:
    from sugar.graphics import style
    GRID_CELL_SIZE = style.GRID_CELL_SIZE
except:
    GRID_CELL_SIZE = 0

from sprites import *

def load_image(path, name, w, h):
    """ create a pixbuf from a SVG stored in a file """
    return gtk.gdk.pixbuf_new_from_file_at_size(
        os.path.join(path+name+'.svg'), int(w), int(h))

class Abacus():

    def __init__(self, canvas, path, parent=None):
        """ Abacus class """
        self.path = path
        self.activity = parent

        if parent is None:        # Starting from command line
            self.sugar = False
            self.canvas = canvas
        else:                     # Starting from Sugar
            self.sugar = True
            self.canvas = canvas
            parent.show_all()

        self.canvas.set_flags(gtk.CAN_FOCUS)
        self.canvas.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.canvas.add_events(gtk.gdk.BUTTON_RELEASE_MASK)
        self.canvas.add_events(gtk.gdk.POINTER_MOTION_MASK)
        self.canvas.connect("expose-event", self._expose_cb)
        self.canvas.connect("button-press-event", self._button_press_cb)
        self.canvas.connect("button-release-event", self._button_release_cb)
        self.canvas.connect("motion-notify-event", self._mouse_move_cb)
        self.width = gtk.gdk.screen_width()
        self.height = gtk.gdk.screen_height()-GRID_CELL_SIZE
        self.sprites = Sprites(self.canvas)
        self.scale = gtk.gdk.screen_height()/900.0
        self.dragpos = 0
        self.press = None

        self.chinese = Suanpan(self)
        self.japanese = Soroban(self)
        self.russian = Schety(self)
        self.mayan = Nepohualtzintzin(self)

        self.chinese.show()
        self.japanese.hide()
        self.russian.hide()
        self.mayan.hide()
        self.mode = self.chinese

    def _button_press_cb(self, win, event):
        win.grab_focus()
        x, y = map(int, event.get_coords())
        self.dragpos = y
        self.press = self.sprites.find_sprite((x,y))
        if self.press is not None and self.press.type != 'bead':
            self.press = None
        return True

    def _mouse_move_cb(self, win, event):
        if self.press is None:
            self.dragpos = 0
            return True
        win.grab_focus()
        x, y = map(int, event.get_coords())
        dy = y-self.dragpos
        self.mode.move_bead(self.press, dy)

    def _button_release_cb(self, win, event):
        if self.press == None:
            return True
        self.press = None
        self.mode.label(self.mode.value())
        return True

    def _expose_cb(self, win, event):
        self.sprites.redraw_sprites()
        return True

    def _destroy_cb(self, win, event):
        gtk.main_quit()


class AbacusGeneric():

    def __init__(self, abacus):
        """ Specify parameters that define the abacus """
        self.abacus = abacus
        self.name = 'suanpan'
        self.num_rods = 15
        self.bot_beads = 2
        self.top_beads = 5
        self.frame_width = 810
        self.frame_height = 420
        self.create()

    def create(self):
        """ Create an abacus. """
        h = (self.bot_beads+2+1+self.top_beads+2)*BHEIGHT*self.abacus.scale
        w = (self.num_rods+1)*(BWIDTH+BOFFSET)*self.abacus.scale
        dy = (self.top_beads+2)*BHEIGHT*self.abacus.scale
        x = (self.abacus.width-w)/2
        y = (self.abacus.height-h)/2
        o =  (BWIDTH+BOFFSET-5)*self.abacus.scale/2

        # Draw the frame...
        self.frame = Sprite(self.abacus.sprites, x-BHEIGHT*self.abacus.scale,
                            y-BHEIGHT*self.abacus.scale,
                            load_image(self.abacus.path, self.name+"_frame",
                            self.frame_width*self.abacus.scale,
                            self.frame_height*self.abacus.scale))
        self.frame.type = 'frame'

        # then draw the rods...
        self.rods = []
        dx = (BWIDTH+BOFFSET)*self.abacus.scale
        for i in range(self.num_rods):
            self.rods.append(Sprite(self.abacus.sprites, x+i*dx+o, y,
                                    load_image(self.abacus.path,
                                               self.name+"_rod",
                                               10*self.abacus.scale, h)))

        for i in self.rods:
             i.type = 'rod'

        # and then the beads.
        self.beads = []
        o =  (BWIDTH-BOFFSET)/2*self.abacus.scale/2
        for i in range(self.num_rods):
            for b in range(self.top_beads):
                self.beads.append(Sprite(self.abacus.sprites, x+i*dx+o,
                                         y+b*BHEIGHT*self.abacus.scale,
                                         load_image(self.abacus.path, "white",
                                                    BWIDTH*self.abacus.scale,
                                                    BHEIGHT*self.abacus.scale)))
            for b in range(self.bot_beads):
                self.beads.append(Sprite(self.abacus.sprites, x+i*dx+o,
                                         y+(self.top_beads+5+b)*BHEIGHT\
                                            *self.abacus.scale,
                                         load_image(self.abacus.path, "white",
                                                    BWIDTH*self.abacus.scale,
                                                    BHEIGHT*self.abacus.scale)))

        for i in self.beads:
             i.type = 'bead'
             i.state = 0

        # Draw the dividing bar on top.
        self.bar = Sprite(self.abacus.sprites, x, y+dy,
                          load_image(self.abacus.path, "divider_bar",
                                     w, BHEIGHT*self.abacus.scale))

        self.bar.type = 'frame'
        self.bar.set_label_color('white')

    def hide(self):
        """ Hide the rod, beads and frame. """
        for i in self.rods:
            i.hide()
        for i in self.beads:
            i.hide()
        self.bar.hide()
        self.frame.hide()

    def show(self):
        """ Show the rod, beads and frame. """
        self.frame.set_layer(99)
        for i in self.rods:
            i.set_layer(100)
        for i in self.beads:
            i.set_layer(101)
        self.bar.set_layer(102)

    def value(self):
        """ Return a string representing the value of each rod. """
        string = ''
        v = []
        for r in range(self.num_rods+1): # +1 for overflow
            v.append(0)

        # Tally the values on each rod.
        for i, b in enumerate(self.beads):
            r = i/(self.top_beads+self.bot_beads)
            j = i%(self.top_beads+self.bot_beads)
            if b.state == 1:
                if j < self.top_beads:
                    v[r+1] += 5
                else:
                    v[r+1] += 1

        # Carry to the left if a rod has a value > 9.
        for j in range(self.num_rods):
            if v[len(v)-j-1] > 9:
                v[len(v)-j-1] -= 10
                v[len(v)-j-2] += 1

        # Convert values to a string.
        for j in v:
            if string != '' or j > 0:
                string += str(j)
        return(string)

    def label(self, string):
        """ Label the crossbar with the string. (Used with self.value) """
        self.bar.set_label(string)

    def move_bead(self, bead, dy):
         """ Move a bead (or beads) up or down a rod. """
         i = self.beads.index(bead)
         b = i%(self.top_beads+self.bot_beads)

         if b < self.top_beads:
             if dy > 0 and bead.state == 0:
                 bead.move_relative((0, 2*BHEIGHT*self.abacus.scale))
                 bead.state = 1
                 # Make sure beads below this bead are also moved.
                 for ii in range(self.top_beads-b):
                     if self.beads[i+ii].state == 0:
                         self.beads[i+ii].move_relative((0,
                                                   2*BHEIGHT*self.abacus.scale))
                         self.beads[i+ii].state = 1
             elif dy < 0 and bead.state == 1:
                 bead.move_relative((0, -2*BHEIGHT*self.abacus.scale))
                 bead.state = 0
                 # Make sure beads above this bead are also moved.
                 for ii in range(b+1):
                     if self.beads[i-ii].state == 1:
                         self.beads[i-ii].move_relative((0,
                                                  -2*BHEIGHT*self.abacus.scale))
                         self.beads[i-ii].state = 0
         else:
             if dy < 0 and bead.state == 0:
                 bead.move_relative((0, -2*BHEIGHT*self.abacus.scale))
                 bead.state = 1
                 # Make sure beads above this bead are also moved.
                 for ii in range(b-self.top_beads+1):
                     if self.beads[i-ii].state == 0:
                         self.beads[i-ii].move_relative((0,
                                                  -2*BHEIGHT*self.abacus.scale))
                         self.beads[i-ii].state = 1
             elif dy > 0 and bead.state == 1:
                 bead.move_relative((0, 2*BHEIGHT*self.abacus.scale))
                 bead.state = 0
                 # Make sure beads below this bead are also moved.
                 for ii in range(self.top_beads+self.bot_beads-b):
                     if self.beads[i+ii].state == 1:
                         self.beads[i+ii].move_relative((0,
                                                   2*BHEIGHT*self.abacus.scale))
                         self.beads[i+ii].state = 0


class Nepohualtzintzin(AbacusGeneric):

    def __init__(self, abacus):
        """ Specify parameters that define the abacus """
        self.abacus = abacus
        self.name = 'nepohualtzintzin'
        self.num_rods = 13
        self.bot_beads = 4
        self.top_beads = 3
        self.frame_width = 730
        self.frame_height = 420
        self.create()

    def value(self):
        """ Override default: base 20 """
        string = ''
        v = []
        for r in range(self.num_rods+1): # +1 for overflow
            v.append(0)

        # Tally the values on each rod.
        for i, b in enumerate(self.beads):
            r = i/(self.top_beads+self.bot_beads)
            j = i%(self.top_beads+self.bot_beads)
            if b.state == 1:
                if j < self.top_beads:
                    v[r+1] += 5*pow(2,self.num_rods-r-1)
                else:
                    v[r+1] += 1*pow(2,self.num_rods-r-1)

        # Carry to the left if a rod has a value > 9.
        for j in range(self.num_rods):
            if v[len(v)-j-1] > 9:
                units = v[len(v)-j-1]%10
                tens = v[len(v)-j-1]-units
                v[len(v)-j-1] = units
                v[len(v)-j-2] += tens/10

        # Convert values to a string.
        for j in v:
            if string != '' or j > 0:
                string += str(int(j))
        return(string)


class Suanpan(AbacusGeneric):

    def __init__(self, abacus):
        """ Create a Chinese abacus: 15 by (5,2). """
        self.abacus = abacus
        self.name = "suanpan"
        self.num_rods = 15
        self.bot_beads = 5
        self.top_beads = 2
        self.frame_width = 810
        self.frame_height = 420
        self.create()


class Soroban(AbacusGeneric):

    def __init__(self, abacus):
        """ create a Japanese abacus: 15 by (4,1) """
        self.abacus = abacus
        self.name = "soroban"
        self.num_rods = 15
        self.bot_beads = 4
        self.top_beads = 1
        self.frame_width = 810
        self.frame_height = 360
        self.create()


class Schety(AbacusGeneric):

    def __init__(self, abacus):
        """ Create a Russian abacus: 15 by 10 (with one rod of 4 beads). """
        self.abacus = abacus
        self.name = "schety"
        self.num_rods = 15
        self.top_beads = 0
        self.bot_beads = 10
        self.frame_width = 810
        self.frame_height = 420
        self.create()

    def create(self):
        """ Override default in order to make a short rod """
        # 10 beads + 2 spaces
        h = (self.bot_beads+2)*BHEIGHT*self.abacus.scale
        w = (self.num_rods+1)*(BWIDTH+BOFFSET)*self.abacus.scale
        x = (self.abacus.width-w)/2
        y = (self.abacus.height-h)/2

        # Draw the frame.
        self.frame = Sprite(self.abacus.sprites, x-BHEIGHT*self.abacus.scale,
                            y-BHEIGHT*self.abacus.scale,
                            load_image(self.abacus.path, self.name+"_frame",
                            self.frame_width*self.abacus.scale,
                            self.frame_height*self.abacus.scale))
        self.frame.type = 'frame'

        # Draw the rods...
        self.rods = []
        o =  (BWIDTH+BOFFSET-5)*self.abacus.scale/2
        dx = (BWIDTH+BOFFSET)*self.abacus.scale
        for i in range(self.num_rods):
            self.rods.append(Sprite(self.abacus.sprites, x+i*dx+o, y,
                                    load_image(self.abacus.path,
                                               self.name+"_rod",
                                               10, h)))

        for i in self.rods:
             i.type = 'rod'

        # and then the beads.
        self.beads = []
        o =  (BWIDTH-BOFFSET)/2*self.abacus.scale/2
        for i in range(self.num_rods):
            if i == 10:
                for b in range(4):
                    if b in [1,2]:
                        color = 'black'
                    else:
                        color = 'white'
                    self.beads.append(Sprite(self.abacus.sprites, x+i*dx+o,
                                         y+(8+b)*BHEIGHT*self.abacus.scale,
                                         load_image(self.abacus.path, color,
                                                    BWIDTH*self.abacus.scale,
                                                    BHEIGHT*self.abacus.scale)))
            else:
                for b in range(self.bot_beads):
                    if b in [4,5]:
                        color = 'black'
                    else:
                        color = 'white'
                    self.beads.append(Sprite(self.abacus.sprites, x+i*dx+o,
                                         y+(2+b)*BHEIGHT*self.abacus.scale,
                                         load_image(self.abacus.path, color,
                                                    BWIDTH*self.abacus.scale,
                                                    BHEIGHT*self.abacus.scale)))

        for i in self.beads:
             i.type = 'bead'
             i.state = 0

        # Draw a bar for the label on top.
        self.bar = Sprite(self.abacus.sprites, x, y-BHEIGHT*self.abacus.scale,
                          load_image(self.abacus.path, "divider_bar",
                                     w, BHEIGHT*self.abacus.scale))

        self.bar.type = 'frame'
        self.bar.set_label_color('white')

    def value(self):
        """ Override to account for fourths """
        string = ''
        v = []
        for r in range(self.num_rods+1): # +1 for overflow
            v.append(0)

        # Tally the values on each rod.
        for i, b in enumerate(self.beads):
            if i < 100:
                r = i/self.bot_beads
                if b.state == 1:
                    v[r+1] += 1
            # The 'short' rod
            elif i < 104:
                r = 10
                if b.state == 1:
                    v[r+1] += 2.5
            else:
                r = (i+6)/self.bot_beads
                if b.state == 1:
                    v[r+1] += 1

        # Carry to the left if a rod has a value > 9.
        # First, process the short rod;
        if v[11] == 10:
            v[10] += 1
        else:
            v[12] += int(v[11])
            v[13] += int(10*v[11]-10*int(v[11]))

        # then, check the rods to the right of the short rod;
        for j in range(4):
            if v[len(v)-j-1] > 9:
                v[len(v)-j-1] -= 10
                if j < 3:
                    v[len(v)-j-2] += 1
                else:
                    v[len(v)-j-3] += 1 # skip over the short rod

        # and finally, the rest of the rods.
        for j in range(6,16):
            if v[len(v)-j-1] > 9:
                v[len(v)-j-1] -= 10
                v[len(v)-j-2] += 1

        # Convert values to a string.
        for i, j in enumerate(v):
            if i == 11:
                string += '.'
            elif string != '' or j > 0:
                string += str(j)
        return(string)

    def move_bead(self, bead, dy):
         """ Override to account for short rod """
         i = self.beads.index(bead)
         r = i/self.bot_beads
         # Take into account the rod with just 4 beads
         if r < 10:
             o = 2
             b = i%self.bot_beads
             n = self.bot_beads
         elif i > 99 and i < 104:
             o = 8
             b = i%self.bot_beads
             n = 4
         else:
             o = 2
             b = (i+6)%self.bot_beads
             n = self.bot_beads
         if dy < 0 and bead.state == 0:
             bead.move_relative((0, -o*BHEIGHT*self.abacus.scale))
             bead.state = 1
             # Make sure beads above this bead are also moved.
             for ii in range(b+1):
                 if self.beads[i-ii].state == 0:
                     self.beads[i-ii].move_relative((0,
                                                  -o*BHEIGHT*self.abacus.scale))
                     self.beads[i-ii].state = 1
         elif dy > 0 and bead.state == 1:
             bead.move_relative((0, o*BHEIGHT*self.abacus.scale))
             bead.state = 0
             # Make sure beads below this bead are also moved.
             for ii in range(n-b):
                 if self.beads[i+ii].state == 1:
                     self.beads[i+ii].move_relative((0,
                                                   o*BHEIGHT*self.abacus.scale))
                     self.beads[i+ii].state = 0
