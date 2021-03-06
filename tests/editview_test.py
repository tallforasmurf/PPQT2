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
Unit test #1 for editview.py: simple tests with no visibility
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
my_path = os.path.realpath(__file__)
test_path = os.path.dirname(my_path)
files_path = os.path.join(test_path,'Files')
ppqt_path = os.path.dirname(test_path)
sys.path.append(ppqt_path)
from PyQt5.QtWidgets import QApplication, QWidget
app = QApplication(sys.argv)
app.setOrganizationName("PGDP")
app.setOrganizationDomain("pgdp.net")
app.setApplicationName("PPQT2")
from PyQt5.QtCore import QSettings
settings = QSettings()

import utilities

import dictionaries
settings = QSettings()
settings.clear()
settings.setValue("paths/dicts_path",files_path)
settings.setValue("dictionaries/default_tag","en_GB")
import mainwindow
mw = mainwindow.MainWindow(settings)
# mainwindow made a book and set it new-empty
the_book = mw.open_books[0]
# grab the editview, no api defined or needed
ev = the_book.editv
em = the_book.get_edit_model()


text = '''1. Now is the time
2. For all good bits
3. To come to the aid
4. Of their byte.
'''*40
em.setPlainText(text)

from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt # namespace for keys etc.

mw.show()

#vp = ev.Editor.viewport()
#print('viewport w {0} h{1}'.format(vp.width(),vp.height()))
#vb = ev.Editor.verticalScrollBar()
#print('vertical min {0} max {1}'.format(vb.minimum(),vb.maximum()))

#while utilities.ok_cancel_msg('Make a selection','i make heem veezeebul'):
    #QTest.qWait(4000)
    #ev.center_this(ev.Editor.textCursor())
    #fm = ev.Editor.fontMetrics()
    #print('fm h {0} l {1} sp {2}'.format(
        #fm.height(), fm.leading(), fm.lineSpacing() ) )
    ##ed = ev.Editor
    ##tc = ed.textCursor()
    ##print('cursor pa',tc.position(),tc.anchor())
    ##qr = ed.cursorRect(tc)
    ##print('crect xywh',qr.x(),qr.y(),qr.width(),qr.height())
    ##vp = ed.viewport()
    ##qr = vp.geometry()
    ##print('viewp xywh',qr.x(),qr.y(),qr.width(),qr.height())
#app.exec_()
#exit()

# now to the testing

key_names = {
    'up':Qt.Key_Up,'dn':Qt.Key_Down,'lf':Qt.Key_Left,'rt':Qt.Key_Right
    }
mod_names = {
    'ctl':Qt.ControlModifier, 'shf':Qt.ShiftModifier,
    'alt':Qt.AltModifier }

test_target = None

def key_into( key, mod=None, wait=50 ):
    xkey = key_names[key] if isinstance(key,str) else key
    xmod = mod_names[mod] if mod else Qt.NoModifier
    QTest.keyClick( test_target, xkey, xmod, wait )

def key_seq(seq):
    for (key, mod) in seq :
        key_into(key, mod)

def check_sel(str):
    qtc = ev.get_cursor()
    sel = qtc.selectedText()
    print('{0} v {1}'.format(str,sel))
    return str == sel

test_target = ev.Editor
# wait half a sec, key ctrl-up
key_into('up','ctl',200)
# then shift-right to select "1."
key_seq( [('rt','shf'),('rt','shf')] )
# check that
assert check_sel('1.')

# click in the linenumber field, select-all, key a 3 and return
test_target = ev.LineNumber
QTest.mouseClick(test_target,Qt.LeftButton)
key_into(Qt.Key_A, 'ctl')
key_into(Qt.Key_3)
key_into(Qt.Key_Enter)
# focus should now be back to editor, shift-right to select "3."
test_target = ev.Editor
key_seq( [('rt','shf'),('rt','shf')] )
# check that
assert check_sel('3.')
# try a couple of invalid line numbers, each time verifying the
# selection hasn't changed.
test_target = ev.LineNumber
QTest.mouseClick(test_target,Qt.LeftButton)
key_into(Qt.Key_A, 'ctl')
key_into(Qt.Key_0)
key_into(Qt.Key_Enter)
assert check_sel('3.')
assert check_log('invalid line number',logging.ERROR)
QTest.mouseClick(test_target,Qt.LeftButton)
key_into(Qt.Key_A, 'ctl')
key_into(Qt.Key_9)
key_into(Qt.Key_9)
key_into(Qt.Key_9)
key_into(Qt.Key_Enter)
assert check_sel('3.')
assert check_log('invalid line number',logging.ERROR)

# click in the image name field, select all, key X and return
# then verify that the field has been cleared and the editor
# position hasn't changed.
test_target = ev.ImageFilename
QTest.mouseClick(test_target,Qt.LeftButton)
key_into(Qt.Key_A, 'ctl')
key_into(Qt.Key_X)
key_into(Qt.Key_Enter)
# focus should now be back to editor with "3." still selected
check_sel('3.')
dbg=test_target.text()
assert test_target.text() == ''
assert check_log('invalid image name',logging.INFO)
# check zoom keys
import fonts
test_target = ev.Editor
pts = ev.Editor.font().pointSize()
key_into(Qt.Key_Plus, 'ctl')
ptz  = ev.Editor.font().pointSize()
assert ptz == (pts+1)
while ptz < fonts.POINT_SIZE_MAXIMUM:
    key_into(Qt.Key_Plus, 'ctl')
    ptz = ev.Editor.font().pointSize()
key_into(Qt.Key_Plus, 'ctl') # take it to max
key_into(Qt.Key_Plus, 'ctl') # past max
assert check_log('rejecting zoom',logging.ERROR)
while ptz > fonts.POINT_SIZE_MINIMUM:
    key_into(Qt.Key_Minus, 'ctl')
    ptz = ev.Editor.font().pointSize()
key_into(Qt.Key_Minus, 'ctl') # to min
key_into(Qt.Key_Minus, 'ctl') # past min
assert check_log('rejecting zoom',logging.ERROR)
# stay up?
#app.exec_()
