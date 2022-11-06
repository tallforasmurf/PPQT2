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
Unit test for colors.py. Originally it wasn't going to need a unit test
driver, just using it from mainwindow would be enough, but it has
acquired a lot of behavior.
'''
import test_boilerplate as T
import logging
T.set_up_paths()
T.make_app()

import constants as C
import colors
from PyQt6.QtGui import (QColor,QBrush, QTextCharFormat)

# check initialize
# check defaults on empty settings

T.settings.clear()
colors.initialize(T.settings)
colors.shutdown(T.settings)
assert T.settings.value('colors/spell_color') == '#ff00ff' # == magenta
assert T.settings.value('colors/spell_style') == QTextCharFormat.UnderlineStyle.WaveUnderline
assert T.settings.value('colors/scanno_color') == '#d8bfd8' # == 'thistle'
assert T.settings.value('colors/scanno_style') == QTextCharFormat.UnderlineStyle.NoUnderline
assert T.settings.value('colors/current_line') == '#fafae0'
assert T.settings.value('colors/current_line_style') == QTextCharFormat.UnderlineStyle.NoUnderline
assert T.settings.value('colors/find_range') == "#ccffff"
assert T.settings.value('colors/find_range_style') == QTextCharFormat.UnderlineStyle.NoUnderline
assert T.settings.value('colors/modified_name') == '#ff0000' # == 'red'

# make some changes
SIGCOUNT = 0
def dingdong():
    global SIGCOUNT
    SIGCOUNT += 1
colors.notify_me(dingdong)

colors.set_modified_color(QColor('#101010'))
assert SIGCOUNT == 1
assert colors.get_modified_color().name() == '#101010'

qtcf = QTextCharFormat()
qtcf.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)
qtcf.setUnderlineColor(QColor('#202020'))
colors.set_current_line_format(qtcf)
assert SIGCOUNT == 2
s0cf = QTextCharFormat()
colors.get_current_line_format(s0cf)
assert '#202020' == s0cf.underlineColor().name()
assert s0cf.underlineStyle() == QTextCharFormat.UnderlineStyle.WaveUnderline

s0cf.setUnderlineStyle(QTextCharFormat.UnderlineStyle.NoUnderline)
s0cf.setBackground(QColor('#303030'))
colors.set_find_range_format(s0cf)
assert SIGCOUNT == 3
s0cf = QTextCharFormat()
colors.get_find_range_format(s0cf)
assert '#303030' == s0cf.background().color().name()
assert s0cf.underlineStyle() == QTextCharFormat.UnderlineStyle.NoUnderline

s1cf = QTextCharFormat()
s1cf.setUnderlineStyle(QTextCharFormat.UnderlineStyle.DashDotDotLine)
s1cf.setUnderlineColor(QColor('#303030'))
colors.set_scanno_format(s1cf)
assert SIGCOUNT == 4
s2cf = colors.get_scanno_format()
assert s2cf.underlineStyle() == QTextCharFormat.UnderlineStyle.DashDotDotLine
assert s2cf.underlineColor().name() == '#303030'

s3cf = QTextCharFormat()
s3cf.setUnderlineColor(QColor('#404040'))
s3cf.setUnderlineStyle(QTextCharFormat.UnderlineStyle.DashUnderline)
colors.set_spelling_format(s3cf)
assert SIGCOUNT == 5
s4cf = colors.get_spelling_format()
assert s4cf.underlineStyle() == QTextCharFormat.UnderlineStyle.DashUnderline
assert s4cf.underlineColor().name() == '#404040'

colors.shutdown(T.settings)
assert T.settings.value('colors/spell_color') == '#404040' # == magenta
assert T.settings.value('colors/spell_style') == QTextCharFormat.UnderlineStyle.DashUnderline
assert T.settings.value('colors/scanno_color') == '#303030' # == 'thistle'
assert T.settings.value('colors/scanno_style') == QTextCharFormat.UnderlineStyle.DashDotDotLine
assert T.settings.value('colors/current_line') == '#202020'
assert T.settings.value('colors/find_range') == '#303030'
assert T.settings.value('colors/modified_name') == '#101010' # == 'red'

T.settings.clear() # don't leave junk for next time...

# manual - check color dialog
# first time hit cancel
uqc = colors.choose_color("Initial s.b. BLUE hit CANCEL",QColor('#000080'))
assert uqc is None
# second time pick #800080
uqc = colors.choose_color("Initial s.b. GREEN pick #800080",QColor('#008000'))
assert uqc.name() == '#800080'
