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

Defines a class for the edit object, which implements the user
access to a document for editing, based on QPlainTextEdit.

Given a reference to its data (editdata.py) in creation by the Book object.

Implements all keyboard actions (ctl-F, etc) in the editor.

Implements the syntax highlighter that colors scannos and spelling errors.
Calls on a WordData object to identify scannos and spelling errors.

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

    go_to_tb(tb)         given a text block, put the edit cursor at its start

'''
xp_word = "(\\w*(\\[..\\])?\\w+)+"
xp_hyap = "(" + xp_word + "[\\'\\-\u2019])*" + xp_word
#reWord = QRegExp(xp_hyap, Qt.CaseInsensitive)

import regex
from PyQt5.Qt import Qt # Qt.namespace
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QTextBlock, QTextCursor

import editview_uic
import fonts
import logging
editview_logger = logging.getLogger(name='editview')

class EditView( QWidget, editview_uic.Ui_EditViewWidget ):
    def __init__(self, my_book, parent=None):
        # Initialize our superclass(es)
        super().__init__(parent)
        # Save the link to our book
        self.my_book = my_book
        # Save access to the document itself
        self.document = my_book.get_edit_model()
        # Save access to the word list and page data
        self.word_model = my_book.get_word_model()
        self.page_model = my_book.get_page_model()
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
        # TODO: How is the initial font size set? It can't be in settings
        # because the user should be able to set it independently in
        # different edit windows, so which one wins at shutdown? In fact
        # it needs to be metadata!
        # Connect the editor to the document.
        self.Editor.setDocument(self.document)
        # Set the fonts of our widgets.
        self.set_fonts()
        # Put the document name in our widget
        self.DocName.setText(self.my_book.get_bookname())
        # Connect the Editor's modificationChanged signal to our slot.
        self.Editor.modificationChanged.connect(self.mod_change_signal)
        # Set the color of the DocName by faking that signal.
        self.mod_change_signal(self.document.isModified())
        # Connect the returnPressed signal of the LineNumber widget
        # to our go to line method.
        self.LineNumber.returnPressed.connect(self.line_number_request)
        # Connect returnPressed of the ImageFilename widget to our slot.
        self.ImageFilename.returnPressed.connect(self.image_request)
        # Connect the Editor's cursorPositionChanged signal to our slot
        self.Editor.cursorPositionChanged.connect(self.cursor_moved)


    # Set the fonts of all widgets. Done in a method because this
    # needs to be redone when the fontsChanged signal happens.
    def set_fonts(self):
        general = fonts.get_general() # default font size
        self.setFont(general) # set self, propogates to children
        mono = fonts.get_fixed(self.my_book.get_font_size())
        self.Editor.setFont(mono) # the editor is monospaced

    # Slot to receive the modificationChanged signal from the document.
    # Change the color of the DocName to match.
    def mod_change_signal(self,bool):
        # TODO: get color from colors.py
        color = 'color:Magenta;font-weight:bold;' if bool else 'color:Black;font-weight:normal;'
        self.DocName.setStyleSheet(color)

    # This slot receives the ReturnPressed signal from the LineNumber field.
    # Get the specified textblock by number, or if it doesn't exist, the end
    # textblock, and use that to position the document. There is no input
    # mask on the LineEdit (it made the cursor act weird) so test for int
    # value and clear the field if not. Make sure focus goes back to editor.
    def line_number_request(self):
        try:
            lnum = int(self.LineNumber.text())
            tb = self.document.findBlockByLineNumber(lnum-1) # text block is origin-0
            if not tb.isValid() : raise ValueError
        except ValueError:
            editview_logger.info('Request for invalid line number {0}'.format(self.LineNumber.text()))
            # TODO figure out how to beep
            self.cursor_moved() # restore current line nbr the easy way
            self.Editor.setFocus(Qt.TabFocusReason)
            return
        # TODO make it self.center_this instead
        self.go_to_tb(tb)

    # This slot receives the ReturnPresssed signal from ImageFilename.
    # Ask the page database for the index of the user-entered folio value
    # and if it knows one, get the position of it and set that.
    def image_request(self):
        fname = self.ImageFilename.text()
        pn = self.page_model.name_index(fname)
        if pn is not None :
            self.center_position(self.page_model.position(pn))
        else : # unknown image filename, restore current value the easy way
            editview_logger.info('Request for invalid image name {0}'.format(self.ImageFilename.text()))
            # TODO figure out how to beep
            self.cursor_moved()
            self.Editor.setFocus(Qt.TabFocusReason)

    # This slot is connected to Editor's cursorPositionChanged signal. Change
    # the contents of the folio, line number and column number displays to
    # match the new position.
    def cursor_moved(self):
        tc = self.Editor.textCursor()
        bn = tc.blockNumber()
        self.LineNumber.setText(str(bn+1)) # block #s are origin-0
        cn = tc.positionInBlock()
        self.ColNumber.setText(str(cn))
        pn = self.page_model.page_index(tc.position())
        if pn is not None : # the page model has info on this position
            self.ImageFilename.setText(self.page_model.filename(pn))
        else: # no image data, or positioned above page 1
            self.ImageFilename.setText('')

    # Center a position or text selection on in the middle of the window.
    # If a selection is taller than 1/2 the window height, put the top of
    # the selection higher, but in no case off the top of the window.

    def center_position(self, pos):
        tc = self.Editor.textCursor()
        tc.setPosition(pos)
        self.center_this(tc)

    def center_this(self, tc):
        #TODO Implement properly
        self.show_this(tc)

    # Position the cursor at a given document character position or the top
    # of a selection. Call our cursor_moved slot to update the widgets at the
    # bottom of the window, because just setting our text cursor doesn't do
    # that. Make sure the focus ends up in the editor.

    def show_position(self, pos):
        tc = self.Editor.textCursor()
        tc.setPosition(pos)
        self.show_this(tc)

    def show_this(self, tc):
        self.Editor.setTextCursor(tc)
        self.cursor_moved()
        self.Editor.setFocus(Qt.TabFocusReason)

    # Position the cursor at the head of a given QTextBlock (line)
    # and get the focus. Does not assume tb is a valid textblock.
    def go_to_tb(self, tb):
        if not tb.isValid():
            tb = self.document.end()
        self.show_position(tb.position())
