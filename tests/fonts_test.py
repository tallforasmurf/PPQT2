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
Unit test for fonts.py. Originally it wasn't going to need a unit test
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
import fonts
from PyQt5.QtGui import (QFont, QFontInfo, QFontDatabase)

# check initialize
# check defaults on empty settings
def same_font(qf1, qf2):
    return qf1.family() == qf2.family() and qf1.pointSize() == qf2.pointSize()

settings.clear()
myfdb = QFontDatabase()
genqf = myfdb.systemFont(QFontDatabase.GeneralFont)
fonts.initialize(settings)
assert same_font(genqf,fonts.get_general())
monqf = fonts.get_fixed()
dbg = monqf.family()
assert monqf.family() == 'Liberation Mono'
assert monqf.pointSize() == C.DEFAULT_FONT_SIZE
SIGBOOL = None
def slot(boola):
    global SIGBOOL
    SIGBOOL = boola
fonts.notify_me(slot)
fonts.set_general(genqf) # should be no signal
assert SIGBOOL is None
palqf = myfdb.font('Palatino','Normal',18)
fonts.set_general(palqf) # should cause signal(false)
assert SIGBOOL == False # altho None is never true, it isn't False
couqf = myfdb.font('Courier','Normal',17)
fonts.set_fixed(couqf) # should cause signal(true)
assert SIGBOOL
# check shutdown
fonts.shutdown(settings)
assert settings.value('fonts/general_family') == palqf.family()
assert settings.value('fonts/mono_family') == couqf.family()
assert settings.value('fonts/general_size') == palqf.pointSize()
assert settings.value('fonts/mono_size') == couqf.pointSize()
# check scale
ps = genqf.pointSize()
genqf = fonts.scale(C.CTL_SHFT_EQUAL, genqf)
assert (ps+1) == genqf.pointSize()
genqf = fonts.scale(C.CTL_MINUS, genqf)
assert ps == genqf.pointSize()
genqf.setPointSize(fonts.POINT_SIZE_MINIMUM)
genqf = fonts.scale(C.CTL_MINUS, genqf)
assert genqf.pointSize() == fonts.POINT_SIZE_MINIMUM
assert check_log('rejecting zoom',logging.ERROR)
genqf.setPointSize(fonts.POINT_SIZE_MAXIMUM)
genqf = fonts.scale(C.CTL_SHFT_EQUAL, genqf)
assert genqf.pointSize() == fonts.POINT_SIZE_MAXIMUM
assert check_log('rejecting zoom',logging.ERROR)
genqf = fonts.scale(C.CTL_LEFT,genqf)
assert genqf.pointSize() == fonts.POINT_SIZE_MAXIMUM
assert check_log('ignoring non-zoom key',logging.ERROR)
# exit # <<---  uncomment for automated run
# manual: check font dialog
# cancel the first one
genqf = fonts.choose_font(True)
assert genqf is None
# accept the second
genqf = fonts.choose_font(True)
assert genqf is not None
print (genqf.family(), genqf.pointSize())
# third is for general not mono
genqf = fonts.choose_font(False)
assert genqf is not None
print (genqf.family(), genqf.pointSize())
