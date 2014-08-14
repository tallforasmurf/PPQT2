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
Unit test for mainwindow.py - MINIMAL test of startup and shutdown
checking geometry save
'''
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Unit test module boilerplate stuff
#
# set up logging to a stream
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
def empty_log():
    ''' return True if the log stream is empty,
    else print it and return false'''
    global log_stream
    log_data = log_stream.getvalue()
    if 0 == len(log_data) : return True
    print(log_data)
    return False
def _write_fdict(settings, file_dict, array_key):
    fnames = sorted(file_dict.keys())
    settings.beginWriteArray(array_key,len(fnames))
    for f in range(len(fnames)) :
        settings.setArrayIndex(f)
        settings.setValue('filename',fnames[f])
        settings.setValue('filepath',file_dict[fnames[f]])
    settings.endArray()
def _read_fdict(settings, array_key):
    f_dict = {}
    f_count = settings.beginReadArray(array_key)
    for f in range(f_count): # it may be 0
        settings.setArrayIndex(f)
        f_dict[settings.value('filename')] = settings.value('filepath')
    settings.endArray()
    return f_dict

import sys
import os
my_path = os.path.realpath(__file__)
test_path = os.path.dirname(my_path)
files_path = os.path.join(test_path,'Files')
ppqt_path = os.path.dirname(test_path)
sys.path.append(ppqt_path)
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

# Set up the app so that settings work -- this in lieu of the ppqt2.py
# Note the app name is distinct from the old, so that v1 and v2 can
# be used simultaneously.
app.setOrganizationName("PGDP")
app.setOrganizationDomain("pgdp.net")
app.setApplicationName("PPQT2")
from PyQt5.QtCore import QSettings
settings = QSettings()

# and awayyyy we go
import constants as C
import mainwindow
from PyQt5.QtCore import Qt,QPoint,QSize

# FIRST test: see if settings properly saved on window close
# clear all items from the settings, forcing startup in default condition
# we will check saved values at end
settings.clear()
mw = mainwindow.MainWindow(settings)
# change the size etc from the defaults
mw.move(QPoint(123,231))
x = C.STARTUP_DEFAULT_SIZE.width() + 7
y = C.STARTUP_DEFAULT_SIZE.height() + 7
mw.resize(QSize(x,y))
mw.close() # invokes closeEvent()
mwp = settings.value("mainwindow/position")
assert mwp.x()==123
assert mwp.y()==231
mws = settings.value("mainwindow/size")
assert mws.width()==x
assert mws.height()==y
# log won't be empty because of dict messages
#assert empty_log()
app.quit()
# idle a bit after quit to let garbage be collected
from PyQt5.QtTest import QTest
QTest.qWait(200)
