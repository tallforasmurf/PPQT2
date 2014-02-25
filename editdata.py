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

    all_lines()          iterator returning the text of each QTextBlock as a
                         Python string in turn: "for line in all_lines()"

    a_to_z_lines(a, z)   iterator returning text of each line from a to z
                         inclusive.

    z_to_a_lines(a, z)   iterator returning the text of each line from z
                         working numerically back to a.

    cursor_lines(c)      iterator returning the text of each line spanned
                         by the selection of a QTextCursor c.

    all_blocks()         iterator returning each QTextBlock in turn.

    a_to_z_blocks(a, z)  iterator returning QTextBlocks from a to z inclusive.

'''
from PyQt5.QtGui import (
    QTextBlock,
    QTextCursor,
    QTextDocument,
    QAbstractTextDocumentLayout)
from PyQt5.QtWidgets import (
    QPlainTextDocumentLayout
    )

class Document(QTextDocument):
    # TODO study qtdocument and do many overrides - resource? redos?
    def __init__(self, my_book):
        super().__init__(parent = my_book)
        # set up cached copy of document text, see full_text()
        self._text = None
        self.contentsChanged.connect(self.text_modified)

        # TODO do I want to customize the layout?
        self.setDocumentLayout(QPlainTextDocumentLayout(self))

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

    def text_modified(self):
        self._text = None

    # The following functions return iterators over sequences of
    # QTextBlocks, producing a Python string of the contents of each.
    # They gives read-access to sequences of lines, as for a census
    # or when parsing text for reflow.
    #
    # Note that findBlockByNumber(x)==end() for any x that is invalid,
    # whether negative or greater than blockCount.
    #
    # 1. The whole document from top to bottom, as for a census.
    #
    def all_lines(self):
        tb = self.findBlockByNumber(0)
        while tb != self.end():
            yield tb.text()
            tb = tb.next()
    #
    # 2. A range of lines from block #a to #z inclusive, guarding
    # against invalid ranges and a completely empty doc.
    #
    def a_to_z_lines(self, a, z):
        tb = self.findBlockByNumber(a)
        tbx = self.findBlockByNumber(z) # if invalid, self.end()
        if a <= z and a >= 0 and tb != self.end() :
            while True:
                yield tb.text()
                if tb == tbx : break
                tb = tb.next()
    #
    # 3. A range of lines from block #z to #a inclusive in reverse
    # sequence.
    #
    def z_to_a_lines(self, a, z):
        tb = self.findBlockByNumber(z)
        tbx = self.findBlockByNumber(a)
        if a <= z and a >= 0 and tb != self.end() :
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
        return self.a_to_z_lines(a,z)

    # The following functions return iterators over sequences of
    # QTextBlocks, returning the QTextBlocks themselves. These are
    # only used when access to QTextBlock methods are needed, as
    # for example setUserData.
    #
    # 1. The whole document from top to bottom, as for a census.
    #
    def all_blocks(self):
        tb = self.findBlockByNumber(0)
        while tb != self.end():
            yield tb
            tb = tb.next()
    #
    # 2. A range of lines from block #a to #z inclusive, guarding
    # against invalid ranges.
    #
    def a_to_z_blocks(self, a, z):
        tb = self.findBlockByNumber(a)
        tbx = self.findBlockByNumber(z)
        if a >= 0 and a <= z and tb != self.end() :
            while True :
                yield tb
                if tb == tbx : break
                tb = tb.next()
