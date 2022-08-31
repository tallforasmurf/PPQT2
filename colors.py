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
        colors.py

Global color (actually, text-character-format) resource for PPQT2.

This module stores the currently selected styles and colors for
scanno highlights, spelling-error highlights, current line and find range.

The following are called by the mainwindow at startup and shutdown:

    initialize(settings) Retrieve color choices from saved settings,
                         or set the defaults.

    shutdown(settings)   Save current color choices in app settings.

The following are interrogated by an editview:

    get_modified_color() Return a QColor to use for the document name
                         when it is modified.

    get_scanno_format()  Return a QTextCharFormat with the chosen
                         style and color for scanno highlighting.

    get_spelling_format() Return a QTextCharFormat with the chosen
                         style and color for spelling-error highlighting.

    get_current_line_format() Update a QTextCharFormat with the
                         current choices of color and line style for
                         the current line highlight.

    get_find_range_format() Update a QTextCharFormat with the
                         current choices of color and line style for
                         the limited find range highlight

The following are used by the Preferences dialog:

    choose_color(title, qc_initial, parent=None ) Present a QColorDialog
        to the user headed by the given title, set to initial color,
        centered over parent. Return a QColor or None if cancelled.

    set_modified_color(qcolor) Set the color to use in the document name.
        (in fact, this is not called, it is not currently a Preference)

    set_scanno_format(fmt) Set the scanno highlight text format.

    set_spelling_format(fmt) Set the spelling-error highlight format.

    set_current_line_format(fmt) set the current-line highlight format.

    set_find_range_format(fmt) set the find-range highlight format.

    set_defaults() restore all colors and styles to default values

Regarding the colorChange signal, see comments in fonts.py.
'''

from PyQt6.QtCore import Qt, QCoreApplication
_TR = QCoreApplication.translate

import logging
colors_logger = logging.getLogger(name='colors')
import constants as C
from PyQt6.QtGui import QBrush, QColor, QTextCharFormat
from PyQt6.QtWidgets import QColorDialog

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Create a global object that can send the colorChange signal. Objects
# that want to know when the user changes color preferences, connect
# to this signal: colors.notify_me(my_slot)
#

from PyQt6.QtCore import QObject, pyqtSignal

class ColorSignaller(QObject):
    colorChange = pyqtSignal()
    def connect(self, slot):
        self.colorChange.connect(slot)
    def send(self):
        self.colorChange.emit()

_SIGNALLER = ColorSignaller()

def notify_me(slot):
    colors_logger.debug('Connecting colorChange signal to {}'.format(slot.__name__))
    _SIGNALLER.connect(slot)
def _emit_signal():
    colors_logger.debug('Emitting colorChange()')
    _SIGNALLER.send()

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
#
# Establish the static global choices of the colors and styles. These are
# updated in set_defaults(), initialize(), and the set_* methods.

_CL_COLOR = QColor('#FAFAE0') # color background of the current edit line
_CL_STYLE = QTextCharFormat.UnderlineStyle.NoUnderline # line style, usually no-underline
_FR_COLOR = QColor('#CCFFFF') # color background of a limited find range
_FR_STYLE = QTextCharFormat.UnderlineStyle.NoUnderline # line style, usually no-underline
_SNO_COLOR = QColor('thistle') # color to highlight scannos
_SNO_STYLE = QTextCharFormat.UnderlineStyle.NoUnderline # scanno highlight style
_SPU_COLOR = QColor('magenta') # color to highlight spelling errors
_SPU_STYLE = QTextCharFormat.UnderlineStyle.WaveUnderline # spelling highlight style

def initialize(settings):
    global _CL_COLOR, _CL_STYLE, _FR_COLOR, _FR_STYLE
    global _SPU_COLOR, _SPU_STYLE, _SNO_COLOR, _SNO_STYLE
    colors_logger.debug('colors:initializing')
    set_defaults(False) # set defaults and do not signal
    _SPU_COLOR = QColor( settings.value('colors/spell_color',_SPU_COLOR.name()) )
    _SPU_STYLE = settings.value('colors/spell_style',_SPU_STYLE)
    _SPU_STYLE = int( _SPU_STYLE )
    _SNO_COLOR = QColor( settings.value('colors/scanno_color',_SNO_COLOR.name()) )
    _SNO_STYLE = settings.value('colors/scanno_style',_SNO_STYLE)
    _SNO_STYLE = int( _SNO_STYLE )
    _CL_COLOR = QColor( settings.value('colors/current_line',_CL_COLOR.name()) )
    _CL_STYLE = settings.value( 'colors/current_line_style', _CL_STYLE )
    _CL_STYLE = int( _CL_STYLE )
    _FR_COLOR = QColor( settings.value('colors/find_range',_FR_COLOR.name()) )
    _FR_STYLE = settings.value( 'colors/find_range_style', _FR_STYLE )
    _FR_STYLE = int( _FR_STYLE )

def shutdown(settings):
    global _CL_COLOR, _CL_STYLE, _FR_COLOR, _FR_STYLE
    global _SPU_COLOR, _SPU_STYLE, _SNO_COLOR, _SNO_STYLE
    colors_logger.debug('colors:saving settings')
    settings.setValue('colors/spell_color',_SPU_COLOR.name())
    settings.setValue('colors/spell_style',_SPU_STYLE)
    settings.setValue('colors/scanno_color',_SNO_COLOR.name())
    settings.setValue('colors/scanno_style',_SNO_STYLE)
    settings.setValue('colors/current_line',_CL_COLOR.name())
    settings.setValue('colors/current_line_style', _CL_STYLE)
    settings.setValue('colors/find_range',_FR_COLOR.name())
    settings.setValue('colors/find_range_style', _FR_STYLE)

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Functions called by editview to get text formats for four different
# highlight types. In each case return a QTextCharFormat that reflects the
# current color and underline-style set from preferences.
#
# For the current-line style and usually, the find-range style, editview
# needs the fullWidthSelection property set, and we do that here.

# Create a QTextCharFormat based on a color and underline value.

def _make_format( color, line_type ):
    qtcf = QTextCharFormat()
    qtcf.setUnderlineStyle(line_type)
    if line_type == QTextCharFormat.UnderlineStyle.NoUnderline:
        # make a background color format
        qtcf.setBackground(QBrush(color)) # background get a QBrush
    else :
        # make an underline format
        qtcf.setUnderlineColor(color) # underline color gets a QColor
    return qtcf

def get_current_line_format():
    qtcf = _make_format(_CL_COLOR, _CL_STYLE )
    qtcf.setProperty( QTextCharFormat.Property.FullWidthSelection, True )
    return qtcf

def get_find_range_format( full_width=True ):
    qtcf = _make_format( _FR_COLOR, _FR_STYLE )
    qtcf.setProperty( QTextCharFormat.Property.FullWidthSelection, full_width )
    return qtcf

def get_scanno_format():
    return _make_format( _SNO_COLOR, _SNO_STYLE )

def get_spelling_format():
    return _make_format( _SPU_COLOR,_SPU_STYLE )

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Functions called by the Preferences dialog.

def set_defaults(signal=True):
    global _CL_COLOR, _CL_STYLE, _FR_COLOR, _FR_STYLE
    global _SPU_COLOR, _SPU_STYLE, _SNO_COLOR, _SNO_STYLE
    colors_logger.debug('Resetting colors and styles to defaults')
    _CL_COLOR = QColor('#FAFAE0') # very light yellow
    _CL_STYLE = QTextCharFormat.NoUnderline # bg only no underline
    _FR_COLOR = QColor('#CCFFFF') # very light blue
    _FR_STYLE = QTextCharFormat.NoUnderline # bg, no-underline
    _SNO_COLOR = QColor('thistle') # lavender, no underline
    _SNO_STYLE = QTextCharFormat.NoUnderline
    _SPU_COLOR = QColor('magenta') # strong red wavy underline
    _SPU_STYLE = QTextCharFormat.WaveUnderline
    if signal: _emit_signal()

# Extract the two important features of a QTextCharFormat, its line style
# and its color.

def _parse_format(qtfc):
    line_type = qtfc.underlineStyle()
    if line_type == QTextCharFormat.UnderlineStyle.NoUnderline:
        qc = qtfc.background().color()
    else:
        qc = qtfc.underlineColor()
    return (QColor(qc), line_type)

def set_current_line_format(qtcf):
    global _CL_COLOR, _CL_STYLE
    (_CL_COLOR, _CL_STYLE) = _parse_format(qtcf)
    _emit_signal()
    colors_logger.debug('Set current line format to {} {}'.format(int(_CL_STYLE),_CL_COLOR.name()))

def set_find_range_format(qtcf):
    global _FR_COLOR, _FR_STYLE
    (_FR_COLOR, _FR_STYLE) = _parse_format(qtcf)
    _emit_signal()
    colors_logger.debug('Set find range format to {} {}'.format(int(_FR_STYLE),_FR_COLOR.name()))

def set_scanno_format(qtcf):
    global _SNO_COLOR, _SNO_STYLE
    (_SNO_COLOR, _SNO_STYLE) = _parse_format(qtcf)
    _emit_signal()
    colors_logger.debug('Set scanno format to {0} {1}'.format(int(_SNO_STYLE),_SNO_COLOR.name()))

def set_spelling_format(qtcf):
    global _SPU_COLOR, _SPU_STYLE
    (_SPU_COLOR, _SPU_STYLE) = _parse_format(qtcf)
    _emit_signal()
    colors_logger.debug('Set spelling format to {0} {1}'.format(int(_SPU_STYLE),_SPU_COLOR.name()))

# Generic color-picker dialog to be called by the Preferences dialog.
#   parent: widget over which to center the dialog.
#   title: a translated title for the dialog, e.g. "Choose scanno highlight color"
#   qc_initial: starting color value.
# Returns None if the user cancels, or the chosen QColor.

def choose_color(title, qc_initial, parent=None ):
    qc = QColorDialog.getColor( qc_initial, parent, title )
    if qc.isValid() : return qc
    return None
