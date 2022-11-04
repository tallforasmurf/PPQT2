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
Unit test #1 for imageview: basic interactions with the book.
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
from PyQt5.QtCore import Qt, QFile, QIODevice, QTextStream
from PyQt5.QtTest import QTest
import sys
import os
my_path = os.path.realpath(__file__)
test_path = os.path.dirname(my_path)
file_path = os.path.join(test_path,'Files')
ppqt_path = os.path.dirname(test_path)
sys.path.append(ppqt_path)
import utilities
import metadata
import constants as C
# load a single-line metadata section - depends on mm
def load_header(mgr, section, parm, vers=None):
    stream = utilities.MemoryStream()
    if vers :
        stream << metadata.open_line('VERSION', vers)
    stream << metadata.open_line(section, parm)
    stream.rewind()
    mgr.load_meta(stream)
# dump all metadata and look at a specified one-line section to see
# that it matches.
def check_header(mgr, section, expected):
    stream = utilities.MemoryStream()
    mgr.write_meta(stream)
    stream.rewind()
    while True:
        line = stream.readLine()
        if stream.atEnd(): break
        if line.startswith('{{'+section) : break
    assert line == expected

from PyQt5.QtWidgets import QApplication,QWidget
from PyQt5.QtCore import QSettings
app = QApplication(sys.argv)

import mainwindow
# Create a main window, which creates an untitled book, which creates a page model
mw = mainwindow.MainWindow(QSettings())
# cheat and reach into the mainwindow and get that book
the_book = mw.open_books[0]

# get a ref to the imageviewer, make it big
iv = the_book.imagev
iv.resize(500,600)

# get a ref to the metadata manager used by load/check_header
mm = the_book.get_meta_manager()

# exercise the meta read/writes
load_header(mm,C.MD_IZ,'0.42')
check_header(mm,C.MD_IZ,'{{'+C.MD_IZ+' 0.42}}')
# get the default link-bits
check_header(mm,C.MD_IX,'{{'+C.MD_IX+' 1}}')
load_header(mm,C.MD_IX,'3')
check_header(mm,C.MD_IX,'{{'+C.MD_IX+' 3}}')
# check invalid meta
load_header(mm,C.MD_IZ,'2.0001')
check_log('Invalid IMAGEZOOM',logging.ERROR)
load_header(mm,C.MD_IZ,'0.14')
check_log('Invalid IMAGEZOOM',logging.ERROR)
load_header(mm,C.MD_IZ,'-0.20')
check_log('Invalid IMAGEZOOM',logging.ERROR)
load_header(mm,C.MD_IZ,'')
check_log('Invalid IMAGEZOOM',logging.ERROR)
load_header(mm,C.MD_IX,'1.1')
check_log('Invalid IMAGELINKING',logging.ERROR)
load_header(mm,C.MD_IX,'')
check_log('Invalid IMAGELINKING',logging.ERROR)
load_header(mm,C.MD_IX,'4')
check_log('Invalid IMAGELINKING',logging.ERROR)


# Load the book with our test book
path_to_sb = os.path.join(file_path,'small_book.txt')
qfile = QFile(path_to_sb)
qfile.open(QIODevice.OpenModeFlag.ReadOnly)
doc_stream = utilities.FileBasedTextStream(qfile)
the_book.new_book(doc_stream, None, None, None)


ed = the_book.get_edit_view().Editor

# put it on the screen, s.b. all gray, wait 500ms
mw.show()
QTest.qWait(1000)

# jump to page 3
ed.find('bazongas')
QTest.qWait(1000)

# page down a few times pausing each, then up
QTest.keyClick(iv, Qt.Key.Key_PageDown, Qt.KeyboardModifier.NoModifier, 100)
QTest.keyClick(iv, Qt.Key.Key_PageDown, Qt.KeyboardModifier.NoModifier, 100)
QTest.keyClick(iv, Qt.Key.Key_PageDown, Qt.KeyboardModifier.NoModifier, 100)
QTest.keyClick(iv, Qt.Key.Key_PageDown, Qt.KeyboardModifier.NoModifier, 100)
QTest.keyClick(iv, Qt.Key.Key_PageDown, Qt.KeyboardModifier.NoModifier, 100)
QTest.keyClick(iv, Qt.Key.Key_PageUp, Qt.KeyboardModifier.NoModifier, 100)
QTest.keyClick(iv, Qt.Key.Key_PageUp, Qt.KeyboardModifier.NoModifier, 100)

# click on the pct spinner and key a couple of numbers
pct = iv.zoom_pct # totally cheating here
QTest.mouseClick(pct,Qt.MouseButton.LeftButton)
QTest.keyClick(pct,Qt.Key.Key_A,Qt.KeyboardModifier.ControlModifier,250)
QTest.keyClicks(pct,'22')

# key the zoom keys a few times
QTest.keyClick(iv, Qt.Key.Key_Plus, Qt.KeyboardModifier.ControlModifier, 100)
QTest.keyClick(iv, Qt.Key.Key_Plus, Qt.KeyboardModifier.ControlModifier, 100)
QTest.keyClick(iv, Qt.Key.Key_Plus, Qt.KeyboardModifier.ControlModifier, 100)
QTest.keyClick(iv, Qt.Key.Key_Plus, Qt.KeyboardModifier.ControlModifier, 100)
QTest.keyClick(iv, Qt.Key.Key_Minus, Qt.KeyboardModifier.ControlModifier, 100)
QTest.keyClick(iv, Qt.Key.Key_Minus, Qt.KeyboardModifier.ControlModifier, 100)
QTest.keyClick(iv, Qt.Key.Key_Minus, Qt.KeyboardModifier.ControlModifier, 100)
QTest.keyClick(iv, Qt.Key.Key_Minus, Qt.KeyboardModifier.ControlModifier, 100)
QTest.keyClick(iv, Qt.Key.Key_Minus, Qt.KeyboardModifier.ControlModifier, 100)
QTest.keyClick(iv, Qt.Key.Key_Minus, Qt.KeyboardModifier.ControlModifier, 100)

QTest.keyClick(iv, Qt.Key.Key_PageDown, Qt.KeyboardModifier.NoModifier, 100)
QTest.keyClick(iv, Qt.Key.Key_PageDown, Qt.KeyboardModifier.NoModifier, 100)
QTest.keyClick(iv, Qt.Key.Key_PageDown, Qt.KeyboardModifier.NoModifier, 100)
QTest.keyClick(iv, Qt.Key.Key_PageDown, Qt.KeyboardModifier.NoModifier, 100)
QTest.keyClick(iv, Qt.Key.Key_PageDown, Qt.KeyboardModifier.NoModifier, 100)
QTest.keyClick(iv, Qt.Key.Key_PageDown, Qt.KeyboardModifier.NoModifier, 100)
QTest.keyClick(iv, Qt.Key.Key_PageDown, Qt.KeyboardModifier.NoModifier, 100)
QTest.keyClick(iv, Qt.Key.Key_PageDown, Qt.KeyboardModifier.NoModifier, 100)
QTest.keyClick(iv, Qt.Key.Key_PageDown, Qt.KeyboardModifier.NoModifier, 100)
QTest.keyClick(iv, Qt.Key.Key_PageDown, Qt.KeyboardModifier.NoModifier, 100)

tow = iv.zoom_to_width
toh = iv.zoom_to_height
QTest.mouseClick(tow,Qt.MouseButton.LeftButton)
QTest.qWait(1000)
QTest.mouseClick(toh,Qt.MouseButton.LeftButton)
QTest.qWait(1000)


# leave it up?
#app.exec_()

