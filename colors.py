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
__copyright__ = "Copyright 2013, 2014 David Cortesi"
__maintainer__ = "David Cortesi"
__email__ = "tallforasmurf@yahoo.com"

'''
        colors.py

Global color resource for PPQT2.

This module stores the currently selected styles and colors for at least,
scanno highlights and spelling-error highlights and current line.

The following are called by the mainwindow at startup and shutdown:

    initialize(settings) Retrieve color choices from saved settings,
                         or set the defaults.

    shutdown(settings)   Save color choices in app settings.

The following are interrogated by an editview:

    get_modified_color() Return a QColor to use for the document name
                         when it is modified.

    get_scanno_format()  Return a QTextCharFormat with the chosen
                         style and color for scanno highlighting.

    get_spelling_format() Return a QTextCharFormat with the chosen
                         style and color for spelling-error highlighting.

    get_current_line_brush() Return a QBrush to use for the background
                        color of the current line.

    get_find_range_brush() Return a QBrush to use for the background
                         color a limited find range.

The following are used by the Preferences dialog:

    choose_color(title, qc_initial, parent=None ) Present a QColorDialog
        to the user headed by the given title, set to initial color,
        centered over parent. Return a QColor or None if cancelled.

    set_modified_color(qcolor) Set the color to use in the document name.

    set_scanno_format(fmt) Set the scanno highlight text format.

    set_spelling_format(fmt) Set the spelling-error highlight format.

    set_current_line_color(qcolor) set the current-line highlight brush to a color

    set_find_range_brush(qcolor) set the find-range background brush

    set_defaults() restore all colors and styles to default values

Regarding the colorChange signal, see comments in fonts.py.
'''

from PyQt5.QtCore import QCoreApplication
_TR = QCoreApplication.translate

import logging
colors_logger = logging.getLogger(name='colors')
import constants as C
from PyQt5.QtGui import QBrush, QColor, QTextCharFormat
from PyQt5.QtWidgets import QColorDialog

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Create a global object that can send the colorChange signal. Objects
# that want to know when the user changes color preferences, connect
# to this signal: colors.notify_me(my_slot)
#

from PyQt5.QtCore import QObject, pyqtSignal

class ColorSignaller(QObject):
    colorChange = pyqtSignal()
    def connect(self, slot):
        self.colorChange.connect(slot)
    def send(self):
        self.colorChange.emit()

_SIGNALLER = ColorSignaller()

def notify_me(slot):
    colors_logger.debug('Connecting colorChange signal to ',slot.__name__)
    _SIGNALLER.connect(slot)
def _emit_signal():
    colors_logger.debug('Emitting colorChange()')
    _SIGNALLER.send()

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Internal function to create a QTextCharFormat. If the line_type (one of the
# UnderlineStyle enum values) is NoUnderLine, make a format for a background
# color, such as used with highlighting scannos.
#
# Otherwise the line_type is an underline, e.g. SpellCheckUnderline; we make
# a format for that with style of underline with the given color.

def _make_format( qcolor = QColor('Black'), line_type = QTextCharFormat.NoUnderline):
    qtcf = QTextCharFormat()
    if line_type == QTextCharFormat.NoUnderline:
        # make a background-color format
        qtcf.setBackground(QBrush(qcolor))
    else :
        # make an underline format
        qtcf.setUnderlineColor(qcolor)
        qtcf.setUnderlineStyle(line_type)
    return qtcf

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Extract the two important features of a QTextCharFormat, its line style
# and its color.

def _parse_format(qtfc):
    line_type = qtfc.underlineStyle()
    if line_type == QTextCharFormat.NoUnderline:
        qc = qtfc.background().color()
    else:
        qc = qtfc.underlineColor()
    return (QColor(qc), line_type)


# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
#
# Initialize the colors and styles from the settings. Current values are
# stored in the following globals.

_MFD_COLOR = QColor('red') # color of modified file's name
_CL_COLOR = QColor('#FAFAE0') # color background of the current edit line
_FR_COLOR = QColor('#CCFFFF') # color background of a limited find range
_SNO_COLOR = QColor('thistle') # color to highlight scannos
_SNO_STYLE = QTextCharFormat.NoUnderline # scanno highlight style
_SPU_COLOR = QColor('magenta') # color to highlight spelling errors
_SPU_STYLE = QTextCharFormat.WaveUnderline # spelling highlight style

def initialize(settings):
    global _SPU_COLOR,_SPU_STYLE,_SNO_COLOR,_SNO_STYLE,_CL_COLOR,_FR_COLOR,_MFD_COLOR
    colors_logger.debug('colors:initializing')
    set_defaults(False) # set defaults and do not signal
    _SPU_COLOR = QColor( settings.value('colors/spell_color',_SPU_COLOR.name()) )
    _SPU_STYLE = settings.value('colors/spell_style',_SPU_STYLE)
    _SNO_COLOR = QColor( settings.value('colors/scanno_color',_SNO_COLOR.name()) )
    _SNO_STYLE = settings.value('colors/scanno_style',_SNO_STYLE)
    _CL_COLOR = QColor( settings.value('colors/current_line',_CL_COLOR.name()) )
    _FR_COLOR = QColor( settings.value('colors/find_range',_FR_COLOR.name()) )
    _MFD_COLOR = QColor( settings.value('colors/modified_name',_MFD_COLOR.name()) )

def shutdown(settings):
    global _SPU_COLOR,_SPU_STYLE,_SNO_COLOR,_SNO_STYLE,_CL_COLOR,_MFD_COLOR
    colors_logger.debug('colors:saving settings')
    settings.setValue('colors/spell_color',_SPU_COLOR.name())
    settings.setValue('colors/spell_style',_SPU_STYLE)
    settings.setValue('colors/scanno_color',_SNO_COLOR.name())
    settings.setValue('colors/scanno_style',_SNO_STYLE)
    settings.setValue('colors/current_line',_CL_COLOR.name())
    settings.setValue('colors/find_range',_FR_COLOR.name())
    settings.setValue('colors/modified_name',_MFD_COLOR.name())

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Functions called by any module needing to use a color or text format.

def get_modified_color():
    return QColor(_MFD_COLOR)

def get_current_line_brush():
    global _CL_COLOR
    return QBrush(_CL_COLOR)

def get_find_range_brush():
    global _FR_COLOR
    return QBrush(_FR_COLOR)

def get_scanno_format():
    global _SNO_COLOR, _SNO_STYLE
    return _make_format(_SNO_COLOR, _SNO_STYLE)

def get_spelling_format():
    global _SPU_COLOR, _SPU_STYLE
    return _make_format(_SPU_COLOR,_SPU_STYLE)

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Functions called by the Preferences dialog.

def set_defaults(signal=True):
    global _SPU_COLOR,_SPU_STYLE,_SNO_COLOR,_SNO_STYLE,_CL_COLOR,_MFD_COLOR
    colors_logger.debug('Resetting colors and styles to defaults')
    _MFD_COLOR = QColor('red')
    _CL_COLOR = QColor('#FAFAE0') # very light yellow
    _FR_COLOR = QColor('#CCFFFF') # very light blue
    _SNO_COLOR = QColor('thistle')
    _SNO_STYLE = QTextCharFormat.NoUnderline
    _SPU_COLOR = QColor('magenta')
    _SPU_STYLE = QTextCharFormat.WaveUnderline
    if signal: _emit_signal()

def set_modified_color(qc):
    global _MFD_COLOR
    colors_logger.debug('Set modified color to {0}'.format(qc.name()))
    _MFD_COLOR = QColor(qc)
    _emit_signal()

def set_current_line_color(qc):
    global _CL_COLOR
    _CL_COLOR = QColor(qc)
    _emit_signal()
    colors_logger.debug('Set current line color to {0}'.format(qc.name()))

def set_find_range_color(qc):
    global _FR_COLOR
    _FR_COLOR = QColor(qc)
    _emit_signal()
    colors_logger.debug('Set find range color to {0}'.format(qc.name()))

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
#
# Note: passing DontUseNativeDialog in Mac OS because the native
# OSX dialog does not display the title string!

def choose_color(title, qc_initial, parent=None ):
    option = QColorDialog.DontUseNativeDialog if C.PLATFORM_IS_MAC else 0
    qc = QColorDialog.getColor( qc_initial, parent, title, option)
    if qc.isValid() : return qc
    return None
