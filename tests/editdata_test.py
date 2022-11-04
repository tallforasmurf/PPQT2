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
Unit test for editdata.py
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
import sys
import os
path = os.path.realpath(__file__)
path = os.path.dirname(path)
path = os.path.dirname(path)
sys.path.append(path)
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

from PyQt5.QtCore import QObject, QSettings
from PyQt5.QtGui import QTextBlock, QTextCursor
import editdata
import mainwindow
mw = mainwindow.MainWindow(QSettings())
the_book = mw.open_books[0]
the_doc = the_book.get_edit_model()

# edit data with some >ascii data
test_lines = ['Ōne','twő','thrĕep']
test_data = '\n'.join(test_lines)
the_doc.setPlainText(test_data)
#print('|'+the_doc.full_text()+'|')
#print(the_doc.blockCount())
assert the_doc.blockCount() == 3
assert the_doc.full_text() == test_data
assert the_doc._text is not None
# check that modified signal received
tc = QTextCursor(the_doc)
tc.setPosition(0)
tc.deleteChar()
assert the_doc._text is None
the_doc.undo(tc) # put text back to original

j = 0
for line in the_doc.all_lines():
    assert line == test_lines[j]
    j+= 1
for line in the_doc.z_to_a_lines(1,3):
    j -= 1
    assert line == test_lines[j]
assert j==0
# j now 0, following should detect error, yield nothing
for line in the_doc.a_to_z_lines(-1,2):
    j += 1
assert j==0
for line in the_doc.a_to_z_lines(1,0):
    j += 1
assert j==0
# a to z for a==z
for line in the_doc.a_to_z_lines(1,1) :
    assert line == test_lines[0]
tc.setPosition(5) # middle of 2nd line
for line in the_doc.cursor_lines(tc):
    assert line == test_lines[1]
tc.setPosition(10) # middle of 3rd line
tc.movePosition(1,QTextCursor.MoveMode.KeepAnchor)
j = 0
for line in the_doc.cursor_lines(tc):
    assert line == test_lines[j]
    j += 1
j = 0
for tb in the_doc.all_blocks():
    assert tb.text() == test_lines[j]
    j += 1
j = 1
for tb in the_doc.a_to_z_blocks(1,2):
    assert tb.text() == test_lines[j]
    j += 1
