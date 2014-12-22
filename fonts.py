__license__ = '''
 License (GPL-3.0) :
    This file is part of PPQT Version 2.
    PPQT is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You can find a copy of the GNU General Public License in the file
    extras/COPYING.TXT included in the distribution of this program, or see:
    <http://www.gnu.org/licenses/>.
'''
__version__ = "2.0.0"
__author__  = "David Cortesi"
__copyright__ = "Copyright 2013, 2014, 2015 David Cortesi"
__maintainer__ = "David Cortesi"
__email__ = "tallforasmurf@yahoo.com"

'''
            fonts.py
Font resource for PPQT2.

This module is imported by mainwindow on startup, when it calls
initialize(). The services offered are designed so that other widgets
don't have to know about the QFont/QFontInfo API.

The following are called from the mainwindow:

    initialize(settings) creates a font database, makes sure it has
        our favorite Liberation Mono font, and identifies the user's
        preferred monospaced and general fonts from settings.

    shutdown(settings) saves current font choices in the settings.

The following are called by widgets that allow font changes:

    notify_me(slot) sets the caller's slot to receive the fontChanged
        signal, emitted when the user changes the general or fixed
        font preference.

    POINT_SIZE_MINIMUM static constants that limit font zoom range.
    POINT_SIZE_MAXIMUM

    get_fixed() returns a QFont for the selected monospaced font
        at a specified or default point size.

    get_general() returns a QFont for the selected general font
        at a specified or default point size.

    scale() scales the size of a font up or down 1 point and returns the
        modified QFont.

The following are called by the Preferences dialog:

    choose_font() puts up a font-choice dialog for fixed or general
        and returns the choice, or None if the user cancels.
        Called from preferences.

    set_fixed(qf) set the user's choice of mono font, and if it is a
        change from the previous font, emits the fontChanged(True) signal,
        so widgets that have monospaced elements can change them.

    set_general(qf) set the user's choice of UI font, and if it is
        a change, emits the fontChanged(False) signal. This is probably
        only handled by the main window object.

    set_defaults() returns to the default families and sizes.

Signal generation: in the new PyQt5 signal/slot API, a signal is an attribute
of a class. This module is mostly "static global" methods, but it needs to
emit the fontChanged(bool) signal. In order to do that, it needs a class and
an object of that class. So we define a class FontSignaller, make one
instance of that class, and use it as our signal-emitter. We don't make the
class available but rather provide the static global method notify_me(slot)
to connect a slot (any executable) to the signal.

'''
import logging
fonts_logger = logging.getLogger(name='fonts')

import constants as C

from PyQt5.QtCore import QCoreApplication
_TR = QCoreApplication.translate

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Create a global object that can send the fontChange signal. Objects
# that want to know when the user changes font preferences, connect
# to this signal: fonts.notify_me(my_slot)
#

from PyQt5.QtCore import (
    pyqtSignal,
    QObject
    )

class FontSignaller(QObject):
    fontChange = pyqtSignal(bool)
    def connect(self, slot):
        self.fontChange.connect(slot)
    def send(self,boola):
        self.fontChange.emit(boola)

_SIGNALLER = FontSignaller()

def notify_me(slot):
    fonts_logger.debug('Connecting fontChange signal to {}'.format(slot.__name__))
    _SIGNALLER.connect(slot)
def _emit_signal(boola):
    fonts_logger.debug('Emitting fontChange signal({})'.format(boola) )
    _SIGNALLER.send(boola)

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Static globals and functions to manage them.
#
# Generate a font database and make sure it contains Liberation Mono
# and Cousine, loading them from our resources module.
#

from PyQt5.QtGui import (
    QFont,
    QFontDatabase
)
from PyQt5.QtWidgets import QFontDialog

_FONT_DB = QFontDatabase()
_FONT_DB.addApplicationFont(':/liberation_mono.ttf')
_FONT_DB.addApplicationFont(':/cousine.ttf')

# Return a list of available monospaced families for use in the preferences
# dialog. Because for some stupid reason the font database refuses to
# acknowledge that liberation mono and cousine are in fact, monospaced,
# insert those names too.

def list_of_good_families():
    selection = _FONT_DB.families() # all known family names
    short_list = [family for family in selection if _FONT_DB.isFixedPitch(family) ]
    short_list.insert(0,'Liberation Mono')
    short_list.insert(0,'Cousine')
    return short_list

# Primary use of these global constants is in unit test
POINT_SIZE_MINIMUM = 6 # smallest point size for zooming
POINT_SIZE_MAXIMUM = 48 # largest for zooming

# These globals contain the current defaults, see initialize()
_MONO_SIZE = C.DEFAULT_FONT_SIZE
_GENL_SIZE = C.DEFAULT_FONT_SIZE
_MONO_FAMILY = ''
_GENL_FAMILY = ''
_MONO_QFONT = QFont()
_GENL_QFONT = QFont()

# Set default values for all font settings.
def set_defaults():
    global _GENL_SIZE,_MONO_SIZE,_GENL_FAMILY,_MONO_FAMILY,_GENL_QFONT,_MONO_QFONT
    # get the name of the font family the DB thinks is the default UI font
    _GENL_FAMILY = _FONT_DB.systemFont(QFontDatabase.GeneralFont).family()
    # default to the name of our preferred font (which we know exists)
    _MONO_FAMILY = 'Liberation Mono'
    # set default sizes
    _MONO_SIZE = C.DEFAULT_FONT_SIZE
    _GENL_SIZE = C.DEFAULT_FONT_SIZE
    # create QFonts based on the defaults
    _GENL_QFONT = QFont(_GENL_FAMILY,_GENL_SIZE)
    _MONO_QFONT = QFont(_MONO_FAMILY,_MONO_SIZE)

def initialize(settings):
    global _GENL_SIZE,_MONO_SIZE,_GENL_FAMILY,_MONO_FAMILY,_GENL_QFONT,_MONO_QFONT
    fonts_logger.debug('Fonts initializing')
    set_defaults()
    # Read the saved names out of the settings, with above defaults
    _GENL_FAMILY = settings.value( 'fonts/general_family', _GENL_FAMILY )
    _MONO_FAMILY = settings.value( 'fonts/mono_family', _MONO_FAMILY )
    # Read the saved point-sizes, with current defaults
    _GENL_SIZE = settings.value( 'fonts/general_size', _GENL_SIZE )
    _MONO_SIZE = settings.value( 'fonts/mono_size', _MONO_SIZE )
    # Set fonts for those values. We do not go through set_fixed/_general()
    # because there is no need to trigger a fontChanged signal, this is
    # happening before any visible widget is initializing.
    _GENL_QFONT = QFont( _GENL_FAMILY, _GENL_SIZE )
    _MONO_QFONT = QFont( _MONO_FAMILY, _MONO_SIZE )

def shutdown(settings):
    fonts_logger.debug('Saving font info in settings')
    settings.setValue( 'fonts/general_family', _GENL_FAMILY )
    settings.setValue( 'fonts/mono_family', _MONO_FAMILY )
    settings.setValue( 'fonts/general_size', _GENL_SIZE )
    settings.setValue( 'fonts/mono_size', _MONO_SIZE )

# At some future time the following get/sets might need some
# logic, who knows, but for now they just access the above globals.

def get_fixed(point_size=None):
    qf_mono = QFont(_MONO_QFONT)
    qf_mono.setPointSize(_MONO_SIZE if point_size is None else point_size)
    return qf_mono

def get_general(point_size=None):
    qf_general = QFont(_GENL_QFONT)
    qf_general.setPointSize(_GENL_SIZE if point_size is None else point_size)
    return qf_general

# Called from editview and others to zoom a current font up or down 1 point,
# depending on the key, which should be one of constants.KEYS_ZOOM. Limit the
# font size range.

def scale(zoom_key, qfont ) :
    if zoom_key in C.KEYS_ZOOM :
        pts = qfont.pointSize()
        pts += (-1 if zoom_key == C.CTL_MINUS else 1)
        if (pts >= POINT_SIZE_MINIMUM) and (pts <= POINT_SIZE_MAXIMUM) :
            qfont.setPointSize(pts)
        else:
            fonts_logger.error('rejecting zoom to {0} points'.format(pts))
    else:
        fonts_logger.error('ignoring non-zoom key argument')
    return qfont

# The following are for use from the Preferences dialog.
#
# todo? Could this use QFontComboBox? No it could not, because that's a
# drop-down not a full dialog. However the preferences dialog could use
# QFontComboBox instead of calling this method.
#

def set_fixed(qfont):
    global _MONO_FAMILY, _MONO_QFONT, _MONO_SIZE
    fonts_logger.debug('fonts:set_fixed')
    if qfont.family() != _MONO_FAMILY or qfont.pointSize() != _MONO_SIZE :
        # mono font is changing family a/o size
        _MONO_QFONT = QFont(qfont) # copy the argument
        _MONO_FAMILY = qfont.family()
        _MONO_SIZE = qfont.pointSize()
        _emit_signal(True)

def font_from_family(family):
    qf = QFont(family)
    qf.setPointSize(_MONO_SIZE)
    return qf

# When preference is actually designed, we go with our own combobox
# instead of the full font dialog. Also, decided NOT to support user
# choice of the general UI font.

#def choose_font(mono=True, parent=None):
    #fonts_logger.debug('choose_font mono={0}'.format(mono))
    #if mono :
        #caption = _TR('fonts.py',
                      #'Select a monospaced font for editing',
                      #'Font choice dialog caption')
        #initial = _MONO_QFONT
    #else :
        #caption = _TR('fonts.py',
                      #'Select the font for titles, menus, and buttons',
                      #'Font choice dialog caption')
        #initial = _GENL_QFONT
    #(new_font, ok) = QFontDialog.getFont(initial,parent,caption)
    #if ok : return new_font
    #else: return None

#def set_general(qfont):
    #global _GENL_FAMILY, _GENL_SIZE, _GENL_QFONT
    #fonts_logger.debug('fonts:set_general')
    #if qfont.family() != _GENL_FAMILY or qfont.pointSize() != _GENL_SIZE :
        ## general font is changing
        #_GENL_QFONT = QFont(qfont)
        #_GENL_FAMILY = qfont.family()
        #_GENL_SIZE = qfont.pointSize()
        #_emit_signal(False)
