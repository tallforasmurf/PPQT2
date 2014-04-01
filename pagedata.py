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

                          PAGEDATA.PY

Defines a class to store info extracted from page boundary lines and act as
the Data Model for pageview.py, which displays the page table with user
controls. Defines some constants used by pagedata and pageview.

One of these objects is created by each Book object. It:
  * is called by the Book to load metadata for a known book.
  * is called by the Book to scan page separators for a new book.
  * is called by the Book during save, to write metadata.
  * acts as data model to the the Pages view panel
  * also is data model to the Images view panel
  * also is data model to the Edit view panel (for folio number display)

    Load Process

When the Book is created it creates a PageData object which registers a
reader and writer for the PAGETABLE metadata section. The main window tells
the Book to load either a known file (one with matching .meta file) or a new
file (without). In the first case the metadata manager calls the registered
read_pages method to store the page info from the metadata file.

In the second case the Book calls the scan_pages() method, which uses the
editdata's all_blocks iterator to scan the document and extract the key info
from all page separator lines. At either time QTextCursors are created to mark
the start of each page in the book.

scan_pages() is only called the first time a document is loaded. From
then on we save and load page info in the metadata file.

    Save Process

The metadata manager calls the write_pages() method to write the metadata
lines. The format is unchanged from V1.

    Data Storage

This "data model" has 6 items to store about each scan page:

  * The page start offset in the document. This is stored as a QTextCursor so
  that Qt will update it continuously as the document is edited -- sometimes!
  See the note on Page Boundary Cursors below.

  * The scan image filename string, usually a number like "002" or "0075" but
  sometimes alphanumeric.

  * Three ints related to the Folio value:
       - the folio rule, e.g. C.FolioRuleAdd1
       - the folio format, e.g. C.FolioFormatArabic
       - the folio number, e.g. 17

  * A string of proofer names separated by backslashes, e.g.
        \\Frau Sma\\fsmwalb\Scribe
    When writing the metadata file, spaces within this string are replaced
    with C.UNICODE_EN_SPACE so the string will remain a unit under split().
    Note also some names may be null, as the 1st and 3rd in the example.

In effect this is a 6-column table indexed by row number. However
in memory, data is in lists indexed by row number:

  * cursor_list is a list of QTextCursor objects
  * filename_list is a list of filename strings
  * folio_list is a list of three-item lists [rule,format,number]
    -- a list not a tuple because it needs to be mutable
  * proofer_list is a list of lists containing proofer names, e.g.
    [ "", "Frau Sma", "", "fsmwalb", "Scribe" ] with u2002's converted.

    Public Methods

pagedata has two clients: imageview displays the scan images using the filenames;
and pageview displays all the data in the Pages panel.

    active()    returns True when pagedata is available, False else.

    page_count()returns the count of pages (for sizing the page table).

    page_index(P)  returns the row index for the page that contains
                document offset P, or None if P precedes the first page.
                This is called every time the edit cursor moves.

    filename(R) returns the filename string for row R.

    proofers(R) returns the proofer string list for row R.

    folios(R)   returns the folio item list for row R.

    set_folios(R, [rule,fmt,nbr]) update the folio values for row j.

    Page Boundary Cursors

We rely on Qt to keep the page-start cursors accurate under editing. This
does not always happen. Under some types of edit, the start-offset of a
page can be misplaced.

Specifically, if the user selects a span of text that includes one or more
page boundaries, and deletes or replaces that span of text, the cursor(s)
that mark(s) the start(s) of the page(s) move to the end of the changed or
deleted span. This part is inevitable (what else could the editor do?), but
it does mean that if a span of text covering two or more pages is
deleted/replaced, the affected page boundaries all end up pointing to the
same point, the end of the replaced span.

The bug (bugreports.qt-project.org/browse/QTBUG-32689) is that if you UNDO
such an edit change -- as in "OMG did I really just delete three pages?
Quick, control-z!" -- the cursors are NOT restored to their former positions
but remain pointing to the end of the now-restored section of text. So Undo
fails to restore the page boundary positions once they are moved.

Note that in the Reflow process, which often replaces spans of text that
overlap page boundaries, there is special code to preserve these markers.
However if you reflow and then Undo, bug 32689 bites you.

One possible approach would be to give the user a "Refresh" button on the
Pages panel, asking us to re-scan the page separator lines, if they still
exist. (If they have been deleted, nothing could be done.) This refresh would
look for psep lines and update only the start offsets and cursors, preserving
any folio work that had been done. This could also be coded as a standalone
utility. (This wouldn't help reflow, which is done after page sep lines are
deleted.)

'''
import logging
pagedata_logger = logging.getLogger(name='pagedata')

import regex
import constants as C
import metadata
import editdata
from PyQt5.QtGui import QTextBlock, QTextCursor

# This regex recognizes a page separator line and captures:
#   1: image filename -- usually but not always numeric
#   2: string of proofer names divided by backslashes
# The compiled regex can be a global because in use, it
# creates a match object that is private to the caller.

re_line_sep = regex.compile(
    '''-----File: ([^\\.]+)\\.png---((\\\\[^\\\\]*)+)\\\\-*'''
    ,regex.IGNORECASE)

class PageData(object):
    def __init__(self, my_book):
        self.my_book = my_book
        # Save reference to the metamanager
        self.metamgr = my_book.get_meta_manager()
        # Save reference to the edited document
        self.document = my_book.get_edit_model()
        # Set up lists
        self.cursor_list = []
        self.filename_list = []
        self.folio_list = []
        self.proofers_list = []
        # Flag indicating we have data and are open for business
        self._active = False
        # Last-returned position and row
        self.last_pos = None
        self.last_row = 0
        # Register to read and write metadata
        self.metamgr.register(C.MD_PT, self.read_pages, self.write_pages)

    #
    # Scan all lines of a new document and create page sep info.
    # We fetch QTextBlocks, not just content strings, because we
    # need to get the .position() of the matching lines.
    #
    # Set all folios to Arabic, Add 1, and the sequence number.
    # This operation creates new data, so we set metadata_modified.
    #
    def scan_pages(self):
        global re_line_sep
        # first page is Arabic starting at 1
        rule = C.FolioRuleSet
        fmt = C.FolioFormatArabic
        nbr = 1
        for qtb in self.document.all_blocks() :
            m = re_line_sep.match(qtb.text())
            if m :
                # capture the image filename
                fname = m.group(1)
                # secure the proofers as a list, omitting the
                # null element caused by the leading '\'
                plist = m.group(2).split('\\')[1:]
                qtc = QTextCursor(self.document)
                qtc.setPosition(qtb.position())
                self.cursor_list.append(qtc)
                self.filename_list.append(fname)
                self.folio_list.append( [rule,fmt,nbr] )
                self.proofers_list.append(plist)
                # remaining pages are ditto, add 1, next number
                rule = C.FolioRuleAdd1
                fmt = C.FolioFormatSame
                nbr += 1
        if 0 < len(self.cursor_list) : # we found at least 1
            self.my_book.metadata_modified()
            self._active = True
            self._add_stopper()

    # common to scan_pages and read_pages, add a search-stopper
    # to the list of cursors - see page_at() below.
    def _add_stopper(self) :
        qtc = QTextCursor(self.document)
        qtc.setPosition( self.document.characterCount()-1 )
        self.cursor_list.append(qtc)

    # Read the metadata lines and store in our lists. This should be called
    # only once per book. The lists are not cleared at the start so if the
    # metadata file has multiple PAGETABLEs, they will accumulate. The data
    # format is the same between V1 and V2, 6 space-delimited items, e.g.
    #     35460 027 \\fmmarshall\\fsmwalb\Scribe 0 0 22
    #
    # Note that unlike worddata we make no allowances here for user
    # meddling/editing of page data, except for guarding it in a try block.
    #
    def read_pages(self, stream, sentinel, vers, parm):
        for line in metadata.read_to(stream, sentinel):
            try:
                # throws exception if not exactly 6 items
                (P, fn, pfrs, rule, fmt, nbr) = line.split(' ')
                tc = QTextCursor(self.document)
                # throws exception if P not an int
                tc.setPosition(int(P))
                # check that P was valid document position
                if int(P) != tc.position() : raise ValueError("Invalid document position")
                self.cursor_list.append(tc)
                self.filename_list.append(fn)
                self.folio_list.append( [int(rule), int(fmt), int(nbr)] )
                # get list of proofer strings, dropping opening null string
                # due to leading backslash.
                plist = pfrs.replace(C.UNICODE_EN_SPACE,' ').split('\\')[1:]
                self.proofers_list.append(plist)
            except Exception as who_cares:
                pagedata_logger.error('invalid line of page metadata:')
                pagedata_logger.error('  "'+line+'"')
        if 0 < len(self.filename_list) :
            self._active = True
            self._add_stopper()

    # Write our data as metadata lines. In the page separator lines
    # the proofers begin with backslash and are delimited with backslash.
    # For now-inscrutable reasons I kept that (instead of simple join)
    # format for the metadata file.

    def write_pages(self, stream, sentinel):
        if not self._active : return # don't write an empty section
        stream << metadata.open_line(sentinel)
        for R in range(len(self.filename_list)):
            P = self.cursor_list[R].position()
            fn = self.filename_list[R]
            plist = self.proofers_list[R]
            # proofer string with leading and delimiting backslash
            pfs = '\\'+ ('\\'.join(plist).replace(' ',C.UNICODE_EN_SPACE))
            [rule, fmt, nbr] = self.folio_list[R]
            stream << '{0} {1} {2} {3} {4} {5}\n'.format(
                     P,  fn, pfs, rule, fmt, nbr )
        stream << metadata.close_line(sentinel)

    # Return the row index R of the scan page matching a document offset.
    # Return None if the user is "off the top" in text preceding the first
    # page. imageview and editview call this every time the user moves the
    # cursor, so it needs to be quick. Use binary search to find the cursor
    # in the cursor_list with the highest position less than or equal to the
    # given offset.
    #
    # Speed the search with heuristics based on these assumptions:
    # * we get called from multiple widgets for any one cursor move
    # * the user typically moves the cursor forward, incrementing P
    # * forward or backward, the user typically stays on one page for a while.
    # So we keep track of the last-checked position P and also the
    # row index of the last-returned page R and its filename value F.
    # If P == last_position : return F
    # If P > cursor_list[R].position(),
    #     if P < cursor_list[R+1].position(): return F
    #     else setup binary search between R and max
    # else setup binary search between 0 and R

    def page_index(self,P):
        if self._active:
            if P < self.cursor_list[0].position() :
                # user is fiddling around in text preceding page 1
                self.last_row = 0 # must keep a valid row
                return None
            if P == self.last_pos : return self.last_row
            self.last_pos = P
            R = self.last_row
            if P >= self.cursor_list[R].position() :
                if P < self.cursor_list[R+1].position() :
                    return R # still in same page span
                hi = len(self.cursor_list) - 1 # moved on, search in ..
                lo = R # .. upper part of list
            else :
                hi = R # moved back, search in lower part of list
                lo = 0
            while lo < hi :
                mid = (lo + hi)//2
                if P < self.cursor_list[mid].position() :
                    hi = mid
                else :
                    lo = mid + 1
            self.last_row = lo-1
            return self.last_row
        # else not active
        return None # no data

    # Use filename_list as the official length; cursor_list has an extra row.
    def active(self) :
        return self._active
    def page_count(self) :
        return len(self.filename_list)

    # Return page values for display by pageview. Note that
    # returning a reference to a list (like the list of folio data)
    # means the caller can modify it in place. However to maintain
    # the integrity of the model/view structure, pagedata does not do
    # this, it calls set_folios with one or more modified values.
    #
    # At this time there is no need to modify proofer names.

    def filename(self, R):
        try :
            return self.filename_list[R]
        except IndexError as I:
            return ''

    def proofers(self, R):
        try :
            return self.proofers_list[R]
        except IndexError as I:
            return []

    def folios(self, R):
        try :
            return self.folio_list[R]
        except IndexError as I:
            return []

    def set_folios(self, R, rule = None, fmt = None, nbr = None ):
        try:
            if rule : self.folio_list[R][0] = rule
            if fmt : self.folio_list[R][1] = fmt
            if nbr : self.folio_list[R][2] = nbr
            self.my_book.metadata_modified()
        except IndexError as I :
            pass
