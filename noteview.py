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
                          noteview.py

Define a class to implement the Notes panel.

Based on QPlainTextEdit, and uses the default QTextDocument, hence it
incorporates its own minimal "model" and does not need a "notesdata.py".

One Noteview object is created by a Book as it initializes. Immediately
registers to read and write the NOTES section of metadata. The Book puts a
reference to the object in its PANELDICT, so whenever the Book becomes
active, the Noteview is displayed in the Notes tab.

It tracks its own QTextDocument's modification changes, and tells the Book
when the mod state changes.

Implements a keyEvent method to provide keystrokes for insertion of
{line#} and [image#] values, and to navigate to a noted line or image:

    shift-ctl-m inserts {line#}
    ctl-m when cursor is in or next to {line#}, jumps to that line
    shift-ctl-p inserts {image#}
    clt-p when cursor is in or next to [image#], jumps to that page
       n.b. not a conflict with "print" because we don't support print at all

Implements a simple (non-regex) Find:
    ctl-f brings up a simple modal dialog for Find text with OK and Cancel
    ctl-g does a find-again for last text

Implements text zoom similarly to the editview:
    ctl-plus zooms larger
    ctl-minus zooms smaller

Implements a minimal Edit menu with cut/copy/paste/undo/redo linked
to the builtin QPlainTextEdit slots. Enables that menu on focus-in,
disables it on focus-out.

TODO: resolve issues re keystrokes in mac os
'''
import constants as C
import fonts
import mainwindow
import utilities
import regex
from PyQt6.QtWidgets import (
    QAbstractScrollArea,
    QPlainTextDocumentLayout,
    QPlainTextEdit,
    QTextEdit,
    QMenu
    )
from PyQt6.QtGui import (
    QTextDocument,
    QTextCursor,
    QKeySequence
    )
from PyQt6.QtGui import QPalette
from PyQt6.QtCore import Qt, QCoreApplication
_TR = QCoreApplication.translate

class NotesPanel(QPlainTextEdit):
    def __init__(self, my_book, parent=None):
        super().__init__(parent)
        self.book = my_book
        ''' Where we store the last-sought-for find string '''
        self.find_text = None
        ''' Register to read and write metadata '''
        my_book.get_meta_manager().register( C.MD_NO, self._read_meta, self._save_meta )
        '''
        Set our only font (we don't care about the general font, only mono)
        This gets the Book's default size as it hasn't loaded a document yet.
        '''
        self.setFont(fonts.get_fixed(my_book.get_font_size()))
        ''' hook up to be notified of a change in font choice '''
        fonts.notify_me(self.font_change)
        ''' Set up our document not using the default one '''
        a_document = QTextDocument()
        a_document.setDocumentLayout(QPlainTextDocumentLayout(a_document))
        self.setDocument(a_document)
        ''' Turn off linewrap mode '''
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        '''
        The following kludge allows us to get the correct highlight color on
        focus-in. For unknown reasons Qt makes us use the "Inactive" color
        group even after focus-in. See focusInEvent() and focusOutEvent()
        below.
        '''
        self.palette_active = QPalette(self.palette())
        self.palette_inactive = QPalette(self.palette())
        b = self.palette().brush(QPalette.ColorGroup.Active,QPalette.ColorRole.Highlight)
        self.palette_active.setBrush(QPalette.ColorGroup.Inactive,QPalette.ColorRole.Highlight,b)
        '''
        Set the cursor shape to IBeam -- no idea why this supposed default
        inherited from QTextEdit, doesn't happen. But it doesn't.
        '''
        self.viewport().setCursor(Qt.CursorShape.IBeamCursor)
        ''' Hook up a slot to notice that the document has changed its
        modification state. '''
        self.document().modificationChanged.connect(self.yikes)
        ''' Create the list of actions for our edit menu and save it
        for use on focus-in. '''
        self.ed_action_list = [
            (C.ED_MENU_UNDO, self.undo, QKeySequence.StandardKey.Undo),
            (C.ED_MENU_REDO,self.redo,QKeySequence.StandardKey.Redo),
            (None, None, None),
            (C.ED_MENU_CUT,self.cut,QKeySequence.StandardKey.Cut),
            (C.ED_MENU_COPY,self.copy,QKeySequence.StandardKey.Copy),
            (C.ED_MENU_PASTE,self.paste,QKeySequence.StandardKey.Paste),
            (None, None, None),
            (C.ED_MENU_FIND,self.find_action,QKeySequence.StandardKey.Find),
            (C.ED_MENU_NEXT,self.find_next_action,QKeySequence.StandardKey.FindNext)
            ]
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    '''
    Save the current notes text to a metadata file. We write the whole text
    as one string, so the JSON is {"NOTES":"humongous string..."} At this
    point we are no longer "modified" so clear that state.
    '''
    def _save_meta(self, section):
        self.document().setModified(False)
        return self.toPlainText()

    '''
    Read notes text from a metadata file. Clear our internal document just to
    be sure. Then install the JSON value which is a (possibly very long)
    string. Set it as not-modified and put the cursor on the first line.
    '''
    def _read_meta(self,section,value,version):
        self.document().clear()
        self.setPlainText(value)
        tc = QTextCursor(self.document())
        tc.setPosition(0)
        self.setTextCursor(tc)
        self.document().setModified(False) # will cause a call of self.yikes
        self.font_change(True) # update font selection

    '''
    Notify our book of a change in the modification state.
    This slot gets the modificationChanged(bool) signal from our document.
    '''
    def yikes(self, boolean):
        self.book.metadata_modified(boolean,C.MD_MOD_NO)

    '''
    Intercept the focus-in and -out events and use them to display
    and hide our edit menu as needed.
    '''
    def focusInEvent(self, event):
        mainwindow.set_up_edit_menu(self.ed_action_list)
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        mainwindow.hide_edit_menu()
        super().focusOutEvent(event)

    ''' Get notified of a change in the user's choice of font '''
    def font_change(self,is_mono):
        if is_mono :
            self.setFont(fonts.get_fixed(self.book.get_font_size()))

    '''
    Implement a simple Find dialog. utilities.getFindMsg returns
    (ok,find-text). This is a simple find from the present cursor position
    downward, case-insensitive. If we get no hit we try once more from the
    top, thus in effect wrapping.
    '''

    ''' The actual search, factored out of the two actions '''
    def _do_find(self):
        if not self.find(self.find_text): # no hits going down
            self.moveCursor(QTextCursor.MoveOperation.Start) # go to top
            if not self.find(self.find_text): # still no hit
                utilities.beep()

    '''
    Edit > Find (^f) action gets a string to look for, initialized
    with up to 40 chars of the current selection.
    '''
    def find_action(self):
        ''' Show the find dialog initialized with the current selection. '''
        prep_text = self.textCursor().selectedText()[:40]
        self.find_text = utilities.get_find_string(
            _TR('Notes panel find dialog','Text to find'),
            self, prep_text)
        if self.find_text is not None :
            self._do_find()

    '''
    Edit > Find Next (^g) action: if there is no active find-text
    pretend that ^f was hit, otherwise repeat the search.
    '''
    def find_next_action(self):
        if self.find_text is not None :
            self._do_find()
        else :
            self.find_action()

    '''
    Re-implement keyPressEvent to provide these functions:
      * ctrl-plus and ctrl-minus zoom the font size one point.
      * ctl-alt-M inserts the current line number as {nnn}
      * alt-M looks for a nearby {nnn}, selects it, and asks our editor
            to jump to that line.
      * ctl-alt-P insert the current page (scan) filename as [xxx]
      * alt-P looks for a nearby [nnn], selects it, and asks our editor
            to jump to that page position.
    '''
    def keyPressEvent(self, event):
        #utilities.printKeyEvent(event) # dbg
        kkey = int( int(event.modifiers().value) & C.KBD_MOD_PAD_CLEAR) | int(event.key())
        if kkey in C.KEYS_NOTES :
            # this is a key we do handle, so...
            event.accept()
            if kkey in C.KEYS_ZOOM :
                self.setFont( fonts.scale( kkey, self.font() ) )
            elif (kkey == C.CTL_SHFT_M): # ctrl/cmd-m with shift
                self.insert_line()
            elif (kkey == C.CTL_M): # ctl-m
                self.go_to_line()
            elif (kkey == C.CTL_SHFT_P): # ctl/cmd-p with shift
                self.insert_page()
            elif (kkey == C.CTL_P): #ctl/cmd-P
                self.go_to_page()
        else: # not one of our keys at all
            event.ignore() # ensure the accepted flag is off
        if not event.isAccepted() : # if we didn't handle it, pass it up
            super().keyPressEvent(event)

    '''
    On ctl-shft-m (mac: cmd-shft-m), insert the current edit line number in
    notes as {nnn}
    '''
    def insert_line(self):
        tc = self.textCursor()
        bn = self.book.get_edit_view().get_line_number() # line num
        tc.insertText(u"{{{0}}}".format(bn))

    '''
    Class variable of a compiled regex for line number syntax. Allowing
    spaces because I'm just a nice guy.
    '''
    rex_line_number = regex.compile('\{\s*(\d+)\s*\}')

    '''
    On ctl-m (mac: cmd-m) look for a {nnn} line number "near" our cursor in
    the notes. We require the target to be in the same logical line as
    the cursor. The strategy is to first find-backwards for '{',
    then find-forward for regex {(\d+)\}
    '''
    def go_to_line(self):
        tb = self.textCursor().block()
        line = tb.text()
        pos = self.textCursor().positionInBlock()
        ''' Find the rightmost { left of the cursor position '''
        j = line.rfind('{',0,pos+1)
        if 0 > j :
            utilities.beep()
            return
        ''' Find {nnn} starting at that point '''
        match = self.rex_line_number.search(line,j)
        if match is None :
            utilities.beep()
            return
        try:
            line_number = int(match.group(1))
        except ValueError:
            utilities.beep()
            return
        ''' Select the found value, then move the editor putting focus in it '''
        self.textCursor().setPosition( tb.position()+match.end() )
        self.textCursor().setPosition( tb.position()+match.start(), QTextCursor.MoveMode.KeepAnchor )
        self.book.get_edit_view().go_to_line_number(line_number)

    '''
    Class variable of a compiled regex for page string syntax. Allowing
    spaces because I'm just a nice guy.
    '''
    rex_page_name = regex.compile('\[\s*([^\]]+)\s*\]')

    '''
    On ctl-shft-p (mac: cmd-shft-p), insert the current scan image name
    if there is one, as [xxx]. If there isn't one, you get just [].
    '''
    def insert_page(self):
        tc = self.textCursor()
        pn = self.book.get_edit_view().get_image_name() # page filename
        tc.insertText(u"[{0}]".format(pn))

    '''
    On ctl-p (mac: cmd-p) look for a [xxx] page name "near" our cursor in
    the notes. We require the target to be in the same logical line as the
    cursor. The strategy is to first find-backwards for '[', then
    find-forward for regex [(.+)]
    '''
    def go_to_page(self):
        tb = self.textCursor().block()
        line = tb.text()
        pos = self.textCursor().positionInBlock()
        ''' Find the rightmost [ left of the cursor position '''
        j = line.rfind('[',0,pos+1)
        if 0 > j :
            utilities.beep()
            return
        ''' Find [xxx] starting at that point '''
        match = self.rex_page_name.search(line,j)
        if match is None :
            utilities.beep()
            return
        ''' Select the found value, then move the editor putting focus in it '''
        self.textCursor().setPosition( tb.position()+match.end() )
        self.textCursor().setPosition( tb.position()+match.start(), QTextCursor.MoveMode.KeepAnchor )
        self.book.get_edit_view().go_to_image_name(match.group(1))
