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

The following are interrogated by an editview:

    get_modified_color() Return a QColor to use for the document name
                         when it is modified.

    get_scanno_format()  Return a QTextCharFormat with the chosen
                         style and color for scanno highlighting.

    get_spelling_format() Return a QTextCharFormat with the chosen
                         style and color for spelling-error highlighting.

    get_current_line_brush() Return a QBrush to use for the background
                        color of the current line.

The following are used by the TODO preferences dialog:

    choose_color(message) Present a QColorDialog to the user headed by
                         the given message, return a QColor or None if cancelled.

    set_modified_color(qcolor) Set the color to use in the document name.

    set_scanno_color(qcolor) Set the scanno highlight color

    set_spelling_fmt(fmt) Set the spelling-error highlight format (may
                          include underline or just background brush).

    set_current_line_color(qcolor) set the current-line highlight brush to a color

    set_defaults() restore all colors and styles to default values

The following are called by the mainwindow at startup and shutdown:

    initialize(settings) Retrieve color choices from saved settings,
                         or set the defaults.

    shutdown(settings)   Save color choices in app settings.

Regarding the colorChange signal, see comments in fonts.py.
'''
from PyQt5.QtCore import QCoreApplication, QObject, pyqtSignal
_TR = QCoreApplication.translate

class ColorSignaller(QObject):
    colorChange = pyqtSignal()
    def connect(self, slot):
        self.colorChange.connect(slot)
    def send(self):
        self.colorChange.emit()

_SIGNALLER = ColorSignaller()
def notify_me(slot):
    _SIGNALLER.connect(slot)
def _emit_signal():
    _SIGNALLER.send()

from PyQt5.QtGui import QBrush, QColor, QTextCharFormat
from PyQt5.QtWidgets import QColorDialog
import logging
colors_logger = logging.getLogger(name='colors')

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

def _parse_format(qtfc):
    line_type = qtfc.underlineStyle()
    if line_type == QTextCharFormat.NoUnderline:
        qc = qtfc.background().color()
    else:
        qc = qtfc.underlineColor()
    return (QColor(qc), line_type)

_MFD_COLOR = QColor('red') # color of modified file's name

def get_modified_color():
    return QColor(_MFD_COLOR)

def set_modified_color(qc):
    global _MFD_COLOR
    _MFD_COLOR = qc
    _emit_signal()
    colors_logger.debug('Set modified color to {0}'.format(qc.name()))

_CL_COLOR = QColor('#FAFAE0') # very light yellow

def get_current_line_brush():
    global _CL_COLOR
    return QBrush(_CL_COLOR)

def set_current_line_color(qc):
    global _CL_COLOR
    _CL_COLOR = QColor(qc)
    _emit_signal()
    colors_logger.debug('Set current line color to {0}'.format(qc.name()))

_SNO_COLOR = QColor('thistle') # color to highlight scannos
_SNO_STYLE = QTextCharFormat.NoUnderline

def get_scanno_format():
    global _SNO_COLOR, _SNO_STYLE
    return _make_format(_SNO_COLOR, _SNO_STYLE)

def set_scanno_format(qtcf):
    global _SNO_COLOR, _SNO_STYLE
    (_SNO_COLOR, _SNO_STYLE) = _parse_format(qtcf)
    _emit_signal()
    colors_logger.debug('Set scanno format to {0} {1}'.format(int(_SNO_STYLE),_SNO_COLOR.name()))

_SPU_COLOR = QColor('magenta')
_SPU_STYLE = QTextCharFormat.WaveUnderline

def get_spelling_format():
    global _SPU_COLOR, _SPU_STYLE
    return _make_format(_SPU_COLOR,_SPU_STYLE)

def set_spelling_format(qtcf):
    global _SPU_COLOR, _SPU_STYLE
    (_SPU_COLOR, _SPU_STYLE) = _parse_format(qtcf)
    _emit_signal()
    colors_logger.debug('Set spelling format to {0} {1}'.format(int(_SPU_STYLE),_SPU_COLOR.name()))

# Generic color-picker dialog. Caller (preferences) must pass a
# translated title suitable for the title line of the dialog,
# and a QColor for the initial value. Returns None if the user
# cancels, or the chosen QColor.

def choose_color(title, qc_initial, parent=None ):
    qc = QColorDialog.getColor( qc_initial, parent, title )
    if qc.isValid() : return qc
    return None

# Initialize the colors and styles from the settings.

def initialize(settings):
    global _SPU_COLOR,_SPU_STYLE,_SNO_COLOR,_SNO_STYLE,_CL_COLOR,_MFD_COLOR
    colors_logger.debug('colors:initializing')
    set_defaults(False) # set defaults and do not signal
    _SPU_COLOR = QColor( settings.value('colors/spell_color',_SPU_COLOR.name()) )
    _SPU_STYLE = settings.value('colors/spell_style',_SPU_STYLE)
    _SNO_COLOR = QColor( settings.value('colors/scanno_color',_SNO_COLOR.name()) )
    _SNO_STYLE = settings.value('colors/spell_style',_SNO_STYLE)
    _CL_COLOR = QColor( settings.value('colors/current_line',_CL_COLOR.name()) )
    _MFD_COLOR = QColor( settings.value('colors/modified_name',_MFD_COLOR.name()) )

def shutdown(settings):
    global _SPU_COLOR,_SPU_STYLE,_SNO_COLOR,_SNO_STYLE,_CL_COLOR,_MFD_COLOR
    colors_logger.debug('colors:saving settings')
    settings.setValue('colors/spell_color',_SPU_COLOR.name())
    settings.setValue('colors/spell_style',_SPU_STYLE)
    settings.setValue('colors/scanno_color',_SNO_COLOR.name())
    settings.setValue('colors/scanno_style',_SNO_STYLE)
    settings.setValue('colors/current_line',_CL_COLOR.name())
    settings.setValue('colors/modified_name',_MFD_COLOR.name())

def set_defaults(signal=True):
    global _SPU_COLOR,_SPU_STYLE,_SNO_COLOR,_SNO_STYLE,_CL_COLOR,_MFD_COLOR
    _SPU_COLOR = QColor('magenta')
    _SPU_STYLE = QTextCharFormat.WaveUnderline
    _SNO_COLOR = QColor('thistle')
    _SNO_STYLE = QTextCharFormat.NoUnderline
    _CL_COLOR = QColor('#FAFAE0') # very light yellow
    _MFD_COLOR = QColor('red')
    if signal: _emit_signal()
    colors_logger.debug('Resetting colors and styles to defaults')
