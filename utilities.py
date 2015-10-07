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
__copyright__ = "Copyright 2013, 2014, 2015 David Cortesi"
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
    QFileDevice,
    QFileInfo,
    QIODevice,
    QTemporaryFile,
    QTextStream,
    QTextCodec,
    QByteArray
)
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QMessageBox,
    QPlainTextEdit,
    QProgressDialog,
    QPushButton,
    QVBoxLayout
)
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
    def __missing__(self, key): # called key is not in dict
        ret = self.f_of_x(key)  # calculate default value f(key)
        self[key] = ret         # save it in the dict for later
        return ret              # return it now

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
    return ( qfi.fileName(), qfi.canonicalPath() )

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Class MemoryStream provides a QTextStream based on an in-memory buffer
# which will not go out of scope causing a crash. It also provides the
# convenient methods rewind() and writeLine(). QTextStream.pos() is
# overridden to do a flush() before returning the position, otherwise
# it is never accurate. Note that pos() returns a count of bytes, while
# the units being written are 16-bit Unicode chars. Hence the sequence
# mst = MemoryStream(); mst.writeLine('FOO'); mst.pos() --> 8
#

class MemoryStream(QTextStream):
    def __init__(self):
        # Create a byte array that stays in scope as long as we do
        self.buffer = QByteArray()
        # Initialize the "real" QTextStream with a ByteArray buffer.
        super().__init__(self.buffer, QIODevice.ReadWrite)
        # The default codec is codecForLocale, which might vary with
        # the platform, so set a codec here for consistency. UTF-16
        # should entail minimal or no conversion on input or output.
        self.setCodec( QTextCodec.codecForName('UTF-16') )
    def pos(self):
        self.flush()
        return super().pos()
    def cpos(self) :
        return int( self.pos()/2 )
    def rewind(self):
        self.flush()
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
#   writeLine(str) to write a string with return
#   basename() to return the filename without its *final* suffix
#   suffix() to return the *final* suffix of the filename
#   filename() to return the filename with suffix(es)
#   folderpath() to return the canonical path to the containing folder
#   flush() calls the flush() method of our QFile. This overrides the flush()
#      method of QTextStream, which does not return a result. QFile.flush()
#      returns True for success, False for error.
#   show_error(action, parent) displays a warning message based on
#      the value of QFile.error() centered over parent, a window. This would
#      presumably be called after reading or flushing a file.

class FileBasedTextStream(QTextStream):
    def __init__(self, qfile):
        super().__init__(qfile)
        self.saved_file = qfile
        self.qfi = None # may never need this
    def rewind(self):
        self.flush()
        self.seek(0)
    def writeLine(self, str):
        self << str
        self << '\n'
    def open_mode(self):
        return self.saved_file.openMode()
    def fullpath(self):
        if self.qfi is None:
            self.qfi = QFileInfo(self.saved_file)
        return self.qfi.canonicalFilePath()
    def folderpath(self):
        if self.qfi is None:
            self.qfi = QFileInfo(self.saved_file)
        return self.qfi.canonicalPath()
    def filename(self):
        if self.qfi is None:
            self.qfi = QFileInfo(self.saved_file)
        return self.qfi.fileName()
    def basename(self):
        if self.qfi is None:
            self.qfi = QFileInfo(self.saved_file)
        return self.qfi.completeBaseName()
    def suffix(self):
        if self.qfi is None:
            self.qfi = QFileInfo(self.saved_file)
        return self.qfi.suffix()
    def flush(self):
        super().flush() # make sure text buffer goes to device
        return self.device().flush() # do a real flush
    def show_error( self, action, parent ):
        error_number = self.device().error()
        if error_number : # is not 0, no error
            error_string = self.device().errorString()
            msg_string = 'Error {} ({}) on {}'.format(
                error_number, error_string, action )
            warning_msg( msg_string, self.fullpath(), parent )

# This is where we enforce our rule on encodings: we support only UTF-8 and
# ISO8859-1 (a.k.a. Latin-1), and of course ASCII which is a proper subset of
# both. UTF-8 is the default, but before opening a file we check the filename
# string for "-l" or "-ltn" or "-lat" before the suffix, (as in
# scannos-lat.txt) or a suffix of ".ltn", and default those to Latin-1.
# Otherwise we open it UTF-8.
#
def _check_encoding(fname):
    enc = C.ENCODING_UTF
    if '-l.' in fname \
    or '-ltn.' in fname \
    or '-lat.' in fname \
    or fname.endswith('.ltn') :
        enc = C.ENCODING_LATIN
    return enc

# Convert a QFile for a valid path, into a FileBasedTextStream.
# Refactored out of the following functions.
def _qfile_to_stream(a_file, I_or_O, encoding=None):
    if not a_file.open(I_or_O | QIODevice.Text) :
        f_info = QFileInfo(a_file) # for the name
        utilities_logger.error('Error {0} ({1}) opening file {2}'.format(
            a_file.error(), a_file.errorString(), f_info.fileName() ) )
        return None
    fbts = FileBasedTextStream(a_file)
    fbts.setCodec(_check_encoding(fbts.filename()) if encoding is None else encoding)
    return fbts

# Convert a canonical file path to an input FileBasedTextStream, allowing for
# the case that it might not exist.
def path_to_stream(requested_path, encoding=None):
    a_file = QFile(requested_path)
    if not a_file.exists():
        utilities_logger.error('Request for nonexistent input file {0}'.format(requested_path))
        return None
    return _qfile_to_stream(a_file, QIODevice.ReadOnly, encoding)

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
        return _qfile_to_stream(a_file, QIODevice.ReadOnly, encoding)
    return None

# Given a FileBasedTextStream, look for a file with the same filename plus an
# additional suffix (e.g. foo.html.ppqt or foo.txt.bin) and if found, return
# a new stream for it.

def related_suffix(FBTS, suffix=C.METAFILE_SUFFIX, encoding=None):
    target = FBTS.filename() + '.' + suffix
    return related_file(FBTS, target, encoding)

# Given a FileBasedTextStream, look for a file with the same basename
# (e.g. given foo.html.blah, look for foo.html) and if there is just
# one such, return a new stream for it.

def file_less_suffix(FBTS):
    qd = QDir( FBTS.folderpath() )
    qd.setFilter(QDir.Files | QDir.Readable)
    if qd.exists(FBTS.basename()):
        a_file = QFile( qd.absoluteFilePath(FBTS.basename()) )
        return _qfile_to_stream(a_file, FBTS.open_mode())
    return None

# Convert a canonical file path to an output FileBasedTextStream, or return
# None if that isn't possible.
def path_to_output(requested_path, encoding=None):
    a_file = QFile(requested_path)
    return _qfile_to_stream(a_file, QIODevice.WriteOnly, encoding)

# Given a FileBasedTextStream, try to open an output file of the same
# basename but different suffix. Using the rather circuitous Qt
# equivalent of os.path.join.
def related_output(FBTS, suffix, encoding=None):
    qd = QDir( FBTS.folderpath() )
    target = FBTS.filename() + '.' + suffix
    a_file = QFile( qd.absoluteFilePath(target) )
    return _qfile_to_stream(a_file, QIODevice.WriteOnly, encoding)

# Create and return a FileBasedTextStream in a temporary location. Uses
# QTemporaryFile. When the FBTS is garbage-collected, the temp qfile goes out
# of scope and is automatically deleted. Although based on a QTemporaryFile
# all functions of FBTS work including filename, folderpath, rewind, etc.
def temporary_file(encoding = 'UTF-8'):
    tf = QTemporaryFile()
    tf.open() # actually create the file
    fbts = FileBasedTextStream(tf)
    fbts.setCodec(encoding)
    return fbts

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# File-related message routines.
#
# The following is a wrapper on QFileDialog.getOpenFileName, the Qt dialog
# for getting a path to an existing readable file.
#
# If the user selects a file it is opened as an input FileBasedTextStream.
# Return is a FileBasedTextStream ready to read, or None.
#
# Arguments:
#   caption: explanatory caption for the dialog (caller must TRanslate)
#   parent: optional QWidget over which to center the dialog
#   filter: optional filter string, see QFileDialog examples
#   starting_path: optional path to begin search, e.g. book path
# Encoding is not passed, so encoding depends on the filename or suffix.

def ask_existing_file(caption, parent=None, starting_path='', filter_string='',encoding=None):
    # Ask the user to select a file
    (chosen_path, _) = QFileDialog.getOpenFileName(
            parent,
            caption,
            starting_path, filter_string
        )
    if len(chosen_path) == 0 : # user pressed Cancel
        return None
    return path_to_stream(chosen_path,encoding)

# The following is a wrapper on QFileDialog.getSaveFileName, the Qt dialog
# for getting a path to a writeable file path.
#
# If the user selects a path, it is opened as an output FileBasedTextStream.
# Return is either that stream or None.
#
# Arguments:
#   caption: explanatory caption for the dialog (caller must TRanslate)
#   parent: optional QWidget over which to center the dialog
#   filter: optional filter string, see QFileDialog examples
#   starting_path: optional path to begin search, e.g. book path
# Encoding is not passed, so encoding depends on the filename or suffix.

def ask_saving_file(caption, parent=None, starting_path='', filter_string='', encoding=None):
    (chosen_path, _) = QFileDialog.getSaveFileName(
            parent,
            caption,
            starting_path, filter_string
        )
    if len(chosen_path) == 0 : # user pressed Cancel
        return None
    return path_to_output(chosen_path,encoding)

# The following uses QFileDialog.getOpenFileName to get the name of an existing
# file and then tests that the file is executable. Note that the static function
# getOpenFilename does not provide for a QDir.Executable enum-type filter. It
# only supports text-style filters e.g. "*.jpg" but that won't work to choose
# an executable in every platform. So we test for execut-ability on the return.
#
# If the user selects a file and it is executable, the full path is returned.
# Used to get the path to bookloupe and possibly other executable helpers.
#
# Arguments:
#   caption: explanatory caption for the dialog (caller must TRanslate)
#   parent: optional QWidget over which to center the dialog
#   starting_path: supposedly initializes the dialog but at least in Mac OS
#     seems to not have any effect.
#
# Return is a path, or '' if the user pressed Cancel, or None if the
# user selected an existing but non-executable file.

def ask_executable(caption, parent=None, starting_path=''):
    (chosen_path, _) = QFileDialog.getOpenFileName(
            parent,
            caption,
            starting_path,''
        )
    if len(chosen_path) == 0 : # user pressed Cancel
        return ''
    qfi = QFileInfo(chosen_path)
    if not qfi.isExecutable() :
        return None
    return chosen_path
#
# The following is a wrapper on QFileDialog.getExistingDirectory, the Qt
# dialog for getting a path to an existing folder. Used for choosing the
# extras and dictionary folders.
#
# Arguments:
#   caption: explanatory caption for the dialog (caller must TRanslate)
#   parent: optional QWidget over which to center the dialog
#   starting_path: optional path to begin search, e.g. book path
#
# Return is a path, or '' if the user pressed Cancel.

def ask_folder(caption, parent=None, starting_path=''):
    chosen_path = QFileDialog.getExistingDirectory(
            parent,
            caption,
            starting_path
        )
    return chosen_path

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#  General Message routines
#
# Display a modal request for a selection from a list of options using
# QInputDialog.getItem. Return the chosen item. Arguments are:
#
#   title : the title of the dialog
#   caption: explanatory text above the choice list
#      -- both title and explanation must be TRanslated by caller.
#   item_list: a Python list of strings, the available choice items
#   parent: required QWidget over which to center the dialog
#   current=0: optional index of the currently-chosen item
#
# QInputDialog returns a tuple of the actual text of the selected item or of
# the default item, and boolean True for OK or false for Cancel.

def choose_from_list(title, caption, item_list, parent, current=0):
    (item_text, ok) = QInputDialog.getItem(
        parent,
        title, caption,
        item_list, current,
        editable=False)
    if ok : return item_text
    return None

# Make an annoying noise of some kind.

def beep():
    QApplication.beep()

# Internal function to initialize a QMessageBox object with an icon,
# a main message line, and an optional second message line. The
# QMessageBox is used for all dialogs that need only button-clicks.
# Note that there seems no way to keep it from treating the informative
# text line as rich text, despite setTextFormat.

def _make_message ( text, icon, info = '', parent=None):
    mb = QMessageBox( parent )
    mb.setTextFormat(Qt.PlainText)
    mb.setText( text )
    mb.setIcon( icon )
    if info:
        mb.setInformativeText( info.replace('<','&lt;') )
    return mb

# Display a modal info message, blocking until the user clicks OK.
# No return value.

def info_msg ( text, info = '', parent=None ):
    mb = _make_message(text, QMessageBox.Information, info, parent)
    mb.exec_()

# Display a modal warning message, blocking until the user clicks OK.
# No return value.

def warning_msg ( text, info = '', parent=None ):
    mb = _make_message(text, QMessageBox.Warning, info, parent)
    mb.exec_()

# Display a modal query message, blocking until the user clicks OK/Cancel
# Return True for OK, False for Cancel.

def ok_cancel_msg ( text, info = '', parent=None ):
    mb = _make_message ( text, QMessageBox.Question, info, parent)
    mb.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    return QMessageBox.Ok == mb.exec_()

# Display a Save/Discard/Cancel choice and return True/False/None
# respectively. This is used by mainwindow when shutting down
# or when closing a modified file.

def save_discard_cancel_msg( text, info = '', parent=None ):
    mb = _make_message( text, QMessageBox.Warning, info, parent)
    mb.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
    mb.setDefaultButton(QMessageBox.Save)
    ret = mb.exec_()
    if ret == QMessageBox.Cancel : return None
    return ret == QMessageBox.Save

# Generic internal method to display a modal request for string input and
# wait for Ok or Cancel. The parameters are:
#
# * title is the dialog window title
# * caption is the text line above the string input field
#      -- both must be TRanslated by the caller
# * parent is the widget over which to center (required)
# * prepared='' is optional text to put in the input field
# * ok_label=None If a different OK is wanted, e.g. Find
#
# The return is a tuple of (OK-not-cancel, input-text).

def _string_query( title, caption, parent, prepared='', ok_label=None ):
    qd = QInputDialog(parent)
    qd.setInputMode(QInputDialog.TextInput)
    if ok_label is not None :
        qd.setOkButtonText(ok_label)
    qd.setTextValue(prepared)
    qd.setWindowTitle(title)
    qd.setLabelText(caption)
    ok = ( QDialog.Accepted == qd.exec_() )
    answer = qd.textValue() if ok else ''
    return (ok, answer)

# A general get-a-string from the user dialog. Inputs:
#
# * title, window title
# * caption, explanatory line above input field
#    -- both translated by the caller
# * parent, required widget over which to center
# * prepared='', optional text for the input field
#
# Return is None if the user Cancels, otherwise the input text.

def get_string( title, caption, parent, prepared='') :
    (ok, answer) = _string_query(title,caption,parent,prepared)
    if ok: return answer
    return None

#
# A simple find dialog, used by the Notes and other panels. Inputs:
#
# * parent, widget over which to center the dialog
# * caption, explanatory line above input field
#      must be translated by the caller
# * prepared='', optional text to pre-load input field
#
# Return is entered text, or None meaning Cancel was clicked.

def get_find_string(caption, parent, prepared = ''):
    (ok, answer) = _string_query(C.FIND_BUTTON,caption,parent,prepared,ok_label=C.FIND_BUTTON)
    if ok : return answer
    return None
#
# Create a QProgressDialog with no Cancel button and a 0.5-second display
# time, based on a title string and parent widget passed by the caller. The
# maximum value is set to 100. The user can either call setValue() in integer
# percents, or call setMaximum() to set a different end-value.
#
def make_progress(caption,  parent):
    progress = QProgressDialog( caption, None, 0, 100, parent)
    progress.setMinimumDuration(500)
    return progress

#
# Create a QDialog containing a PlainTextEdit as its input widget.
# This is used by the book to display and input book meta-info.
# Here we display the dialog and if the user clicks OK, we return
# the text in the editor. If Cancel, we return None.
#
# We are not translating the words OK and Cancel.
#
def show_info_dialog( caption, parent, initial_text ):
    dialog = QDialog( parent )
    dialog.setWindowTitle( caption )
    # Create OK and Cancel buttons in a horizontal box.
    ok_button = QPushButton("OK")
    ok_button.setDefault(True)
    ok_button.clicked.connect(dialog.accept)
    cancel_button = QPushButton("Cancel")
    cancel_button.setDefault(False)
    cancel_button.clicked.connect(dialog.reject)
    hbox = QHBoxLayout()
    hbox.addWidget(cancel_button,0)
    hbox.addStretch()
    hbox.addWidget(ok_button,0)
    # Lay out a Plain Text Edit above the buttons.
    vbox = QVBoxLayout()
    pt_editor = QPlainTextEdit()
    pt_editor.document().setPlainText( initial_text )
    vbox.addWidget(pt_editor,1)
    vbox.addLayout(hbox,0)
    dialog.setLayout(vbox)
    result = dialog.exec_()
    if result :
        return pt_editor.document().toPlainText()
    else :
        return None

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Decimal integer to Roman-numeral conversion, used by both pagedata (for
# folio values) and fnoteview (for renumbering footnotes).
# Adapted from Mark Pilgrim's "Dive Into Python".
_ROMAN_MAP = (('M',  1000),
              ('CM', 900),
              ('D',  500),
              ('CD', 400),
              ('C',  100),
              ('XC', 90),
              ('L',  50),
              ('XL', 40),
              ('X',  10),
              ('IX', 9),
              ('V',  5),
              ('IV', 4),
              ('I',  1))
def to_roman( n, lc=True ):
    if (0 < n < 5000) and int(n) == n :
        result = ""
        for numeral, integer in _ROMAN_MAP:
            while n >= integer:
                result += numeral
                n -= integer
    else : # invalid number, log but don't raise an exception
        utilities_logger.error(
            'Invalid number for roman numeral {}'.format(n) )
        result = "????"
    if lc : result = result.lower()
    return result

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Decimal to alpha conversion, used by fnotview for renumbering.
# input 1..18278 (26 + 26^2 + 26^3) yields output A..ZZZ.

AlphaMap = u'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
def to_alpha( n, lc=True ) :
    result = ''
    if (0 < n < 18278) and int(n) == n :
        while True :
            ( n, m ) = divmod( n-1, 26 )
            result = AlphaMap[m] + result
            if n == 0 : break
    else :
        utilities_logger.error(
            'Invalid number for alpha conversion {}'.format(n) )
        result = '???'
    if lc : result = result.lower()
    return result

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
        18:'Hide',
        103:'WindowBlocked',
        104:'WindowUnblocked'
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
    if t == 7 : # Key Release gets special details
        printKeyEvent(event)
    elif t in _Mevs :
        printMouseEvent(event)
    elif t == 207:
        printIMQ(event) # whatever that is
    else:
        s = 'spontaneous' if (t != 12 and event.spontaneous()) else ''
        n = _Evs[t] if t in _Evs else str(t)
        print('event type ',n,s)
