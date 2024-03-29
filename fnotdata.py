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
                          FNOTDATA.PY

Defines a class to store the footnote info of one Book. Acts as the Data Model
for fnotview.py which displays footnote data and offers user controls.

                    Important nomenclature:

A footnote KEY is a symbol that links an ANCHOR to a NOTE. Typically one
character (such as A or ¶) but can be multiple such as xviii or 97.

An ANCHOR consists of a KEY in square brackets[A] (with no spaces). It
* appears in a text but never at column 0
* never appears inside a word, so that [oe] is not an anchor

A NOTE consists of one or more adjacent complete lines that
* begins in column 0 with "[Footnote k:" where k is a KEY
* begins on a line that follows the line containing the matching ANCHOR
* ends with a line having a right square bracket as its final character
* may contain ANCHORs to (sub)footnotes
* may contain square brackets other than Anchors as long as the right
  bracket does not fall at the end of the line (which ends the NOTE).
* may contain poetry, lists, tables, block quotes, nonformatted text
  (/*, /X or /C sections) and transliterations such as [Greek:]
* may NOT contain [Illustration...] or [Sidenote...] markup (because
  these markups also end with a right square bracket at line-end).
* may NOT contain another NOTE, i.e. footnotes may not be nested

It is not required that KEYs be unique. (It is common for most KEYs in a PG
text to be proofed as A and a few as B.) However it is required that

(a) the ANCHOR with Key k precedes the NOTE with the matching Key k
(b) NOTES with the same KEY appear in the same sequence as their ANCHORs;
    that is, any Anchor [A] is matched to the first following [Footnote A:

Here is a valid example:

  Text[A] and more text[A]
  ...
  [Footnote A: this note contains[i] an anchor.]
  [Footnote A: this note matches the second anchor A and runs
  to multiple -- [text in brackets but not at end of line] --
  lines]
  [Footnote i: inner note anchored in first note A.]

                   Logical Database Structure

The database managed in this module has these logical columns:

Key:            The key text from a footnote, e.g. A or iv or 92.

Class:          The class of the key, one of:
                 0   IVX     uppercase roman numeral
                 1   ABC     uppercase alpha
                 2   ivx     lowercase roman numeral
                 3   abc     lowercase alpha
                 4   123     decimal
                 5   *\u00A4\u00A7 (star, currency, section) symbol class

Anchor Line:     The text block (line) number containing the anchor

Note Line:       The text block number of the matching Note

Length:          The count of lines of the matched Note

Text:            The opening few characters of the Note such as
                    "[Footnote A: This note has..."

The example above might produce the following logical table:

 Key   Class  Anchor Line Note Line   Length   Text
  A     ABC      1535       1570         1      Footnote A: this note has[i..
  A     ABC      1535       1571         3      Footnote A: this is the sec..
  i     ivx      1570       1574         1      Footnote i: inner note refe..

The table is actually implemented as a list of lists, each list having just
two members: [ ACursor, NCursor] where ACursor is a QTextCursor that selects
the the KEY in the ANCHOR, and NCursor selects all the lines of the NOTE.

The other values (key, class, Anchor Line#, Note Line#, Note Length, Note
Text) can be extracted from the two QTextCursors. Qt maintains the text
cursors while the user is editing the document, so the line numbers, length
and text remain accurate despite editing.

              Refresh Process

Initially the table is empty. The refresh() method is called from the
fnotview module at user request. Refresh scans the document line by line
looking for anchors and notes. We use the QTextDocument find() method and
QRegularExpression items for this search, because these result in QTextCursors.

The document is scanned twice, first to build a list of Anchors, then to
build a list of Notes. The two lists are merged and the table is built from
the matching (Anchor, Note) pairs. If any Anchors and Notes remain unmatched
they are stored as mismatched entries, in which either ACursor or NCursor is
None, showing either an anchor with no note, or vice versa.

              Metadata

Methods _fnote_save() and _fnote_load are registered to read/write footnote
metadata.

_fnote_save() writes the database as a list of lists,

  [ [ Aa, Az, Na, Nz ]... ]

where Aa is the position and Az the anchor of the ACursor, and Na is the
position and Nz the anchor of the NCursor. _fnote_load can reconstruct the
pairs of cursors from these numbers.

0,0 is saved where either cursor is stored as None. An Anchor cannot begin at
the start of a line, while a Note cannot appear in line 0 because it must
follow the line containing its Anchor; hence 0,0 is impossible for either
cursor.

A signal FnotesLoaded is emitted after loading.

              Constants

The module offers these public constants, referenced by fnotview:
KeyClass_IVX = 0
KeyClass_ABC = 1
KeyClass_ivx = 2
KeyClass_abc = 3
KeyClass_123 = 4
KeyClass_sym = 5

              Query Methods

The following methods are provided for the use of the footnote view display.

    refresh(prog_bar) sweep the document and find all Anchors and Notes.
                      prog_bar is a QProgressDialog to update.

    count()           returns the number of items in the database.

    mismatches()      returns the integer count of mismatched Anchors
                      and Notes. When nonzero, it is impossible to renumber
                      or to move notes.

    key(n)            returns the KEY string for row n.

    key_class(n)      returns the CLASS (enum) for row n.

    anchor_line(n)    returns the line number of the anchor for n,
                      or None if row n has no Anchor (unmatched Note)

    note_line(n)      returns the first line number of the note for n,
                      or None if row n has no Note (unmatched Anchor)

    note_size(n)      returns the number of lines in Note n or 0 if
                      row n has no Note (unmatched Anchor)

    note_text(n,t=0)  returns the initial t characters of the note N,
                      or the full text "[Footnote K: ....]" when t=0.
                      Returns an empty string if there is no Note n.

    set_key(n,key)    change key value of the Anchor/Note pair n to
                      key (used when renumbering notes).

    find_zones()      sweep the document and find all /F..F/ markers,
                      and return the number found.

    move_notes()      move all notes that are not already in a footnote
                      section, into the next higher footnote section
                      if any. Notes in a section, and notes where there
                      is no following section, are not moved.


The Query methods take advantage of the expected sequence of calls to
QTableModel.data(): that it will call for each column of a single row before
moving on to the next row. On the first call for a given "n" row number, the
cursors for that row are used to derive five logical column values (key,
class, aline, nline, nlen) anticipating they will be called for sequentially.

Note on QTextCursor use: A QTextCursor has two values, anchor and position,
to define the text it selects. Qt doesn't care which is lower (closer to the
top of the doc) but QTextDocument.find() returns anchor < position(), i.e.
the cursor is "positioned" at the end of the found text, with the anchor at
the start. So we try to keep that relation on all cursors.

'''
import regex
import constants as C
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtCore import QObject, QRegularExpression
from PyQt6.QtGui import QTextCursor
import logging
fnotdata_logger = logging.getLogger(name='fnotdata')

'''
 Module Constants, used by fnotview
 
 TODO should be an Enum?
'''
KeyClass_IVX = 0
KeyClass_ABC = 1
KeyClass_ivx = 2
KeyClass_abc = 3
KeyClass_123 = 4
KeyClass_sym = 5

'''

The FnoteData class definition. One instance of this is constructed per book.

'''
class FnoteData(QObject):
    '''
    Define a signal to emit upon complete load of a non-empty table, either
    during refresh or metadata input. Used by fnotview.
    '''
    FootNotesLoaded = pyqtSignal()

    def __init__(self, my_book) :
        super().__init__(None)
        '''
        Save reference to our parent Book, used to access the editor and
        metadata manager.
        '''
        self.book = my_book
        ''' Register our metadata reader/writer pair. '''
        self.book.get_meta_manager().register(
            C.MD_FN, self._fnot_reader, self._fnote_save)
        ''' Save a reference to our QTextDocument. '''
        self.doc = self.book.get_edit_model()
        '''
        Save a reference to our edit view, which coins cursor objects. No
        actually do that later because when we are initializing, the editview
        has not been created.
        '''
        self.eview = None
        ''' This is the actual database, a list of two-item lists. '''
        self.the_list = []
        ''' The count of currently unmatched items, Anchors plus Notes '''
        self.count_of_unpaired_keys = 0
        '''
        Items from the last row queried, cached because we expect fnotview to
        refer to all of these before moving to another row. See _load_row().
        '''
        self.last_row = None
        self.last_key = ''
        self.last_anchor = None
        self.last_note = None
        ''' list of footnote zone cursors, see find_zones(). '''
        self.zone_cursors = []
        '''
        Set up QRegularExpressions and regexes we use out of line. This creates members:
        note_finder_re
        anchor_finder_re
        class_re_list
        '''
        self._set_up_res()

    ''' Reset our database to empty. '''
    def _reset(self):
        self.the_list = []
        self.count_of_unpaired_keys = 0
        self.last_row = None

    '''
    
    Refresh process:
    
    * Set up a progress bar, which will only display if this takes a some
      time, which it usually does not.
    
    * Using QTextDocument.find, scan the document top to bottom to find all
      Anchors and make a list of them as QTextCursors.
    
    * Again scan, this time finding Notes, and making a list of QTextCursor
      items which each select a Note in full to its end.
    
    * Merge the lists by matching each Anchor to the nearest following
      matching Note. Add the matched cursor pairs to the_list.
    
    * Add any remaining unmatched Anchors and Notes to the_list as
      unmatched items, incrementing count_of_unpaired_keys.
    
    A QProgressDialog is passed, and we update it during the process.
    (creating such a dialog is the job of the View, not the Model!)
    '''
    def _refresh(self, progresso) :
        '''
        Initialize the progress dialog. As we scan the doc twice, its max
        value is twice the document length.
        '''
        progress_half = self.doc.characterCount()
        progresso.setMaximum(2 * progress_half)
        progresso.setValue(0)
        ''' Clear the database '''
        self._reset()
        ''' Pass one: look for Anchors '''
        anchors_list = []
        find_tc = self.doc.find( self.anchor_finder_qre, QTextCursor( self.doc ) )
        while not find_tc.isNull() :
            '''
            find_tc now selects the whole Anchor [Key] but we want to select
            only the Key. The means to do this are awkward.
            '''
            a = find_tc.anchor() + 1
            p = find_tc.position() - 1
            find_tc.setPosition( a, QTextCursor.MoveMode.MoveAnchor )
            find_tc.setPosition( p, QTextCursor.MoveMode.KeepAnchor )
            progresso.setValue( p )
            '''
            Special case: the PGDP conventional diphthong [oe] or [OE] looks
            like an alpha key, and we manually exclude it.
            '''
            if not self._is_oe( find_tc.selectedText() ) :
                anchors_list.append( QTextCursor(find_tc) )
            ''' restore loop invariant '''
            find_tc = self.doc.find( self.anchor_finder_qre, find_tc )
        ''' Pass two: look for Notes '''
        notes_list = []
        find_tc = self.doc.find( self.note_finder_qre, QTextCursor( self.doc ) )
        while not find_tc.isNull() :
            progresso.setValue( progress_half + find_tc.position() )
            '''
            find_tc now selects just "[Footnote Key:" but we want to extend
            it to all the lines of the note. Proceed by text blocks until we
            have one that ends like this.]
            '''
            while True:
                ''' "drag" to the end of the block selecting the whole line. '''
                find_tc.movePosition( QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor )
                if find_tc.selectedText().endswith(']') :
                    break # find_tc selects a whole Note
                ''' Make sure we have not reached the end of the document. '''
                if find_tc.atEnd() :
                    '''
                    Reached end of document looking for the closing line of
                    [Footnote... As there is no closing bracket, it is not a
                    legal Note. If there was a matching Anchor it will go
                    unmatched and the user will be informed that way.
                    '''
                    find_tc.clearSelection()
                    break
                else : # there is another line, move to its head and try again
                    find_tc.movePosition(QTextCursor.MoveOperation.NextBlock,QTextCursor.MoveMode.KeepAnchor)
            # end of while true looking for end of Note
            if find_tc.hasSelection() : # we did find a line or lines ending in ]
                notes_list.append( QTextCursor( find_tc ) )
            find_tc = self.doc.find( self.note_finder_qre, find_tc )
        # end while not find_tc.isNull

        '''
        Now, anchors_list is all the Anchors, and notes_list is all the
        Notes, each in sequence by document position. For each Anchor in
        sequence, find the first Note with a matching Key at a higher line
        number. If there is one, add the matched pair to the_list and delete
        the Note from its list. If there is no match, copy the Anchor to a
        list of unmatched Anchors (because we can't del() from anchors_list
        while we are looping over it).
        
        Despite appearances this is not an MxN process because we remove
        Notes from the list when they are matched, so most Anchors find a
        match on the 1st or 2nd test, or not at all.
        '''
        orphan_anchors_list = []
        for anchor_tc in anchors_list :
            hit = False
            anchor_line = self._cursor_start_line(anchor_tc)
            for note_tc in notes_list :
                hit = anchor_tc.selectedText() == self._key_from_note(note_tc) \
                    and anchor_line < self._cursor_start_line(note_tc)
                if hit : break
            if hit : # a match was made
                self.the_list.append( [anchor_tc, note_tc] )
                notes_list.remove(note_tc)
            else : # no match was found
                orphan_anchors_list.append(anchor_tc)
        '''
        All matches have been made. Unmatched Anchors are in orphan_anchors_list.
        Now add them to the_list as unmatched items, in their line number order
        (basically an insertion sort).
        '''
        for anchor_tc in orphan_anchors_list :
            this_anchor_line = self._cursor_start_line( anchor_tc )
            j = 0
            while j < len(self.the_list) : # old-fashioned loop
                that_anchor_line = self._cursor_start_line( self.the_list[j][0] )
                if this_anchor_line <= that_anchor_line :
                    break
                j += 1
            self.the_list.insert( j, [anchor_tc, None] )
        '''
        Any Notes that remain in notes_list are unmatched. Now insert them in
        the_list. Another insertion sort,but there are now also possibly
        unmatched Anchors in the_list.
        '''
        for note_tc in notes_list :
            this_note_line = self._cursor_end_line( note_tc )
            j = 0
            while j < len(self.the_list) :
                list_note_line = self._cursor_start_line( self.the_list[j][1] )
                if list_note_line : # is not None from an unmatched Anchor
                    if this_note_line <= list_note_line :
                        break
                j += 1
            self.the_list.insert( j, [None, note_tc] )
        '''
        Tidy up
        '''
        self.count_of_unpaired_keys = len(orphan_anchors_list) + len(notes_list)
        progresso.reset()
        if self.count() : # there were some footnotes
            self.FootNotesLoaded.emit() # tell the view panel.

    '''
    
    Metadata writing and reading.

    When writing metadata on document save, just throw the database out there.
    '''
    def _fnote_save(self, section):
        meta_list = []
        for [anchor_tc, note_tc] in self.the_list :
            if anchor_tc is not None:
                a_a = anchor_tc.anchor()
                a_p = anchor_tc.position()
            else :
                a_a, a_p = 0, 0
            if note_tc is not None:
                n_a = note_tc.anchor()
                n_p = note_tc.position()
            else :
                n_a, n_p = 0, 0
            meta_list.append( [ a_a, a_p, n_a, n_p ] )
        # end of for the_list
        return meta_list

    '''
    On document load, read back what _fnote_save wrote. However, allow for
    the user having messed around with the file. Also make sure that cursor
    anchors are less than cursor positions.
    '''
    def _fnot_reader(self, section, value, version ):
        self._reset()
        if not isinstance(value, list) :
            fnotdata_logger.error(
                'FOOTNOTES metadata is not a list of lists, ignoring' )
            return
        if self.eview is None :
            '''
            During __init__ we didn't have an edit view. Now during document
            load, we had better have one.
            '''
            self.eview = self.book.get_edit_view()
        for item in value :
            try :
                [a_a, a_p, n_a, n_p] = item # exception if not [a,b,c,d]
                a_a = int(a_a) # exceptions if not int values
                a_p = int(a_p)
                n_a = int(n_a)
                n_p = int(n_p)
                if (a_a == 0 and a_p == 0) or (a_a >= 0 and a_a < a_p) : pass
                else : raise ValueError
                if (n_a == 0 and n_p == 0) or (n_a >= 0 and n_a < n_p) : pass
                else : raise ValueError
                if (a_a + a_p) :
                    anchor_tc = self.eview.make_cursor(a_p, a_a)
                else : # anchor is 0,0
                    anchor_tc = None
                if (n_a + n_p) :
                    note_tc = self.eview.make_cursor(n_p, n_a)
                else : # note is 0,0
                    note_tc = None
                self.the_list.append( [ anchor_tc, note_tc ] )
            except:
                fnotdata_logger.error(
                    'FOOTNOTES metadata item is invalid, ignoring: {}'.format(item) )
        # end for item in value
        if self.count() : # there were some footnotes
            self.FootNotesLoaded.emit() # tell the view panel.

    '''
    Analysis methods to get values from text cursor selections. These are
    internal subroutines factored out of the public class methods above.
    '''

    ''' Case-insensitive test whether a Python string == OE/oe/Oe/oE '''
    def _is_oe(self, s):
        return s.lower() == 'oe'

    '''
    Given a QTextCursor, return the number of the document line for the
    end of its selection. Probably that's its position() value but don't
    assume that; use selectionEnd instead. Allow for missing cursors (None).
    '''
    def _cursor_end_line(self, tc):
        if tc is not None:
            return self.doc.findBlock( tc.selectionEnd() ).blockNumber()
        return None
    '''
    Given a QTextCursor, return the document line number for the start of
    its selection, which is probably its anchor() value but don't assume
    that. Allow for missing cursors (None).
    '''
    def _cursor_start_line(self, tc):
        if tc is not None:
            return self.doc.findBlock( tc.selectionStart() ).blockNumber()
        return None

    '''
    Given a QTextCursor presumably for a Note, return the count of lines
    that its selection spans. Allow for missing cursors (None).
    '''
    def _cursor_line_count(self, tc):
        if tc is not None :
            return 1 + self._cursor_end_line(tc) - self._cursor_start_line(tc)
        return 0

    '''
    Given a Key string, return its class number. Uses the class_re_list
    set up earlier.
    '''
    def _key_class_code(self, key):
        for (class_number, test_regex) in self.class_re_list :
            if test_regex.fullmatch(key) is not None :
                return class_number
        fnotdata_logger.error('Unclassifiable key '+key)
        return None

    '''
    Given a QTextCursor selecting a Note, isolate the Key and return it.
    Use the regex version of note_finder_re in which the Key is group(1).
    '''
    def _key_from_note(self, tc):
        if tc is not None :
            m = self.note_finder_re.match(tc.selectedText())
            if m is not None : # and it should never be
                return m.group(1)
        return ''

    '''
    Public methods to support wordview.py, as documented in the prolog.
    '''

    def refresh(self, progresso):
        self._refresh(progresso)
        return self.count()

    def count(self):
        return len(self.the_list)

    def mismatches(self):
        return self.count_of_unpaired_keys

    def _load_row(self, n):
        self.last_row = n
        [self.last_anchor, self.last_note] = self.the_list[n]
        if self.last_anchor is not None :
            self.last_key = self.last_anchor.selectedText()
        else :
            self.last_key = self._key_from_note(self.last_note)

    def key(self, n):
        if n != self.last_row: self._load_row(n)
        return self.last_key

    def key_class(self, n):
        if n != self.last_row: self._load_row(n)
        return self._key_class_code(self.last_key)

    def anchor_line(self, n):
        if n != self.last_row: self._load_row(n)
        return self._cursor_start_line(self.last_anchor)

    def note_line(self, n):
        if n != self.last_row: self._load_row(n)
        return self._cursor_start_line(self.last_note)

    def note_size(self, n):
        if n != self.last_row: self._load_row(n)
        return self._cursor_line_count(self.last_note)

    def note_text(self, n, t=0):
        if n != self.last_row: self._load_row(n)
        if self.last_note is not None:
            txt = self.last_note.selectedText()
            if (t) and t < len(txt) :
                txt = txt[:t] + '...'
            return txt
        return ''

    '''
    For renumbering notes, alter the Key text of a matched pair of Anchor and Note.
    
    We assume fnotview cannot call this for a mismatched pair, because it
    only permits renumbering when the mismatch count is 0. It passes a
    work_tc as a cursor that has an open EditBlock, so that renumbering will
    be undoable as a single step.
    
    We have to copy the anchor and note cursors into work_tc before changing
    the key text. Then in case the new text has a different length from the
    old, update the cursors in the database to match
    '''
    def set_key(self, j, new_key, work_tc):
        [anchor_tc, note_tc] = self.the_list[j]
        old_key = anchor_tc.selectedText()
        key_len_diff = len(new_key) - len(old_key)
        ''' Update the Anchor text '''
        anchor_start = anchor_tc.selectionStart()
        work_tc.setPosition( anchor_start, QTextCursor.MoveMode.MoveAnchor )
        work_tc.setPosition( anchor_tc.selectionEnd(), QTextCursor.MoveMode.KeepAnchor )
        work_tc.insertText( new_key ) # that replaces the Key in the Anchor
        ''' Reset the anchor_tc to select the replaced Key '''
        anchor_tc.setPosition( anchor_start, QTextCursor.MoveMode.MoveAnchor )
        anchor_tc.setPosition( anchor_start+len(new_key), QTextCursor.MoveMode.KeepAnchor )
        ''' Update the Note. First, extract its full text as a Python string.'''
        note_text = note_tc.selectedText()
        note_start = note_tc.selectionStart()
        '''
        Locate the key as group(1) of a match against the note text
            [Footnote xiv: ...]
            start(1)--^  ^--end(1)
        '''
        match = self.note_finder_re.match( note_text )
        ''' point work_tc at the Key within the note '''
        work_tc.setPosition( note_tc.selectionStart() + match.start(1), QTextCursor.MoveMode.MoveAnchor )
        work_tc.setPosition( note_tc.selectionStart() + match.end(1), QTextCursor.MoveMode.KeepAnchor )
        ''' replace the key in the note '''
        work_tc.insertText( new_key )
        ''' Reposition the note_tc to account for a change in the length of the key. '''
        note_tc.setPosition( note_start, QTextCursor.MoveMode.MoveAnchor )
        note_tc.setPosition( note_start + len(note_text) + key_len_diff, QTextCursor.MoveMode.KeepAnchor )

    '''
    Record the defined footnote zones as a list of lists, [tcA, tcZ] where
    the cursors have this relationship:
        tcA --> /F
              ...Unknown, often null, text in the zone before search
              ...Notes moved to this zone already...
        tcZ --> /nF/
    On the move, moved notes are inserted at tcZ pushing /n/F downward.
    '''
    def find_zones(self):
        doc_text = self.doc.full_text()
        self.zone_cursors = []
        match = self.zone_finder_re.search(doc_text) # start from 0
        while match : # is not None
            # print(match.start(1),match.start(2)) # dbg
            tcA = QTextCursor(self.doc)
            tcA.setPosition(match.start(1))
            tcZ = QTextCursor(self.doc)
            tcZ.setPosition(match.start(2))
            self.zone_cursors.append( [ tcA, tcZ ] )
            match = self.zone_finder_re.search(doc_text, match.end())
        # end while match
        return len(self.zone_cursors)

    '''
    Implement move-notes, moving each footnote to the nearest following
    footnote zone.
    
    The move logic has to allow for the chance that any Note might be
    inside a note section already. We do NOT allow for the pathological
    chance that a note might straddle a zone (chance there is a /F line
    INSIDE a Note text).
    
    We assume fnotview will call for a refresh before this operation, and
    will not call it when there are mismatches or if the list is empty.
    
    Also assume that fnotview will call for a refresh after this operation
    in order to correct the anchor cursors of embedded footnotes.
    
    The move logic needs to be a single undo operation. That means all text
    changes have to go through a single QTextCursor, work_tc, which is
    passed as a parameter.
    TODO: need progress bar???
    '''

    def move_notes(self, work_tc):
        for [anchor_tc, note_tc] in self.the_list :
            note_line = self._cursor_end_line(note_tc)
            ''' Find the first zone that starts below the note '''
            for [tcA, tcZ] in self.zone_cursors :
                if note_line < self._cursor_start_line(tcZ) :
                    ''' the note precedes the end of this section '''
                    break # stop, this is the section if any is
            # end for zone
            if note_line > self._cursor_start_line(tcZ) :
                '''
                The above loop must have ended naturally, not with a break,
                so this note, and any remaining notes, are past the end
                of the last zone in the list. We can do no more.
                '''
                break
            if note_line >= self._cursor_end_line(tcA) :
                ''' this note is already inside this zone '''
                continue # to the next note
            '''
            Note defined by note_tc is above the start of zone tcA/tcZ, so we
            will move it. Duplicate the note text with leading and trailing
            newlines to the end of the zone.
            '''
            note_text = note_tc.selectedText() # cache the note text
            work_tc.setPosition(tcZ.position()) # point to end of zone
            '''
            Inserting text into the document ahead of the position in tcZ
            causes Qt to update tcZ automatically.
            '''
            work_tc.insertText( '\n' + note_text + '\n' )
            '''
            Erase the original note text and the newlines before and after,
            using work_tc so it is part of the undo action.
            '''
            work_tc.setPosition(note_tc.anchor()-1)
            work_tc.setPosition(note_tc.position()+1, QTextCursor.MoveMode.KeepAnchor)
            work_tc.removeSelectedText()
            ''' Set note_tc to point to the new location of the note text. '''
            note_tc.setPosition(tcZ.position() - len(note_text) - 2)
            note_tc.setPosition(tcZ.position() - 1,QTextCursor.MoveMode.KeepAnchor)
        # end for notes in the_list
    # end move_notes

    '''
    As part of initialization, set up the regexes we use. Here and in the
    rest of the app we prefer the Python package regex, but in order to use
    QTextDocument.find() we also need some QRegularExpression. They are not reentrant so
    must be members of the object, not globals or class members.
    '''
    def _set_up_res(self):
        global KeyClass_IVX,KeyClass_ABC,KeyClass_ivx,KeyClass_abc,KeyClass_123,KeyClass_sym
        '''
        The following tuple is ordered to be indexed by the KeyClass_* globals.
        '''
        class_re_strings = (
            '[IVXLCDM]{1,19}', # ROMAN to MMMMDCCCCLXXXXVIII (4998)
            '[A-Z]{1,3}',      # ALPHA to AAA to ZZZ
            '[ivxlcdm]{1,19}', # roman to whatever
            '[a-z]{1,3}',      # alpha to aaa to zzz
            '\d{1,4}',         # decimal to 9999
            '[\*\u00a4\u00a7\u00b6\u2020\u2021]' # star currency section para dagger dbl-dagger
            )
        '''
        Set up a single QRegularExpression that recognizes anchors of all the above
        types, [A], [xviii], [*] etc
        '''
        anchor_finder_string = '\[(' + '|'.join(class_re_strings) + ')\]'
        self.anchor_finder_qre = QRegularExpression(anchor_finder_string)
        '''
        Set up the RE that recognizes the opening of a note "[Footnote K:",
        for K being any of the above key types. Make both QRegularExpression and regex
        versions.
        '''
        note_finder_string = '\[Footnote\s+(' + '|'.join(class_re_strings) + ')\s*\:'
        self.note_finder_qre = QRegularExpression( note_finder_string )
        self.note_finder_re = regex.compile( note_finder_string )
        '''
        
        Set up the RE that finds footnote zones /F..F/. This is applied to
        the complete document text in Python, so we can use regex.
        
        In a match object, Group 1 is (/F), so start(1) is the character
        index of the /F line. Group 2 is (\nF/) so start(2) is the index of
        the newline preceding the F/ line. Moved notes, with newlines front
        and back, will be inserted at start(2).
        
        The final group stops with either \n or $, in case the final F/ is
        end of document without \n.
        '''
        self.zone_finder_re = regex.compile( '\n(\\/F).*?(\nF\\/)(\n|$)', regex.DOTALL )
        '''
        Set up a list of tuples, (class#, re-for-class), ordered from most
        likely (cap alpha, numeric, lowercase alpha, symbol), but also ordered
        so that roman numerals are prioritized over alphabetics. These are
        Python regexes because they are applied to Python strings, not to the
        QTextDocument.
        '''
        self.class_re_list = [
            ( KeyClass_IVX, regex.compile(class_re_strings[KeyClass_IVX]) ),
            ( KeyClass_ABC, regex.compile(class_re_strings[KeyClass_ABC]) ),
            ( KeyClass_123, regex.compile(class_re_strings[KeyClass_123]) ),
            ( KeyClass_ivx, regex.compile(class_re_strings[KeyClass_ivx]) ),
            ( KeyClass_abc, regex.compile(class_re_strings[KeyClass_abc]) ),
            ( KeyClass_sym, regex.compile(class_re_strings[KeyClass_sym]) )
            ]
        # end of _set_up_res
