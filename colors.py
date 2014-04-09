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

The following are used by a TODO preferences dialog:

    choose_color(message) Present a QColorDialog to the user and
                         return a QColor or None if cancelled.

    make_format( color, line_type = QTextCharFormat.NoUnderline )
                        Create a QTextCharFormat for either a background
                        color (default line_type) or for an underline of
                        the specified type and QColor.

    set_scanno_format(fmt) Set the scanno highlight QTextFormat

    set_spelling_fmt(fmt) set the spelling-error highlight format

    set_current_line_format(fmt) set the current-line highlight format

'''

from PyQt5.QtGui import QBrush, QColor, QTextCharFormat, QTextBlockFormat

MD_COLOR = QColor('red')
SC_COLOR = QColor('thistle')
SP_COLOR = QColor('lightpink')
CL_COLOR = QColor('#FAFAE0') # very light yellow

# TODO temps
def get_modified_color():
    return MD_COLOR

def get_scanno_format():
    qtcf = QTextCharFormat()
    qtcf.setBackground(QBrush(SC_COLOR))
    return qtcf

def get_spelling_format():
    qtcf = QTextCharFormat()
    qtcf.setUnderlineStyle(QTextCharFormat.SpellCheckUnderline)
    qtcf.setUnderlineColor(SP_COLOR)
    return qtcf

def get_current_line_brush():
    return QBrush(CL_COLOR)

def set_scanno_format(qtcf):
    pass
def set_spelling_format(qtcf):
    pass
def set_current_line_format(qtdf):
    pass