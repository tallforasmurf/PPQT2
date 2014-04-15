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

    initialize(settings) Retrieve color choices from saved settings,
                         or set the defaults.

    shutdown(settings)   Save color choices in app settings.

    get_modified_color() Return a QColor to use for the document name
                         when it is modified.

    set_modified_color(qcolor) Set the color to use in the document name.

    get_scanno_format()  Return a QTextCharFormat with the chosen
                         style and color for scanno highlighting.

    set_scanno_format(fmt) Set the scanno highlight QTextCharFormat

    get_spelling_format() Return a QTextCharFormat with the chosen
                         style and color for spelling-error highlighting.

    set_spelling_fmt(fmt) set the spelling-error highlight format.

    get_current_line_brush() Return a QBrush to use for the background
                        color of the current line.

    set_current_line_color(qcolor) set the current-line highlight brush to a color

The following are used by a TODO preferences dialog:

    choose_color(message) Present a QColorDialog to the user headed by
                         the given message, return a QColor or None if cancelled.

    make_format( color, line_type = QTextCharFormat.NoUnderline )
                        Create a QTextCharFormat for either a background
                        color (default line_type) or for an underline of
                        the specified type and QColor.


'''

from PyQt5.QtGui import QBrush, QColor, QTextCharFormat, QTextBlockFormat
import logging
colors_logger = logging.getLogger(name='colors')

MD_COLOR = QColor('red')
SC_COLOR = QColor('thistle')
SP_COLOR = QColor('magenta')
CL_COLOR = QColor('#FAFAE0') # very light yellow

# TODO temps
def choose_color(message):
    colors_logger.error('Unimplemented:choose color')

def make_format( qcolor = QColor('Black'), line_type = QTextCharFormat.NoUnderline):
    qtcf = QTextCharFormat()
    if line_type == QTextCharFormat.NoUnderline:
        # make a background-color format
        qtcf.setBackground(QBrush(qcolor))
    else :
        # make an underline format
        qtcf.setUnderlineColor(qcolor)
        qtcf.setUnderlineStyle(line_type)
    return qtcf

def initialize(settings):
    colors_logger.error('Unimplemented:initialize')

def shutdown(settings):
    colors_logger.error('Unimplemented:shutdown')

def get_modified_color():
    return MD_COLOR

def set_modified_color():
    colors_logger.error('Unimplemented:set modified color')

def get_scanno_format():
    qtcf = QTextCharFormat()
    qtcf.setBackground(QBrush(SC_COLOR))
    return qtcf

def set_scanno_format(qtcf):
    colors_logger.error('Unimplemented:set scanno format')

def get_spelling_format():
    global SP_COLOR
    qtcf = make_format(SP_COLOR,QTextCharFormat.WaveUnderline)
    return qtcf

def set_spelling_format(qtcf):
    colors_logger.error('Unimplemented:set spelling format')

def get_current_line_brush():
    return QBrush(CL_COLOR)

def set_current_line_format(qtdf):
    colors_logger.error('Unimplemented:set scanno format')