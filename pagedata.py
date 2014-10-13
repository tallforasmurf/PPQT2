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
  * also is data model to the Images view panel (for page boundaries and filenames)
  * also is data model to the Edit view panel (for folio number display)

    Load Process

When the Book is created it creates a PageData object which registers a
reader and writer for the PAGETABLE metadata section.

If the main window tells the Book to load a known file (one with matching
.meta file), the metadata manager calls the registered read_pages method to
store the page info from the metadata file.

If the main window tells the Book to load a new file, one with no metadata,
the Book calls the scan_pages() method. It uses the editdata module
all_blocks iterator to scan the document and extract the key info from any
page separator lines. When the book is later saved, these data are saved
in the .meta file for next time, so page boundary lines are checked only the
first time a file is opened.

In either case QTextCursors are created to mark the start of each page.

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

  * Three ints related to the Folio value, defined in constants.py:
       - the folio rule, e.g. C.FolioRuleAdd1
       - the folio format, e.g. C.FolioFormatArabic
       - the folio number, e.g. 17

  * A string of proofer names separated by backslashes, e.g.
  \\Frau Sma\\fsmwalb\Scribe

  Spaces are permitted in proofer names ("Frau Sma"), but when writing the
  metadata file, spaces within this string are replaced with
  C.UNICODE_EN_SPACE so the string will remain a unit under split(). Some
  names may be null, as the 1st and 3rd in the example.

In effect this is a 6-column table indexed by row number. However
in memory, data is in lists indexed by row number:

  * cursor_list is a list of QTextCursor objects
  * filename_list is a list of filename strings
  * folio_list is a list of three-item lists [rule,format,number]
    -- not a list of tuples because the items are mutable
  * proofer_list is a list of lists containing proofer names, e.g.
    [ "", "Frau Sma", "", "fsmwalb", "Scribe" ] with u2002's converted.

    Public Methods

pagedata has three clients: imageview needs the scan image filename for the
current edit cursor location; editview needs the same to display in its
status line; and pageview displays all the data in the Pages panel.

    active()    returns True when pagedata is available, False else.

    page_count()returns the count of pages (for sizing the page table).

    page_index(P)  returns the row index R for the page that contains
                document position P, or None if P precedes the first page.

    name_index(fname) returns the row index R of the page with filename
                fname, if it exists.

    position(R) returns the document position for row R

    filename(R) returns the filename string for row R.

    folio_string(R) returns the formatted display of the folio for row R.

    proofers(R) returns the list of proofer name strings for row R.

    folio_info(R)   returns the folio item list for row R.

    set_folios(R, rule, fmt, number) update the folio values for row R.


    Page Boundary Cursor Maintenance

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

This can occur but is rarely an issue under normal post-processing. In
Version 1, the Reflow process often replaced spans of text that overlapped
page boundaries but it took pains to preserve the markers in the reflowed
text. However the user was encouraged to reflow and then Undo, and on Undo,
bug 32689 would bite. In version 2, we do not support inline Reflow (only a
translation to a new file with new page boundaries). So page boundary cursors
will be less often misplaced.

'''
import logging
pagedata_logger = logging.getLogger(name='pagedata')

import regex
import constants as C
import metadata
import editdata
from PyQt5.QtGui import QTextBlock, QTextCursor

'''
This regex recognizes page separator lines. In a typical book a page
separator line looks like:

 -----File: 001.png---\Johannes\marialice\Clog\Johannes\Adair\--------------

where each \something is the handle of a proofer who worked on that page.
It seemed that in some books, proofers are absent:

 -----File: 001.png---------------------------------------------------------

This defeats the regex used in V1, which expected at least one proofer name.
(However this turned out to be user error operating on an incomplete file.)
Regardless, the regex below handles either alternative and captures:

    group(1) : the image filename -- usually but not always numeric
    group(3) : string of proofer names divided by backslashes, or None.

The compiled regex can be a global because in use, it creates a match
object that is private to the caller.
'''

re_line_sep = regex.compile(
    '^-+File: ([^\\.]+)\\.png-(-*((\\\\[^\\\\]*)+)\\\\-*|-+)$'
    ,regex.IGNORECASE)

class PageData(object):
    def __init__(self, my_book):
        self.my_book = my_book
        # Save reference to the metamanager
        self.metamgr = my_book.get_meta_manager()
        # Get a reference to the edited document
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
        # Set of rows having an explicit folio format, as opposed to "same"
        self.explicit_formats = set()
        # Register to read and write metadata
        self.metamgr.register(C.MD_PT, self.read_pages, self.write_pages)

    #
    # Scan all lines of a new document and create page sep info. We fetch
    # QTextBlocks, not just content strings, because we need to get the
    # .position() of the matching lines.
    #
    # Set all folios to Arabic, Add 1, and the sequence number. This
    # operation creates new data, so we set metadata_modified.
    #
    def scan_pages(self):
        global re_line_sep
        # first page is Arabic starting at 1
        rule = C.FolioRuleSet
        fmt = C.FolioFormatArabic
        nbr = 1
        self.explicit_formats = {0}
        for qtb in self.document.all_blocks() :
            m = re_line_sep.match(qtb.text())
            if m :
                # capture the image filename
                fname = m.group(1)
                if m.group(3) is not None :
                    # record proofers as a list, omitting the
                    # null element caused by the leading '\'
                    plist = m.group(3).split('\\')[1:]
                else :
                    # sep. line with no proofers, minimal list
                    plist = ['']
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
            self.my_book.metadata_modified(True, C.MD_MOD_FLAG)
            self._active = True
            self._add_stopper()

    # common to scan_pages and read_pages, add a search-stopper
    # to the list of cursors - see page_at() below for use.
    def _add_stopper(self) :
        qtc = QTextCursor(self.document)
        qtc.setPosition( self.document.characterCount()-1 )
        self.cursor_list.append(qtc)

    # Read the metadata lines and store in our lists. This should be called
    # only once per book. The lists are not cleared at the start so if the
    # metadata file has multiple PAGETABLE sections, they will accumulate.
    # The data format is the same in V1 and V2, 6 space-delimited items, e.g.
    #
    #     35460 027 \\fmmarshall\\fsmwalb\Scribe 0 0 22
    #
    # or, when there were no proofer names in the separator lines,
    #
    #     34560 027 \\ 0 0 22
    #
    # Note that unlike worddata we make no allowances here for user
    # meddling/editing of page data, except for guarding it in a try block.
    #
    def read_pages(self, stream, sentinel, vers, parm):
        valid_rule = {C.FolioRuleAdd1,C.FolioRuleSet,C.FolioRuleSkip}
        valid_fmt = {C.FolioFormatArabic,C.FolioFormatLCRom,C.FolioFormatUCRom,C.FolioFormatSame}
        last_fmt = C.FolioFormatArabic
        last_pos = -1 # ensure monotonically increasing positions
        for line in metadata.read_to(stream, sentinel):
            try:
                # throws exception if not exactly 6 items
                (P, fn, pfrs, rule, fmt, nbr) = line.split(' ')
                P = int(P) # throws exception if not valid int string
                tc = QTextCursor(self.document)
                tc.setPosition(P) # no effect if P negative or too big
                if (tc.position() != P) or (P < last_pos) :
                    raise ValueError("Invalid document position")
                last_pos = P
                rule = int(rule)
                fmt = int(fmt)
                nbr = int(nbr)
                if not ( (rule in valid_rule) and (fmt in valid_fmt) and (nbr >= 0) ) :
                    raise ValueError("Invalid folio info")
                # All looks good, do permanent things
                self.cursor_list.append(tc)
                self.filename_list.append(fn)
                self.folio_list.append( [rule, fmt, nbr] )
                if fmt != C.FolioFormatSame :
                    self.explicit_formats.add(len(self.folio_list)-1)
                # get list of proofer strings, dropping opening null string
                # due to leading backslash. If it is only '\\' the result
                # is the list [''].
                plist = pfrs.replace(C.UNICODE_EN_SPACE,' ').split('\\')[1:]
                self.proofers_list.append(plist)
            except Exception as thing:
                pagedata_logger.error('invalid line of page metadata: '+thing.args[0])
                pagedata_logger.error('  ignoring "'+line+'"')
        if 0 < len(self.filename_list) :
            self._active = True
            self._add_stopper()

    # Write our data as metadata lines. In the page separator lines
    # the proofers begin with backslash and are delimited with backslash.
    # For now-inscrutable reasons I kept that format (instead of simple join)
    # in the V1 the metadata file.

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

    def active(self) :
        return self._active
    # Use filename_list as the official length; cursor_list has an extra row.
    def page_count(self) :
        return len(self.filename_list)

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

    # Return the index of a user-entered filename (in editview). This is
    # called only from the edit view when the user keys an image name and
    # hits return. There is NO constraint on image filenames. Although they
    # are conventionally just numbers, 0005.png, 099.png, etc., there is no
    # requirement that they be numeric or ascending: frontispiece.png,
    # indexA.png, all ok. Here we are just doing a linear search of the list.
    #
    # If linear search should become a performance problem, then during
    # reading or scanning of the page metadata we could store an inverse dict
    # of {name:row#} so we could do a quick hash lookup of any fname.

    def name_index(self, fname):
        if self.active() :
            for j in range(len(self.filename_list)):
                if fname == self.filename_list[j] :
                    return j
        return None # no data, or fname not found

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
        except:
            pagedata_logger.info('Invalid index {0} to filename'.format(R))
            return None

    # Return the display form of the folio number based on its value and
    # explicit format. Note we are computing folio strings from numeric
    # on demand. If this is a performance problem, they could be precomputed
    # and kept in the database -- with some extra trouble.

    def folio_string(self, R):
        global toRoman
        try :
            [rule, fmt, number] = self.folio_list[R]
            if rule == C.FolioRuleSkip :
                return ''
            if fmt == C.FolioFormatSame :
                fmt = self.folio_format(R) # calculate actual, see below
            if fmt == C.FolioFormatArabic :
                return str(number)
            return toRoman(number, fmt == C.FolioFormatLCRom)
        except IndexError:
            pagedata_logger.error('Invalid index {0} to folio_string'.format(R))
            return ''

    def position(self, R):
        try :
            return self.cursor_list[R].position()
        except IndexError:
            pagedata_logger.error('Invalid index {0} to position'.format(R))
            return 0

    def set_position(self, R, pos):
        try :
            self.cursor_list[R].setPosition(pos)
        except :
            pagedata_logger.error('Problem setting position of page {) to {}'.format(R,pos))

    def proofers(self, R):
        try :
            return self.proofers_list[R]
        except IndexError:
            pagedata_logger.error('Invalid index {0} to proofers'.format(R))
            return []

    # Return the raw folio items Rule, Format, and Number. Format is very
    # probably folioFormatSame.

    def folio_info(self, R):
        try :
            return self.folio_list[R]
        except IndexError:
            pagedata_logger.error('Invalid index {0} to folio_info'.format(R))
            return []

    # Return the actual folio format, resolving the "same" to the next
    # higher explicit format.

    def folio_format(self, R):
        try :
            fmt = self.folio_list[R][1]
            if fmt == C.FolioFormatSame :
                nearest_explicit = 0
                for an_index in self.explicit_formats:
                    if (an_index >= nearest_explicit) and (an_index < R) :
                        nearest_explicit = an_index
                fmt = self.folio_list[nearest_explicit][1]
            return fmt
        except IndexError:
            pagedata_logger.error('Invalid index {0} to folio_format'.format(R))
            return C.FolioFormatArabic

    def set_folios(self, R, rule = None, fmt = None, number = None ):
        try:
            if rule is not None :
                self.folio_list[R][0] = rule
            if fmt is not None :
                self.folio_list[R][1] = fmt
                if fmt == C.FolioFormatSame :
                    self.explicit_formats.discard(R)
                else :
                    self.explicit_formats.add(R)
            if number is not None : self.folio_list[R][2] = number
            self.my_book.metadata_modified(True, C.MD_MOD_FLAG)
        except IndexError:
            pagedata_logger.error('Invalid index {0} to set_folios'.format(R))
            pass

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Decimal-to-Roman numeral converter, adapted from Mark Pilgrim's
# "Dive Into Python".
_ROMAN_MAP = (('M',  1000),
              ('CM', 900),
              ('D',  500),
              ('CD', 400),
              ('C',  100),
              ('XC', 90),
              ('L',  50),
              ('XL', 40),
              ('X',  10),
              ('IX', 9),
              ('V',  5),
              ('IV', 4),
              ('I',  1))
def toRoman( n, lc=True ):
    if (0 < n < 5000) and int(n) == n :
        result = ""
        for numeral, integer in _ROMAN_MAP:
            while n >= integer:
                result += numeral
                n -= integer
    else : # invalid number, log but don't raise an exception
        pagedata_logger.error('Invalid number for roman numeral {0}'.format(n))
        result = "????"
    if lc : result = result.lower()
    return result
