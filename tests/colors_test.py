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

import io
log_stream = io.StringIO()
import logging
logging.basicConfig(stream=log_stream,level=logging.INFO)
def check_log(text, level):
    '''check that the log_stream contains the given text at the given level,
       and rewind the log, then return T/F'''
    global log_stream
    level_dict = {logging.DEBUG:'DEBUG',
                  logging.INFO:'INFO',
                  logging.WARN:'WARN',
                  logging.ERROR:'ERROR',
                  logging.CRITICAL:'CRITICAL'}
    log_data = log_stream.getvalue()
    x = log_stream.seek(0)
    x = log_stream.truncate()
    return (-1 < log_data.find(text)) & (-1 < log_data.find(level_dict[level]))
# add .. dir to sys.path so we can import ppqt modules which
# are up one directory level
import sys
import os
my_path = os.path.realpath(__file__)
test_path = os.path.dirname(my_path)
files_path = os.path.join(test_path,'Files')
ppqt_path = os.path.dirname(test_path)
sys.path.append(ppqt_path)
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)
app.setOrganizationName("PGDP")
app.setOrganizationDomain("pgdp.net")
app.setApplicationName("PPQT2")
from PyQt5.QtCore import QSettings
settings = QSettings()
import constants as C
import colors
from PyQt5.QtGui import (QColor,QBrush, QTextCharFormat)

# check initialize
# check defaults on empty settings

settings.clear()
colors.initialize(settings)
colors.shutdown(settings)
assert settings.value('colors/spell_color') == '#ff00ff' # == magenta
assert settings.value('colors/spell_style') == QTextCharFormat.WaveUnderline
assert settings.value('colors/scanno_color') == '#d8bfd8' # == 'thistle'
assert settings.value('colors/scanno_style') == QTextCharFormat.NoUnderline
assert settings.value('colors/current_line') == '#fafae0'
assert settings.value('colors/modified_name') == '#ff0000' # == 'red'

# make some changes
SIGCOUNT = 0
def dingdong():
    global SIGCOUNT
    SIGCOUNT += 1
colors.notify_me(dingdong)

colors.set_modified_color(QColor('#101010'))
assert SIGCOUNT == 1
assert colors.get_modified_color().name() == '#101010'

colors.set_current_line_color(QColor('#202020'))
assert SIGCOUNT == 2
qb = colors.get_current_line_brush()
assert type(qb) == type(QBrush())
assert '#202020' == qb.color().name()

s1cf = QTextCharFormat()
s1cf.setUnderlineStyle(QTextCharFormat.DashDotDotLine)
s1cf.setUnderlineColor(QColor('#303030'))
colors.set_scanno_format(s1cf)
assert SIGCOUNT == 3
s2cf = colors.get_scanno_format()
assert s2cf.underlineStyle() == QTextCharFormat.DashDotDotLine
assert s2cf.underlineColor().name() == '#303030'

s3cf = QTextCharFormat()
s3cf.setUnderlineColor(QColor('#404040'))
s3cf.setUnderlineStyle(QTextCharFormat.DashUnderline)
colors.set_spelling_format(s3cf)
assert SIGCOUNT == 4
s4cf = colors.get_spelling_format()
assert s4cf.underlineStyle() == QTextCharFormat.DashUnderline
assert s4cf.underlineColor().name() == '#404040'

colors.shutdown(settings)
assert settings.value('colors/spell_color') == '#404040' # == magenta
assert settings.value('colors/spell_style') == QTextCharFormat.DashUnderline
assert settings.value('colors/scanno_color') == '#303030' # == 'thistle'
assert settings.value('colors/scanno_style') == QTextCharFormat.DashDotDotLine
assert settings.value('colors/current_line') == '#202020'
assert settings.value('colors/modified_name') == '#101010' # == 'red'

settings.clear() # don't leave junk for next time...

## manual - check color dialog
## first time hit cancel
#uqc = colors.choose_color("Initial s.b. BLUE hit CANCEL",QColor('#000080'))
#assert uqc is None
## second time pick #800080
#uqc = colors.choose_color("Initial s.b. GREEN pick #800080",QColor('#008000'))
#assert uqc.name() == '#800080'
