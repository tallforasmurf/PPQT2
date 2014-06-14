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

    go_to_block(tb)      given a text block, put the edit cursor at its start
                         and show it via show_this.

    get_cursor()         Return a COPY of the current edit cursor.
    get_cursor_val()     Return a tuple of (pos, anchor)
    set_cursor(tc)       Set a new edit cursor.
    make_cursor(pos,anchor) Return a QTextCursor with that position and anchor


'''

import regex
from PyQt5.Qt import Qt, QEvent, QObject, QCoreApplication
_TR = QCoreApplication.translate

from PyQt5.QtWidgets import (
    QAction,
    QFileDialog,
    QMenu,
    QTextEdit,
    QWidget
    )
from PyQt5.QtGui import (
    QBrush,
    QSyntaxHighlighter,
    QTextBlock,
    QTextBlockFormat,
    QTextCursor,
    QTextCharFormat,
    QTextDocument
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

class EditView( QWidget, editview_uic.Ui_EditViewWidget ):
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
        # invoke the UI setup defined by pyuic5, passing this
        # object as the parameter that setupUi refers to as "EditWidget".
        # It creates and initializes all the sub-widgets under the
        # following properties of "self":
        #     .Editor - the QPlainTextEditor
        #     .DocName - QLabel for the document filename
        #     .Folio - QLabel for the current folio value
        #     .ImageFilename - QLineEdit for the current image filename
        #     .LineNumber - QLineEdit for the line number
        #     .ColNumber - QLabel for the cursor column
        #
        # Those names are the only dependencies between this code
        # and the QDesigner/pyuic5 output.
        self.setupUi(self)
        # Connect the editor to the document.
        self.Editor.setDocument(self.document)
        # Set up mechanism for a current-line highlight
        self.current_line_fmt = QTextBlockFormat()
        self.normal_line_fmt = QTextBlockFormat()
        self.normal_line_fmt.setBackground(QBrush(Qt.white))
        self.last_text_block = self.Editor.textCursor().block()
        # Set the fonts of our widgets.
        self.font_change(False) # update all fonts to default
        # hook up to be notified of a change in font choice
        fonts.notify_me(self.font_change)
        # Get the current highlight colors. This sets members scanno_format,
        # spelling_format, current_line_thing, norm_style and mod_style.
        self._set_colors()
        colors.notify_me(self._set_colors)
        # Put the document name in our widget
        self.DocName.setText(self.my_book.get_book_name())
        # Connect the Editor's modificationChanged signal to our slot.
        self.Editor.modificationChanged.connect(self._mod_change_signal)
        # Connect the returnPressed signal of the LineNumber widget
        # to our go to line method.
        self.LineNumber.returnPressed.connect(self._line_number_request)
        # Connect returnPressed of the ImageFilename widget to our slot.
        self.ImageFilename.returnPressed.connect(self._image_request)
        # Connect the Editor's cursorPositionChanged signal to our slot
        self.Editor.cursorPositionChanged.connect(self._cursor_moved)
        # Fill in the line and column number by faking that signal
        self._cursor_moved(force=True)
        # Filter the Editor's key events. We have to do this because,
        # when the Editor widget is created by Qt Creator, we do not
        # get the option of inserting a keyPressEvent() slot in it.
        self.Editor.installEventFilter(self)
        # Create and install our context menu
        self.context_menu = self._make_context_menu()
        self.setContextMenuPolicy(Qt.DefaultContextMenu)
        # Push the focus into the editor
        self.Editor.setFocus(Qt.MouseFocusReason)

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    #                 INTERNAL METHODS

    # Set up text formats for the current line, spellcheck words
    # and for scanno words. Done in a method because this has to be
    # redone when the colorsChanged signal happens.
    def _set_colors(self):
        self.scanno_format = colors.get_scanno_format()
        self.spelling_format = colors.get_spelling_format()
        self.current_line_fmt.setBackground(colors.get_current_line_brush())
        self.norm_style = 'color:Black;font-weight:normal;'
        self.mod_style = 'color:' + colors.get_modified_color().name() + ';font-weight:bold;'
        # Fake the mod-change signal to update the document name color
        self._mod_change_signal(self.document.isModified())

    # Slot to receive the modificationChanged signal from the document.
    # Change the color of the DocName to match.
    def _mod_change_signal(self,bool):
        self.DocName.setStyleSheet(self.mod_style if bool else self.norm_style)

    # This slot receives the ReturnPressed signal from the LineNumber field.
    # Get the specified textblock by number, or if it doesn't exist, the end
    # textblock, and use that to position the document. There is no input
    # mask on the LineEdit (it made the cursor act weird) so test for int
    # value and clear the field if not. Make sure focus goes back to editor.
    def _line_number_request(self):
        try:
            lnum = int(self.LineNumber.text())
            tb = self.document.findBlockByLineNumber(lnum-1) # text block is origin-0
            if not tb.isValid() : raise ValueError
        except ValueError:
            utilities.beep()
            editview_logger.info('Request for invalid line number {0}'.format(self.LineNumber.text()))
            # force update of line # display
            self._cursor_moved(force=True) # restore current line nbr the easy way
            self.Editor.setFocus(Qt.TabFocusReason)
            return
        self.go_to_block(tb)

    # This slot receives the ReturnPresssed signal from ImageFilename.
    # Ask the page database for the index of the user-entered folio value
    # and if it knows one, get the position of it and set that.
    def _image_request(self):
        fname = self.ImageFilename.text()
        pn = self.page_model.name_index(fname)
        if pn is not None :
            self.center_position(self.page_model.position(pn))
        else : # unknown image filename, restore current value
            utilities.beep()
            editview_logger.info('Request for invalid image name {0}'.format(self.ImageFilename.text()))
            self._cursor_moved(force=True)
            self.Editor.setFocus(Qt.TabFocusReason)

    # This slot is connected to Editor's cursorPositionChanged signal, so is
    # called whenever the cursor moves for any reason, i.e. very very often!
    # It is also called directly when one of the internal methods below moves
    # the cursor. Change the contents of the column number display. If the
    # cursor has moved to a different line, change also the line number, scan
    # image name, and folio displays to match the new position.
    def _cursor_moved(self, force=False):
        tc = self.Editor.textCursor()
        self.ColNumber.setText( str( tc.positionInBlock() ) )
        tb = tc.block()
        if tb == self.last_text_block and not force :
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
        # clear any highlight on the previous current line
        temp_cursor = QTextCursor(self.last_text_block)
        temp_cursor.setBlockFormat(self.normal_line_fmt)
        # remember this new current line
        self.last_text_block = tb
        # and set its highlight
        temp_cursor = QTextCursor(tb)
        temp_cursor.setBlockFormat(self.current_line_fmt)

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
                    self.my_book.metadata_modified()
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
    # The choose-scanno and choose-dictionary actions are passed along to the
    # book. These are called by the triggered signal of the menu items.
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

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    #                 PUBLIC METHODS

    # Called by the parent Book prior to a Save-As renaming the book.
    def book_renamed(self,name):
        self.DocName.setText(name)

    # Slot to receive the fontsChanged signal. If it is the UI font, set
    # that, which propogates to all children including Editor, so set the
    # editor's mono font in any case, but using our current point size.
    # Also called from the book when reading metadata.

    def font_change(self,is_mono):
        if not is_mono :
            self.setFont(fonts.get_general())
        self.Editor.setFont(fonts.get_fixed(self.my_book.get_font_size()))

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    #                 Cursor positioning
    #
    # Position the cursor at the head of a given QTextBlock (line)
    # and get the focus. Does not assume tb is a valid textblock.

    def go_to_block(self, tb):
        if not tb.isValid():
            tb = self.document.end()
        self.show_position(tb.position())

    # Position the document to show a given character position.
    # Breaks the current selection if any. Does not necessarily
    # center the new position.

    def show_position(self, pos):
        tc = QTextCursor(self.Editor.textCursor())
        tc.setPosition(pos)
        self.show_this(tc)

    # Make a selection visible. Breaks the current selection if any.
    # Does not necessarily center the new selection.

    def show_this(self, tc):
        self.Editor.setTextCursor(tc)
        self._cursor_moved()
        self.Editor.setFocus(Qt.TabFocusReason)

    # Center a position or text selection in the middle of the window. Called
    # e.g. from Find to display the found selection. If a selection is taller
    # than 1/2 the window height, put the top of the selection higher, but in
    # no case off the top of the window.
    #
    # Two problems arise: One, cursorRect gives only the height of the actual
    # cursor, not of the selected text. To find out the height of the full
    # selection we have to get a cursorRect for the start of the selection,
    # and another for the end of it. Two, the rectangles returned by
    # .cursorRect() and by .viewport().geometry() are in pixel units, while
    # the vertical scrollbar is sized in logical text lines. So we work out
    # the adjustment as a fraction of the viewport, times the scrollbar's
    # pageStep value to get lines.

    def center_position(self, pos):
        tc = self.Editor.textCursor()
        tc.setPosition(pos)
        self.center_this(tc)

    def center_this(self, tc):
        # Establish the selection so we can play with the cursor
        self.Editor.setTextCursor(tc)
        # Get the ends of the selection in character position units.
        top_point = tc.selectionStart()
        bot_point = tc.selectionEnd()
        # Get the topmost pixel of the topmost character.
        tc.setPosition(top_point)
        selection_top = self.Editor.cursorRect(tc).top()
        # Save the height in pixels of one line
        line_height = self.Editor.cursorRect(tc).height()
        # Get the bottom-most pixel of the bottom-most character
        tc.setPosition(bot_point)
        selection_bot = self.Editor.cursorRect(tc).bottom()
        # Height of the selection in pixels, versus 1/2 the viewport height
        selection_height = selection_bot - selection_top + 1
        view_height = self.Editor.viewport().geometry().height()
        view_half = int(view_height/2)
        pixel_adjustment = 0
        if selection_height < view_half :
            # Selected text is less than half the window height. Center the
            # top of the selection by making cursor_top equal view_half.
            pixel_adjustment = selection_top - view_half # may be negative
        else :
            # selected text is taller than half the window.
            if selection_height < (view_height - line_height) :
                # All selected text fits in the viewport (with a little
                # free): center the selection in the viewport.
                pixel_adjustment = (selection_top + (selection_height/2)) - view_half
            else :
                # Selection is bigger than the viewport. Put the top of the
                # text near the top of the viewport.
                pixel_adjustment = selection_top - line_height
        # Convert the pixel adjustment to a line-adjustment, based on the
        # assumption that one scrollbar pageStep is the height of the viewport
        # in lines.
        adjust_fraction = pixel_adjustment / view_height
        vscroller = self.Editor.verticalScrollBar()
        page_step = vscroller.pageStep()
        adjust_lines = int(page_step * adjust_fraction)
        target = vscroller.value() + adjust_lines
        if (target >= 0) and (target <= vscroller.maximum()) :
            vscroller.setValue(target)
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
