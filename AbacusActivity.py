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

import pygtk
pygtk.require('2.0')
import gtk
import gobject

import sugar
from sugar.activity import activity
try: # 0.86+ toolbar widgets
    from sugar.bundle.activitybundle import ActivityBundle
    from sugar.activity.widgets import ActivityToolbarButton
    from sugar.activity.widgets import StopButton
    from sugar.graphics.toolbarbox import ToolbarBox
    from sugar.graphics.toolbarbox import ToolbarButton
    _new_sugar_system = True
except ImportError:
    _new_sugar_system = False
from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.menuitem import MenuItem
from sugar.graphics.icon import Icon
from sugar.datastore import datastore

from gettext import gettext as _
import locale

import logging
_logger = logging.getLogger("abacus-activity")

from abacus_window import Abacus, Custom

def button_factory(icon_name, tooltip, callback, toolbar):
    """Factory for making toolbar buttons"""
    my_button = ToolButton( icon_name )
    my_button.set_tooltip(tooltip)
    my_button.props.sensitive = True
    my_button.connect('clicked', callback)
    if hasattr(toolbar, 'insert'): # the main toolbar
        toolbar.insert(my_button, -1)
    else:  # or a secondary toolbar
        toolbar.props.page.insert(my_button, -1)
    my_button.show()
    return my_button

def label_factory(label, toolbar):
    """ Factory for adding a label to a toolbar """
    my_label = gtk.Label(label)
    my_label.set_line_wrap(True)
    my_label.show()
    _toolitem = gtk.ToolItem()
    _toolitem.add(my_label)
    toolbar.insert(_toolitem, -1)
    _toolitem.show()
    return my_label

def spin_factory(default, min, max, callback, toolbar):
    _spin_adj = gtk.Adjustment(default, min, max, 1, 32, 0)
    my_spin = gtk.SpinButton(_spin_adj, 0, 0)
    _spin_id = my_spin.connect('value-changed', callback)
    my_spin.set_numeric(True)
    my_spin.show()
    _toolitem = gtk.ToolItem()
    _toolitem.add(my_spin)
    toolbar.insert(_toolitem, -1)
    _toolitem.show()
    return my_spin

#
# Sugar activity
#
class AbacusActivity(activity.Activity):

    def __init__(self, handle):
        """ Initiate activity. """
        super(AbacusActivity,self).__init__(handle)

        if _new_sugar_system:
            # Use 0.86 toolbar design
            toolbar_box = ToolbarBox()

            # Buttons added to the Activity toolbar
            activity_button = ActivityToolbarButton(self)
            toolbar_box.toolbar.insert(activity_button, 0)
            activity_button.show()

            # Suanpan (Chinese abacus) 2:5
            self.chinese = button_factory('Con', _('Suanpan'), self._chinese_cb,
                                          toolbar_box.toolbar)

            # Decimal (decimal abacus) 0:10
            self.decimal = button_factory("Doff", _('Decimal'),
                                          self._decimal_cb, toolbar_box.toolbar)

            separator = gtk.SeparatorToolItem()
            separator.props.draw = False
            separator.set_expand(False)
            separator.show()
            toolbar_box.toolbar.insert(separator, -1)

            # The Abacus toolbar (all of the variations)
            abacus_toolbar = gtk.Toolbar()

            # Soroban (Japanese abacus) 1:4
            self.japanese = button_factory("Joff", _('Soroban'),
                                           self._japanese_cb, abacus_toolbar)

            # Schety (Russian abacus) 0:10
            self.russian = button_factory("Roff", _('Schety'),
                                          self._russian_cb, abacus_toolbar)

            # Nepohualtzintzin (Mayan abacus) 3:4 (base 20)
            self.mayan = button_factory("Moff", _('Nepohualtzintzin'),
                                        self._mayan_cb, abacus_toolbar)

            # Binary (base 2)
            self.binary = button_factory("Boff", _('Binary'), self._binary_cb,
                                         abacus_toolbar)

            # Hexadecimal (base 16)
            self.hex = button_factory("Hoff", _('Hexadecimal'), self._hex_cb,
                                      abacus_toolbar)

            # Fractions (1/2, 1/3, 1/4,...)
            self.fraction = button_factory("Foff", _('Fraction'),
                                           self._fraction_cb, abacus_toolbar)

            abacus_toolbar_button = ToolbarButton(
                    page=abacus_toolbar,
                    icon_name='list-add')
            abacus_toolbar.show()
            toolbar_box.toolbar.insert(abacus_toolbar_button, -1)
            abacus_toolbar_button.show()


            # The Customization submenu (roll your own)
            custom_toolbar = gtk.Toolbar()

            self._rods_label = label_factory(_("Rods:")+" ", custom_toolbar)
            self._rods_spin = spin_factory(15, 1, 20, self._rods_spin_cb,
                                           custom_toolbar)

            self._top_label = label_factory(_("Top:")+" ", custom_toolbar)
            self._top_spin = spin_factory(2, 0, 4, self._top_spin_cb,
                                           custom_toolbar)

            self._bottom_label = label_factory(_("Bottom:")+" ", custom_toolbar)
            self._bottom_spin = spin_factory(5, 1, 20, self._bottom_spin_cb,
                                           custom_toolbar)

            self._value_label = label_factory(_("Factor:")+" ", custom_toolbar)
            self._value_spin = spin_factory(5, 1, 20, self._value_spin_cb,
                                            custom_toolbar)

            self._base_label = label_factory(_("Base:")+" ", custom_toolbar)
            self._base_spin = spin_factory(10, 1, 24, self._base_spin_cb,
                                            custom_toolbar)


            # Custom
            self._custom = button_factory("new-game", _('Custom'),
                                           self._custom_cb, custom_toolbar)

            custom_toolbar_button = ToolbarButton(
                    page=custom_toolbar,
                    icon_name='view-source')
            custom_toolbar.show()
            toolbar_box.toolbar.insert(custom_toolbar_button, -1)
            custom_toolbar_button.show()

            separator = gtk.SeparatorToolItem()
            separator.props.draw = False
            separator.set_expand(True)
            separator.show()
            toolbar_box.toolbar.insert(separator, -1)

            # The ever-present Stop Button
            stop_button = StopButton(self)
            stop_button.props.accelerator = _('<Ctrl>Q')
            toolbar_box.toolbar.insert(stop_button, -1)
            stop_button.show()

            self.set_toolbar_box(toolbar_box)
            toolbar_box.show()

            # no sharing at the moment...
            # self.max_participants = 1

        else:
            # Use pre-0.86 toolbar design
            self.toolbox = activity.ActivityToolbox(self)
            self.set_toolbox(self.toolbox)

            self.projectToolbar = ProjectToolbar(self)
            self.toolbox.add_toolbar( _('Project'), self.projectToolbar )

            self.customToolbar = CustomToolbar(self)
            self.toolbox.add_toolbar( _('Custom'), self.customToolbar )

            self.toolbox.show()

            # no sharing at the moment...
            # try:
            #    self.toolbox.share.hide()
            # except:
            #    self.toolbox.props.visible = False

        # Create a canvas
        canvas = gtk.DrawingArea()
        canvas.set_size_request(gtk.gdk.screen_width(),
                                gtk.gdk.screen_height())
        self.set_canvas(canvas)
        canvas.show()
        self.show_all()

        # Initialize the canvas
        self.abacus = Abacus(canvas, self)

        # Read the current mode from the Journal
        try:
            self._rods_spin.set_value(int(self.metadata['rods']))
            self._top_spin.set_value(int(self.metadata['top']))
            self._bottom_spin.set_value(int(self.metadata['bottom']))
            self._value_spin.set_value(int(self.metadata['factor']))
            self._base_spin.set_value(int(self.metadata['base']))
        except:
            pass
        try:
            if self.metadata['abacus'] == 'suanpan':
                self._chinese_cb(None)
            elif self.metadata['abacus'] == 'soroban':
                self._japanese_cb(None)
            elif self.metadata['abacus'] == 'schety':
                self._russian_cb(None)
            elif self.metadata['abacus'] == 'nepohualtzintzin':
                self._mayan_cb(None)
            elif self.metadata['abacus'] == 'binary':
                self._binary_cb(None)
            elif self.metadata['abacus'] == 'hexadecimal':
                self._hex_cb(None)
            elif self.metadata['abacus'] == 'fraction':
                self._fraction_cb(None)
            elif self.metadata['abacus'] == 'decimal':
                self._decimal_cb(None)
            elif self.metadata['abacus'] == 'custom':
                self._custom_cb(None)
            else:
                self._chinese_cb(None)
        except:
            pass
        try:
            self.abacus.mode.set_value(self.metadata['value'])
            self.abacus.mode.label(self.abacus.mode.value())
        except:
            pass

    def _all_off(self):
        self.chinese.set_icon("Coff")
        self.japanese.set_icon("Joff")
        self.russian.set_icon("Roff")
        self.mayan.set_icon("Moff")
        self.binary.set_icon("Boff")
        self.hex.set_icon("Hoff")
        self.fraction.set_icon("Foff")
        self.decimal.set_icon("Doff")
        self.abacus.chinese.hide()
        self.abacus.japanese.hide()
        self.abacus.russian.hide()
        self.abacus.mayan.hide()
        self.abacus.binary.hide()
        self.abacus.hex.hide()
        self.abacus.fraction.hide()
        self.abacus.decimal.hide()
        if self.abacus.custom is not None:
            self.abacus.custom.hide()

    def _rods_spin_cb(self, button):
        return

    def _top_spin_cb(self, button):
        return

    def _bottom_spin_cb(self, button):
        return

    def _value_spin_cb(self, button):
        return

    def _base_spin_cb(self, button):
        return

    def _custom_cb(self, button):
        """ Display the custom abacus; hide the others """
        self._all_off()
        self.abacus.custom = Custom(self.abacus,
                             self._rods_spin.get_value_as_int(),
                             self._top_spin.get_value_as_int(),
                             self._bottom_spin.get_value_as_int(),
                             self._value_spin.get_value_as_int(),
                             self._base_spin.get_value_as_int())
        self.abacus.custom.show()
        self.abacus.mode = self.abacus.custom
        _logger.debug("Setting mode to %s" % (self.abacus.mode.name))

    def _chinese_cb(self, button):
        """ Display the suanpan; hide the others """
        self._all_off()
        self.chinese.set_icon("Con")
        self.abacus.chinese.show()
        self.abacus.mode = self.abacus.chinese
        _logger.debug("Setting mode to %s" % (self.abacus.mode.name))

    def _japanese_cb(self, button):
        """ Display the soroban; hide the others """
        self._all_off()
        self.japanese.set_icon("Jon")
        self.abacus.japanese.show()
        self.abacus.mode = self.abacus.japanese
        _logger.debug("Setting mode to %s" % (self.abacus.mode.name))

    def _russian_cb(self, button):
        """ Display the schety; hide the others """
        self._all_off()
        self.russian.set_icon("Ron")
        self.abacus.russian.show()
        self.abacus.mode = self.abacus.russian
        _logger.debug("Setting mode to %s" % (self.abacus.mode.name))

    def _mayan_cb(self, button):
        """ Display the nepohualtzintzin; hide the others """
        self._all_off()
        self.mayan.set_icon("Mon")
        self.abacus.mayan.show()
        self.abacus.mode = self.abacus.mayan
        _logger.debug("Setting mode to %s" % (self.abacus.mode.name))

    def _binary_cb(self, button):
        """ Display the binary; hide the others """
        self._all_off()
        self.binary.set_icon("Bon")
        self.abacus.binary.show()
        self.abacus.mode = self.abacus.binary
        _logger.debug("Setting mode to %s" % (self.abacus.mode.name))

    def _hex_cb(self, button):
        """ Display the hex; hide the others """
        self._all_off()
        self.hex.set_icon("Hon")
        self.abacus.hex.show()
        self.abacus.mode = self.abacus.hex
        _logger.debug("Setting mode to %s" % (self.abacus.mode.name))

    def _decimal_cb(self, button):
        """ Display the decimal; hide the others """
        self._all_off()
        self.decimal.set_icon("Don")
        self.abacus.decimal.show()
        self.abacus.mode = self.abacus.decimal
        _logger.debug("Setting mode to %s" % (self.abacus.mode.name))

    def _fraction_cb(self, button):
        """ Display the fraction; hide the others """
        self._all_off()
        self.fraction.set_icon("Fon")
        self.abacus.fraction.show()
        self.abacus.mode = self.abacus.fraction
        _logger.debug("Setting mode to %s" % (self.abacus.mode.name))

    def write_file(self, file_path):
        """ Write the bead positions to the Journal """
        _logger.debug("Saving current abacus to Journal: %s " % (
                       self.abacus.mode.name))
        try:
            self.metadata['abacus'] = self.abacus.mode.name
            self.metadata['value'] = self.abacus.mode.value(True)
            self.metadata['rods'] = str(self._rods_spin.get_value_as_int())
            self.metadata['top'] = str(self._top_spin.get_value_as_int())
            self.metadata['bottom'] = str(self._bottom_spin.get_value_as_int())
            self.metadata['factor'] = str(self._value_spin.get_value_as_int())
            self.metadata['base'] = str(self._base_spin.get_value_as_int())
        except:
            pass

#
# Custom toolbar for pre-0.86 toolbars
#
class CustomToolbar(gtk.Toolbar):

    def __init__(self, pc):
        """ Initiate 'old-style' toolbars."""
        gtk.Toolbar.__init__(self)
        self.activity = pc

        self._rods_label = gtk.Label(_("Rods:")+" ")
        self._rods_label.set_line_wrap(True)
        self._rods_label.show()
        self._rods_toolitem = gtk.ToolItem()
        self._rods_toolitem.add(self._rods_label)
        self.insert(self._rods_toolitem, -1)
        self._rods_toolitem.show()

        self._rods_spin_adj = gtk.Adjustment(15, 1, 20, 1, 32, 0)
        self.activity._rods_spin = gtk.SpinButton(self._rods_spin_adj, 0, 0)
        self._rods_spin_id = self.activity._rods_spin.connect('value-changed',
                                                    self.activity._rods_spin_cb)
        self.activity._rods_spin.set_numeric(True)
        self.activity._rods_spin.show()
        self.tool_item_rods = gtk.ToolItem()
        self.tool_item_rods.add(self.activity._rods_spin)
        self.insert(self.tool_item_rods, -1)
        self.tool_item_rods.show()

        self._top_label = gtk.Label(" "+_("Top:")+" ")
        self._top_label.set_line_wrap(True)
        self._top_label.show()
        self._top_toolitem = gtk.ToolItem()
        self._top_toolitem.add(self._top_label)
        self.insert(self._top_toolitem, -1)
        self._top_toolitem.show()

        self._top_spin_adj = gtk.Adjustment(2, 0, 4, 1, 32, 0)
        self.activity._top_spin = gtk.SpinButton(self._top_spin_adj, 0, 0)
        self._top_spin_id = self.activity._top_spin.connect('value-changed',
                                                     self.activity._top_spin_cb)
        self.activity._top_spin.set_numeric(True)
        self.activity._top_spin.show()
        self.tool_item_top = gtk.ToolItem()
        self.tool_item_top.add(self.activity._top_spin)
        self.insert(self.tool_item_top, -1)
        self.tool_item_top.show()

        self._bottom_label = gtk.Label(" "+_("Bottom:")+" ")
        self._bottom_label.set_line_wrap(True)
        self._bottom_label.show()
        self._bottom_toolitem = gtk.ToolItem()
        self._bottom_toolitem.add(self._bottom_label)
        self.insert(self._bottom_toolitem, -1)
        self._bottom_toolitem.show()

        self._bottom_spin_adj = gtk.Adjustment(5, 1, 15, 1, 32, 0)
        self.activity._bottom_spin = gtk.SpinButton(self._bottom_spin_adj, 0, 0)
        self._bottom_spin_id = self.activity._bottom_spin.connect(
                                 'value-changed', self.activity._bottom_spin_cb)
        self.activity._bottom_spin.set_numeric(True)
        self.activity._bottom_spin.show()
        self.tool_item_bottom = gtk.ToolItem()
        self.tool_item_bottom.add(self.activity._bottom_spin)
        self.insert(self.tool_item_bottom, -1)
        self.tool_item_bottom.show()

        self._value_label = gtk.Label(" "+_("Factor:")+" ")
        self._value_label.set_line_wrap(True)
        self._value_label.show()
        self._value_toolitem = gtk.ToolItem()
        self._value_toolitem.add(self._value_label)
        self.insert(self._value_toolitem, -1)
        self._value_toolitem.show()

        self._value_spin_adj = gtk.Adjustment(5, 1, 20, 1, 32, 0)
        self.activity._value_spin = gtk.SpinButton(self._value_spin_adj, 0, 0)
        self._value_spin_id = self.activity._value_spin.connect('value-changed',
                                                   self.activity._value_spin_cb)
        self.activity._value_spin.set_numeric(True)
        self.activity._value_spin.show()
        self.tool_item_value = gtk.ToolItem()
        self.tool_item_value.add(self.activity._value_spin)
        self.insert(self.tool_item_value, -1)
        self.tool_item_value.show()

        self._base_label = gtk.Label(" "+_("Base:")+" ")
        self._base_label.set_line_wrap(True)
        self._base_label.show()
        self._base_toolitem = gtk.ToolItem()
        self._base_toolitem.add(self._base_label)
        self.insert(self._base_toolitem, -1)
        self._base_toolitem.show()

        self._base_spin_adj = gtk.Adjustment(10, 1, 20, 1, 32, 0)
        self.activity._base_spin = gtk.SpinButton(self._base_spin_adj, 0, 0)
        self._base_spin_id = self.activity._base_spin.connect('value-changed',
                                                    self.activity._base_spin_cb)
        self.activity._base_spin.set_numeric(True)
        self.activity._base_spin.show()
        self.tool_item_base = gtk.ToolItem()
        self.tool_item_base.add(self.activity._base_spin)
        self.insert(self.tool_item_base, -1)
        self.tool_item_base.show()

        # Custom
        self.activity._custom = ToolButton( "new-game" )
        self.activity._custom.set_tooltip(_('Custom'))
        self.activity._custom.props.sensitive = True
        self.activity._custom.connect('clicked', self.activity._custom_cb)
        self.insert(self.activity._custom, -1)
        self.activity._custom.show()

#
# Project toolbar for pre-0.86 toolbars
#
class ProjectToolbar(gtk.Toolbar):

    def __init__(self, pc):
        """ Initiate 'old-style' toolbars."""
        gtk.Toolbar.__init__(self)
        self.activity = pc

        # Chinese style
        self.activity.chinese = ToolButton( "Con" )
        self.activity.chinese.set_tooltip(_('Saunpan'))
        self.activity.chinese.props.sensitive = True
        self.activity.chinese.connect('clicked', self.activity._chinese_cb)
        self.insert(self.activity.chinese, -1)
        self.activity.chinese.show()

        # Japanese style
        self.activity.japanese = ToolButton( "Joff" )
        self.activity.japanese.set_tooltip(_('Soroban'))
        self.activity.japanese.props.sensitive = True
        self.activity.japanese.connect('clicked', self.activity._japanese_cb)
        self.insert(self.activity.japanese, -1)
        self.activity.japanese.show()

        # Russian style
        self.activity.russian = ToolButton( "Roff" )
        self.activity.russian.set_tooltip(_('Schety'))
        self.activity.russian.props.sensitive = True
        self.activity.russian.connect('clicked', self.activity._russian_cb)
        self.insert(self.activity.russian, -1)
        self.activity.russian.show()

        # Mayan style
        self.activity.mayan = ToolButton( "Moff" )
        self.activity.mayan.set_tooltip(_('Nepohualtzintzin'))
        self.activity.mayan.props.sensitive = True
        self.activity.mayan.connect('clicked', self.activity._mayan_cb)
        self.insert(self.activity.mayan, -1)
        self.activity.mayan.show()

        # Binary style
        self.activity.binary = ToolButton( "Boff" )
        self.activity.binary.set_tooltip(_('Binary'))
        self.activity.binary.props.sensitive = True
        self.activity.binary.connect('clicked', self.activity._binary_cb)
        self.insert(self.activity.binary, -1)
        self.activity.binary.show()

        # Hexadecimal style
        self.activity.hex = ToolButton( "Hoff" )
        self.activity.hex.set_tooltip(_('Hexadecimal'))
        self.activity.hex.props.sensitive = True
        self.activity.hex.connect('clicked', self.activity._hex_cb)
        self.insert(self.activity.hex, -1)
        self.activity.hex.show()

        # decimal style
        self.activity.decimal = ToolButton( "Doff" )
        self.activity.decimal.set_tooltip(_('Decimal'))
        self.activity.decimal.props.sensitive = True
        self.activity.decimal.connect('clicked', self.activity._decimal_cb)
        self.insert(self.activity.decimal, -1)
        self.activity.decimal.show()

        # Fraction style
        self.activity.fraction = ToolButton( "Foff" )
        self.activity.fraction.set_tooltip(_('Fraction'))
        self.activity.fraction.props.sensitive = True
        self.activity.fraction.connect('clicked', self.activity._fraction_cb)
        self.insert(self.activity.fraction, -1)
        self.activity.fraction.show()
