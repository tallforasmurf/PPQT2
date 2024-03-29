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
                         editview.py

Defines a class for the edit object, which implements the user access to a
document for editing, based on QPlainTextEdit.

Implements all keyboard actions (ctl-F, etc) in the editor.

Implements the syntax highlighter that colors scannos and spelling errors.
Calls on a WordData object to identify scannos and spelling errors.

Provides a basic Edit menu with Undo/Redo, Cut/Copy/Paste,
and Find-action same as our keystrokes: Find Selected/Next/Prior

Provides a context menu with these user commands:
    Mark Scannos
    Mark Spelling
    Choose Dictionary
    Choose Scanno File
    Edit Metadata

Offers these additional methods:

    set_find_range(tc)   Set the selection defined by textCursor tc as the
                         limited find-range and highlight it. Called from findview.

    clear_find_range()   Make the limited find-range highlighting go away.

    center_this(tc)      Given a text cursor with a selection, put the top
                         of the selection in the middle of the window, unless
                         the selection is taller than 1/2 the window in which
                         case put the top of the selection as high as needed
                         but in no case, off the top of the window.

    center_position(pos) Same as center_this but for an integer position.

    show_this(tc)        given a text cursor with a selection, make sure
                         the top of the selection is visible in the edit
                         window. If it is already visible, do nothing, else
                         pass to center_this().

    show_position(pos)   Same a show_this but for an integer position.

    go_to_line_number('nn') Given a string representing a line number,
                         position the cursor at the head of that line.

    go_to_block(tb)      given a text block, put the edit cursor at its start
                         and show it via show_this.

    get_cursor()         Return a COPY of the current edit cursor.
    get_cursor_val()     Return a tuple of (pos, anchor) for the current edit cursor.
    set_cursor(tc)       Set a new edit cursor.
    make_cursor(pos,anchor) Return a QTextCursor with that position and anchor

'''

import regex
from PyQt6.QtCore import Qt, QObject, QCoreApplication, QSize
_TR = QCoreApplication.translate

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPlainTextEdit,
    QSizePolicy,
    QSpacerItem,
    QTextEdit,
    QVBoxLayout,
    QWidget
    )
from PyQt6.QtGui import (
    QAction,
    QBrush,
    QKeySequence,
    QSyntaxHighlighter,
    QTextBlockFormat,
    QTextCursor,
    QTextCharFormat,
    QTextDocument,
    QTextFormat
    )
import fonts
import colors
import logging
editview_logger = logging.getLogger(name='editview')
import constants as C
import utilities
import mainwindow

'''
Define a syntax highlighter object which is linked into our edit widget.
The EditView below instantiates one of this object.

Commence with a regular expression that matches a word token, including a
word that is hyphenated and/or has an apostrophe. First, define an expression
for a word token which may include pgdp-style specials like [:u] or ['e].
'''
re_base_word = "(\\w*(\\[..\\])?\\w+)+"
'''
Now extend that to allow an internal (not terminal) apostrophe
or hyphen, allowing for both ascii and curly apostrophes.
Zero or more base word plus hyphen/apostrophe, then base word.
'''
re_hyap = "(" + re_base_word + "[\\'\\-\u2019])*" + re_base_word
'''
Compile that as a frozen RE.
'''
re_word = regex.compile(re_hyap, regex.IGNORECASE)
'''
Now the highlighter class. The init argument is a reference to the EditView,
from which we pull the highlighting formats. We initialize our parent class
with no text document. Later we will be attached to the real document with a
call to setDocument.
'''

class HighLighter(QSyntaxHighlighter):
    def __init__(self, editv, book):
        super().__init__(None)
        # Save reference to our EditView for getting formats later
        self.editv = editv
        # Save references direct to the scanno and spelling checker
        # methods of the worddata model.
        self.scanno = book.get_word_model().scanno_test
        self.speller = book.get_word_model().spelling_test
    '''

    When highlighting is first turned on (by calling the parent class's
    setDocument() method) the linked QTextDocument calls this function for
    every text line in the whole document, at least to judge by the
    hang-time. Later it only calls it to look at a line as it changes in
    editing. In either case it behooves us to be as quick as possible.
    
    Either one or both of editv.scanno_check or editv.spell_check are True
    because if they aren't, EditView would have set our document to null.
    
    We sample the highlight formats at the time we are called so we get
    the latest choice of color and style. We cache the scanno and spelling
    switches to save on python name-dict scans.
    '''
    def highlightBlock(self, text):
        global re_word
        scanno_fmt = self.editv.scanno_format
        spelling_fmt = self.editv.spelling_format
        sc = self.editv.scanno_check
        sp = self.editv.spelling_check
        # iterate over all word tokens in the text.
        for match in re_word.finditer(text):
            t = match.group(0) # text of matched token
            p = match.start() # index of start of token in text
            l = len(t) # length of token
            if sc : # we are checking for scannos:
                if self.scanno(t) :
                    self.setFormat(p,l,scanno_fmt)
            if sp : # we are checking spelling:
                if self.speller(t) :
                    self.setFormat(p,l,spelling_fmt)
'''
Define a custom QPlainTextEdit. This differs from the stock variety in that
it has a keyEvent override to trap and handle numerous special keystrokes,
and in using the mainwindow to populate a custom edit menu.
'''
class PTEditor( QPlainTextEdit ):

    editFindKey = pyqtSignal(int)

    def __init__(self, parent, my_book):
        super().__init__(parent)
        self.my_book = my_book # Need access to book
        self.ed_action_list = [
            (C.ED_MENU_UNDO, self.undo, QKeySequence.StandardKey.Undo),
            (C.ED_MENU_REDO, self.redo, QKeySequence.StandardKey.Redo),
            (None, None, None),
            (C.ED_MENU_CUT, self.cut, QKeySequence.StandardKey.Cut),
            (C.ED_MENU_COPY,self.copy,QKeySequence.StandardKey.Copy),
            (C.ED_MENU_PASTE,self.paste,QKeySequence.StandardKey.Paste),
            (None, None, None),
            (C.ED_MENU_FIND, lambda:self.emit_key(C.CTL_F),QKeySequence.StandardKey.Find),
            (C.ED_MENU_FIND_SELECTED, lambda:self.emit_key(C.CTL_SHFT_F),0),
            (C.ED_MENU_NEXT, lambda:self.emit_key(C.CTL_G) ,QKeySequence.StandardKey.FindNext),
            (C.ED_MENU_PRIOR, lambda:self.emit_key(C.CTL_SHFT_G), QKeySequence.StandardKey.FindPrevious),
            (None, None, None),
            (C.ED_MENU_TO_LOWER, lambda:self.case_mod(C.CTL_SHFT_L), QKeySequence(C.CTL_SHFT_L) ),
            (C.ED_MENU_TO_UPPER, lambda:self.case_mod(C.CTL_SHFT_U), QKeySequence(C.CTL_SHFT_U) ),
            (C.ED_MENU_TO_TITLE, lambda:self.case_mod(C.CTL_SHFT_I), QKeySequence(C.CTL_SHFT_I) )
            ]

    def emit_key(self, kkey) :
        self.editFindKey.emit(kkey)

    def focusInEvent(self, event) :
        mainwindow.set_up_edit_menu(self.ed_action_list)
        super().focusInEvent(event)
    def focusOutEvent(self, event) :
        mainwindow.hide_edit_menu()
        super().focusOutEvent(event)

    def keyPressEvent(self, event):
        #utilities.printKeyEvent(event)
        kkey = int( int(event.modifiers().value) & C.KBD_MOD_PAD_CLEAR) | int(event.key())
        if kkey in C.KEYS_EDITOR :
            event.accept() # yes, this is one we handle
            if kkey in C.KEYS_FIND :
                # ^f, ^g, etc. -- just pass them straight to the Find panel
                self.editFindKey.emit(kkey)
            elif kkey in C.KEYS_ZOOM :
                self.setFont( fonts.scale(kkey, self.font()) )
                self.my_book.save_font_size(self.font().pointSize())
            elif kkey in C.KEYS_CASE_MOD :
                # change case of selection if any
                self.case_mod(kkey)
            elif kkey in C.KEYS_BOOKMARKS :
                # Something to do with a bookmark. They are kept in the Book
                # because they are read and written in the metadata.
                mark_number = int(event.key()) - 0x31  # number in 0..8
                mark_list = self.my_book.bookmarks # quick reference to the list
                if kkey in C.KEYS_MARK_SET : # alt-1..9, set bookmark
                    # Set a bookmark to the current edit selection
                    mark_list[mark_number] = QTextCursor(self.textCursor())
                    self.my_book.metadata_modified(True, C.MD_MOD_FLAG)
                elif kkey in C.KEYS_MARK : # ctl-1..9, go to mark
                    # Move to the save position including a saved selection
                    if mark_list[mark_number] is not None :
                        self.parent().center_this(mark_list[mark_number])
                else : # shft-ctl-1..9, go to mark, extending selection
                    if mark_list[mark_number] is not None:
                        pos = mark_list[mark_number].position()
                        tc = QTextCursor(self.textCursor())
                        tc.setPosition(pos, QTextCursor.MoveMode.KeepAnchor)
                        self.setTextCursor(tc)
                        self.ensureCursorVisible()
        else: # not a key for the editor, pass it on.
            event.ignore()
            super().keyPressEvent(event)
    '''
    Execute case modification, to upper, to lower, to title, on the current
    selection. This was easy in the days of Latin-1. But Python
    string.lower/upper/title is Unicode-aware so no problem.
    
    Use re_word (above) and exploit the implicit match-loop of re.sub()
    to apply a nonce function to every word. The lambda for title case
    uses a trick documented under str.title in the python docs.
    '''
    def case_mod(self, kkey) :
        tc = self.textCursor()
        if not tc.hasSelection() :
            return # no selection, nothing to do
        text = tc.selectedText() # full selection as string
        start_pos = tc.selectionStart()
        if kkey == C.CTL_SHFT_L :
            func = lambda m : m.group(0).lower()
        elif kkey == C.CTL_SHFT_U :
            func = lambda m : m.group(0).upper()
        else:
            func = lambda m : m.group(0)[0].upper() + m.group(0)[1:].lower()
        new_text = re_word.sub( func, text ) # do it!
        tc.insertText( new_text )
        tc.setPosition( start_pos, QTextCursor.MoveMode.MoveAnchor )
        tc.setPosition( start_pos + len(new_text), QTextCursor.MoveMode.KeepAnchor )
        self.setTextCursor(tc)


class EditView( QWidget ):
    def __init__(self, my_book, focusser, parent=None):
        # Initialize our superclass(es)
        super().__init__(parent)
        # Save the link to our book and the focus function
        self.my_book = my_book
        self.focusser = focusser # function to call on focus-in
        # Save access to the document itself
        self.document = my_book.get_edit_model()
        # Save access to the word list and page data
        self.word_model = my_book.get_word_model()
        self.page_model = my_book.get_page_model()
        # Initialize highlighting switches and create the highlighter.
        self.highlighter = HighLighter(self,my_book)
        self.scanno_check = False
        self.spelling_check = False
        self.my_book.get_meta_manager().register(C.MD_EH, self._read_switches, self._save_switches)
        '''
        Take our UI setup out of line. self._uic creates and
        initializes all the sub-widgets under self. :
            .Editor - the QPlainTextEditor
            .DocName - QLabel for the document filename
            .Folio - QLabel for the current folio value
            .ImageFilename - QLineEdit for the current image filename
            .LineNumber - QLineEdit for the line number
            .ColNumber - QLabel for the cursor column
            .norm_style - stylesheet for unmodified book name
            .mod_style - stylesheet for modified book name
        Signals from these widgets are hooked up below.
        '''
        self._uic()
        # Connect the editor to the document.
        self.Editor.setDocument(self.document)
        # Set up mechanism for a current-line highlight and a find-range
        # highlight. This consists of a list of two "extra selections".
        # An "extra selection" is basically a tuple of a cursor and a
        # format. See set_find_range, clear_find_range, _set_colors
        # and _cursor_moved.
        self.last_text_block = None # to know when cursor moves to new line
        self.current_line_sel = QTextEdit.ExtraSelection()
        self.current_line_fmt = colors.get_current_line_format()
        self.range_sel = QTextEdit.ExtraSelection()
        self.range_sel.cursor = QTextCursor(self.document) # null cursor
        self.extra_sel_list = [self.range_sel, self.current_line_sel]
        # Sign up to get a signal on a change in font choice
        fonts.notify_me(self.font_change)
        # Fake that signal to set the fonts of our widgets.
        self.one_line_height = 0 # updated in font_change
        self.font_change(False)
        # Sign up to get a signal on a change of color preferences.
        colors.notify_me(self._set_colors)
        # Fake the signal to set up widgets. This sets .scanno_format,
        # .spelling_format, .current_line_sel, .range_sel, .norm_style and
        # .mod_style.
        self._set_colors()
        # Put the document name in our widget
        self.DocName.setText(self.my_book.get_book_name())
        # Set the cursor shape to IBeam -- no idea why this supposed default
        # inherited from QTextEdit, doesn't happen. But it doesn't.
        # self.Editor.viewport().setCursor(Qt.CursorShape.IBeamCursor)
        # Connect the Editor's modificationChanged signal to our slot.
        self.Editor.modificationChanged.connect(self.mod_change_signal)
        # Connect the returnPressed signal of the LineNumber widget
        # to our go to line method.
        self.LineNumber.returnPressed.connect(self._line_number_enter)
        # Connect returnPressed of the ImageFilename widget to our slot.
        self.ImageFilename.returnPressed.connect(self._image_enter)
        # Connect the Editor's cursorPositionChanged signal to our slot
        self.Editor.cursorPositionChanged.connect(self._cursor_moved)
        # Fill in the line and column number by faking that signal
        self._cursor_moved()
        # Create and install our context menu
        self.context_menu = self._make_context_menu()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)
        # Hideous hack: the Book calls center_this with the saved cursor value
        # read from the metadata. However at that time the editor is
        # (apparently) not fully initialized and although the cursor is
        # set, it is not in the center of the window. We looked and looked
        # for some event that reliably means the editor is ready to display
        # and settled on paintEvent. If center_this has been called before
        # the first paint event, the call is repeated.
        self.first_paint_event = True
        self.first_center_tc = None

        # End of __init__()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.first_paint_event :
            self.first_paint_event = False
            if self.first_center_tc is not None :
                self.center_this( self.first_center_tc )
                self.first_center_tc = None

    # Metadata load and save of the scanno/spelling highlight switches
    def _save_switches(self, section):
        return (self.scanno_check, self.spelling_check)

    def _read_switches(self, sentinel, value, version):
        # check that value is a tuple of two ints and ignore it if not
        try:
            (sc, sp) = value
            sc = int(sc)
            sp = int(sp)
        except:
            sc = False
            sp = False
        self.scanno_check = sc
        self.scanno_action.setChecked( sc )
        self.spelling_check = sp
        self.spelling_action.setChecked( sp )
    '''

                    INTERNAL METHODS

    Set up text formats for the current line, find-range, spellcheck words
    and scanno words. This method is called to set up the colors initially
    and is the slot to receive the colorsChanged signal.
    '''
    def _set_colors(self):
        self.scanno_format = colors.get_scanno_format()
        self.spelling_format = colors.get_spelling_format()
        if self.scanno_check or self.spelling_check :
            # force redo of all scanno/spellcheck highlights
            self._clear_highlights()
            self._start_highlights()
        self.current_line_fmt = colors.get_current_line_format()
        self.current_line_sel.format = QTextCharFormat(self.current_line_fmt)
        if self.range_sel.cursor.hasSelection() :
            self.range_sel.format = colors.get_find_range_format(True)
        self.Editor.setExtraSelections(self.extra_sel_list) # force refresh of both
    '''
    Slot to receive the modificationChanged signal from the document.
    Also called from the book when metadata changes state.
    Change the color of the DocName to match.
    '''
    def mod_change_signal(self,boolean):
        self.DocName.setStyleSheet(self.mod_style if self.my_book.get_save_needed() else self.norm_style)
    '''
    This slot receives the ReturnPressed signal from the LineNumber field.
    '''
    def _line_number_enter(self):
        self.go_to_line_number(self.LineNumber.text())
    '''
    This slot receives the ReturnPresssed signal from ImageFilename.
    '''
    def _image_enter(self):
        self.go_to_image_name(self.ImageFilename.text())
    '''
    This slot is connected to Editor's cursorPositionChanged signal, so is
    called whenever the cursor moves for any reason, i.e. very very often! It
    is also called directly when one of the internal methods below moves the
    cursor. Change the contents of the column number display. If the cursor
    has moved to a different line, change also the line number, scan image
    name, and folio displays to match the new position. Update the "extra
    selection" that puts highlighting on the current line.
    '''
    def _cursor_moved(self):
        tc = QTextCursor(self.Editor.textCursor()) # copy of cursor
        self.ColNumber.setText( str( tc.positionInBlock() ) )
        tb = tc.block()
        if tb == self.last_text_block :
            return # still on same line, nothing more to do
        # Fill in line-number widget, line #s are origin-1
        self.LineNumber.setText( str( tb.blockNumber()+1 ) )
        # Fill in the image name and folio widgets
        pn = self.page_model.page_index(tc.position())
        if pn is not None : # the page model has info on this position
            self.ImageFilename.setText(self.page_model.filename(pn))
            self.Folio.setText(self.page_model.folio_string(pn))
        else: # no image data, or cursor is above page 1
            self.ImageFilename.setText('')
            self.Folio.setText('')
        # Change the current-line "extra selection" to the new current line.
        # Note: the cursor member of the extra selection may not have a
        # selection. If it does, the current line highlight disappears. The
        # cursor "tc" may or may not have a selection; to make sure, we clone
        # it and remove any selection from it.
        cltc = QTextCursor(tc)
        cltc.setPosition(tc.position(),QTextCursor.MoveMode.MoveAnchor)
        # Set the cloned cursor into the current line extra selection object.
        self.current_line_sel.cursor = cltc
        # Re-assign the list of extra selections to force update of display.
        self.Editor.setExtraSelections(self.extra_sel_list)
    '''
    Slot to receive the fontsChanged signal. If it is the UI font, set
    that, which propogates to all children including Editor, so set the
    editor's mono font in any case, but using our current point size.
    Also called from the book when reading metadata.
    '''
    def font_change(self,is_mono):
        if not is_mono :
            self.setFont(fonts.get_general())
        self.Editor.setFont(fonts.get_fixed(self.my_book.get_font_size()))
        self.one_line_height = self.Editor.fontMetrics().lineSpacing()
    '''
    
                    CONTEXT MENU
    
    Define the five actions for our context menu, then make the menu.
    
    The mark-scannos and mark-spelling choices are checkable and their
    toggled signal is connected to these slots.
    
    The problem is that both types of highlights are done by the same
    highlighter, and it is only called when it is first started (and during
    editing of single lines later). Thus to make a change in highlighting,
    for example to turn on or off scanno highlighting, requires stopping the
    syntax highlighter, which clears all highlights, then restarting it.
    
    We stop the highlighter by assigning it to an empty document, and we
    start it by assigning it to our actual document.
    '''
    
    def _clear_highlights(self):
        self.highlighter.setDocument(QTextDocument())

    def _start_highlights(self):
        self.highlighter.setDocument(self.document)
    '''
    These are called by the triggered signal of the menu items. The first
    two toggle the highlighting of scannos and spelling.
    
    In each case we first ask, were we highlighting anything (either scannos
    or spelling)? in which case we need to stop the highlighter. Then we ask,
    given the current toggle, are we now highlighting anything? In which case
    we need to start the highlighter.
    '''
    def _act_mark_scannos(self,toggle):
        before = self.scanno_check or self.spelling_check
        self.scanno_check = toggle
        after = self.scanno_check or self.spelling_check
        if before :
            self._clear_highlights()
        if after :
            self._start_highlights()

    def _act_mark_spelling(self, toggle):
        before = self.scanno_check or self.spelling_check
        self.spelling_check = toggle
        after = self.scanno_check or self.spelling_check
        if before :
            self._clear_highlights()
        if after :
            self._start_highlights()
    '''
    The choose-scanno and choose-dictionary context menu actions are passed
    along to the book. It asks the user to choose a file or a dict, and if a
    new file or dict is selected, it causes the word model to load the new
    scannos or recheck spelling with the new dict. The highlighter works off
    the values stored by the word model.
    '''
    def _act_choose_scanno(self) :
        new = self.my_book.ask_scanno_file()
        if self.scanno_check and new:
            # Scanno highlighting is on and the file changed.
            # Turn it off and on to reset the marks.
            self._act_mark_scannos(False)
            self._act_mark_scannos(True)

    def _act_choose_dict(self) :
        new = self.my_book.ask_dictionary()
        if self.spelling_check and new:
            # Spellcheck highlighting is on and the dictionary changed
            # Turn it off and on again to reset the marks.
            self._act_mark_spelling(False)
            self._act_mark_spelling(True)
    '''
    The "Edit Metadata" context menu action is passed directly to the book
    for implementation because it stores that information.
    
    Create the menu itself. This is part of initialization.
    Save references to the Toggle actions Mark Scannos/Mark Spelling
    so their toggles can be tripped externally.
    '''
    def _make_context_menu(self):
        m = QMenu(self)
        
        act1 = QAction( _TR("EditViewWidget","Mark Scannos","context menu item"), m )
        act1.setCheckable(True)
        act1.setToolTip( _TR("EditViewWidget",
                                "Turn on or off marking of words from the scanno file",
                                "context menu tooltip") )
        act1.toggled.connect(self._act_mark_scannos)
        self.scanno_action = act1
        m.addAction(act1)
        
        act2 = QAction( _TR("EditViewWidget","Mark Spelling","context menu item"), m )
        act2.setCheckable(True)
        act2.setToolTip( _TR("EditViewWidget",
                                "Turn on or off marking words that fail spellcheck",
                                "context menu tooltip") )
        act2.toggled.connect(self._act_mark_spelling)
        self.spelling_action = act2
        m.addAction(act2)
        
        act3 = QAction( _TR("EditViewWidget","Scanno File...","context menu item"), m )
        act3.setToolTip( _TR("EditViewWidget",
                                "Choose a file of scanno (common OCR error) words",
                                "context menu tooltip") )
        act3.triggered.connect(self._act_choose_scanno)
        m.addAction(act3)
        
        act4 = QAction( _TR("EditViewWidget","Dictionary...","context menu item"), m )
        act4.setToolTip( _TR("EditViewWidget",
                                "Choose the primary spelling dictionary for this book",
                                "context menu tooltip") )
        act4.triggered.connect(self._act_choose_dict)
        m.addAction(act4)
        
        act5 = QAction( _TR("EditViewWidget", "Edit Book Facts...", "context menu item"), m )
        act5.setToolTip( _TR("EditViewWidget",
                         "Edit the Title, Author and other facts about the book",
                         "context menu tooltip") )
        act5.triggered.connect(self.my_book.edit_book_facts)
        m.addAction(act5)
        
        return m
    '''
    Override the parent's contextMenuEvent to display and execute that menu.
    '''
    def contextMenuEvent(self, event):
        self.context_menu.exec(event.globalPos())
    
    '''

                     PUBLIC METHODS
    
    Retrieve the current image filename. Called from Notes.
    '''
    def get_image_name(self):
        return self.ImageFilename.text()
    '''
    Go to page image by name: Ask the page database for the index of the
    user-entered filename value and if it recognizes it, get the position
    of it and set that. This is called from _image_enter and also from
    the Notes panel.
    '''
    def go_to_image_name(self, name_string):
        pn = self.page_model.name_index(name_string)
        if pn is not None :
            self.center_position(self.page_model.position(pn))
        else : # unknown image filename, restore current value
            utilities.beep()
            editview_logger.debug('Request for invalid image name {0}'.format(self.ImageFilename.text()))
            self._cursor_moved()
        self.Editor.setFocus(Qt.FocusReason.TabFocusReason)
    '''
    Retrieve the current line number string. Called from Notes.
    '''
    def get_line_number(self):
        return self.LineNumber.text()
    '''
    Get the origin-0 text block number of the current cursor.
    Called from Footnote View.
    '''
    def get_line(self):
        tc = self.Editor.textCursor()
        cp = tc.selectionStart()
        tb = self.document.findBlock(cp)
        return tb.blockNumber()
    '''
    Called by the parent Book when the book is renamed as part of Save-As.
    Change the name in the window and clear any find-range selection (why?)
    '''
    def book_renamed(self,name):
        self.DocName.setText(name)
        self.clear_find_range()
    '''
    Methods to manage the cursor that defines the valid range for
    find/replace. Called from findview.py to set, clear, or retrieve the
    current find range. When a limited range is set, make it visible. The
    actual find range is either the whole document or else the selection in
    the cursor that is embedded in the range_sel ExtraSelection.

    Set the current edit cursor's selection as the find range.
    '''
    def set_find_range(self):
        tc = self.Editor.textCursor()
        self.range_sel.cursor.setPosition(tc.selectionEnd())
        self.range_sel.cursor.setPosition(tc.selectionStart(), QTextCursor.MoveMode.KeepAnchor)
        self.range_sel.format = colors.get_find_range_format(True)
        self.Editor.setExtraSelections(self.extra_sel_list)
    '''
    Clear the current find range. Must set the format to null to avoid
    leaving a bit of background color around.
    '''
    def clear_find_range(self):
        self.range_sel.cursor.clearSelection()
        self.range_sel.format = QTextCharFormat()
        self.Editor.setExtraSelections(self.extra_sel_list)
    '''    
    Return a cursor defining the bounds of the current find range. If there
    is no limited find range, return a cursor covering the entire document.
    '''
    def get_find_range(self):
        tc = QTextCursor(self.range_sel.cursor) # copy of range cursor
        if not tc.hasSelection() :
            tc.select(QTextCursor.SelectionType.Document)
        return tc
    '''
    Called from other panels who need to connect editor signals,
    e.g. the Find panel.
    '''
    def get_actual_editor(self):
        return self.Editor
    '''
                     Cursor positioning
    
    Go to line number as a string: called from the _line_number_enter slot
    when the user types a new line number into that field. Also from the
    Notes panel.
    
    Given a supposed line number as a string 'nnn' but dare not assume an
    integer string value, or a valid line number. If invalid, beep and do
    nothing.
    '''
    def go_to_line_number(self, lnum_string):
        try:
            lnum = int(lnum_string) - 1 # text block # is origin-0
            self.go_to_line(lnum)
        except ValueError: # from int() or explicit
            utilities.beep()
            editview_logger.error('Request to show invalid line number {0}'.format(lnum_string))
    '''
    Go to line number as an integer: called from above, and from the
    Footnotes and Bookloupe panels. Position at a particular text block by
    number (origin-0). Allows -1 to mean end of file.
    '''
    def go_to_line(self, line_number):
        try:
            tb = self.document.findBlockByLineNumber(line_number)
            if not tb.isValid() :
                tb = self.document.end()
                if line_number != -1 :
                    raise ValueError
        except ValueError: # bad line_number
            editview_logger.error('Request to show invalid line number {0}'.format(line_number))
        self.go_to_block(tb) # regardless - see below
    '''
    Position the cursor at the head of a given QTextBlock (line) and make
    that line visible. Does not assume tb is a valid textblock. Currently
    only called from above but could be called directly.
    '''
    def go_to_block(self, tb):
        if not tb.isValid():
            editview_logger.error('Request to show invalid text block')
            tb = self.document.lastBlock()
        self.show_position(tb.position())
    '''
    Position the document to show a given character position. Called from
    imageview and loupeview. Breaks the current selection if any. Does not
    assume the position is valid.
    '''
    def show_position(self, pos):
        try:
            pos = int(pos)
            if (pos < 0) or (pos >= self.document.characterCount() ) :
                raise ValueError
        except:
            utilities.beep()
            editview_logger.error('Request to show invalid position {0}'.format(pos))
            pos = self.document.characterCount()-1
        tc = QTextCursor(self.Editor.textCursor())
        tc.setPosition(pos)
        self.show_this(tc)
    '''
    Make a selection visible. Breaks the current selection if any. Called
    only from above, but could be called directly. Centers the desired
    position.
    '''
    def show_this(self, tc):
        self.Editor.setTextCursor(tc)
        self.Editor.centerCursor()
        self.Editor.setFocus(Qt.FocusReason.TabFocusReason)

    def center_position(self, pos):
        tc = self.Editor.textCursor()
        tc.setPosition(pos)
        self.center_this(tc)

    def center_this(self, tc):
        if self.first_paint_event :
            self.first_center_tc = tc
        self.Editor.setTextCursor(QTextCursor(tc))
        self.Editor.centerCursor()
        self.Editor.setFocus(Qt.FocusReason.TabFocusReason)
    '''
    Lots of other code needs a textcursor for the current document.
    '''
    def get_cursor(self):
        return QTextCursor(self.Editor.textCursor())
    '''
    Return the essence of the cursor as a tuple (position,anchor)
    '''
    def get_cursor_val(self):
        return (self.Editor.textCursor().position(), self.Editor.textCursor().anchor())
    '''
    Some other code likes to reposition the edit selection.
    TODO: document what and why.
    '''
    def set_cursor(self, tc):
        self.Editor.setTextCursor(tc)
    '''
    Make a valid cursor based on position and anchor values possibly
    input by the user.
    '''
    def make_cursor(self, position, anchor):
        mx = self.document.characterCount()
        tc = QTextCursor(self.Editor.textCursor()) # clone a cursor
        anchor = min( max(0,anchor), mx ) # guaranteed valid anchor
        position = min ( max(0,position), mx ) # .. and position
        tc.setPosition(anchor)
        tc.setPosition(position,QTextCursor.MoveMode.KeepAnchor)
        return tc
    '''
               INITIALIZE UI
    
    First we built the Edit panel using Qt Creator which produced a large and
    somewhat opaque block of code that had to be mixed in by multiple
    inheritance. This had several drawbacks, so the following is a "manual"
    UI setup, using code drawn from that generated code.
    '''
    def _uic(self):
        '''
        First set up the properties of "self", a QWidget.
        '''
        self.setObjectName("EditViewWidget")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(False) # don't care to bind height to width
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QSize(250, 250))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setWindowTitle("")
        self.setToolTip("")
        self.setStatusTip("")
        self.setWhatsThis("")
        '''
        Set up our primary widget, the editor
        '''
        self.Editor = PTEditor(self,self.my_book) # defined 700 lines earlier
        self.Editor.setObjectName("Editor")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(2) # Edit deserves all available space
        sizePolicy.setVerticalStretch(2)
        sizePolicy.setHeightForWidth(False)
        self.Editor.setSizePolicy(sizePolicy)
        self.Editor.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.Editor.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.Editor.setAcceptDrops(True)
        self.Editor.setLineWidth(2)
        self.Editor.setDocumentTitle("")
        self.Editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        '''
        Set up the frame that will contain the bottom row of widgets
        It doesn't need a parent and doesn't need to be a class member
        because it will be added to a layout, which parents it.
        '''
        bot_frame = QFrame()
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(False)
        bot_frame.setSizePolicy(sizePolicy)
        bot_frame.setMinimumSize(QSize(0, 24))
        bot_frame.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        bot_frame.setFrameShape(QFrame.Shape.Panel)
        bot_frame.setFrameShadow(QFrame.Shadow.Sunken)
        bot_frame.setLineWidth(3)
        '''
        Set up the horizontal layout that will contain the following
        objects. Its parent is the frame, which gives it a look?
        '''
        HBL = QHBoxLayout(bot_frame)
        HBL.setContentsMargins(4,2,4,2)
        '''
        Set up DocName, the document name widget. It is parented
        to the bot_frame and positioned by the layout.
        '''
        self.DocName = QLabel(bot_frame)
        self.DocName.setText("")
        self.norm_style = 'color:Black;font-weight:normal;'
        self.mod_style = 'color:Red;font-weight:bold;'
        self.DocName.setStyleSheet( self.norm_style )
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(2)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(False)
        self.DocName.setSizePolicy(sizePolicy)
        self.DocName.setMinimumSize(QSize(60, 12))
        self.DocName.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.DocName.setFrameShape(QFrame.Shape.StyledPanel)
        self.DocName.setObjectName("DocName")
        self.DocName.setToolTip(_TR("EditViewWidget", "Document filename", "tool tip"))
        self.DocName.setWhatsThis(_TR("EditViewWidget", "The filename of the document being edited. It changes color when the document has been modified."))
        HBL.addWidget(self.DocName)
        spacerItem = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        HBL.addItem(spacerItem)
        '''
        Set up the label "Folio:" and the Folio display label
        '''
        FolioLabel = QLabel(bot_frame)
        FolioLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTrailing | Qt.AlignmentFlag.AlignVCenter)
        FolioLabel.setText(_TR("EditViewWidget", "Folio", "label of folio display"))
        HBL.addWidget(FolioLabel)
        self.Folio = QLabel(bot_frame)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(False)
        self.Folio.setSizePolicy(sizePolicy)
        self.Folio.setMinimumSize(QSize(30, 12))
        self.Folio.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.Folio.setFrameShape(QFrame.Shape.StyledPanel)
        self.Folio.setAlignment( Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTrailing | Qt.AlignmentFlag.AlignVCenter )
        self.Folio.setObjectName("Folio display")
        self.Folio.setToolTip(_TR("EditViewWidget", "Folio value for current page", "tooltip"))
        self.Folio.setStatusTip(_TR("EditViewWidget", "Folio value for the page under the edit cursor", "statustip"))
        self.Folio.setWhatsThis(_TR("EditViewWidget", "The Folio (page number) value for the page under the edit cursor. Use the Pages panel to adjust folios to agree with the printed book.","whats this"))
        HBL.addWidget(self.Folio)
        spacerItem = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        HBL.addItem(spacerItem)
        FolioLabel.setBuddy(self.Folio)
        '''
        Set up the image filename lineedit and its buddy label.
        '''
        ImageFilenameLabel = QLabel(bot_frame)
        ImageFilenameLabel.setAlignment( Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTrailing | Qt.AlignmentFlag.AlignVCenter )
        ImageFilenameLabel.setText(_TR("EditViewWidget", "Image", "Image field label"))
        HBL.addWidget(ImageFilenameLabel)
        self.ImageFilename = QLineEdit(bot_frame)
        sizePolicy = QSizePolicy( QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed )
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(False)
        self.ImageFilename.setSizePolicy(sizePolicy)
        self.ImageFilename.setMinimumSize(QSize(30, 12))
        self.ImageFilename.setMouseTracking(False)
        self.ImageFilename.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.ImageFilename.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.ImageFilename.setAcceptDrops(True)
        self.ImageFilename.setInputMask("")
        self.ImageFilename.setAlignment( Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTrailing | Qt.AlignmentFlag.AlignVCenter )
        self.ImageFilename.setObjectName("ImageFilename")
        self.ImageFilename.setToolTip(_TR("EditViewWidget", "Scan image filename", "Image tooltip"))
        self.ImageFilename.setStatusTip(_TR("EditViewWidget", "Filename of the scan image under the edit cursor", "Image status tip"))
        self.ImageFilename.setWhatsThis(_TR("EditViewWidget", "This is the name of the scanned image that produced the text under the edit cursor. This image file is displayed in the Image panel.","Image whats this"))
        HBL.addWidget(self.ImageFilename)
        spacerItem =  QSpacerItem(0, 0,  QSizePolicy.Policy.Expanding,  QSizePolicy.Policy.Minimum)
        HBL.addItem(spacerItem)
        ImageFilenameLabel.setBuddy(self.ImageFilename)
        '''
        Set up the line number lineedit and its buddy label.
        '''
        LineNumberLabel = QLabel(bot_frame)
        LineNumberLabel.setText(_TR("EditViewWidget", "Line#", "Line number label"))
        LineNumberLabel.setAlignment( Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTrailing | Qt.AlignmentFlag.AlignVCenter )
        HBL.addWidget(LineNumberLabel)
        self.LineNumber = QLineEdit(bot_frame)
        sizePolicy = QSizePolicy( QSizePolicy.Policy.Expanding,  QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(False)
        self.LineNumber.setSizePolicy(sizePolicy)
        self.LineNumber.setMinimumSize(QSize(0, 12))
        self.LineNumber.setMouseTracking(False)
        self.LineNumber.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.LineNumber.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.LineNumber.setAcceptDrops(True)
        self.LineNumber.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.LineNumber.setCursorPosition(0)
        self.LineNumber.setAlignment( Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTrailing | Qt.AlignmentFlag.AlignVCenter )
        self.LineNumber.setPlaceholderText("")
        self.LineNumber.setCursorMoveStyle(Qt.CursorMoveStyle.LogicalMoveStyle)
        self.LineNumber.setObjectName("LineNumber")
        self.LineNumber.setToolTip(_TR("EditViewWidget", "Line number at cursor", "Line number tooltip"))
        self.LineNumber.setStatusTip(_TR("EditViewWidget", "Line number under cursor or top of current selection","Line number statustip"))
        self.LineNumber.setWhatsThis(_TR("EditViewWidget", "The line number in the document where the edit cursor is, or the top line of the selection. Enter a new number to jump to that line.","Line number whatsthis"))
        ImageFilenameLabel.setBuddy(self.ImageFilename)
        HBL.addWidget(self.LineNumber)
        spacerItem = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        HBL.addItem(spacerItem)
        '''
        Set up the column number field and its buddy label.
        '''
        ColNumberLabel = QLabel(bot_frame)
        ColNumberLabel.setAlignment( Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTrailing | Qt.AlignmentFlag.AlignVCenter )
        ColNumberLabel.setText(_TR("EditViewWidget", "Col#", "Col number label"))
        HBL.addWidget(ColNumberLabel)
        self.ColNumber = QLabel(bot_frame)
        sizePolicy = QSizePolicy( QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(False)
        self.ColNumber.setSizePolicy(sizePolicy)
        self.ColNumber.setMinimumSize(QSize(30, 12))
        self.ColNumber.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.ColNumber.setFrameShape(QFrame.Shape.StyledPanel)
        self.ColNumber.setFrameShadow(QFrame.Shadow.Plain)
        self.ColNumber.setLineWidth(1)
        self.ColNumber.setAlignment( Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTrailing | Qt.AlignmentFlag.AlignVCenter )
        self.ColNumber.setObjectName("ColNumber")
        self.ColNumber.setToolTip(_TR("EditViewWidget", "Cursor column number", "tool tip"))
        self.ColNumber.setStatusTip(_TR("EditViewWidget", "Cursor column number", "status tip"))
        self.ColNumber.setWhatsThis(_TR("EditViewWidget", "The column number position of the cursor in the current line.","whatsthis"))
        HBL.addWidget(self.ColNumber)
        '''
        Set up a vertical layout and put two items in it, the editor and HBL
        '''
        VBL = QVBoxLayout()
        VBL.setContentsMargins(8, 8, 8, 8)
        VBL.addWidget(self.Editor)
        VBL.addWidget(bot_frame)
        self.setLayout(VBL)
        # end of _uic