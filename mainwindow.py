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
__version__ = "2.1.0"
__author__  = "David Cortesi"
__copyright__ = "Copyright 2013, 2014, 2015 David Cortesi"
__maintainer__ = "David Cortesi"

'''
                          mainwindow.py

Create and manage the main window, menus, and toolbars.

This code:

1. Manages app-level global resources used by other modules, such as

  * the path(s) to user resources "extras" and spellcheck dicts (via paths module)
  * default spellcheck dictionary tags (via dictionaries module)
  * fonts (via the font module)
  * highlighting styles and colors (via colors module)
  * the Help file and its display panel (via helpview)
  * the app-level Preferences (via preferences)

2. Creates the app-level menu structure, and defines all the menu actions.

3. Creates the widgets that display the various "view" objects that comprise
   the entire user interface.

4. Instantiates and manages multiple Book objects.

5. Maintains a sequence of integers for successive "untitled-n" booknames
   (kept & used by the File > New menu action)

6. Manages the change of user focus from one document to another, switching
   all the dependent panels of the incoming Book for those of the outgoing
   one (see focus_me()).

TODO Support the user action of dragging a panel out of the tab-set to be an
independent window, or vice-versa.

'''
from PyQt6.QtCore import (
    Qt,
    QByteArray,
    QCoreApplication,
    QPoint,
    QTimer
    )
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QMainWindow,
    QMenu,
    QMenuBar,
    QSplitter,
    QTabWidget,
    QWidget
    )
_TR = QCoreApplication.translate
import os# TODO remove
import preferences
import constants as C

'''

Manage the Edit menu for our sub-panels. The issue is that the Edit menu of
the app is global to the whole app, but the user interacts with one panel at
a time, the editview, perhaps the notes, then the footnotes etc. Not all
panels have a use for the Edit menu, but those that do, have unique uses for
the Edit actions like cut, paste etc. Paste with the Notes panel active needs
to call an action defined in the notesview module.

Each panel that does support Edit actions calls set_up_edit_menu() each time
it gets a focus-in event. This populates the Edit menu with QActions defined
by that panel, and makes the Edit menu visible. On focus-out, the panel calls
hide_edit_menu() to make the menu invisible.
'''
_EDIT_MENU = None # global reference to the only Edit menu, see _uic.
_LAST_MENU = None # id of last action list to populate the edit menu

'''
Populate the edit menu. The action_list is a list of triples,
('Title',slot,key), as required by QMenu.addAction. The caller can pass
(None,None,None) to get a menu separator.

We test the Python id of the given action_list so we can avoid the setup
work when, as often happens, one panel gets focus-in multiple times without
another panel having changed the menu.
'''
def set_up_edit_menu( action_list ) :
    global _EDIT_MENU, _LAST_MENU

    _EDIT_MENU.setEnabled(True) # make visible
    if id( action_list ) != _LAST_MENU :
        _LAST_MENU = id( action_list )
        _EDIT_MENU.clear()
        for (title, slot, key) in action_list :
            if title is None :
                _EDIT_MENU.addSeparator()
            else :
                act = _EDIT_MENU.addAction(title)
                act.setShortcut(key)
                act.triggered.connect(slot)

def hide_edit_menu():
    global _EDIT_MENU
    if not C.PLATFORM_IS_WIN :
        _EDIT_MENU.setEnabled(False)
    else :
        # Under Windows 7, when you click on the Edit menu button, it causes
        # an immediate focus-out event for the active panel. (Apparently the
        # machinery for keyboard accelerators causes the menu to act as a 
        # focus-taking widget?) That causes the above .setEnabled(False) call
        # to be issued whenever the user clicks on Edit, which makes the menu
        # unusable as a menu. So we do not do that in Windows.
        #
        # This has as a result that when you click on a panel that does not
        # declare its own edit menu, the prior panel's edit menu remains
        # active, including the actions. This produces some odd behaviors. I
        # really should add edit menu action lists to at least the Find
        # panel.
        pass
'''

Class of the single main window instance.

One instance of this class is created by ppqt.py at startup, and the open
QSettings object is passed.

The details of the following are coded out of line in the _uic method.

* Get info from settings, including recent files and files open in the
  previous session.
  
* Create the app window.

* Create the menus.

If there were files open in a previous session, ask if we should reopen
them, and do so -- or just create a single New file.

Respond to menu actions and other UI inputs until shutdown.

On close event, save stuff into settings and call sub-modules to do the
same.

Files that are not open now, for example the list of recent files, are kept
as complete absolute path strings. The utilities module has some useful
functions for working with these.

The set of currently-open files is stored as a dict { n: Book-object }
where n is a sequence number assigned when a file is opened. The file name,
path, and other info can be interrogated from the Book-object.
'''

import paths
import fonts
import dictionaries
import colors
import constants as C
import logging
import utilities
#import helpview
import book
#import translators # TODO - reenable translators
mainwindow_logger = logging.getLogger(name='main_window')
# from PyQt6.QtTest import QTest # dbg

'''
Dicts copied from the following are used to keep track of the several
view-panel objects owned by each Book. A new Book gets a copy and fills
it in with references to its view objects. The main window keeps a copy
that has references to the objects currently being displayed. These
dicts are used and updated by the focus_me() method.

The keys 'Images' through 'Loupe' are the labels of the view panels. The Book
object initializes their values with references to the widgets that
implement those panels.

Key 'default' is the default sequence of panel tabs, left to right, used by
the book to set itself up.

Key 'tab_list' is a list of tab labels in their actual sequence at the time
a book loses focus, as the user may have rearranged them.

Key 'current' is the tab index of the panel tab that was active when the
book lost focus, e.g. index of the Find or Fnote panel.

When a book loses focus, its panel labels and current index are stored
under 'tab_list' and the index of the current tab under 'current'. When a
book comes into focus the panel tabset is rebuilt in the correct sequence
from this info.
TODO: CHANGE THIS TO A DATA CLASS!
'''

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

    def __init__(self, settings):
        super().__init__()
        # Save the settings object for now and shutdown time.
        self.settings = settings
        # Initialize extras and dicts paths first, as other modules use them
        paths.initialize(settings)
        # Initialize our font db
        fonts.initialize(settings)
        # Set our font, which will propogate to our child widgets.
        fonts.notify_me(self._font_change) # ask for a signal
        self._font_change(False) # fake a signal now
        # Initialize the dictionary apparatus
        dictionaries.initialize(settings)
        # Initialize the color choices
        colors.initialize(settings)
        # Initialize the sequence number for opened files
        self.book_number = 0
        # Initialize the path to the last-opened file, used to
        # start file-open dialogs.
        self.last_open_path = '.'
        # Initialize our dict of active panels
        self.panel_dict = PANEL_DICT.copy()
        # Initialize our dict of open documents {seqno:Book}
        self.open_books = {}
        self.focus_book = None # seqno of book in focus, see _focus_me
        # Initialize the list of recent files
        self.recent_files = []
        # Initialize the handle of a help display widget
        self.help_widget = None # later, if at all
        # Finished initializing after the app is running
        QTimer.singleShot(300,self.finish_init)
        # Create the main window and set up the menus.
        self._uic()

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # As part of setup we often need to show the user a dialog, but when our
    # __init__ is first called, our window has not been shown and the
    # app.exec() call has not been made. If ok_cancel_msg() is used in that
    # condition, there is a big delay and spinning cursor on the mac. So this
    # code is called from a one-shot timer 300ms after the window has been
    # created, so we are sure the app is processing events etc.
    def finish_init(self):
        #self.finish_init = False # never do this again
        # Initialize the set of files actually open when we shut down.
        last_session = self._read_flist('mainwindow/open_files')
        if len(last_session) : # there were some files open
            if len(last_session) == 1 :
                msg = _TR('Start-up dialog', 'One book was open at the end of the last session.')
            else:
                msg = _TR('Start-up dialog', '%n books were open at the end of the last session.',
                          n=len(last_session) )
            info = _TR("Start-up dialog", "Click OK to re-open all")
            if utilities.ok_cancel_msg( msg, info, parent=self) :
                for file_path in last_session :
                    ftbs = utilities.path_to_stream(file_path)
                    if ftbs :
                        self._open(ftbs)
        if 0 == len(self.open_books) :
            # We did not re-open any books, either because there were
            # none, or the user said No, or perhaps they were not found.
            self._new() # open one, new, book.

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # Slot to receive the currentChanged signal from the editview tabset.
    # Look through self.open_books and find the one whose edit widget is
    # now current, and do a focus_me for it.
    def _editview_change(self, index):
        if index > -1 :
            eview = self.editview_tabset.widget(index)
            for (seqno, book) in self.open_books.items() :
                if eview == book.get_edit_view() :
                    self.focus_me(seqno)
                    return
            mainwindow_logger.error('cannot relate editview tab index to book')

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # Make a selected book the focus of all panels. This is called explicitly
    # when a book is first created, and when the editview tabset changes the
    # current selection. It is called also when an editview gets a focus-in
    # event.
    # Display that Book's various "-view" objects in panels, in the order
    # that the user left them and with the same active panel as before. Note
    # that a book (editview) can get a focus-in event when it was already the
    # focus in this sense, for example if this app was hidden and then
    # brought to the front. So be prepared for redundant calls.

    def focus_me(self, book_index):
        outgoing = self.focus_book
        if book_index == outgoing : return # redundant call
        mainwindow_logger.debug(
            'focusing {0} = {1}'.format(book_index,self.open_books[book_index].get_book_name())
        )
        self.focus_book = book_index
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

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # Called by the current book to make a particular tab the visible one,
    # e.g. to make the Find visible on a ^F. The argument is a widget
    # that should occupy one of the current tabs. Ask the tabset for its
    # index, and if it is found, make that the current index. (If it is
    # not found, log it and do nothing.)

    def make_tab_visible(self, tabwidg):
        ix = self.panel_tabset.indexOf(tabwidg)
        if ix >= 0 : # widget exists in this tabset
            self.panel_tabset.setCurrentIndex(ix)
            return
        mainwindow_logger.error('Request to show nonexistent widget')

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
        index = self.editview_tabset.addTab(
            new_book.get_edit_view(), new_book.get_book_name() )
        self.editview_tabset.setTabToolTip(index,
                _TR('Tooltip of edit of new unsaved file',
                    'this file has not been saved') )
        self.focus_me(seq)
    #
    # For use from translators, do the New operation and return the Book
    # that is created so it can be loaded with translated text.

    def do_new(self) :
        self._new()
        return self.open_books[self.focus_book]

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
            self._open( fbts )

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # Open a file, given the document as a FileBasedTextStream, and META
    # means our metafile suffix (C.METAFILE_SUFFIX).
    # * If file opened is fname.META, look for a file named fname; if it
    #   exists open it instead, e.g. given foo.txt.META, open foo.txt.
    #   If it doesn't exist, tell the user and exit.
    # * If a file of the same name and path is already open, just focus
    #   it and exit.
    # * Determine if there is a .META file, a .bin file, or neither
    # * Create a metadata input stream if possible
    # * If no .META, look for good_words and bad_words
    # * If the only open book is an "Untitled-n" and
    #     it is unmodified, delete it.
    # * Call Book.old_book() or .new_book() as appropriate
    # * Add this book's editview to the edit tabset
    # * Give this book the focus.

    def _open(self, fbts):
        # look for opening a .META file
        if C.METAFILE_SUFFIX == fbts.suffix():
            fb2 = utilities.file_less_suffix(fbts)
            if fb2 is None :
                m1 = _TR('File:Open','Cannot open a metadata file alone')
                m2 = _TR('File:Open','There is no book file matching ',
                         'filename follows this') + fbts.filename()
                utilities.warning_msg(m1, m2, parent=self)
                return
            # we see foo.txt with foo.txt.META, silently open it
            fbts = fb2
        # look for already-open file
        seq = self._is_already_open(fbts.fullpath())
        if seq is not None :
            self.focus_me(seq)
            return
        # start collecting auxiliary streams
        gw_stream = None
        bw_stream = None
        #gg_stream = None
        # open the metadata stream, which is always UTF-8
        meta_stream = utilities.related_suffix(fbts, C.METAFILE_SUFFIX, encoding=C.ENCODING_UTF8)
        if meta_stream is None :
            # opening book without metadata; look for .bin which is always LTN1
            # This is no longer supported - somebody who cares, can write a
            # .bin-to-JSON utility if they want.
            #bin_stream = utilities.related_suffix(fbts,'bin',encoding=C.ENCODING_LATIN)
            #if bin_stream :
                #gg_stream = metadata.translate_bin(bin_stream,fbts)
            # Look for good_words.txt, bad_words.txt.
            gw_stream = utilities.related_file( fbts, 'good_words*.*' )
            bw_stream = utilities.related_file( fbts, 'bad_words*.*' )
        seq = self.book_number
        # If the only open book is the new one created at startup or when all
        # books are closed (which will have key 0), and it has not been
        # modified, get rid of it.
        if len(self.open_books) == 1 \
        and 0 == list(self.open_books.keys())[0] \
        and self.open_books[0].get_book_name().startswith('Untitled-') \
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
            a_book.new_book( fbts, gw_stream, bw_stream )
        index = self.editview_tabset.addTab(
            a_book.get_edit_view(), a_book.get_book_name())
        self.editview_tabset.setTabToolTip(index,
            a_book.get_book_folder() )
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
                meta_stream = utilities.related_output(doc_stream,C.METAFILE_SUFFIX)
                if not meta_stream:
                    utilities.warning_msg(
                        _TR('File:Save', 'Unable to open metadata file for writing.'),
                        _TR('File:Save', 'Use loglevel=error for details.'),
                        parent=self )
                    return False
            else:
                utilities.warning_msg(
                    _TR('File:Save', 'Unable to open book file for writing.'),
                    _TR('File:Save', 'Use loglevel=error for details.'),
                    parent=self )
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
            self.editview_tabset.setTabToolTip(
                self.editview_tabset.currentIndex(),
                active_book.get_book_folder() )
            self._add_to_recent(fbts.fullpath())
            fbts = None # discard that object
            return self._save()
        else:
            return False

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # Implement Close. If the active book is modified, ask if it should
    # be saved. If it is 'Untitled-' that will turn into Save As.
    def _close(self):
        target_index = self.focus_book # active edit tab is to close
        target_book = self.open_books[target_index]
        if target_book.get_save_needed() :
            # Compose message of translated parts because _TR does not
            # allow for incorporating strings, only numbers.
            msg = _TR('File Close dialog', 'x file ', 'filename follows here')
            msg += target_book.get_book_name()
            msg += _TR('File Close dialog', ' has been modified!', 'filename precedes this')
            ret = utilities.save_discard_cancel_msg(
                msg,
                info = _TR('File Close dialog',
                           'Save it, Discard changes, or Cancel Closing?'),
                parent=self )
            if ret is None : # Cancel
                return
            if ret : # True==Save
                self._save()
        # Now, get rid of the active book in 3 steps,
        # 1, close the book's tab in the editview tabset. We don't know which
        # tab it is, because the user can drag tabs around.
        i = self.editview_tabset.indexOf(target_book.get_edit_view())
        # The following causes another tab to be focussed, changing self.focus_book
        # and saving target_book's tabs in target_book, not that we care.
        self.editview_tabset.removeTab(i)
        # 2, remove the book from our dict of open books.
        del self.open_books[target_index]
        # 3, if there are any open books remaining, the tab widget has
        # activated one of them by its rules, which caused a show signal and
        # entry to _focus_me already. However if there are no remaining books
        # there was no show signal or focus_me and the closed book's panels
        # are still in the tabset.
        if 0 == len(self.open_books) :
            self.book_number = 0 # restart the sequence
            self.focus_book = None
            self._new()
        # One way or the other, a focus_me has removed all references to
        # active_book's view panels except those in its PANEL_DICT. So the
        # following assignment should remove the last reference to the book,
        # and schedule the book and associated objects for garbage collect.
        target_book = None

    ## -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    ## Implement a Translate... submenu command. Call translators.xlt_book
    ## with the book object that is currently in focus. If the process works
    ## xlt_book will create a new book by calling do_new() and load it.
    ##
    #def _xlt_a_book( self ):
        #book = self.open_books[ self.focus_book ]
        #datum = self.sender().data()
        #translators.xlt_book( book, datum, self )

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # Implement loading and saving find panel user buttons. Start the search
    # for files in the active book's folder. User can navigate to extras
    # if need be.
    def _find_save(self):
        target_book = self.open_books[self.focus_book]
        find_panel = target_book.get_find_panel()
        stream = utilities.ask_saving_file(
            _TR('File:Save Find Buttons open dialog',
                'Choose file to contain find button definitions'),
            self,
            starting_path=target_book.get_last_find_button_path(),
            encoding='UTF-8')
        if stream : # is not None, file is open
            target_book.set_last_find_button_path( stream.fullpath() )
            find_panel.user_button_output(stream)
        # else user hit cancel, forget it

    def _find_load(self):
        target_book = self.open_books[self.focus_book]
        find_panel = target_book.get_find_panel()
        stream = utilities.ask_existing_file(
            _TR('File:Load Find Buttons open dialog',
                'Choose a file of find button definitions'),
            self,
            starting_path=target_book.get_last_find_button_path(),
            encoding='UTF-8')
        if stream :# is not None, we opened it
            target_book.set_last_find_button_path( stream.fullpath() )
            find_panel.user_button_input(stream)
            target_book.metadata_modified(True,C.MD_MOD_FLAG)

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # Maintain the list of "recent" file paths. The list is kept in usage
    # order, so if a path is in the list now, delete it and then add it to
    # the front. Keep it at a max of 9 items by deleting the oldest if
    # necessary.
    def _add_to_recent(self, path):
        if path in self.recent_files :
            del self.recent_files[self.recent_files.index(path)]
        self.recent_files.insert(0,path)
        self.recent_files = self.recent_files[:9]

    # Upon the aboutToShow signal from the File menu, populate the Recent
    # submenu with a list of files, but only the ones that are currently
    # accessible. If one is on a volume (e.g. USB stick) and you unmount the
    # volume, the path should not appear in the menu until the volume is
    # mounted again.
    def _open_recent(self):
        path = self.sender().data()
        fbts = utilities.path_to_stream(path)
        if fbts :
            self._open(fbts)

    def _build_recent(self):
        active_files = []
        self.recent_menu.clear()
        self.recent_menu.setEnabled(False)
        for path in self.recent_files:
            seq = self._is_already_open(path)
            if (seq is None) and utilities.file_is_accessible(path) :
                active_files.append( path )
        if 0 == len(active_files):
            return
        self.recent_menu.setEnabled(True)
        for ( i, path ) in enumerate( active_files, start=1 ) :
            ( folder, fname ) = os.path.split( path )
            act = self.recent_menu.addAction(
                '{0} {1} {2}'.format( i, fname, folder )
                )
            act.setData( path )
            act.triggered.connect( self._open_recent )

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # User has chosen a different font; if it is the general font, set
    # that here so it will propogate to our children. n.b. this is never
    # used as the preference for UI font is not implemented.
    def _font_change(self, is_mono):
        if not is_mono:
            self.setFont(fonts.get_general())

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # Preferences menu action triggered. Create a Preferences dialog and
    # show it.
    def _preferences( self ) :
        p = preferences.PreferenceDialog( self )
        r = p.exec_()


    ## -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    ## Help menu action triggered. If the Help widget has not yet been
    ## created, create it. Otherwise just show it and raise it.
    #def _show_help(self):
        #if self.help_widget is None:
            #self.help_widget = helpview.HelpWidget()
        #self.help_widget.show()
        #self.help_widget.raise_()

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
        global _EDIT_MENU
        # Create the tabset that displays editviews
        self.editview_tabset = QTabWidget()
        self.editview_tabset.setMovable(True) # let user move tabs around
        self.editview_tabset.currentChanged.connect(self._editview_change)
        # Create the tabset that displays find, notes, help &etc.
        self.panel_tabset = QTabWidget()
        self.panel_tabset.setMovable(True)
        # Create the splitter that contains the above two parts.
        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)
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
        self.restoreState(
            self.settings.value("mainwindow/windowstate", QByteArray() ) )
        # Store a reference to the application menubar. In Mac OS this
        # is a parentless menubar; other platforms it is the default.
        if C.PLATFORM_IS_MAC :
            self.menu_bar = QMenuBar() # parentless menu bar for Mac OS
        else :
            self.menu_bar = self.menuBar() # refer to the default one
        # Create the File menu, located in our menu_bar.
        self.file_menu = self.menu_bar.addMenu(_TR('Menu name', '&File'))
        # Populate the File menu with actions.
        #  File:New -> _new()
        work = self.file_menu.addAction( _TR('File menu command','&New') )
        work.setShortcut(QKeySequence.StandardKey.New)
        work.setToolTip( _TR('File:New tooltip','Create a new, empty document') )
        work.triggered.connect(self._new)
        #  File:Open -> _file_open()
        work = self.file_menu.addAction( _TR('File menu command','&Open') )
        work.setShortcut(QKeySequence.StandardKey.Open)
        work.setToolTip( _TR('File:Open tooltip','Open an existing book') )
        work.triggered.connect(self._file_open)
        #  File:Save -> _file_save()
        work = self.file_menu.addAction( _TR('File menu command', '&Save') )
        work.setShortcut(QKeySequence.StandardKey.Save)
        work.setToolTip( _TR('File:Save tooltip','Save the active book') )
        work.triggered.connect(self._save)
        #  Save As -> _file_save_as()
        work = self.file_menu.addAction( _TR('File menu command', 'Save &As') )
        work.setShortcut(QKeySequence.StandardKey.SaveAs)
        work.setToolTip( _TR('File:Save As tooltip','Save the active book under a new name') )
        work.triggered.connect(self._save_as)
        #  Close -> _close()
        work = self.file_menu.addAction( _TR('File menu command', 'Close') )
        work.setShortcut(QKeySequence.StandardKey.Close)
        work.setToolTip( _TR('File:Close tooltip', 'Close the active book') )
        work.triggered.connect(self._close)
        #  Load Find Buttons -> _find_load()
        work = self.file_menu.addAction( _TR('File menu command', 'Load Find Buttons') )
        work.setToolTip( _TR('File:Load Find Buttons tooltip',
            'Load a file of definitions for the custom buttons in the Find panel' )
                         )
        work.triggered.connect(self._find_load)
        #  Save Find Buttons -> _find_save()
        work = self.file_menu.addAction( _TR('File menu command', 'Save Find Buttons') )
        work.setToolTip( _TR('File:Save Find Buttons tooltip',
                              'Save definitions of the custom buttons in the Find panel' )
                         )
        work.triggered.connect(self._find_save)

        ## Translate... gets a submenu with an entry for every Translator
        ## in extras/Translators (if any). The actions connect to _xlt_a_book.
        #self.translate_submenu = translators.build_xlt_menu( self, self._xlt_a_book )
        #self.file_menu.addMenu( self.translate_submenu )

        # Open Recent gets a submenu that is added to the File menu.
        # The aboutToShow signal is connected to our _build_recent slot.
        self.recent_menu = QMenu( _TR('Sub-menu name', '&Recent Files') )
        work = self.file_menu.addMenu( self.recent_menu )
        work.setToolTip( _TR('File:Recent tooltip', 'List of recently-used files to open') )
        self.file_menu.aboutToShow.connect(self._build_recent)

        # Put in a divider above the Help, Preferences and Quit actions.
        self.file_menu.addSeparator()

        ## Help opens or un-hides the Help viewer
        #work = self.file_menu.addAction( _TR('Help menu item', 'Help') )
        #work.setToolTip( _TR( 'Help menu item tooltip', 'Display the Help/User Manual in a separate window' ) )
        #work.triggered.connect(self._show_help)
        #self.file_menu.addAction(work)

        # Preferences: On the Mac, Preferences is automatically moved to the app menu.
        work = self.file_menu.addAction( _TR('Preferences menu item', 'Preferences') )
        work.setToolTip( _TR( 'Preferences menu item tooltip', 'Open the Preferences dialog to set paths, fonts, and text styles') )
        work.setMenuRole( QAction.MenuRole.PreferencesRole )
        work.triggered.connect( self._preferences )

        #  Quit choice, with the menu role that moves it to the app menu
        work = QAction( _TR('Quit command','&Quit'), self )
        work.setMenuRole(QAction.MenuRole.QuitRole)
        work.setShortcut(QKeySequence.StandardKey.Quit)
        work.triggered.connect(self.close)
        self.file_menu.addAction(work)

        # Initialize the list of "recent" files for the File sub-menu.
        # These files were not necessarily open at shutdown, just sometime
        # in the not too distant past.
        self.recent_files = self._read_flist('mainwindow/recent_files')

        # Create the Edit menu in the menu_bar, store a reference to it
        # in a static global, and immediately clear it.
        _EDIT_MENU = self.menu_bar.addMenu( C.ED_MENU_EDIT )
        hide_edit_menu()

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
                msg = _TR('Shutdown message', 'There is one unsaved file')
            else :
                msg = _TR('Shutdown message', 'There are %n unsaved files', n=len(unsaved))
            ret = utilities.save_discard_cancel_msg(
                msg,
                _TR('Shutdown message', 'Save, Discard changes, or Cancel Quit?'),
                parent=self )
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
        paths.shutdown(self.settings)
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
        self.settings.setValue("mainwindow/windowstate",self.saveState())
        # If the Help window is open, close it -- as a modeless widget,
        # it won't close just because we do.
        if self.help_widget : # is not None,
            self.help_widget.close()
        # and that's it, we are done finished, over & out.
        event.accept()
