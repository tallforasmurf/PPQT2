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
                          mainwindow.py

Create and manage the main window, menus, and toolbars.
This code manages app-level global resources, for example
  * the path(s) to user resources (the V1 "extras")
  * tags and paths to available spellcheck dicts (via dictionaries module)
  * fonts (by way of initializing the font module)
  * highlighting styles and colors (by way of colors module)
  * the Help file and its display panel

Within the main window it creates the widgets that display the various
"view" objects.

Instantiates and manages multiple Book objects.

Maintains a sequence of integers for successive "untitled-n" booknames.
Kept & used by File > New action.

Support the user action of dragging a panel out of the tab-set to be an
independent window, or vice-versa.

'''
from PyQt5.QtCore import (
    Qt,
    QByteArray,
    QCoreApplication,
    QDir, QFile, QFileInfo,QIODevice,
    QPoint,
    QSize
    )
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QAction,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMenu,
    QMenuBar,
    QScrollArea,
    QSplitter,
    QTabBar, QTabWidget,
    QWidget
    )
_TR = QCoreApplication.translate
import os# TODO remove

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# The 'extras' folder is needed by several modules, e.g. it is
# the default place to look for dictionaries and find macros.
# It is stored as a global resource in this module and accessed
# by global methods.
_EXTRAS = ''
def set_extras_path(path):
    global _EXTRAS
    _EXTRAS = path
def get_extras_path():
    global _EXTRAS
    return _EXTRAS

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Class of the single main window instance. One instance is created by
# ppqt.py at startup, and the open QSettings object is passed.
#
# The details of the following are coded out of line in the _uic method.
#
# * Get info from settings, including recent files and files open in the
#   previous session.
# * Create the app window.
# * Create the menus.
#
# If there were files open in a previous session, ask if we should reopen
# them, and do so -- or just create a single New file.
#
# Respond to menu actions and other UI inputs until shutdown.
#
# On close event, save stuff into settings and call sub-modules to do the
# same.
#
# Files that are not open now, for example the list of recent files, are kept
# as complete absolute path strings. The utilities module has some useful
# functions for working with these.
#
# The set of currently-open files is stored as a dict { n: Book-object }
# where n is a sequence number assigned when a file is opened. The file name,
# path, and other info can be interrogated from the Book-object.
#

import fonts
import dictionaries
import colors
import constants as C
import logging
import utilities
import metadata
import book
mainwindow_logger = logging.getLogger(name='main_window')

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Dicts copied from the following are used to keep track of the several
# view-panel objects owned by each Book. A new Book gets a copy and fills
# it in with references to its view objects. The main window keeps a copy
# that has references to the objects currently being displayed. The key
# is the name of the panel that appears in its tab. The value is a widget.

PANEL_DICT = {
    'Images':None,
    'Notes':None,
    'Find' :None,
    'Pages':None,
    'Chars':None,
    'Words':None,
    'Fnote':None,
    'Loupe':None,
    'default' : ['Images','Notes','Find','Words','Chars','Pages','Fnote','Loupe'],
    'tab_list' : None, # supplied in Book, updated in focus_me
    'current' : 0
    }

class MainWindow(QMainWindow):

    def __init__(self, settings=None):
        super().__init__()
        # Save the settings object for now and shutdown time.
        self.settings = settings
        # Initialize the sequence number for opened files
        self.book_number = 0
        # Initialize user's choice of extras path if known
        set_extras_path(settings.value("mainwindow/extras_path",''))
        # Initialize the path to the last-opened file, used to
        # start file-open dialogs.
        self.last_open_path = '.'
        # Initialize our font db
        fonts.initialize(settings)
        # Set our font, which will propogate to our child widgets.
        fonts.notify_me(self._font_change) # ask for a signal
        self._font_change(False) # fake a signal now
        # Initialize the dictionary apparatus
        dictionaries.initialize(settings)
        # Initialize the color choices
        colors.initialize(settings)
        # Initialize our dict of active panels
        self.panel_dict = PANEL_DICT.copy()
        # Initialize our dict of open documents {seqno:Book}
        self.open_books = {}
        self.focus_book = None # seqno of book in focus, see _focus_me
        # Initialize the list of recent files
        self.recent_files = []

        # Create the main window and set up the menus.
        self._uic()

        # Initialize the set of files actually open when we shut down.
        last_session = self._read_flist('mainwindow/open_files')
        if len(last_session) : # there were some files open
            if len(last_session) == 1 :
                msg = _TR('Start-up', 'One book was open at the end of the last session.')
            else:
                msg = _TR('Start-up', '%n books were open at the end of the last session.',
                          n=len(last_session) )
            info = _TR("Start-up", "Click OK to re-open all")
            if utilities.ok_cancel_msg( msg, info) :
                for file_path in last_session :
                    ftbs = utilities.path_to_stream(file_path)
                    if ftbs :
                        self._open(ftbs)
        if 0 == len(self.open_books) :
            # We did not re-open any books, either because there were
            # none, or the user said No, or perhaps they were not found.
            self._new() # open one, new, book.

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # Make a selected book the focus of all panels. This happens when a file
    # is first opened, and when a Book's editview widget gets focus-in.
    # Display that Book's various "-view" objects in panels, in the order
    # that the user left them and with the same active panel as before. Note
    # that a book (editview) can get a focus-in event when it was already the
    # focus in this sense, for example if this app was hidden and then
    # brought to the front. So be prepared for redundant calls.
    def focus_me(self, book_index):
        outgoing = self.focus_book
        if book_index == outgoing : return
        # Record the user's arrangement of panels for the outgoing book,
        # as a list of tuples ('tabname', widget) in correct sequence.
        if outgoing is not None : # false first time and after File>Close
            out_panel_dict = self.open_books[outgoing].panel_dict
            widg_list = []
            for ix in range( self.panel_tabset.count() ):
                widg_list.append (
                    (self.panel_tabset.tabText(ix), self.panel_tabset.widget(ix))
                    )
            out_panel_dict['tab_list'] = widg_list
            out_panel_dict['current'] = self.panel_tabset.currentIndex()
        # Change all the panels to the widgets, in the sequence, of the new book
        in_panel_dict = self.open_books[book_index].panel_dict
        widg_list = in_panel_dict['tab_list']
        self.panel_tabset.clear()
        for ix in range( len(widg_list) ):
            (tab_text, widget) = widg_list[ix]
            self.panel_tabset.insertTab(ix, widget, tab_text)
        self.panel_tabset.setCurrentIndex(in_panel_dict['current'])
        self.editview_tabset.setCurrentIndex(
            self.editview_tabset.indexOf(
                self.open_books[book_index].get_edit_view() ) )
        self.focus_book = book_index

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # Implement File>New:
    #    Create a Book object
    #    Call its new_empty() method,
    #    Add it to the open_books dict keyed by its sequence number,
    #    Display its text editor in a tab with the document name, and
    #    Give it the focus.
    def _new(self):
        seq = self.book_number
        self.book_number += 1
        new_book = book.Book( seq, self )
        new_book.new_empty()
        self.open_books[seq] = new_book
        self.editview_tabset.addTab(
            new_book.get_edit_view(), new_book.get_book_name() )
        self.focus_me(seq)


    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # Quick check to see if a file path is already open. Called from _open
    # and from _build_recent (menu). Returned value is the sequence number
    # of the open book, or None.
    def _is_already_open(self, path):
        for (seq, book_object) in self.open_books.items():
            if path == book_object.get_book_full_path() :
                return seq
        return None

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # Implement File>Open. Dialog with the user (file dialog starts with
    # last-used book path). Result is None or a FileBasedTextStream that we
    # pass to _open().
    def _file_open(self) :
        fbts = utilities.ask_existing_file(
            _TR( 'File:Open dialog','Select a book file to open'),
            parent=self, starting_path=self.last_open_path)
        if fbts : # yes a readable file was chosen.
            seq = self._is_already_open(fbts.fullpath())
            if seq is None :
                self._open( fbts )
            else :
                self.focus_me(seq)

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # Open a file, given the document as a FileBasedTextStream
    # * determine if there is a .meta file, a .bin file, or neither
    # * create a metadata input stream if possible
    # * if no .meta, look for good_words and bad_words
    # * if the only open book is the "Untitled-0" made at startup and
    #     it is unmodified, delete it.
    # * call Book.old_book() or .new_book() as appropriate
    # * add this book's editview to the edit tabset
    # * give this book the focus.

    def _open(self, fbts):
        base_name = fbts.basename()
        gw_stream = None
        bw_stream = None
        gg_stream = None
        # open the metadata stream, which is always UTF-8
        meta_stream = utilities.related_suffix(fbts, 'meta', encoding=C.ENCODING_UTF)
        if meta_stream is None :
            # opening book without .meta; look for .bin which is always LTN1
            bin_stream = utilities.related_suffix(fbts,'bin',encoding=C.ENCODING_LATIN)
            if bin_stream :
                gg_stream = metadata.translate_bin(bin_stream,fbts)
            # Look for good_words.txt, bad_words.txt.
            gw_stream = utilities.related_file( fbts, 'good_words*.*' )
            bw_stream = utilities.related_file( fbts, 'bad_words*.*' )
        seq = self.book_number
        # If opening a book, and the only open book is the default new one
        # created at startup, and it has not been modified, get rid of it.
        if seq == 1 \
        and self.open_books[0].get_book_name() == 'Untitled-0' \
        and not self.open_books[0].get_save_needed() :
            self.editview_tabset.clear()
            self.panel_tabset.clear()
            self.focus_book = None
            seq = 0
        else:
            # Some other book open, or user typed into the default New one.
            self.book_number += 1
        # Make the Book object and stow it in our open book dict
        a_book = book.Book( seq, self )
        self.open_books[seq] = a_book
        if meta_stream : # opening a book we previously saved
            a_book.old_book( fbts, meta_stream )
        else :
            a_book.new_book( fbts, gg_stream, gw_stream, bw_stream )
        self.editview_tabset.addTab(a_book.get_edit_view(), a_book.get_book_name())
        self.focus_me(seq)
        self.last_open_path = fbts.folderpath() # start for next open or save
        self._add_to_recent(fbts.fullpath())

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # Save the book that is currently in focus under its present name, if it
    # is modified. Return True if the save completed, else False.
    # If the active book is a New one, force a Save-As action instead.
    def _save(self):
        active_book = self.open_books[self.focus_book]
        if active_book.get_save_needed() :
            if active_book.get_book_name().startswith('Untitled-'):
                return self._save_as()
            doc_stream = utilities.path_to_output( active_book.get_book_full_path() )
            if doc_stream : # successfully opened for output
                meta_stream = utilities.related_output(doc_stream,'meta')
                if not meta_stream:
                    utilities.warning_msg(
                        _TR('File:Save', 'Unable to create metadata file.'),
                        _TR('File:Save', 'Use loglevel=error for details.') )
                    return False
            else:
                utilities.warning_msg(
                    _TR('File:Save', 'Unable to open file for writing.'),
                    _TR('File:Save', 'Use loglevel=error for details.') )
                return False
            return active_book.save_book(doc_stream, meta_stream)

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # Implement Save As. Query the user for a file path and get that as an
    # output FileBasedTextStream. Call the book to rename itself, which makes
    # it modified. Change the text in the edit tab to match. Discard the FBTS
    # and call _save which will make another one.
    def _save_as(self):
        active_book = self.open_books[self.focus_book]
        fbts = utilities.ask_saving_file(
            _TR('File:Save As dialog',
                'Choose a new location and filename for this book' ),
            self, active_book.get_book_folder() )
        if fbts :
            active_book.rename_book(fbts)
            self.editview_tabset.setTabText(
                self.editview_tabset.currentIndex(),
                fbts.filename() )
            self._add_to_recent(fbts.fullpath())
            fbts = None # discard that object
            return self._save()
        else:
            return False

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # Implement Close. If the active book is modified, ask if it should
    # be saved. If it is 'Untitled-' that will turn into Save As.
    def _close(self):
        active_book = self.open_books[self.focus_book]
        if active_book.get_save_needed() :
            # Compose message of translated parts because _TR does not
            # allow for incorporating strings, only numbers.
            msg = _TR('File Close', 'Book file ', 'start of message')
            msg += active_book.get_book_name()
            msg += _TR('File Close', ' has been modified!', 'end of message')
            ret = utilities.save_discard_cancel_msg(
                msg,
                info = _TR('File Close',
                           'Save it, Discard changes, or Cancel Closing?')
                )
            if ret is None : # Cancel
                return
            if ret : # True==Save
                self._save()
        # Now, get rid of the active book in 3 steps,
        # 1, close the book's tab in the editview tabset. We don't know which
        # tab it is, because the user can drag tabs around.
        for i in range(self.editview_tabset.count()):
            if active_book.get_book_name() == self.editview_tabset.tabText(i):
                break
        self.editview_tabset.removeTab(i)
        # 2, remove the book from out dict of open books. Set focus_book, the
        # index of the active book, to None, so that focus_me will not try to
        # save its view panels.
        del self.open_books[self.focus_book]
        self.focus_book = None
        # 3, focus on some other book, the rightmost one if there are any,
        # or else create a new book.
        if len(self.open_books) :
            # There is at least one book still open. Get the book name
            # from the rightmost tab and then find that book in our dict.
            bookname = self.editview_tabset.tabText(self.editview_tabset.count()-1)
            for (seq, book_object) in self.open_books.items():
                if bookname == book_object.get_book_name() : break
            self.focus_me(seq)
        else:
            self._new()
        # the focus_me removed all references to active_book's view panels
        # except those in its PANEL_DICT. So the following should schedule
        # the book and its associated objects for garbage collect.
        active_book = None

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # Maintain the list of "recent" file paths. The list is kept in usage
    # order, so if a path is in the list now, delete it and then add it to
    # the front. Keep it at a max of 9 items by deleting the oldest if
    # necessary.
    def _add_to_recent(self, path):
        if path in self.recent_files :
            del self.recent_files[self.recent_files.index(path)]
        if len(self.recent_files) > 8 :
            del self.recent_files[8]
        self.recent_files.insert(0,path)

    # Upon the aboutToShow signal from the File menu, populate the Recent
    # submenu with a list of files, but only the ones that are currently
    # accessible. If one is on a volume (e.g. USB stick) and you unmount the
    # volume, the path should not appear in the menu until the volume is
    # mounted again.
    def _open_recent(self, path):
        fbts = utilities.path_to_stream(path)
        if fbts :
            self._open(fbts)

    def _build_recent(self):
        active_files = []
        for path in self.recent_files:
            seq = self._is_already_open(path)
            if (seq is None) and utilities.file_is_accessible(path) :
                active_files.append( (utilities.file_split(path),path) )
        if 0 == len(active_files):
            self.recent_menu.setEnabled(False)
            return
        self.recent_menu.setEnabled(True)
        self.recent_menu.clear()
        i = 1
        for ((fname, folder), path) in active_files:
            act = self.recent_menu.addAction(
                '{0} {1} {2}'.format(i,fname,folder)
                )
            act.triggered.connect( lambda: self._open_recent(path) )
            i += 1

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # User has chosen a different font; if it is the general font, set
    # that here so it will propogate to our children.
    def _font_change(self, is_mono):
        if not is_mono:
            self.setFont(fonts.get_general())

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # Create the UI contained within this QMainWindow object. This is a lean
    # main window indeed. We have no toolbar, no status bar, no dock,
    # nothing. Just a splitter with, on the left, a tabset for editviews, and
    # on the right, a scrollbar containing a tabset for panels. (Qt Designer
    # note: it is not possible to build this structure with the Designer. It
    # will not let you put the scroll area into the splitter.)
    #
    # TODO: create a custom QTabWidget using a custom QTabBar to implement
    # drag-out-of-tabset behavior, and use those here.
    def _uic(self):
        # Create the tabset that displays editviews
        self.editview_tabset = QTabWidget()
        self.editview_tabset.setMovable(True) # let user move tabs around
        # Create the tabset that displays find, notes, help &etc.
        self.panel_tabset = QTabWidget()
        self.panel_tabset.setMovable(True)
        # Create the splitter that contains the above two parts.
        self.splitter = QSplitter(Qt.Horizontal, self)
        self.splitter.setChildrenCollapsible(False)
        # Give just a little margin to the left of the editor
        self.splitter.setContentsMargins(8,0,0,0)
        self.splitter.addWidget(self.editview_tabset)
        self.splitter.addWidget(self.panel_tabset)
        # Set that splitter as the main window's central (and only) widget
        self.setCentralWidget(self.splitter)
        # Populate the panel tabset with empty widgets just so there will
        # be tabs that _swap can reference.
        for key in self.panel_dict.keys():
            widj = QWidget()
            self.panel_tabset.addTab(widj,key)
            self.panel_dict[key] = widj
        # Size and position ourself based on saved settings.
        self.move(self.settings.value("mainwindow/position", QPoint(50,50)))
        self.resize(self.settings.value("mainwindow/size", C.STARTUP_DEFAULT_SIZE))
        self.splitter.restoreState(
           self.settings.value("mainwindow/splitter",C.STARTUP_DEFAULT_SPLITTER) )
        # Store a reference to the application menubar. In Mac OS this
        # is a parentless menubar; other platforms it is the default.
        if C.PLATFORM_IS_MAC :
            self.menu_bar = QMenuBar() # parentless menu bar for Mac OS
        else :
            self.menu_bar = self.menuBar # refer to the default one
        # Create the File menu, located in our menu_bar.
        self.file_menu = self.menu_bar.addMenu(_TR('Menu name', '&File'))
        # Populate the File menu with actions.
        #  File:New -> _new()
        work = self.file_menu.addAction( _TR('File menu command','&New') )
        work.setShortcut(QKeySequence.New)
        work.setToolTip( _TR('File:New tooltip','Create a new, empty document') )
        work.triggered.connect(self._new)
        #  File:Open -> _file_open()
        work = self.file_menu.addAction( _TR('File menu command','&Open') )
        work.setShortcut(QKeySequence.Open)
        work.setToolTip( _TR('File:Open tooltip','Open an existing book') )
        work.triggered.connect(self._file_open)
        #  File:Save -> _file_save()
        work = self.file_menu.addAction( _TR('File menu command', '&Save') )
        work.setShortcut(QKeySequence.Save)
        work.setToolTip( _TR('File:Save tooltip','Save the active book') )
        work.triggered.connect(self._save)
        #  Save As -> _file_save_as()
        work = self.file_menu.addAction( _TR('File menu command', 'Save &As') )
        work.setShortcut(QKeySequence.SaveAs)
        work.setToolTip( _TR('File:Save As tooltip','Save the active book under a new name') )
        work.triggered.connect(self._save_as)
        #  Close -> _close()
        work = self.file_menu.addAction( _TR('File menu command', 'Close') )
        work.setShortcut(QKeySequence.Close)
        work.setToolTip( _TR('File:Close tooltip', 'Close the active book') )
        work.triggered.connect(self._close)
        # Open Recent gets a submenu that is added to the File menu.
        # The aboutToShow signal is connected to our _build_recent slot.
        self.recent_menu = QMenu( _TR('Sub-menu name', '&Recent Files') )
        work = self.file_menu.addMenu( self.recent_menu )
        work.setToolTip( _TR('File:Recent tooltip', 'List of recently-used files to open') )
        self.file_menu.aboutToShow.connect(self._build_recent)
        #  divider if not Mac
        if not C.PLATFORM_IS_MAC:
            self.file_menu.addSeparator()
        #  Preferences with the menu role that on mac, moves to the app menu
        #  Quit with the menu role that moves it to the app menu
        work = QAction( _TR('Quit command','&Quit'), self )
        work.setMenuRole(QAction.QuitRole)
        work.setShortcut(QKeySequence.Quit)
        work.triggered.connect(self.close)
        self.file_menu.addAction(work)

        # Initialize the list of "recent" files for the File sub-menu.
        # These files were not necessarily open at shutdown, just sometime
        # in the not too distant past.
        self.recent_files = self._read_flist('mainwindow/recent_files')


    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # Functions related to shutdown and management of settings.
    #
    # Factor out the job of reading/writing a list of files in the settings.
    # Input is a settings array key string like 'mainwindow/recent_files'
    # Output is a possibly empty list of canonical-file-path strings.
    def _read_flist(self, array_key):
        f_list = []
        f_count = self.settings.beginReadArray(array_key)
        for f in range(f_count): # which may be 0
            self.settings.setArrayIndex(f)
            f_list.append( self.settings.value('filepath') )
        self.settings.endArray()
        return f_list
    # Input is an array key and a possibly empty list of path strings
    def _write_flist(self, file_list, array_key):
        if len(file_list):
            self.settings.beginWriteArray( array_key, len(file_list) )
            for f in range(len(file_list)) :
                self.settings.setArrayIndex( f )
                self.settings.setValue( 'filepath',file_list[f] )
            self.settings.endArray()

    # Reimplement QWidget.closeEvent in order to save any open files
    # and update the settings.
    def closeEvent(self, event):
        # If there are any unsaved books, ask the user if they should be
        # saved. If the answer is yes, try to do so.
        unsaved = []
        for (seq, book_object) in self.open_books.items() :
            if book_object.get_save_needed() :
                unsaved.append(seq)
        if len(unsaved):
            if len(unsaved) == 1 :
                msg = _TR('Shutdown', 'There is one unsaved file')
            else :
                msg = _TR('Shutdown', 'There are %n unsaved files', n=len(unsaved))
            ret = utilities.save_discard_cancel_msg(
                msg, _TR('Shutdown', 'Save, Discard changes, or Cancel Quit?') )
            if ret is None :
                # user wants to cancel shutdown
                event.ignore()
                return
            if ret :
                # User want to save. Focus each unsaved file and call _save.
                # For all but "Untitled-n" documents this will be silent. For
                # those, it will open a save-as dialog. We ignore the return
                # from this because we cannot distinguish between a cancelled
                # file-open dialog and a file write error.
                for seq in unsaved :
                    self.focus_me(seq)
                    self._save()
        # Clear the settings so that old values don't hang around
        self.settings.clear()
        # Tell the submodules to save their current global values.
        colors.shutdown(self.settings)
        fonts.shutdown(self.settings)
        dictionaries.shutdown(self.settings)
        # Save the list of currently-open files in the settings, but do not
        # save any whose filename matches "Untitled-#" because that is an
        # unsaved New file (which the user chose not to save, above).
        open_paths = []
        for (index, book_obj) in self.open_books.items() :
            if not book_obj.get_book_name().startswith('Untitled-'):
                open_paths.append( book_obj.get_book_full_path() )
        self._write_flist( open_paths, 'mainwindow/open_files' )
        # Save the list of "recent" files in the settings.
        self._write_flist(self.recent_files, 'mainwindow/recent_files')
        # Save this window's position and size and splitter state
        self.settings.setValue("mainwindow/size",self.size())
        self.settings.setValue("mainwindow/position",self.pos())
        self.settings.setValue("mainwindow/splitter",self.splitter.saveState())
        # Save user's choice of extras path
        self.settings.setValue("mainwindow/extras_path",get_extras_path())
        # and that's it, we are done finished, over & out.
        event.accept()
