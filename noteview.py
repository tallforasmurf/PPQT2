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
                          noteview.py

Define a class to implement the Notes panel.

Based on QPlainTextEdit, and uses the default QTextDocument, hence it
incorporates its own minimal "model" and does not need a "notesdata.py".

One Noteview object is created by a Book as it initializes. Immediately
registers to read and write the NOTES section of metadata. The Book puts a
reference to the object in its PANELDICT, so whenever the Book becomes
active, the Noteview is displayed in the Notes tab.

It tracks its QTextDocument's modification changes, and tells the Book
when the mod state changes.

Implements a keyEvent method to provide keystrokes for insertion of
{line#} and [image#] values, and to navigate to a noted line or image.
    ctl-alt-m inserts {line#}
    ctl-m when cursor is in or next to {line#}, jumps to that line
    ctl-alt-p inserts {image#}
    clt-p when cursor is in or next to [image#], jumps to that page

Implements a simple (non-regex) Find:
    ctl-f brings up a simple modal dialog for Find text with OK and Cancel
    ctl-g does a find-again for last text
    ctl-shift-g does a find-again backward

Implements text zoom similarly to the editview:
    ctl-plus zooms larger
    ctl-minus zooms smaller

Implements a minimal Edit menu with cut/copy/paste/undo/redo linked
to the builtin QPlainTextEdit slots. Enables that menu on focus-in,
disables it on focus-out.

TODO: resolve issues re keystrokes in mac os
TODO: Book to save metadata mods on per-object basis so if Notes backs
      out its mods, it can clear that status.
TODO: Propogate that change to Worddata?
'''
import constants as C
import metadata
import fonts
import mainwindow
import utilities
import regex
from PyQt5.QtWidgets import (
    QAbstractScrollArea,
    QPlainTextDocumentLayout,
    QPlainTextEdit,
    QTextEdit,
    QMenu,
    QMenuBar
    )
from PyQt5.QtGui import (
    QTextDocument,
    QTextBlock,
    QTextCursor,
    QKeySequence
    )
from PyQt5.QtGui import QPalette,QBrush
from PyQt5.QtCore import Qt, QCoreApplication
_TR = QCoreApplication.translate

class NotesPanel(QPlainTextEdit):
    def __init__(self, my_book, parent=None):
        super().__init__(parent)
        self.book = my_book
        # Where we store the last-sought-for find string
        self.find_text = None
        # Register to read and write metadata
        my_book.get_meta_manager().register( C.MD_NO, self.read_meta, self.save_meta )
        # Set our only font (we don't care about the general font, only mono)
        # n.b. this gets the Book's default size as it hasn't loaded a document
        # yet.
        self.setFont(fonts.get_fixed(my_book.get_font_size()))
        # hook up to be notified of a change in font choice
        fonts.notify_me(self.font_change)
        # Set up our document not using the default one
        a_document = QTextDocument()
        a_document.setDocumentLayout(QPlainTextDocumentLayout(a_document))
        self.setDocument(a_document)
        # Turn off linewrap mode
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        # The following kludge allows us to get the correct highlight
        # color on focus-in. For unknown reasons Qt makes us use the
        # "Inactive" color group even after focus-in. See focusInEvent()
        # and focusOutEvent() below.
        self.palette_active = QPalette(self.palette())
        self.palette_inactive = QPalette(self.palette())
        b = self.palette().brush(QPalette.Active,QPalette.Highlight)
        self.palette_active.setBrush(QPalette.Inactive,QPalette.Highlight,b)
        # Set the cursor shape to IBeam -- no idea why this supposed default
        # inherited from QTextEdit, doesn't happen. But it doesn't.
        self.viewport().setCursor(Qt.IBeamCursor)
        # Hook up a slot to notice that the document has changed its
        # modification state.
        self.document().modificationChanged.connect(self.yikes)
        # Create our edit menu and stow it in the menu bar. Disable it.
        ed_menu = QMenu(C.ED_MENU_EDIT,self)
        ed_menu.addAction(C.ED_MENU_UNDO,self.undo,QKeySequence.Undo)
        ed_menu.addAction(C.ED_MENU_REDO,self.redo,QKeySequence.Redo)
        ed_menu.addSeparator()
        ed_menu.addAction(C.ED_MENU_CUT,self.cut,QKeySequence.Cut)
        ed_menu.addAction(C.ED_MENU_COPY,self.copy,QKeySequence.Copy)
        ed_menu.addAction(C.ED_MENU_PASTE,self.paste,QKeySequence.Paste)
        ed_menu.addSeparator()
        ed_menu.addAction(C.ED_MENU_FIND,self.find_action,QKeySequence.Find)
        ed_menu.addAction(C.ED_MENU_NEXT,self.find_next_action,QKeySequence.FindNext)
        self.edit_menu = mainwindow.get_menu_bar().addMenu(ed_menu)
        self.edit_menu.setVisible(False)
        # In order to get focus events, we need to set focus policy
        self.setFocusPolicy(Qt.StrongFocus)

    # Save the current notes text to a metadata file. Get each line of
    # text (text block) in turn. If a line starts with '{{' (which might
    # be a conflict with a metadata sentinel line) prefix it with u\fffd.
    # This is what V.1 did, so we continue it.
    def save_meta(self, qts, sentinel):
        qts << metadata.open_line(sentinel)
        tb = self.document().firstBlock()
        while tb.isValid():
            line = tb.text()
            if line.startswith('{{'):
                line = C.UNICODE_REPL + line
            qts << line
            qts << '\n'
            tb = tb.next()
        qts << metadata.close_line(sentinel)
    # Read notes text from a metadata file. Clear our internal document just
    # to be sure. Get each line from the input stream and append it to the
    # document using the appendPlainText() method of the editor (which ought
    # to be a method of the document, but whatever). Set the cursor to the
    # top. Re-set the font in case the Book read a different size. Set our
    # document to unmodified state.
    def read_meta(self,qts,sentinel,version,parm):
        self.document().clear()
        for line in metadata.read_to(qts,sentinel):
            if line.startswith(C.UNICODE_REPL+'{{'):
                line = line[1:]
            self.appendPlainText(line)
        tc = QTextCursor(self.document())
        tc.setPosition(0)
        self.setTextCursor(tc)
        self.document().setModified(False)
        self.font_change(True) # update font selection

    # Notify our book of a change in the modification state.
    # This slot gets the modificationChanged(bool) signal from our
    # document.
    def yikes(self, boolean):
        self.book.metadata_modified(boolean,C.MD_MOD_NO)

    # Intercept the focus-in and -out events and use them to display
    # and hide our edit menu.
    def focusInEvent(self, event):
        self.edit_menu.setVisible(True)
        self.setPalette(self.palette_active)

    def focusOutEvent(self, event):
        self.edit_menu.setVisible(False)
        self.setPalette(self.palette_inactive)

    # Get notified of a change in the user's choice of font
    def font_change(self,is_mono):
        if is_mono :
            self.setFont(fonts.get_fixed(self.book.get_font_size()))

    # Implement a simple Find dialog. utilities.getFindMsg returns
    # (ok,find-text). This is a simple find from the present cursor position
    # downward, case-insensitive. If we get no hit we try once more from the
    # top, thus in effect wrapping.

    # The actual search, factored out of the two actions
    def _do_find(self):
        if not self.find(self.find_text): # no hits going down
            self.moveCursor(QTextCursor.Start) # go to top
            if not self.find(self.find_text): # still no hit
                utilities.beep()

    # Edit > Find (^f) action gets a string to look for, initialized
    # with up to 40 chars of the current selection.
    def find_action(self):
        # Show the find dialog initialized with
        # a copy of the current selection.
        prep_text = self.textCursor().selectedText()[:40]
        self.find_text = utilities.get_find_string(
            _TR('Notes panel find dialog','Text to find'),
            self, prep_text)
        if self.find_text is not None :
            self._do_find()

    # Edit > Find Next (^g) action: if there is no active find-text
    # pretend that ^f was hit, otherwise repeat the search.
    def find_next_action(self):
        if self.find_text is not None :
            # Some previous string to look for, find-again.
            self._do_find()
        else :
            # no previous string, do beginning find
            self.find_action()

    # Re-implement keyPressEvent to provide these functions:
    #   ctrl-plus and ctrl-minus zoom the font size one point.
    #   ctl-alt-M inserts the current line number as {nnn}
    #   alt-M looks for a nearby {nnn}, selects it, and asks our editor
    #         to jump to that line.
    #   ctl-alt-P insert the current page (scan) filename as [xxx]
    #   alt-P looks for a nearby [nnn], selects it, and asks our editor
    #         to jump to that page position.

    def keyPressEvent(self, event):
        #utilities.printKeyEvent(event)
        kkey = int( int(event.modifiers()) & C.KEYPAD_MOD_CLEAR) | int(event.key())
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

    # on ctl-shft-m (mac: cmd-shft-m), insert the current edit line number in
    # notes as {nnn}
    def insert_line(self):
        tc = self.textCursor()
        bn = self.book.get_edit_view().get_line_number() # line num
        tc.insertText(u"{{{0}}}".format(bn))

    # Class variable of a compiled regex for line number syntax. Allowing
    # spaces because I'm just a nice guy.
    rex_line_number = regex.compile('\{\s*(\d+)\s*\}')

    # on ctl-m (mac: cmd-m) look for a {nnn} line number "near" our cursor in
    # the notes. We require the target to be in the same logical line as
    # the cursor. The strategy is to first find-backwards for '{',
    # then find-forward for regex {(\d+)\}
    def go_to_line(self):
        tb = self.textCursor().block()
        line = tb.text()
        pos = self.textCursor().positionInBlock()
        # Find the rightmost { left of the cursor position
        j = line.rfind('{',0,pos+1)
        if 0 > j :
            utilities.beep()
            return
        # Find {nnn} starting at that point
        match = self.rex_line_number.search(line,j)
        if match is None :
            utilities.beep()
            return
        try:
            line_number = int(match.group(1))
        except ValueError:
            utilities.beep()
            return
        # Select the found value, then move the editor putting focus in it
        self.textCursor().setPosition( tb.position()+match.end() )
        self.textCursor().setPosition( tb.position()+match.start(), QTextCursor.KeepAnchor )
        self.book.get_edit_view().go_to_line_number(line_number)

    # Class variable of a compiled regex for page string syntax. Allowing
    # spaces because I'm just a nice guy.
    rex_page_name = regex.compile('\[\s*([^\]]+)\s*\]')

    # on ctl-shft-p (mac: cmd-shft-p), insert the current scan image name
    # if there is one, as [xxx]. If there isn't one, you get just [].
    def insert_page(self):
        tc = self.textCursor()
        pn = self.book.get_edit_view().get_image_name() # page filename
        tc.insertText(u"[{0}]".format(pn))

    # on ctl-p (mac: cmd-p) look for a [xxx] page name "near" our cursor in
    # the notes. We require the target to be in the same logical line as the
    # cursor. The strategy is to first find-backwards for '[', then
    # find-forward for regex [(.+)]
    def go_to_page(self):
        tb = self.textCursor().block()
        line = tb.text()
        pos = self.textCursor().positionInBlock()
        # Find the rightmost [ left of the cursor position
        j = line.rfind('[',0,pos+1)
        if 0 > j :
            utilities.beep()
            return
        # Find [xxx] starting at that point
        match = self.rex_page_name.search(line,j)
        if match is None :
            utilities.beep()
            return
        # Select the found value, then move the editor putting focus in it
        self.textCursor().setPosition( tb.position()+match.end() )
        self.textCursor().setPosition( tb.position()+match.start(), QTextCursor.KeepAnchor )
        self.book.get_edit_view().go_to_image_name(match.group(1))
