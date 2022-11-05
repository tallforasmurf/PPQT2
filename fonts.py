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

The following are called by all widgets that support font changes:

    notify_me(slot) sets the caller's slot to receive the fontChanged
        signal, emitted when the user changes the general or fixed
        font preference. The caller's slot can then take whatever action
        that widget needs to display itself in the new current font,
        e.g. by calling get_fixed() or get_general().

    POINT_SIZE_MINIMUM static constants that limit font zoom range.
    POINT_SIZE_MAXIMUM

    get_fixed() returns a QFont for the currently selected monospaced font
        at a specified or default point size.

    get_general() returns a QFont for the selected general font
        at a specified or default point size.

    scale() scales the size of a font up or down 1 point and returns the
        modified QFont.

The following are called only by the Preferences dialog:

    choose_font() puts up a font-choice dialog for fixed or general
        and returns the choice, or None if the user cancels.

    set_fixed(qf) set the user's choice of mono font. If it is a
        change from the previous font, we emit the fontChanged(True)
        signal, so widgets that have monospaced elements can change them.

    Note the following has never been implemented! Not here or in Preferences.
    set_general(qf) set the user's choice of UI font. If it is
        a change, we emit the fontChanged(False) signal, so a widget
        that has a general type of text can change (which is probably
        only the main window object).

    set_defaults() returns to the default families and sizes and optionally
        emits the font-changed signal.

Signal generation: as of the PyQt5 signal/slot API, a signal is an attribute
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

from PyQt6.QtCore import QCoreApplication
_TR = QCoreApplication.translate

'''
Create a global object that can send the fontChange signal. Objects that want
to know when the user changes font preferences, connect to this signal:
fonts.notify_me(my_slot)
'''

from PyQt6.QtCore import (
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

'''
Static globals and functions to manage them.

In PyQt5 it was necessary to create an instance of QFontDatabase.
In PyQt6 this is not done; rather the methods of the class are called as static
members. So where previously we created an object under the name _FONT_DB,
now we simply make _FONT_DB a Python reference to the QFontDatabase class.
The syntax of calling its methods remains the same!
'''

from PyQt6.QtGui import (
    QFont,
    QFontDatabase
)
from PyQt6.QtWidgets import QFontDialog

_FONT_DB = QFontDatabase

'''
Ensure that the Liberation Mono and Cousine, fonts are known to the
font system, loading them from our resources module.
'''

_FONT_DB.addApplicationFont(':/liberation_mono.ttf')
_FONT_DB.addApplicationFont(':/cousine.ttf')

'''
Return a list of available monospaced families for use in the preferences
dialog. Because for some stupid reason the font database refuses to
acknowledge that liberation mono and cousine are in fact, monospaced, insert
those names too.
'''
def list_of_good_families():
    selection = _FONT_DB.families() # all known family names
    short_list = [family for family in selection if _FONT_DB.isFixedPitch(family) ]
    short_list.insert(0,'Liberation Mono')
    short_list.insert(0,'Cousine')
    return short_list

'''
For all other modules, specify supported range of font sizes.
'''
POINT_SIZE_MINIMUM = 6 # smallest point size for zooming
POINT_SIZE_MAXIMUM = 48 # largest for zooming

'''
These global variables store the current default values, see initialize()
and set_defaults().
'''
_MONO_SIZE = C.DEFAULT_FONT_SIZE
_GENL_SIZE = C.DEFAULT_FONT_SIZE
_MONO_FAMILY = ''
_GENL_FAMILY = ''
_MONO_QFONT = QFont()
_GENL_QFONT = QFont()

'''
Set default values for all font settings. Called during initialization and
from the Preferences dialog.
'''
def set_defaults(signal=True):
    global _GENL_SIZE,_MONO_SIZE,_GENL_FAMILY,_MONO_FAMILY,_GENL_QFONT,_MONO_QFONT
    # get the name of the font family the DB thinks is the default UI font
    _GENL_FAMILY = _FONT_DB.systemFont(QFontDatabase.SystemFont.GeneralFont).family()
    # default to the name of our preferred font (which we know exists)
    _MONO_FAMILY = 'Liberation Mono'
    # set default sizes
    _MONO_SIZE = C.DEFAULT_FONT_SIZE
    _GENL_SIZE = C.DEFAULT_FONT_SIZE
    # create QFonts based on the defaults
    _GENL_QFONT = QFont(_GENL_FAMILY,_GENL_SIZE)
    _MONO_QFONT = QFont(_MONO_FAMILY,_MONO_SIZE)
    if signal: _emit_signal(True)

'''
Initialize the font system - called from mainwindow.py while starting up
'''
def initialize(settings):
    global _GENL_SIZE,_MONO_SIZE,_GENL_FAMILY,_MONO_FAMILY,_GENL_QFONT,_MONO_QFONT
    fonts_logger.debug('Fonts initializing')
    set_defaults(signal=False)
    # Read the saved names out of the settings, with above defaults
    _GENL_FAMILY = settings.value( 'fonts/general_family', _GENL_FAMILY )
    _MONO_FAMILY = settings.value( 'fonts/mono_family', _MONO_FAMILY )
    # Read the saved point-sizes, with current defaults
    _GENL_SIZE = settings.value( 'fonts/general_size', _GENL_SIZE )
    _GENL_SIZE = int(_GENL_SIZE)
    _MONO_SIZE = settings.value( 'fonts/mono_size', _MONO_SIZE )
    _MONO_SIZE = int(_MONO_SIZE)
    # Set fonts for those values. We do not go through set_fixed/_general()
    # because there is no need to trigger a fontChanged signal, this is
    # happening before any visible widget is initializing.
    _GENL_QFONT = QFont( _GENL_FAMILY, _GENL_SIZE )
    _MONO_QFONT = QFont( _MONO_FAMILY, _MONO_SIZE )

'''
On shutdown, save the user's current font choices. Called from 
mainwindow.py at shutdown.
'''
def shutdown(settings):
    fonts_logger.debug('Saving font info in settings')
    settings.setValue( 'fonts/general_family', _GENL_FAMILY )
    settings.setValue( 'fonts/mono_family', _MONO_FAMILY )
    settings.setValue( 'fonts/general_size', _GENL_SIZE )
    settings.setValue( 'fonts/mono_size', _MONO_SIZE )

'''
At some future time the following get/sets might need some logic, who
knows, but for now they just access the above globals. Called from a number
of modules to retrieve the current font preference.
'''
def get_fixed(point_size=None):
    qf_mono = QFont(_MONO_QFONT)
    qf_mono.setPointSize(_MONO_SIZE if point_size is None else point_size)
    return qf_mono

def get_general(point_size=None):
    qf_general = QFont(_GENL_QFONT)
    qf_general.setPointSize(_GENL_SIZE if point_size is None else point_size)
    return qf_general

'''
Called from editview and others to zoom a current font up or down 1 point.
The caller passes the keystroke value, one of the set constants.KEYS_ZOOM, to
indicate whether it is up or down. We limit the resulting font size range to
the min/max set above.
'''
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

'''
Change the mono font specified to the Preferences module. Notify the
world that it is happening.
'''
def set_fixed(qfont):
    global _MONO_FAMILY, _MONO_QFONT, _MONO_SIZE
    fonts_logger.debug('fonts:set_fixed')
    if qfont.family() != _MONO_FAMILY or qfont.pointSize() != _MONO_SIZE :
        # mono font is changing family a/o size
        _MONO_QFONT = QFont(qfont) # copy the argument
        _MONO_FAMILY = qfont.family()
        _MONO_SIZE = qfont.pointSize()
        _emit_signal(True)
'''
Convert a font family name string to a QFont object at the currently
selected point size. Only used when choosing the fixed font.
'''
def font_from_family(family):
    qf = QFont(family)
    qf.setPointSize(_MONO_SIZE)
    return qf

