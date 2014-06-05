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
from PyQt5.QtCore import (
    QDir,
    QFile,
    QFileInfo,
    QIODevice,
    QTextStream,
    QTextCodec,
    QByteArray)
from PyQt5.QtWidgets import QFileDialog, QInputDialog, QMessageBox
import constants as C # for encoding names
import logging
utilities_logger = logging.getLogger(name='utilities')

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Path-string utilities. Mainwindow stores file paths as complete path
# strings but often needs to extract the filename, as when building the
# recent-files list. We could do that using Python's os.path, or we can use
# Qt's QFileInfo. This version uses QFileInfo but, because it is expected it
# may be called with the same paths repeatedly, and building a QFileInfo
# object is expensive, we cache them using a default dict.
#
# The basic defaultdict class uses a "default factory" that takes no
# arguments. We want a default dict where the default value for member x is
# f(x), or specifically, QFileInfo(x). This can be done with a subclass.
#
# Currently not putting any limit on the size of _FI_DICT. It will presumably
# end up with the sum of all "recent" paths at app startup (max 10) plus all
# files opened during a session (unlikely to be more than 10). It would be
# possible to add a length-limit to this class if needed.

from collections import defaultdict
class key_dependent_default(defaultdict):
    def __init__(self,f_of_x):
        super().__init__(None) # base class doesn't get a factory
        self.f_of_x = f_of_x # save f(x)
    def __missing__(self, key): # called when a default needed
        return self.f_of_x(key)
_FI_DICT = key_dependent_default( QFileInfo )

# Check if a file is accessible: is a file, exists, and is readable. Check
# goes quickly after the first call.

def file_is_accessible(path):
    global _FI_DICT
    qfi = _FI_DICT[path]
    return qfi.exists() and qfi.isFile() and qfi.isReadable()

# Split a full path into a tuple (filename, folderpath)
def file_split(path):
    global _FI_DICT
    qfi = _FI_DICT[path]
    return ( qfi.filename(), qfi.canonicalPath() )

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Class MemoryStream provides a QTextStream based on an in-memory buffer
# which will not go out of scope causing a crash. It also provides the
# convenient methods rewind() and writeLine()

class MemoryStream(QTextStream):
    def __init__(self):
        # Create a byte array that stays in scope as long as we do
        self.buffer = QByteArray()
        # Initialize the "real" QTextStream with a ByteArray buffer.
        super().__init__(self.buffer)
        # The default codec is codecForLocale, which might vary with
        # the platform, so set a codec here for consistency. UTF-16
        # should entail minimal or no conversion on input or output.
        self.setCodec( QTextCodec.codecForName('UTF-16') )
    def rewind(self):
        self.seek(0)
    def writeLine(self, str):
        self << str
        self << '\n'

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# The following class began as a work-around for the annoying problem that
# QTextStream(QFile) depends on the existence of the QFile but does not take
# ownership of it, so if the QFile goes out of scope, the next use of the
# QTextStream will crash Python with a segfault.
#
# It then began to sprout useful methods:
#   rewind() to prepare for a second reading
#   writeline(str) to write a string with return
#   basename() to return the filename without its suffix
#   filename() to return the filename with suffix(es)
#   folderpath() to return the canonical path to the containing folder

class FileBasedTextStream(QTextStream):
    def __init__(self, qfile):
        super().__init__(qfile)
        self.saved_file = qfile
        self.qfi = None # may never need this
    def rewind(self):
        self.seek(0)
    def writeLine(self, str):
        self << str
        self << '\n'
    def basename(self):
        if self.qfi is None:
            self.qfi = QFileInfo(self.saved_file)
        return self.qfi.baseName()
    def filename(self):
        if self.qfi is None:
            self.qfi = QFileInfo(self.saved_file)
        return self.qfi.fileName()
    def folderpath(self):
        if self.qfi is None:
            self.qfi = QFileInfo(self.saved_file)
        return self.qfi.canonicalPath()
    def fullpath(self):
        if self.qfi is None:
            self.qfi = QFileInfo(self.saved_file)
        return self.qfi.canonicalFilePath()

# This is where we enforce our rule on encodings: we support only UTF-8 and
# ISO8859-1 (a.k.a. Latin-1), and of course ASCII which is a proper subset of
# both. UTF-8 is the default, but before opening a file we check the filename
# string for "-l" or "-ltn" before the suffix, (as in scannos-ltn.txt) or a
# suffix of ".ltn", and default to Latin-1. Otherwise we open it UTF-8.
#
def check_encoding(fname):
    enc = C.ENCODING_UTF
    if '-l.' in fname \
    or '-ltn.' in fname \
    or fname.endswith('.ltn') :
        enc = C.ENCODING_LATIN
    return enc

# Convert a QFile for a file known to exist, into a FileBasedTextStream.
# Refactored out of the following functions.
def qfile_to_stream(a_file, encoding=None):
    if not a_file.open(QIODevice.ReadOnly | QIODevice.Text) :
        utilities_logger.error('Error {0} ({1}) opening file {2}'.format(
            a_file.error(), a_file.errorString, chosen_path) )
        return None
    fbts = FileBasedTextStream(a_file)
    fbts.setCodec(check_encoding(fbts.filename()) if encoding is None else encoding)
    return fbts

# Convert a canonical file path to a FileBasedTextStream, allowing
# for the case that it might not exist.
def path_to_stream(requested_path, encoding=None):
    a_file = QFile(requested_path)
    if not a_file.exists():
        utilities_logger.error('Request for nonexistent file {0}'.format(requested_path))
        return None
    return qfile_to_stream(a_file, encoding)

# The following is a wrapper on QFileDialog.getOpenFileName, the Qt dialog
# for getting a path to an existing readable file.
#
# If the user does select a path, it is opened as a FileBasedTextStream.
# Return is either a FileBasedTextStream ready to read, or None.
#
# Arguments:
#   caption: explanatory caption for the dialog (caller must TRanslate)
#   parent: optional QWidget over which to center the dialog
#   filter: optional filter string, see QFileDialog examples
#   starting_path: optional path to begin search, e.g. book path

def ask_existing_file(caption, parent=None, starting_path='', filter_string=''):
    # Ask the user to select a file
    (chosen_path, _) = QFileDialog.getOpenFileName(
            parent,
            caption,
            starting_path, filter_string
        )
    if len(chosen_path) == 0 : # user pressed Cancel
        return None
    return path_to_stream(chosen_path)

# Given a FileBasedTextStream (probably a document opened by the preceding
# function), look for a related file in the same folder and if found, return
# a new stream for it. The filename may be literal 'foo.typ' or a glob
# pattern like 'foo*.*'.

def related_file(FBTS, filename, encoding=None):
    qd = QDir( FBTS.folderpath() )
    qd.setFilter(QDir.Files | QDir.Readable)
    qd.setSorting(QDir.Type | QDir.Reversed)
    qd.setNameFilters( [filename] ) # literal name or 'foo*.*'
    names = qd.entryList()
    if names : # list is not empty, open the first
        a_file = QFile( qd.absoluteFilePath(names[0]) )
        return qfile_to_stream(a_file, encoding)
    return None

# Given a FileBasedTextStream, look for a file with the same basename but a
# different suffix, and if found, return a new stream for it.

def related_suffix(FBTS, suffix, encoding=None):
    target = FBTS.basename() + '.' + suffix
    return related_file(FBTS, target, encoding)


# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#  General Message routines
#
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


# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Diagnostic routines for evaluating events
# TODO REMOVE
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
