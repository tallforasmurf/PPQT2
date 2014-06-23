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
Unit test for noteview.py
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
ppqt_path = os.path.dirname(test_path)
sys.path.append(ppqt_path)
files_path = os.path.join(test_path, 'Files')
# Create an app and empty settings
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)
import constants as C
app.setOrganizationName("PGDP")
app.setOrganizationDomain("pgdp.net")
app.setApplicationName("PPQT2")
from PyQt5.QtCore import QSettings
settings = QSettings()
settings.setValue("dictionaries/path",files_path)
settings.setValue("dictionaries/default_tag","en_US")
import dictionaries
dictionaries.initialize(settings)
# Create a main window which creates a book
settings.clear()
import mainwindow
mw = mainwindow.MainWindow(settings)
the_book = mw.open_books[0] # grab the default book
mm = the_book.get_meta_manager()
# dump some stuff into it and see if we get it back
import utilities
import metadata
import constants as C
stream = utilities.MemoryStream()
astr = metadata.open_string(C.MD_NO)
zstr = metadata.close_string(C.MD_NO)
lstr = [C.UNICODE_REPL+'{{dangerous!}}']
for j in range(19):
    lstr.append('{0} yeah some notes here.'.format(j))
stream.writeLine(astr)
for line in lstr:
    stream.writeLine(line)
stream.writeLine(zstr)
stream.rewind()
mm.load_meta(stream)
stream.rewind()
mm.write_meta(stream)
stream.rewind()
while True:
    line = stream.readLine()
    if stream.atEnd(): break
    if line == astr : break
assert not stream.atEnd()
j = 0
for line in metadata.read_to(stream,C.MD_NO):
    assert lstr[j] == line
    j += 1
mw.show()
app.exec_()

