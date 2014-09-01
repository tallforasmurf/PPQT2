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
                         editview.py

Defines a class for the edit object, which implements the user access to a
document for editing, based on QPlainTextEdit.

Implements all keyboard actions (ctl-F, etc) in the editor.

Implements the syntax highlighter that colors scannos and spelling errors.
Calls on a WordData object to identify scannos and spelling errors.

Provides a context menu with these user commands:
    Mark Scannos
    Mark Spelling
    Choose Dictionary
    Choose Scanno File

Offers these additional methods:

    set_find_range(tc)   Set the selection of tc to be highlighted as the
                         limited find-range. Called from findview.
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
    get_cursor_val()     Return a tuple of (pos, anchor)
    set_cursor(tc)       Set a new edit cursor.
    make_cursor(pos,anchor) Return a QTextCursor with that position and anchor


'''

import regex
from PyQt5.Qt import Qt, QEvent, QObject, QCoreApplication, QSize
_TR = QCoreApplication.translate

from PyQt5.QtWidgets import (
    QAction,
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
from PyQt5.QtGui import (
    QBrush,
    QSyntaxHighlighter,
    QTextBlock,
    QTextBlockFormat,
    QTextCursor,
    QTextCharFormat,
    QTextDocument,
    QTextFormat
    )
import editview_uic
import fonts
import colors
import logging
editview_logger = logging.getLogger(name='editview')
import constants as C
import utilities

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Define a syntax highlighter object which is linked into our edit widget.
# The EditView below instantiates one of this object.
#
# Commence with a regular expression that matches a word token including
# a word that is hyphenated and/or has an apostrophe. First the word token
# which may include pgdp-style special characters like [:u] or ['e].

re_word = "(\\w*(\\[..\\])?\\w+)+"

# Now use that in the context of internal (not terminal) apostrophe
# or hyphen, allowing for both ascii and curly apostrophes.

re_hyap = "(" + re_word + "[\\'\\-\u2019])*" + re_word

re_word = regex.compile(re_hyap, regex.IGNORECASE)

# The init argument is a reference to the EditView, from which we pull the
# highlighting formats. We initialize our parent class with no text document.
# Later we will be attached to the real document with a call to setDocument.

class HighLighter(QSyntaxHighlighter):
    def __init__(self, editv, book):
        super().__init__(None)
        # Save reference to our EditView for getting formats later
        self.editv = editv
        # Save references direct to the scanno and spelling checker
        # methods of the worddata model.
        self.scanno = book.get_word_model().scanno_test
        self.speller = book.get_word_model().spelling_test

    # When highlighting is first turned on (by calling the parent class's
    # setDocument() method) the linked QTextDocument calls this function for
    # every text line in the whole document, at least to judge by the
    # hang-time. Later it only calls it to look at a line as it changes in
    # editing. In either case it behooves us to be as quick as possible.
    #
    # Either one or both of editv.scanno_check or editv.spell_check are True
    # because if they aren't, EditView would have set our document to null.
    #
    # We sample the highlight formats at the time we are called so we get
    # the latest choice of color and style. We cache the scanno and spelling
    # switches to save on python name-dict scans.
    #
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
        #
        # Take our UI setup out of line. self._uic creates and
        # initializes all the sub-widgets under self. :
        #     .Editor - the QPlainTextEditor
        #     .DocName - QLabel for the document filename
        #     .Folio - QLabel for the current folio value
        #     .ImageFilename - QLineEdit for the current image filename
        #     .LineNumber - QLineEdit for the line number
        #     .ColNumber - QLabel for the cursor column
        # Signals from these widgets are hooked up below.
        #
        self._uic()
        # Connect the editor to the document.
        self.Editor.setDocument(self.document)
        # Set up mechanism for a current-line highlight and a find-range
        # highlight. See set_find_range, clear_find_range, _set_colors
        # and _cursor_moved.
        self.last_text_block = None # to know when cursor moves to new line
        self.current_line_sel = QTextEdit.ExtraSelection()
        self.current_line_fmt = QTextCharFormat() # see _set_colors
        self.current_line_fmt.setProperty(QTextFormat.FullWidthSelection, True)
        self.range_sel = QTextEdit.ExtraSelection()
        self.range_sel.cursor = QTextCursor(self.document) # null cursor
        self.range_fmt = QTextCharFormat() # see _set_colors
        self.range_fmt.setProperty(QTextCharFormat.FullWidthSelection, True)
        self.extra_sel_list = [self.current_line_sel, self.range_sel]
        # Sign up to get a signal on a change in font choice
        fonts.notify_me(self.font_change)
        # Fake that signal to set the fonts of our widgets.
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
        self.Editor.viewport().setCursor(Qt.IBeamCursor)
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
        self.setContextMenuPolicy(Qt.DefaultContextMenu)


        #TODO FIX THIS

        # Filter the Editor's key events. We have to do this because,
        # when the Editor widget is created by Qt Creator, we do not
        # get the option of inserting a keyPressEvent() slot in it.
        self.Editor.installEventFilter(self)
        # Push the focus into the editor
        self.Editor.setFocus(Qt.MouseFocusReason)

        # End of __init__()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress :
            return self._editorKeyPressEvent(event)
        if event.type() == QEvent.Show :
            self.focusser()
        return False

    # Re-implement keyPressEvent for the Editor widget to provide bookmarks,
    # text zoom, and find. Because Editor is defined down in the Qt Designer
    # boilerplate, we can't override its keyPressEvent, so we use the above
    # eventFilter to get them. Because this is the eventFilter API not the
    # keyPressEvent API, it doesn't matter if we do event.accept(), it only
    # matters that we return True if we handled the event, False if not.
    #
    #   Zoom:
    # ctrl-plus, ctrl-minus zoom the font size by +/-1 point. Note that since
    # Qt5, QPlainTextEdit has zoomIn/zoomOut slots, but as we also need the
    # function in other panels, we do it ourselves.
    #
    #   Bookmarks:
    # ctrl-n for n in 1..9 jumps the insertion point to bookmark n
    # ctrl-shift-n extends the current selection to bookmark n
    # ctrl-alt-n sets bookmark n to the current position
    #
    #   Find:
    # ctrl-f/F/g/G/t/T/= interact with the Find panel to begin or continue
    # search and replace operations.

    def _editorKeyPressEvent(self, event):
        retval = False # assume we don't handle this event
        kkey = int( int(event.modifiers()) & C.KEYPAD_MOD_CLEAR) | int(event.key())
        if kkey in C.KEYS_EDITOR :
            retval = True # yes, this is one we handle
            if kkey in C.KEYS_FIND :
                # ^f, ^g, etc. -- just pass them straight to the Find panel
                # TODO: define private signal and emit
                # self.emit(SIGNAL("editKeyPress"),kkey)
                pass
            elif kkey in C.KEYS_ZOOM :
                self.Editor.setFont( fonts.scale(kkey, self.Editor.font()) )
                self.my_book.save_font_size(self.Editor.font().pointSize())
            elif kkey in C.KEYS_BOOKMARKS :
                # Something to do with a bookmark. They are kept in the Book
                # because they are read and written in the metadata.
                mark_number = int(event.key()) - 0x31  # number in 0..8
                mark_list = self.my_book.bookmarks # quick reference to the list
                if kkey in C.KEYS_MARK_SET :
                    # Set a bookmark to the current edit selection
                    mark_list[mark_number] = QTextCursor(self.Editor.textCursor)
                    self.my_book.metadata_modified(True, C.MD_MOD_FLAG)
                else : # kkey in C.KEYS_MARK or MARK_SHIFT :
                    # move to saved location, if that bookmark is set,
                    # extending the selection if the shift modifier is on.
                    if mark_list[mark_number] is not None:
                        pos = mark_list[mark_number].position()
                        move_mode = QTextCursor.KeepAnchor if kkey in C.KEYS_MARK_SHIFT \
                               else QTextCursor.MoveAnchor
                        tc = QTextCursor(self.Editor.textCursor)
                        tc.setPosition(pos, move_mode)
                        self.Editor.setTextCursor(tc)
        # else:  not a key for the editor, return False
        return retval

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    #                 INTERNAL METHODS

    # Set up text formats for the current line, spellcheck words
    # and for scanno words. Done in a method because this has to be
    # redone when the colorsChanged signal happens.
    def _set_colors(self):
        self.scanno_format = colors.get_scanno_format()
        self.spelling_format = colors.get_spelling_format()
        self.current_line_fmt.setBackground(colors.get_current_line_brush())
        self.current_line_sel.format = QTextCharFormat(self.current_line_fmt)
        self.range_fmt.setBackground(colors.get_find_range_brush())
        self.range_sel.format = QTextCharFormat(self.range_fmt)
        self.norm_style = 'color:Black;font-weight:normal;'
        self.mod_style = 'color:' + colors.get_modified_color().name() + ';font-weight:bold;'
        # Fake the mod-change signal to update the document name color
        self.mod_change_signal(self.document.isModified())

    # Slot to receive the modificationChanged signal from the document.
    # Also called from the book when metadata changes state.
    # Change the color of the DocName to match.
    def mod_change_signal(self,bool):
        self.DocName.setStyleSheet(self.mod_style if self.my_book.get_save_needed() else self.norm_style)

    # This slot receives the ReturnPressed signal from the LineNumber field.
    def _line_number_enter(self):
        self.go_to_line_number(self.LineNumber.text())

    # This slot receives the ReturnPresssed signal from ImageFilename.
    def _image_enter(self):
        self.go_to_image_name(self.ImageFilename.text())

    # This slot is connected to Editor's cursorPositionChanged signal, so is
    # called whenever the cursor moves for any reason, i.e. very very often!
    # It is also called directly when one of the internal methods below moves
    # the cursor. Change the contents of the column number display. If the
    # cursor has moved to a different line, change also the line number, scan
    # image name, and folio displays to match the new position.
    # Note that we show the current line by changing the text block format,
    # and unfortunately the QTextDocument sees this as an undo-able action,
    # and sets modified state. So we save and restore the unmodified state.
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
        # Change the extra selection to the current line. The cursor needs
        # to have no selection. Yes, we are here because the cursor moved,
        # but that doesn't mean no-selection; it might have moved because
        # of a shift-click extending the selection.
        #xtc.clearSelection()
        self.current_line_sel.cursor = tc
        self.Editor.setExtraSelections(self.extra_sel_list)

    # Slot to receive the fontsChanged signal. If it is the UI font, set
    # that, which propogates to all children including Editor, so set the
    # editor's mono font in any case, but using our current point size.
    # Also called from the book when reading metadata.

    def font_change(self,is_mono):
        if not is_mono :
            self.setFont(fonts.get_general())
        self.Editor.setFont(fonts.get_fixed(self.my_book.get_font_size()))

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    #                 CONTEXT MENU
    #
    # Define the four actions for our context menu, then make the menu.
    #
    # The mark-scannos and mark-spelling choices are checkable and their
    # toggled signal is connected to these slots.
    #
    # The problem is that both types of highlights are done by the same
    # highlighter, and it is only called when it is first started (and
    # during editing of single lines later). Thus any change in highlighting
    # requires stopping it which clears all highlights, then restarting it.

    def _clear_highlights(self):
        self.highlighter.setDocument(QTextDocument())

    def _start_highlights(self):
        self.highlighter.setDocument(self.document)

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
    #
    # These are called by the triggered signal of the menu items. The
    # choose-scanno and choose-dictionary actions are passed along to the
    # book. It asks the user to choose a file or a dict, and if a new file or
    # dict is selected, it causes the word model to load the new scannos or
    # recheck spelling with the new dict. The highlighter works off the
    # values kept by the word model.
    #
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

    #
    # Create the menu itself. This is part of initialization.
    #
    def _make_context_menu(self):
        global _TR
        m = QMenu(self)
        act1 = QAction( _TR("EditViewWidget","Mark Scannos","context menu item"), m )
        act1.setCheckable(True)
        act1.setToolTip( _TR("EditViewWidget",
                                "Turn on or off marking of words from the scanno file",
                                "context menu tooltip") )
        act1.toggled.connect(self._act_mark_scannos)
        m.addAction(act1)
        act2 = QAction( _TR("EditViewWidget","Mark Spelling","context menu item"), m )
        act2.setCheckable(True)
        act2.setToolTip( _TR("EditViewWidget",
                                "Turn on or off marking words that fail spellcheck",
                                "context menu tooltip") )
        act2.toggled.connect(self._act_mark_spelling)
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
        return m
    #
    # Override the parent's contextMenuEvent to display and execute the menu.
    #
    def contextMenuEvent(self, event):
        self.context_menu.exec_(event.globalPos())

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    #                 PUBLIC METHODS
    #
    # Retrieve the current image filename. Called from Notes.

    def get_image_name(self):
        return self.ImageFilename.text()

    # Go to page image by name: Ask the page database for the index of the
    # user-entered filename value and if it recognizes it, get the position
    # of it and set that. This is called from _image_enter and also from
    # the Notes panel.

    def go_to_image_name(self, name_string):
        pn = self.page_model.name_index(name_string)
        if pn is not None :
            self.center_position(self.page_model.position(pn))
        else : # unknown image filename, restore current value
            utilities.beep()
            editview_logger.info('Request for invalid image name {0}'.format(self.ImageFilename.text()))
            self._cursor_moved()
        self.Editor.setFocus(Qt.TabFocusReason)

    # Retrieve the current line number string. Called from Notes.

    def get_line_number(self):
        return self.LineNumber.text()

    # Called by the parent Book when the book is renamed as part of Save-As.

    def book_renamed(self,name):
        self.DocName.setText(name)

    # Set and clear the highlighting on a limited find range. Called from
    # findview.py to make the current find range visible.
    def set_find_range(self,tc):
        wtc  = self.range_sel.cursor
        wtc.setPosition(tc.selectionEnd())
        wtc.setPosition(tc.selectionStart(), QTextCursor.KeepAnchor)
        self.Editor.setExtraSelections(self.extra_sel_list)
    def clear_find_range(self):
        self.range_sel.cursor.clearSelection()
        self.Editor.setExtraSelections(self.extra_sel_list)

    # Called from other panels who need to connect editor signals,
    # e.g. the Find panel.
    def get_actual_editor(self):
        return self.Editor

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    #                 Cursor positioning
    #
    # Go to line number string: called from the _line_number_enter slot and
    # also from the Notes panel. Given a supposed line number as a string
    # 'nnn', get the corresponding textblock and use that to position the
    # document. Do not assume an integer string value or a valid line number;
    # if invalid, beep and do nothing. Finally, make sure focus goes back to
    # editor (it might now be in the Notes panel).
    #
    def go_to_line_number(self, lnum_string):
        try:
            lnum = int(lnum_string) - 1 # text block is origin-0
            tb = self.document.findBlockByLineNumber(lnum)
            if not tb.isValid() : raise ValueError
            self.go_to_block(tb)
        except ValueError: # from int() or explicit
            utilities.beep()
            editview_logger.error('Request to show invalid line number {0}'.format(lnum_string))

    # Position the cursor at the head of a given QTextBlock (line)
    # and get the focus. Does not assume tb is a valid textblock.

    def go_to_block(self, tb):
        if not tb.isValid():
            utilities.beep()
            editview_logger.error('Request to show invalid text block')
            tb = self.document.lastBlock()
        self.show_position(tb.position())

    # Position the document to show a given character position.
    # Breaks the current selection if any. Does not necessarily
    # center the new position. Does not assume the position is valid.

    def show_position(self, pos):
        try:
            pos = int(pos)
            if (pos < 0) or (pos >= self.document.characterCount() ) :
                raise ValueError
        except:
            utilities.beep()
            editview_logger.error('Request to show invalid position {0}'.format(pos))
            pos = self.document.characterCount()
        tc = QTextCursor(self.Editor.textCursor())
        tc.setPosition(pos)
        self.show_this(tc)

    # Make a selection visible. Breaks the current selection if any.
    # Does not necessarily center the new selection.

    def show_this(self, tc):
        self.Editor.setTextCursor(tc)
        self.Editor.ensureCursorVisible()
        self.Editor.setFocus(Qt.TabFocusReason)

    # Center a position or text selection in the middle of the window. Called
    # e.g. from Find to display the found selection. If a selection is taller
    # than 1/2 the window height, put the top of the selection higher, but in
    # no case off the top of the window.
    #
    # All coordinates are in pixels in the viewport coordinate system. Only
    # the vertical (y) coordinates matter, x is always 0.
    #
    # Let L be line spacing from the current fontMetrics. Let V be the viewport
    # .height() and let V2 = V/2-L, coordinate of the middle of the port.
    #
    # To get the coordinates of a line, use QTextEdit.cursorRect() and
    # from it get .y() for the top or .y()+L for the bottom.
    #
    # Let P be the position of the top of the selection. Let S be the
    # height of the selection. Let M be the amount to move P to bring it
    # to the middle of the viewport: M = V2 - P (negative means "up").
    #
    # This is too simple, we need to adjust for a selection where S>V2.
    # Let M = V2 - P - min(V2, max(0, S-V2))
    #
    # To effect a move by M we need to set a new position in the vertical
    # scrollbar. The scrollbar works on arbitrary units from .minimum() to
    # .maximum(). We need to adjust its value by M as a fraction of the total
    # height of the document. Let A be the coordinate of the first line, let
    # Z be the coordinate of the last line; then set the scrollbar to
    # .value() + (M/(Z-A)*(.maximum - .minimum).

    def center_position(self, pos):
        tc = self.Editor.textCursor()
        tc.setPosition(pos)
        self.center_this(tc)

    def _top_pixel_of_pos(self, pos):
        tc = QTextCursor(self.document)
        tc.setPosition(pos)
        return self.Editor.cursorRect(tc).y()

    def center_this(self, tc):
        # The selection in tc might be the current edit cursor, or it might
        # be a different selection e.g. from a Find operation. Establish it
        # as the selection.
        self.Editor.setTextCursor(QTextCursor(tc))
        L = self.Editor.fontMetrics().lineSpacing()
        V = self.Editor.viewport().height()
        V2 = int(V/2) - L
        P = self._top_pixel_of_pos(tc.selectionStart())
        S = self._top_pixel_of_pos(tc.selectionEnd()) - P + L
        M = V2 - P - min(V2, max(0, S - V2))
        A = self._top_pixel_of_pos( self.document.firstBlock().position() )
        Z = self._top_pixel_of_pos( self.document.characterCount()-1 )
        vsb = self.Editor.verticalScrollBar()
        vsb.setValue( vsb.value() - int( (M/(Z-A)) * (vsb.maximum()-vsb.minimum()) ) )
        # who sez BASIC is dead?
        self._cursor_moved()
        self.Editor.setFocus(Qt.TabFocusReason)

    # Lots of other code needs a textcursor for the current document.
    def get_cursor(self):
        return QTextCursor(self.Editor.textCursor())
    # Return the essence of the cursor as a tuple (pos,anc)
    def get_cursor_val(self):
        return (self.Editor.textCursor().position(), self.Editor.textCursor.anchor())
    # Some other code likes to reposition the edit selection:
    def set_cursor(self, tc):
        self.Editor.setTextCursor(tc)
    # Make a valid cursor based on position and anchor values possibly
    # input by the user.
    def make_cursor(self, position, anchor):
        mx = self.document.characterCount()
        tc = QTextCursor(self.Editor.textCursor())
        anchor = min( max(0,anchor), mx )
        position = min ( max(0,position), mx )
        tc.setPosition(anchor)
        tc.setPosition(position,QTextCursor.KeepAnchor)
        return tc

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    #            INITIALIZE UI
    #
    # First we built the Edit panel using Qt Creator which produced a large
    # and somewhat opaque block of code that had to be mixed in by
    # multiple inheritance. This had several drawbacks, so the following
    # is a "manual" UI setup using code drawn from the generated code.
    #
    def _uic(self):
        # First set up the properties of "self", a QWidget.
        self.setObjectName("EditViewWidget")
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(False) # don't care to bind height to width
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QSize(250, 250))
        self.setFocusPolicy(Qt.StrongFocus)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setWindowTitle("")
        self.setToolTip("")
        self.setStatusTip("")
        self.setWhatsThis("")
        # Set up our primary widget, the editor
        self.Editor = QPlainTextEdit(self)
        self.Editor.setObjectName("Editor")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(2) # Edit deserves all available space
        sizePolicy.setVerticalStretch(2)
        sizePolicy.setHeightForWidth(False)
        self.Editor.setSizePolicy(sizePolicy)
        self.Editor.setFocusPolicy(Qt.StrongFocus)
        self.Editor.setContextMenuPolicy(Qt.NoContextMenu)
        self.Editor.setAcceptDrops(True)
        self.Editor.setLineWidth(2)
        self.Editor.setDocumentTitle("")
        self.Editor.setLineWrapMode(QPlainTextEdit.NoWrap)

        # Set up the frame that will contain the bottom row of widgets
        # It doesn't need a parent and doesn't need to be a class member
        # because it will be added to a layout, which parents it.
        bot_frame = QFrame()
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(False)
        bot_frame.setSizePolicy(sizePolicy)
        bot_frame.setMinimumSize(QSize(0, 24))
        bot_frame.setContextMenuPolicy(Qt.NoContextMenu)
        bot_frame.setFrameShape(QFrame.Panel)
        bot_frame.setFrameShadow(QFrame.Sunken)
        bot_frame.setLineWidth(3)

        # Set up the horizontal layout that will contain the following
        # objects. Its parent is the frame, which gives it a look?

        HBL = QHBoxLayout(bot_frame)
        HBL.setContentsMargins(4,2,4,2)

        # Set up DocName, the document name widget. It is parented
        # to the bot_frame and positioned by the layout.

        self.DocName = QLabel(bot_frame)
        self.DocName.setText("")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(2)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(False)
        self.DocName.setSizePolicy(sizePolicy)
        self.DocName.setMinimumSize(QSize(60, 12))
        self.DocName.setContextMenuPolicy(Qt.NoContextMenu)
        self.DocName.setFrameShape(QFrame.StyledPanel)
        self.DocName.setObjectName("DocName")
        self.DocName.setToolTip(_TR("EditViewWidget", "Document filename", "tool tip"))
        self.DocName.setWhatsThis(_TR("EditViewWidget", "The filename of the document being edited. It changes color when the document has been modified."))
        HBL.addWidget(self.DocName)
        spacerItem = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        HBL.addItem(spacerItem)

        # Set up the label "Folio:" and the Folio display label
        FolioLabel = QLabel(bot_frame)
        FolioLabel.setAlignment(Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)
        FolioLabel.setText(_TR("EditViewWidget", "Folio", "label of folio display"))
        HBL.addWidget(FolioLabel)

        self.Folio = QLabel(bot_frame)
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(False)
        self.Folio.setSizePolicy(sizePolicy)
        self.Folio.setMinimumSize(QSize(30, 12))
        self.Folio.setContextMenuPolicy(Qt.NoContextMenu)
        self.Folio.setFrameShape(QFrame.StyledPanel)
        self.Folio.setAlignment( Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter )
        self.Folio.setObjectName("Folio display")
        self.Folio.setToolTip(_TR("EditViewWidget", "Folio value for current page", "tooltip"))
        self.Folio.setStatusTip(_TR("EditViewWidget", "Folio value for the page under the edit cursor", "statustip"))
        self.Folio.setWhatsThis(_TR("EditViewWidget", "The Folio (page number) value for the page under the edit cursor. Use the Pages panel to adjust folios to agree with the printed book.","whats this"))
        HBL.addWidget(self.Folio)
        spacerItem = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        HBL.addItem(spacerItem)
        FolioLabel.setBuddy(self.Folio)

        # Set up the image filename lineedit and its buddy label.
        ImageFilenameLabel = QLabel(bot_frame)
        ImageFilenameLabel.setAlignment( Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter )
        ImageFilenameLabel.setText(_TR("EditViewWidget", "Image", "Image field label"))
        HBL.addWidget(ImageFilenameLabel)
        self.ImageFilename = QLineEdit(bot_frame)
        sizePolicy = QSizePolicy( QSizePolicy.Expanding, QSizePolicy.Fixed )
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(False)
        self.ImageFilename.setSizePolicy(sizePolicy)
        self.ImageFilename.setMinimumSize(QSize(30, 12))
        self.ImageFilename.setMouseTracking(False)
        self.ImageFilename.setFocusPolicy(Qt.ClickFocus)
        self.ImageFilename.setContextMenuPolicy(Qt.NoContextMenu)
        self.ImageFilename.setAcceptDrops(True)
        self.ImageFilename.setInputMask("")
        self.ImageFilename.setAlignment( Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter )
        self.ImageFilename.setObjectName("ImageFilename")
        self.ImageFilename.setToolTip(_TR("EditViewWidget", "Scan image filename", "Image tooltip"))
        self.ImageFilename.setStatusTip(_TR("EditViewWidget", "Filename of the scan image under the edit cursor", "Image status tip"))
        self.ImageFilename.setWhatsThis(_TR("EditViewWidget", "This is the name of the scanned image that produced the text under the edit cursor. This image file is displayed in the Image panel.","Image whats this"))
        HBL.addWidget(self.ImageFilename)
        spacerItem =  QSpacerItem(0, 0,  QSizePolicy.Expanding,  QSizePolicy.Minimum)
        HBL.addItem(spacerItem)
        ImageFilenameLabel.setBuddy(self.ImageFilename)

        # Set up the line number lineedit and its buddy label.
        LineNumberLabel = QLabel(bot_frame)
        LineNumberLabel.setText(_TR("EditViewWidget", "Line#", "Line number label"))
        LineNumberLabel.setAlignment( Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter )
        HBL.addWidget(LineNumberLabel)
        self.LineNumber = QLineEdit(bot_frame)
        sizePolicy = QSizePolicy( QSizePolicy.Expanding,  QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(False)
        self.LineNumber.setSizePolicy(sizePolicy)
        self.LineNumber.setMinimumSize(QSize(0, 12))
        self.LineNumber.setMouseTracking(False)
        self.LineNumber.setFocusPolicy(Qt.ClickFocus)
        self.LineNumber.setContextMenuPolicy(Qt.NoContextMenu)
        self.LineNumber.setAcceptDrops(True)
        self.LineNumber.setLayoutDirection(Qt.LeftToRight)
        self.LineNumber.setCursorPosition(0)
        self.LineNumber.setAlignment( Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter )
        self.LineNumber.setPlaceholderText("")
        self.LineNumber.setCursorMoveStyle(Qt.LogicalMoveStyle)
        self.LineNumber.setObjectName("LineNumber")
        self.LineNumber.setToolTip(_TR("EditViewWidget", "Line number at cursor", "Line number tooltip"))
        self.LineNumber.setStatusTip(_TR("EditViewWidget", "Line number under cursor or top of current selection","Line number statustip"))
        self.LineNumber.setWhatsThis(_TR("EditViewWidget", "The line number in the document where the edit cursor is, or the top line of the selection. Enter a new number to jump to that line.","Line number whatsthis"))
        ImageFilenameLabel.setBuddy(self.ImageFilename)
        HBL.addWidget(self.LineNumber)
        spacerItem = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        HBL.addItem(spacerItem)

        # Set up the column number field and its buddy label.
        ColNumberLabel = QLabel(bot_frame)
        ColNumberLabel.setAlignment( Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter )
        ColNumberLabel.setText(_TR("EditViewWidget", "Col#", "Col number label"))
        HBL.addWidget(ColNumberLabel)
        self.ColNumber = QLabel(bot_frame)
        sizePolicy = QSizePolicy( QSizePolicy.Expanding, QSizePolicy.Preferred )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(False)
        self.ColNumber.setSizePolicy(sizePolicy)
        self.ColNumber.setMinimumSize(QSize(30, 12))
        self.ColNumber.setContextMenuPolicy(Qt.NoContextMenu)
        self.ColNumber.setFrameShape(QFrame.StyledPanel)
        self.ColNumber.setFrameShadow(QFrame.Plain)
        self.ColNumber.setLineWidth(1)
        self.ColNumber.setAlignment( Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter )
        self.ColNumber.setObjectName("ColNumber")
        self.ColNumber.setToolTip(_TR("EditViewWidget", "Cursor column number", "tool tip"))
        self.ColNumber.setStatusTip(_TR("EditViewWidget", "Cursor column number", "status tip"))
        self.ColNumber.setWhatsThis(_TR("EditViewWidget", "The column number position of the cursor in the current line.","whatsthis"))
        HBL.addWidget(self.ColNumber)

        # Set up a vertical layout and put two items in it, the editor and HBL
        VBL = QVBoxLayout()
        VBL.setContentsMargins(8, 8, 8, 8)
        VBL.addWidget(self.Editor)
        VBL.addWidget(bot_frame)
        self.setLayout(VBL)

        # end of _uic