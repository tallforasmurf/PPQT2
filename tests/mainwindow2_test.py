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
Unit test for mainwindow.py - minimal check of settings save of recent files
and open files.
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
def _write_flist(settings, file_list, array_key):
    settings.beginWriteArray(array_key,len(file_list))
    for f in range(len(file_list)) :
        settings.setArrayIndex(f)
        settings.setValue('filepath',file_list[f])
    settings.endArray()
def _read_flist(settings, array_key):
    file_list = []
    f_count = settings.beginReadArray(array_key)
    for f in range(f_count): # it may be 0
        settings.setArrayIndex(f)
        file_list.append(settings.value('filepath'))
    settings.endArray()
    return file_list

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
import mainwindow
from PyQt5.QtCore import Qt,QPoint,QSize

## SECOND test check loading saving recent files and previously open files
## clear the sessions and insert some previous files
## and open files.

mw = None # clear out that mainwindow
settings.clear()
recentlist = ['/the/path/to/glory/recent_1',
            '/the/path/to/glory2/recent_2',
            '/the/path/to/glory3/recent_3']
_write_flist(settings, recentlist, 'mainwindow/recent_files')
# Enable the following to see "Re-open" dialog - click cancel
openlist = ['/somewhere/over/the/rainbow/open_1',
            '/somewhere/over/the/rainbow/open_2']
_write_flist(settings, openlist, 'mainwindow/open_files')
#CLICK CANCEL TO MESSAGE
mw = mainwindow.MainWindow(settings)
mw.close()
# open file list should be empty because cancel clicked
xlist = _read_flist(settings, 'mainwindow/open_files')
assert len(xlist) == 0
# recent file list should go in and come out the same
xlist = _read_flist(settings, 'mainwindow/recent_files')
assert len(xlist) == len(recentlist)
for path in xlist:
    assert path in recentlist
# log may not be empty owing to dictionary path msgs
#assert empty_log()

app.quit()
# idle a bit after quit to let garbage be collected
from PyQt5.QtTest import QTest
QTest.qWait(200)
