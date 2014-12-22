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
                             EDITDATA.PY

The class defined here represents the contents of a document. It is a
QPlainTextDocument with a few added features. The document is the data model
used by the editor itself (editview.py) as well as providing document access
for many other parts of the system.

Externally-available functions, some from QTextDocument, some unique

    super().blockCount() used for loop control and for setting progress
                         bar status for operations that depend on doc size.

    super().setPlainText() load the document, called by the book on load.

    full_text()          get a reference to a (possibly very large) Python string
                         containing the document contents. Used by find, save.

    all_blocks()         iterator returning each QTextBlock in turn.

    a_to_z_blocks(a, z)  iterator returning QTextBlocks from a to z inclusive.

    all_lines()          iterator returning the text of each QTextBlock as a
                         Python string in turn: "for line in all_lines()"

    a_to_z_lines(a, z)   iterator returning text of each line from a to z
                         inclusive, a and z being text block numbers.

    z_to_a_lines(a, z)   iterator returning the text of each line from z
                         working numerically back to a.

    cursor_lines(c)      iterator returning the text of each line spanned
                         by the selection of a QTextCursor c.

'''
from PyQt5.QtGui import (
    QTextBlock,
    QTextDocument,
    QAbstractTextDocumentLayout)
from PyQt5.QtWidgets import (
    QPlainTextDocumentLayout
    )

import fonts

class Document(QTextDocument):
    # TODO study qtdocument and do many overrides - resource? redos?
    def __init__(self, my_book):
        super().__init__(parent = my_book)
        # Initialize slot for cached copy of document text, see full_text()
        self._text = None
        self.contentsChanged.connect(self._text_modified)

        # TODO do I want to customize the layout?
        self.setDocumentLayout(QPlainTextDocumentLayout(self))
        # Set my default font to the current mono font.
        self.setDefaultFont( fonts.get_fixed(my_book.get_font_size()) )

    #
    # Return a reference to a Python string containing the entire document.
    # Under the new (QString-less) API, a call to self.toPlainText gets a
    # Python string which has to have been mem-copied from a QString -- and
    # not simply copied, either, because the \u2029 line delimiters that Qt
    # uses, are converted to \n characters! In a larger book that could be
    # quite a slow operation. So we minimize the number of such copies by
    # caching, returning the same string as long as it is valid. When the
    # user makes any edit change to the document we get a signal and clear
    # self.text.

    def full_text(self):
        if self._text is None :
            self._text = self.toPlainText()
        return self._text

    def _text_modified(self):
        self._text = None

    # The following functions return iterators over sequences of QTextBlocks,
    # returning the QTextBlocks themselves. These are only used when access
    # to QTextBlock methods are needed. pagedata for example needs to know
    # the .position() of the textblocks that contain page separator lines.
    #
    # Note that, A, a QTextDocument is never completely empty, it always
    # contains at least 1 QTextBlock: .blockCount() >= 1 and .begin() != .end()
    #
    # Note B, findBlockByNumber(x)==end() for any x that is invalid,
    # whether negative or greater than blockCount.
    #
    # 1. The whole document from top to bottom, as for a census.
    #
    def all_blocks(self):
        tb = self.begin()
        while tb != self.end():
            yield tb
            tb = tb.next()
    #
    # 2. A range of lines from block #a to #z inclusive, guarding against
    # invalid ranges. We expect that a and z index existing blocks,
    # i.e. 0 <= a < .blockCount, 0 <= z < .blockCount, a <= z.
    #
    # The initial tests guarantee that 0 <= a < .blockCount and a <= z,
    # but we don't check that z < .blockCount; if not, tbx == self.end().
    # So the loop can start with a yield, but it needs two termination
    # checks: have we yielded the valid block z, and if not, have we
    # reached the end of valid blocks?
    #
    def a_to_z_blocks(self, a, z):
        tb = self.findBlockByNumber(a)
        tbx = self.findBlockByNumber(z)
        if a <= z and tb.isValid() :
            while True :
                yield tb # loop invariant: tb is valid and <= tbx
                if tb == tbx : break
                tb = tb.next()
                if not tb.isValid() : break

    # The following functions create iterators over sequences of QTextBlocks,
    # but return the Python string of the contents of each. They gives read
    # access to sequences of lines, as for a census or when parsing text for
    # reflow.
    #
    # 1. The whole document from top to bottom, as for a census.
    #
    def all_lines(self):
        tb = self.begin()
        while tb.isValid():
            yield tb.text()
            tb = tb.next()
    #
    # 2. A range of lines from LINE NUMBER a to z inclusive, guarding
    # against invalid ranges and a completely empty doc. Line #s are
    # origin-1, textblock #s origin-0. Same comments as for a_to_z_blocks.
    #
    def a_to_z_lines(self, a, z):
        tb = self.findBlockByNumber(a - 1)
        tbx = self.findBlockByNumber(z - 1)
        if a <= z and tb.isValid() :
            while True:
                yield tb.text() # loop invariant: here tb is valid and <= tbx
                if tb == tbx : break
                tb = tb.next()
                if not tb.isValid() : break

    #
    # 3. A range of lines from LINE NUMBER z to a inclusive in reverse
    # sequence. If z is not valid we start with lastBlock(). However
    # if a is invalid, we do not know how far to go. Return all lines
    # down to the first? Return just one? We opt for the latter.
    #
    def z_to_a_lines(self, a, z):
        tb = self.findBlockByNumber(z - 1)
        if not tb.isValid() :
            tb = self.lastBlock()
            z = tb.blockNumber() + 1
        tbx = self.findBlockByNumber(a - 1)
        if (a > z) or (not tbx.isValid()) :
            tbx = tb
            a = z
        # here we are sure that both tb.isValid && tbx.isValid
        while True:
            yield tb.text()
            if tb == tbx : break
            tb = tb.previous()
    #
    # 4. A range of lines included in the selection of a text cursor.
    # Includes the first and last lines even if the selection does not
    # completely cover them. Note that a cursor's position and anchor
    # (which define its selection) can be in either sequence.
    #
    def cursor_lines(self, tc):
        ca = min(tc.position(), tc.anchor())
        cz = max(tc.position(), tc.anchor())
        a = self.findBlock(ca).blockNumber()
        z = self.findBlock(cz).blockNumber()
        return self.a_to_z_lines( a+1, z+1 )
