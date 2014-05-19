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
                          utilities.py
A collection of file- and dialog-related functions for use by
other modules.

All uses of QFile, QDir, QFileDialog and the like are isolated to this module
even though that means some lengthy call indirections.

'''
from PyQt5.QtCore import (QDir, QFile, QFileInfo, QIODevice, QTextStream)
from PyQt5.QtWidgets import QFileDialog, QInputDialog, QMessageBox

import logging
utilities_logger = logging.getLogger(name='utilities')

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# The following class is in part a work-around for the annoying problem that
# QTextStream(QFile) depends on the existence of the QFile but does not take
# ownership of it, so if the QFile goes out of scope, the next use of the
# QTextStream will crash Python with a segfault. It also provides for getting
# the file name and path separately from a stream after it is open.

class FileBasedTextStream(QTextStream):
    def __init__(self, qfile):
        super().__init__(qfile)
        self.saved_file = qfile
    def filename(self):
        qfi = QFileInfo(self.saved_file)
        return qfi.fileName()
    def filepath(self):
        qfi = QFileInfo(self.saved_file)
        return qfi.absolutePath()

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
#  File-related convenience functions for sub-modules
#
# This is where we enforce our rule on encodings: we support only UTF-8 and
# ISO8859-1 (a.k.a. Latin-1), and of course ASCII which is a proper subset of
# both. UTF-8 is the default, but before opening a file we check the filename
# string for "-l" or "-ltn" before the suffix, (as in scannos-ltn.txt) or a
# suffix of ".ltn", and default to Latin-1. Otherwise we open it UTF-8.
#
def check_encoding(self, file_path):
    enc = 'UTF-8'
    finfo = QFileInfo(file_path)
    fname = finfo.fileName()
    if '-l.' in fname \
    or '-ltn.' in fname \
    or fname.endswith('.ltn') :
        enc = 'ISO-8859-1'
    return enc

# The following is a wrapper on QFileDialog.getOpenFileName,
# plus, after getting a path, it is opened as a QTextStream. Arguments:
#   caption: explanatory caption for the dialog (caller must TRanslate)
#   parent: optional QWidget over which to center the dialog
#   filter: optional filter string, see QFileDialog examples
#   starting_path: optional path to begin search, e.g. book path
# Return is either a FileBasedTextStream ready to read, or None.

def ask_existing_file(caption, parent=None, starting_path='', filter_string=''):
    # Ask the user to select a file
    (chosen_path, _) = QFileDialog.getOpenFileName(
            parent,
            caption,
            starting_path, filter_string
        )
    if len(chosen_path) == 0 : # user pressed Cancel
        return None
    if not QFile.exists(chosen_path): # Can this happen?
        utilities_logger.error('User chose nonexistent file {0}'.format(chosen_path))
        return None
    a_file = QFile(chosen_path)
    # Open the file - the .Text mode ensures correct newline conversion
    if not a_file.open(QIODevice.ReadOnly | QIODevice.Text) :
        utilities_logger.error('Error {0} ({1}) opening file {2}'.format(
            a_file.error(), a_file.errorString, chosen_path) )
        return None
    enc = self.check_encoding(chosen_path)
    stream = FileBasedTextStream(a_file)
    stream.setCodec(enc) # probably UTF-8, maybe ISO-8859-1
    return stream

# Display a modal request for a selection from a list of options using
# QInputDialog.getItem. Return the chosen item. Arguments are:
#
#   title : the title of the dialog
#   explanation: explanatory text below the title
#        both title and explanation must be TRanslated by caller!
#   item_list: a (python) list of (python) strings, the available items
#   current: optional index of the currently-chosen item
#   parent: optional QWidget over which to center the dialog
#
# QInputDialog returns a tuple of the actual text of the selected item or
# of the default item, and boolean True for OK or false for Cancel.

def choose_from_list(title, explanation, item_list, parent=None, current=0):
    (item_text, ok) = QInputDialog.getItem(
        parent,
        title, explanation,
        item_list, current,
        editable=False)
    if ok : return item_text
    return None

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# General message routines.
#
#Internal function to initialize a Qt message-box object with an icon,
# a main message line, and an optional second message line.

def _make_message ( text, icon, info = ''):
    mb = QMessageBox( )
    mb.setText( text )
    mb.setIcon( icon )
    if info:
        mb.setInformativeText( info )
    return mb

# Display a modal info message, blocking until the user clicks OK.
# No return value.

def info_msg ( text, info = '' ):
    mb = _make_message(text, QMessageBox.Information, info)
    mb.exec_()

# Display a modal warning message, blocking until the user clicks OK.
# No return value.

def warning_msg ( text, info = '' ):
    mb = _make_message(text, QMessageBox.Warning, info)
    mb.exec_()

# Display a modal query message, blocking until the user clicks OK/Cancel
# Return True for OK, False for Cancel.

def ok_cancel_msg ( text, info = '' ):
    mb = _make_message ( text, QMessageBox.Question, info)
    mb.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    return QMessageBox.Ok == mb.exec_()


# TODO remove dbg
from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QMouseEvent, QKeyEvent
def printEventMods(mods):
    '''
    Return a string containing names of the modifier bits in mods.
    mods is from event.modifiers.
    '''
    imods = int(mods)
    cmods = u''
    if imods & Qt.ControlModifier : cmods += u'Ctl '
    if imods & Qt.AltModifier: cmods += u'Alt '
    if imods & Qt.ShiftModifier : cmods += u'Shft '
    if imods & Qt.KeypadModifier : cmods += u'Kpd '
    if imods & Qt.MetaModifier : cmods += u'Meta '
    return cmods
def printKeyEvent(event):
    key = int(event.key())
    mods = int(event.modifiers())
    if key & 0x01000000 : # special/standard key
        print('logical key: mods {0:08X} key {1:08X}'.format(mods,key))
    else:
        cmods = printEventMods(mods)
        cmods += "'{0:c}'".format(key)
        print('data key: mods {0:08X} key {1:08X} {2}'.format(mods,key,cmods))

_Mevs = [2,3,4,5]
_Mnm = {QEvent.MouseButtonPress:'Down',
        QEvent.MouseButtonRelease:'Up',
        QEvent.MouseButtonDblClick:'Dblclick',
        QEvent.MouseMove:'Move'}
_Mbs = {Qt.LeftButton:'Left',
        Qt.RightButton:'Right',
        Qt.MidButton:'Middle'}

def printMouseEvent(event):
    name = _Mnm[event.type()]
    cmods = printEventMods(event.modifiers())
    mbu = _Mbs[event.button()]
    print('{0} {1} button {2} at x{3} y{4}'.format(cmods,mbu,name,event.x(),event.y()))
_Evs = {24:'WindowActivate',
        6:'KeyPress',
        8:'FocusIn',
        9:'FocusOut',
        110:'Tooltip',
        207:'InpMethQuery',
        12:'Paint',
        10:'Enter',
        68:'ChildAdded',
        69:'ChildPolished',
        71:'ChildRemoved',
        23:'FocusAboutToChange',
        25:'WindowDeactivate',
        75:'Polish',
        11:'Leave',
        13:'Move',
        14:'Resize',
        17:'Show',
        26:'ShowToParent',
        74:'PolishRequest',
        43:'MetaCall',
        78:'UpdateLater',
        76:'LayoutRequest',
        31:'Wheel',
        82:'ContextMenu',
        51:'ShortcutOverride',
        18:'Hide'
    }
_IQs = {
    Qt.ImEnabled:'ImEnable',
    Qt.ImMicroFocus:'ImMicroFocus',
    Qt.ImCursorRectangle:'CursorRectangle',
    Qt.ImFont:'ImFont',
    Qt.ImCursorPosition:'CursorPosition',
    Qt.ImSurroundingText:'SurroundingText',
    Qt.ImCurrentSelection:'CurrentSelection',
    Qt.ImMaximumTextLength:'MaxTextLen',
    Qt.ImAnchorPosition:'AnchorPosn',
    Qt.ImHints:'Hints',
    Qt.ImPreferredLanguage:'PreferredLang',
    Qt.ImPlatformData:'PlatformData'
    }

def printIMQ(event):
    '''print input method query'''
    qc = ''
    qs = event.queries()
    for q in _IQs.keys():
        if q & qs :
            qc += _IQs[q]
            qc += ' '
    print('InputMethodQuery for ',qc)

def printEvent(event):
    t = int(event.type())
    if t == 7 : # Key Release (don't print key press)
        printKeyEvent(event)
    elif t in _Mevs :
        printMouseEvent(event)
    elif t == 207:
        printIMQ(event)
    else:
        n = str(t)
        if t in _Evs : n = _Evs[t]
        print('event type ',n)
