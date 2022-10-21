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
__copyright__ = "Copyright 2014, 2015 David Cortesi"
__maintainer__ = "David Cortesi"
__email__ = "tallforasmurf@yahoo.com"

'''
                          wordview.py

Define a class WordPanel(QWidget) to implement the Words panel.

The panel's central feature is WordTableView(QTableView) drawing its data
from a WordTableModel(QAbstractTableModel) which in turn gets its data from
worddata.py.

Above the table are four items, from left to right:
 * a Refresh button that invokes the worddata.refresh() method, and
   resets the table model, and clears the filter popup to "All".

 * a Respect Case checkbox, which affects the sorting of the table.

 * a popup menu (QComboBox) that presents an assortment of different
   filters. When one is chosen, the desired filter is set and the table
   model is reset, so the table redisplays with a filtered selection.

 * a QLabel whose content is the count of words presently displayed.

The table has three columns: Word, Count, and Features. Each cell in the
features column shows a sequence of six characters that indicate:

 * A if the word has any uppercase letters, else -
 * a if the word has any lowercase letters, else -
 * 9 if the word has any digits else, -
 * h if the word has any hyphen else, -
 * p if the word has any apostrophe, else -
 * X if the word fails spellcheck, else -

This string is prepared from the word's property set as stored in
worddata.py, and formatted by the prop_string() method of worddata.py.

When the user makes a selection in the popup menu, it sets up a filter_func
to test properties in the property set and then calls the model's
set_filter() method. This makes the table redisplay with a new selection
of words.

When the table view has the focus (and is currently sorted ascending on the
first column), keying a letter causes it to scroll to words starting with
that letter.

The table view also implements a context menu with these choices:

 * Similar words - words that match the selected word ignoring case,
                   hyphens and apostrophes (it's -> its Its It's)
 * First harmonic - words in a Levenshtein distance of 1 edit
 * Second harmonic - words in a Levenshtein distance of 2 edits

Each of these menu actions searches the words database and makes a set of
matching words. If there are any, it sets up a filter_func that tests a word
for membership in that set, and calls the model set_filter() method. To
return to the unfiltered list, select All in the popup.

To the right of the word table is the left member of a vertical splitter
which is normally all the way right to maximize the word table. When the
splitter is drawn left it exposes a one-column table, the good-words list.
The user can drag one or more words (multiple selections are allowed) from
the table and drop them on the good-words list. This adds the word(s) to the
list and clears the spelling-error flag for those words. The user can select
words in the good-words list and hit Delete to remove them from the list,
which causes those words in the main table to be re-spell-checked and
possibly flagged as spelling errors.

The widget implements its own Edit menu with only the following actions:
  Edit > Copy
     When the focus is in the good-words list, copies the current selection
     to the clipboard. When the focus is in the main widget, copies the
     current selection from the words table to the clipboard. In either
     case, as a space-separated list of words.

  Edit > Paste is available only when the focus is in the good-words list
     table, then it adds words from the clipboard to that list.

  Edit > Delete is available only when the focus is in the good-words list,
     then it deletes words from that table.

Double-clicking a word in the word table puts that word in the paste buffer
(same as Edit>Copy but only for the one double-clicked word, which may or may
not be selected) and also enters it in the Find text field of the Find panel,
with respect case copied from the checkbox above the table, and whole word.
If the word contains hyphens or apostrophes, the search is made a regex with
hyphen converted to [\-\s]* (find to-day, to day, to\nday or today) and
apostrophe converted to '?, find it's or its.
'''
import logging
wordview_logger = logging.getLogger(name='wordview')
import utilities # for make_progress
import constants as C
import worddata # our data model
import mainwindow # for set_up_edit_menu
import regex
import natsort
from PyQt6.QtCore import (
    pyqtSignal,
    Qt,
    QAbstractItemModel,
    QAbstractListModel,
    QAbstractTableModel,
    QCoreApplication,
    QMimeData,
    QModelIndex,
    QSortFilterProxyModel
    )
_TR = QCoreApplication.translate
from PyQt6.QtGui import (
    QDragEnterEvent
)
from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QWidget,
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QListView,
    QMenu,
    QPushButton,
    QSplitter,
    QTableView
    )

'''
           Filtration items stored as static globals.
           
The following groups of values obviously should be kept in parallel.

The actual menu strings of the popup filter menu.
'''
FILTER_MENU_TEXT = [
    _TR('Word filter menu choice','All'),
    _TR('Word filter menu choice','UPPERCASE'),
    _TR('Word filter menu choice','lowercase'),
    _TR('Word filter menu choice','MiXedCaSe'),
    _TR('Word filter menu choice','Numeric'),
    _TR('Word filter menu choice','Alphanumeric'),
    _TR('Word filter menu choice','Hyphenated'),
    _TR('Word filter menu choice','Apostrophe'),
    _TR('Word filter menu choice','Single-letter'),
    _TR('Word filter menu choice','Misspelled')
    ]
'''
The matching filter_func lambdas in the same sequence. Each filter_func
is called with two arguments, w the word token and p the property set.
'''
FILTER_MENU_FUNCS = [
    None,
    lambda w, p : worddata.UC in p and not (worddata.ND in p),
    lambda w, p : worddata.LC in p and not (worddata.ND in p),
    lambda w, p : worddata.MC in p,
    lambda w, p : (worddata.ND in p) and not (worddata.UC in p or worddata.LC in p or worddata.MC in p),
    lambda w, p : (worddata.ND in p) and (worddata.UC in p or worddata.LC in p or worddata.MC in p),
    lambda w, p : worddata.HY in p,
    lambda w, p : worddata.AP in p,
    lambda w, p : 1 == len(w),
    lambda w, p : worddata.XX in p
    ]

'''

Class of our table model.

It connects to the real database in worddata.py to return info from and about
the word table. It implements the standard table model overrides:

flags() : return Qt.itemIsEnabled for all; for column 0 also return
          itemIsSelectable and itemIsDragEnabled.

columnCount() : return the number of columns, 3

rowCount() : return number of words in the current selection as filtered.

headerData() : return the column header name or tooltip string.

data() : return the actual data, or various helpful info about a column.

mimeTypes() : return the mime type we support (text/plain)

mimeData()  : given a list of dragged words, return a QMimeData object.

set_filter() : Not a standard table method, apply or clear filtering
by calling sort with the current filter, sort column and sort order.

set_sort_key() : set the key_func used to sort.

sort() : implement column sorting and filtering including locale-aware
and case-blind sorting.

'''

COL_HEADERS = {
    0: _TR('Word table column head', 'Word' ),
    1: _TR('Word table column head', 'Count' ),
    2: _TR('Word table column head', 'Features')
}
COL_TOOLTIPS = {
    0: _TR('Word table column tooltip', 'Text of the word' ),
    1: _TR('Word table column tooltip', 'Number of times the word appears' ),
    2: _TR('Word table column tooltip', 'A:uppercase a:lowercase 9:digit h:hyphen p:apostrophe X:misspelt')
}
COL_ALIGNMENT = {
    0: Qt.AlignmentFlag.AlignLeft,
    1: Qt.AlignmentFlag.AlignRight,
    2: Qt.AlignmentFlag.AlignHCenter
}
class WordTableModel(QAbstractTableModel):
    def __init__(self, words, parent):
        super().__init__(parent)
        self.words = words # ref to worddata.WordData
        self.current_sort_vector = []
        self.current_sort_col = 0
        self.current_sort_order = Qt.SortOrder.AscendingOrder
        self.current_filter = None
        self.current_sort_key = None

    def flags(self,index):
        if 0 == index.column():
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsDragEnabled
        return Qt.ItemFlag.ItemIsEnabled

    def columnCount(self,index):
        global COL_HEADERS
        if index.isValid() : return 0 # we don't have a tree here
        return len(COL_HEADERS)

    def rowCount(self,index):
        if index.isValid() : return 0 # we don't have a tree here
        return self.words.word_count()

    def headerData(self, col, axis, role):
        global COL_HEADERS, COL_TOOLTIPS
        if (axis == Qt.Orientation.Horizontal) and (col >= 0):
            if role == Qt.ItemDataRole.DisplayRole : # wants actual text
                return COL_HEADERS[col]
            elif (role == Qt.ItemDataRole.ToolTipRole) or (role == Qt.ItemDataRole.StatusTipRole) :
                return COL_TOOLTIPS[col]
        return None # we don't do that

    def data(self, index, role ):
        global COL_ALIGNMENT, COL_TOOLTIPS
        if role == Qt.ItemDataRole.DisplayRole : # wants actual data
            col = index.column()
            row = self.current_sort_vector[ index.row() ]
            if 0 == col :
                ''' Column 0, return the word text '''
                return self.words.word_at( row )
            elif 1 == col :
                ''' Column 1, return the count '''
                return self.words.word_count_at( row )
            else:
                ''' Column 2, get the property set and translate it '''
                props = self.words.word_props_at( row )
                return worddata.prop_string(props)
        elif (role == Qt.ItemDataRole.TextAlignmentRole) :
            return COL_ALIGNMENT[index.column()]
        elif (role == Qt.ItemDataRole.ToolTipRole) or (role == Qt.ItemDataRole.StatusTipRole) :
            return COL_TOOLTIPS[index.column()]
        # don't support other roles
        return None

    '''
    
    Implement a filter method by storing a new filter_func and calling the
    sort() method. Called with either:
    
    * filter_func=None, filter_set=None to clear all filters
    * filter_func as lambda selected by the filter popup menu
    * filter_set as a set of words to be selected
    '''
    def set_filter( self, filter_func = None, filter_set = None ):
        new_filter = filter_func
        if new_filter is None : # caller did not pass a function,
            if filter_set is not None :
                # create a filter_func that tests word membership
                new_filter = lambda w, p : w in filter_set
        # whatever the result, perform a sort
        self.current_filter = new_filter # =None for no filter
        self.sort( self.current_sort_col, self.current_sort_order )

    ''' Note what key-translation to use when sorting, and re-sort. '''
    def set_sort_key(self, key_func ) :
        self.current_sort_key = key_func
        self.sort( self.current_sort_col, self.current_sort_order )

    '''
    
    Implement the sort() method of an Abstract Table Model. Most of the work
    is done by the worddata method get_sort_vector(). It returns an
    indirection vector that lets our data() show things in the requested
    order. Emit the layoutAboutToChange and layoutChanged signals so the view
    knows to refresh.
    '''
    def sort(self, col, order):
        self.current_sort_col = col
        self.current_sort_order = order
        self.layoutAboutToBeChanged.emit([],QAbstractItemModel.LayoutChangeHint.VerticalSortHint)
        self.current_sort_vector = self.words.get_sort_vector(
            col, order, key_func=self.current_sort_key,
            filter_func=self.current_filter )
        self.layoutChanged.emit([],QAbstractItemModel.LayoutChangeHint.VerticalSortHint)

    '''
    Methods related to initiating a drag -- see also the methods
    related to receiving a drop in GoodModel.
    '''
    #def mimeTypes(self):
        #return ['text/plain'] # never called!
    def supportedDragActions(self):
        return Qt.DropAction.CopyAction
    def mimeData(self,ixlist):
        words = []
        for index in ixlist :
            if index.isValid() :
                words.append( self.data(index,Qt.ItemDataRole.DisplayRole) )
        if len(words) :
            md = QMimeData()
            md.setText(' '.join(words))
            return md
        return None

'''
Class of our table View. We subclass QTableView to implement all the table
features, and to implement the context menu and to trap keystrokes and scroll
to that letter.

The constructor gets a reference to the respect-case switch widget so it can
check that when scrolling to a letter, and a reference to the worddata object
so it retrieve words and other info from its "data model".
'''
class WordTableView(QTableView):
    def __init__(self, parent, words, sw_case):
        super().__init__(parent)
        ''' Save access to word data model '''
        self.words = words
        ''' Save access to the respect case switch '''
        self.sw_case = sw_case
        ''' Set up to receive keystrokes '''
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        ''' Set up to allow multiple discontiguous selections '''
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        ''' Set up to allow dragging out '''
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        ''' Set up stuff used in our context menu: '''
        ''' A place for the index of the context-click, gives row for column 0 '''
        self.context_index = None
        ''' Build the context menu of three actions. Don't need to keep a ref
        to the actions because they are parented in the menu. '''
        self.contextMenu = QMenu(self)
        sim_action = self.contextMenu.addAction(
            _TR('Word table context menu choice',
                '&Words similar to this') )
        har1_action = self.contextMenu.addAction(
            _TR('Word table context menu choice',
                '&First harmonic') )
        har2_action = self.contextMenu.addAction(
            _TR('Word table context menu choice',
                '&Second harmonic') )
        ''' Connect the action signals to our slots that do them '''
        sim_action.triggered.connect( self.similar_words )
        har1_action.triggered.connect(self.first_harmonic)
        har2_action.triggered.connect(self.second_harmonic)
        ''' Create the list of actions for our minimal Edit menu. '''
        self.ed_action_list = [
            (C.ED_MENU_COPY,self.copy_action,QKeySequence.StandardKey.Copy),
            (None,None,None),
            (C.ED_MENU_FIND,self.find_action,QKeySequence.StandardKey.Find),
            (C.ED_MENU_NEXT,self.find_next_action,QKeySequence.StandardKey.FindNext)
        ]

    '''
          Methods to implement the Edit menu actions.
    
    Copy: collect the word values from each selected item in a list,
    join it with spaces, and put it on the clipboard.
    '''
    def copy_action(self):
        words = []
        for index in self.selectedIndexes() :
            words.append( index.data() )
        if len(words) : # got any?
            QApplication.clipboard().setText( ' '.join(words) )
    '''
    Find: present a find dialog. Take a single word from the returned string.
    Run through actual words looking for a match, using clean_word so that
    the comparison ignores all hyphens and apostrophes. On hit, select that
    word (row n, column 0) and make it visible; and save the row# and word
    text. On miss, beep and clear the last-row.
    '''
    def find_action(self):
        f_text = utilities.get_find_string(
            _TR( 'Word panel find dialog', 'Enter a word or the beginning of a word to find.'),
            self )
        if f_text : # is neither None nor an empty string
            ''' Take initial word token stripped of spaces '''
            word = f_text.strip().split()[0].strip()
            self.real_find( 0, worddata.clean_word( word ) )
    '''
    Find-next: If a previous find action found something, continue the search
    for that word going forward in the list. Otherwise, just do find_action.
    Note there is no danger of an index error using last_find_row+1 because
    range(N+1,N) is valid, a null list.
    '''
    def find_next_action(self):
        if self.last_find_row :
            self.real_find( self.last_find_row + 1, self.last_find_word )
        else :
            self.find_action()
    '''
    The meat of the find and find-next operations. the word has been cleaned
    of apostrophes and dashes. We have to use our model().data() method to
    cycle through words in sequence because it knows how to use the
    sort-vector.
    '''
    def real_find(self, row, word):
        for j in range( row, self.model().rowCount( QModelIndex() ) ) :
            ix = self.model().index( j, 0 )
            raw_target = self.model().data( ix, Qt.ItemDataRole.DisplayRole )
            clean_target = worddata.clean_word( raw_target )
            if clean_target.startswith( word ) :
                ''' successful find '''
                self.last_find_word = word # note found word...
                self.last_find_row = j # ...and row for find_next_action
                self.clearSelection() # Make the found row the table selection
                self.selectRow( j )
                self.scrollTo( ix, QAbstractItemView.ScrollHint.PositionAtCenter )
                return
        # no hit
        utilities.beep()
        self.last_find_row = None # prevent any find_next_action

    '''
    Intercept the focus-in and -out events and use them to display
    and hide our edit menu.
    '''
    def focusInEvent(self, event):
        mainwindow.set_up_edit_menu(self.ed_action_list)
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        mainwindow.hide_edit_menu()
        super().focusOutEvent(event)

    '''
    Reimplement the parent QTableView keyPressEvent to implement quick
    scrolling in what might be a very large table. With the focus in the
    table, when the user hits a key we want to jump the table to the
    first/next row with that character as initial.
    
    We only look at data character keytrokes with no modifiers or only Shift
    modifier. To explain the tests in the big if statement:
    
    In the Qt KEY_* enum, all function keys and composite keys have
    0x01000000 while ordinary characters lack it, so the first test
    eliminates all those.
    
    Then test if the table is sorted on column 0 (sorted on words, not on the
    count or features column). Finally test that the sort is ascending
    because we can't deal with a reverse sort.
    '''
    def keyPressEvent(self, event):
        key = int(event.key())
        mods = int(event.modifiers().value)
        #utilities.printKeyEvent(event) # dbg
        if ( key < 0x01000000) and \
           ( (mods == Qt.KeyboardModifier.NoModifier) or \
             (mods == Qt.KeyboardModifier.ShiftModifier) ) and \
           (  self.horizontalHeader().sortIndicatorSection() == 0 ) and \
           ( self.horizontalHeader().sortIndicatorOrder() == Qt.SortOrder.AscendingOrder ) :
            ''' We have an ordinary data key with or without shift, and the table
            is sorted on column 0 ascending... '''
            event.accept() # .,.this, we can handle.
            case = self.sw_case.isChecked()
            char = chr(key) # key is normally uppercase regardless shift
            if case and (mods == Qt.KeyboardModifier.NoModifier) :
                char = char.lower() # case matters, make actual lowercase
            ''' Do a binary search over the (sorted) data for initial char '''
            mp = self.model()
            rc = self.sw_case.isChecked()
            hi = mp.rowCount( QModelIndex() )
            lo = 0
            while (lo < hi) :
                mid = (lo + hi) // 2
                cc = mp.data(mp.index(mid,0), Qt.ItemDataRole.DisplayRole )[0]
                if not rc : cc = cc.upper()
                if char > cc :
                    lo = mid + 1
                else :
                    hi = mid
            self.scrollTo(mp.index(lo,0),QAbstractItemView.ScrollHint.PositionAtCenter)
        elif key == Qt.Key.Key_Home :
            self.scrollToTop()
        elif key == Qt.Key.Key_End :
            self.scrollToBottom()
        else : # pass it on to our parent class
            super().keyPressEvent(event)

    '''
    Handle a context menu event (a right-click (Mac: ctrl-click) or the
    Windows Menu button). Ignore it unless the event points to column 0.
    Then pop up our menu on that row. If the user makes a selection in
    the context menu, that creates one of the action signals, passing
    control to one of the following slots.
    '''
    def contextMenuEvent(self,event):
        if 0 == self.columnAt(event.x()) :
            ''' Get the index for the datum under the widget-relative position '''
            self.contextIndex = self.indexAt(event.pos())
            ''' Display the popup menu which needs the global click position '''
            self.contextMenu.exec(event.globalPos())

    ''' Slot for the "Similar words" context menu choice. '''
    def similar_words(self) :
        ''' Get clicked word in uppercase with hyphens and apostrophes stripped '''
        wd = worddata.clean_word(self.contextIndex.data(Qt.ItemDataRole.DisplayRole)).upper()
        hits = set()
        '''
        Scan the whole vocabulary (not just the current filter selection) for words
        that, when similarly cleaned and uppercased, match. There is sure to be at least
        one of them, the one clicked-upon.
        '''
        for j in range(self.words.vocab_count()) :
            wx = self.words.word_at(j)
            if wd == worddata.clean_word(wx).upper() :
                hits.add(wx)
        if len(hits) > 1 :
            ''' set the table to display all and only the similar words '''
            self.model().set_filter( filter_set = hits )
        else: # no matches
            utilities.beep()

    '''
    Slot for the "First Harmonic" context menu choice. We implement both
    first and second harmonic using the "fuzzy match" feature of the regex
    module, which supports exactly the Levenshtein distance matches.
    '''
    def first_harmonic(self):
        word = self.contextIndex.data(Qt.ItemDataRole.DisplayRole)
        rex = regex.compile('^(' + word + '){0<e<2}$',flags=regex.WORD)
        hits = set()
        for j in range(self.words.vocab_count()) :
            wx = self.words.word_at(j)
            if rex.match(wx) :
                hits.add(wx)
        if len(hits) :
            ''' Found at least 1 fuzzy match. Add the word itself to the
            set, and make that set the filter for the table. '''
            hits.add(word)
            self.model().set_filter( filter_set = hits )
        else: # no matches
            utilities.beep()

    ''' Slot for the "Second Harmonic" context menu choice. '''
    def second_harmonic(self):
        word = self.contextIndex.data(Qt.ItemDataRole.DisplayRole)
        rex = regex.compile('^(' + word + '){1<e<3}$',flags=regex.WORD)
        hits = set()
        for j in range(self.words.vocab_count()) :
            wx = self.words.word_at(j)
            if rex.match(wx) :
                hits.add(wx)
        if len(hits) : # did find at least one fuzzy match
            hits.add(word)
            self.model().set_filter( filter_set = hits )
        else: # no matches
            utilities.beep()
'''
Define the list model and list view for the good-words list. The model needs
to support both inserting and removing words (rows). Removing happens when
the view gets a delete key event. Inserting happens when a drop event
happens. Either way we do a model reset.
'''
class GoodModel(QAbstractListModel):
    def __init__(self, words, parent=None):
        super().__init__(parent)
        ''' Save access to the word database '''
        self.words = words
        ''' Save access to parent widget, to position warning message over '''
        self.save_parent = parent
        ''' Load up the list. '''
        self.get_data()

    def get_data(self):
        ''' Refresh our copy of the good words. '''
        self.good_set = self.words.get_good_set()
        self.good_list = sorted(self.good_set)

    def rowCount(self,index) :
        return len(self.good_list)

    def headerData(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole :
            return 'Good Words'
        elif (role == Qt.ItemDataRole.TextAlignmentRole) :
            return Qt.AlignmentFlag.AlignCenter
        return None

    def flags(self, index):
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled

    def data(self, index, role ):
        if role == Qt.ItemDataRole.DisplayRole : # wants actual data
            return self.good_list[index.row()]
        elif (role == Qt.ItemDataRole.TextAlignmentRole) :
            return Qt.AlignmentFlag.AlignLeft
        elif (role == Qt.ItemDataRole.ToolTipRole) or (role == Qt.ItemDataRole.StatusTipRole) :
            return _TR(
                'Good-word list tooltip', 'Words that are always correctly spelled')
        # don't support other roles
        return None

    '''
    Function to remove one or more words from the set, following a delete
    key. Input is a list of words comprising the current list selection.
    Inform the data model of the changes, then refresh our display.
    '''
    def remove_words(self,word_list):
        self.beginResetModel()
        for word in word_list:
            if word in self.good_set :
                self.words.del_from_good_set(word)
        self.get_data()
        self.endResetModel()

    '''    
    Function to add a list of words to the good words set. This is called
    from both dropMimeData below, and from the view when handling the
    Edit>Paste method. We check the count of words being added and if it is
    more than 20, we refuse, on the basis that adding that many words at one
    time is probably a mistake, the clipboard or the dragged text is not what
    the user thinks it is.
    
    Otherwise, give the words to the word data model, then refresh the display.
    '''
    def add_words(self, word_list):
        if len(word_list) <= 20 :
            self.beginResetModel()
            for word in word_list:
                self.words.add_to_good_set(word)
            self.get_data()
            self.endResetModel()
            return True
        utilities.warning_msg(
            _TR('Good-word list drop error',
                'You may not drop more than 20 words at one time on the Good Words list'),
            _TR('Good-word list drop error explanation',
                'There are %n words in the clipboard. This is probably a mistake.',n=len(word_list)),
            self.save_parent)
        return False

    '''
    This method is called at the completion of a drop operation. The second
    argument, qmd, is the mimeData whose text is presumably a text string of
    one or more words. Split it into a list and use add_words above.
    '''
    def dropMimeData(self, qmd, qda, row, column, parent):
        word_list = qmd.text().split()
        return self.add_words( word_list )

'''
The good-words view implements one behavior besides the default list view.
When it has the focus, hitting the delete key causes deletion of the selected
words from the list.
'''
class GoodView(QListView):
    def __init__(self, parent):
        super().__init__(parent)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setMovement(QListView.Movement.Free)
        # Create the list of actions for our minimal Edit menu.
        self.ed_action_list = [
            (C.ED_MENU_COPY,self.copy_action,QKeySequence.StandardKey.Copy),
            (C.ED_MENU_PASTE,self.paste_action, QKeySequence.StandardKey.Paste),
            (C.ED_MENU_DELETE,self.delete_action, QKeySequence.StandardKey.Delete)
        ]

    '''
    The dragEnterEvent and dragMoveEvent methods must be implemented here in
    the *view* and must set event.accept(). Only then will the dropMimeData
    method of the *model* be called. This saves having to write a dropEvent
    in the list view, but it sure is confusing.
    '''
    def dragEnterEvent(self, event):
        if (event.dropAction() == Qt.DropAction.CopyAction) and (event.mimeData().hasText() ) :
            event.accept()
        else :
            event.ignore()
    def dragMoveEvent(self, event):
        event.accept()

    '''
    Intercept the focus-in and -out events and use them to display
    and hide our edit menu.
    '''
    def focusInEvent(self, event):
        mainwindow.set_up_edit_menu(self.ed_action_list)
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        mainwindow.hide_edit_menu()
        super().focusOutEvent(event)

    '''
          Methods to implement the Edit menu actions.
    
    Copy in the good-words list is identical to copy in the Word table.
    Get the selection as a string and put it on the clipboard.
    '''
    def copy_action(self):
        word_list = []
        for index in self.selectedIndexes() :
            word_list.append( index.data() )
        if len(word_list) : # got any?
            QApplication.clipboard().setText( ' '.join(word_list) )
    '''
    Paste gets whatever words are on the clipboard as a list, and
    passes them to the model to add. If there are more than 20 it
    will give an error but we do not check its return.
    '''
    def paste_action(self):
        word_list = QApplication.clipboard().text().strip().split()
        self.model().add_words( word_list )
    '''
    Delete, and also the Delete or Backspace key, removes all
    words that are currently selected.
    '''
    def delete_action(self):
        word_list = []
        for index in self.selectedIndexes() :
            word_list.append( index.data() )
        if len(word_list) :
            self.model().remove_words(word_list)
    '''
    Event handler for keystrokes handles just one key, Delete (or backspace).
    '''
    def keyPressEvent(self, event):
        key = int(event.key())
        if ( key == Qt.Key.Key_Backspace ) or ( key == Qt.Key.Key_Delete ):
            event.accept()
            self.delete_action()
        else :
            event.ignore()

'''

Define the WordView object, the widget that represents the whole panel.

'''
class WordPanel(QWidget) :
    def __init__(self, my_book, parent=None):
        super().__init__(parent)
        ''' Save access to the book '''
        self.my_book = my_book
        ''' Through the book, access the word-data model '''
        self.words = my_book.get_word_model()
        '''
        Out of line, create all the layout stuff. This creates the members:
        * self.view, the WordTableView object (above)
        * self.model, the WordTableModel object (also above)
        * self.refresh, the Refresh button
        * self.sw_case, the Respect Case toggle
        * self.popup, the filter popup menu
        * self.row_count, the label showing the count of rows
        * self.progress, a QProgressDialog used during refresh (currently unused)
        * self.good_model, the good words data model
        * self.good_view, the good words list view
        '''
        self._uic()
        ''' Set up locale-aware sort key functions from natsort '''
        self.case_yes_func = natsort.natsort_keygen(
            alg = ( natsort.ns.LOCALE | natsort.ns.UNGROUPLETTERS | natsort.ns.UNSIGNED | natsort.ns.INT ) )
        self.case_no_func = natsort.natsort_keygen(
            alg = ( natsort.ns.IGNORECASE | natsort.ns.LOCALE | natsort.ns.UNSIGNED | natsort.ns.INT ) )
        '''
        Connect all the various signals to their slots:
        * Refresh button to do_refresh()
        '''
        self.refresh.clicked.connect(self.do_refresh)
        ''' * Popup selection to changes filtering of table '''
        self.popup.activated.connect(self.do_filter)
        ''' Change of Respect Case changes sorting of table '''
        self.sw_case.stateChanged.connect(self.do_set_case)
        self.sw_case.setChecked(True) # start out case-sensitive
        ''' Change of model to be reflected in row_count label '''
        self.model.layoutChanged.connect(self.do_row_count)
        ''' double-click of a table row to do_find() '''
        self.view.doubleClicked.connect(self.do_find)
        ''' Connect worddata changes due to metadata input '''
        self.words.WordsUpdated.connect(self.do_update)

    '''
    Receive the clicked() signal from the Refresh button.
    Clear any filtering being used in the model, but leave the
    current sort column and order alone.
    Note: refresh turns out to be quick enough that there is no
    need to show the progress dialog.
    '''
    def do_refresh(self):
        #self.progress.reset()
        #self.progress.setRange(0,0) # should show a busy indication
        #self.progress.show()
        self.words.refresh() # used to pass self.progress
        #self.setup_table
        # fake a selection of our popup menu, which sets (or clears)
        # the current filter, which performs sort, which updates layout
        self.do_filter( self.popup.currentIndex() )
        #self.progress.reset()
        #self.progress.hide()
        # and reset the good-words list too
        self.good_model.beginResetModel() # 5 usec
        self.good_model.get_data() # 10 usec
        self.good_model.endResetModel() # 35 usec

    '''
    Receive the WordsUpdated signal from the words model, indicating that
    the display of all words, or good words, may have changed owing to
    metadata input. Force a model reset of both models.
    '''
    def do_update(self):
        self.model.set_filter() # which performs sort, which updates layout
        self.good_model.beginResetModel()
        self.good_model.get_data()
        self.good_model.endResetModel()

    ## When the contents of the table have changed (refresh or a
    ## change of filter) set up table display parameters.
    #def setup_table(self):
        #self.row_count.setNum(self.model.rowCount())
        ##self.view.resizeRowsToContents()
        ##self.view.sortByColumn(0,Qt.SortOrder.AscendingOrder)
        #self.view.setColumnWidth(0,180)
        #self.view.setColumnWidth(1,50)

    '''
    Tap into the layoutChanged signal from the model as a cue
    to update the rowcount label.
    '''
    def do_row_count(self) :
        self.row_count.setNum( self.model.rowCount( QModelIndex() ) )

    '''
    Receive the activated signal from the filter combobox. The argument
    is the index of the selected item. Use that to select one of the
    FILTER_MENU_FUNCS and set that as the current filter_func on the
    table model. When the select is "All", the filter_func is None.
    '''
    def do_filter(self, fnumber) :
        self.model.set_filter( FILTER_MENU_FUNCS[ fnumber ] )

    '''
    Receive the stateChanged signal from the Respect Case switch
    and call the model's set_sort_key() with an appropriate key_func.
    '''
    def do_set_case(self, state ) :
        new_key_func = self.case_no_func
        if state : new_key_func = self.case_yes_func
        self.model.set_sort_key( new_key_func )

    '''
    Two compiled regexes as class variables. Each defines a search for the
    visually-ambiguous versions of a character. The regex is used to find
    every matching character and replace it with the search pattern, for use
    when a word is put in the find panel.
    
    HYPHEN-MINUS, SOFT HYPHEN, HYPHEN, NON-BREAKING HYPHEN
    '''
    RE_PAT_HYPHEN = '''[\-\u00ad\u2010\u2011]'''
    RE_HYPHEN = regex.compile(RE_PAT_HYPHEN)
    ''' APOSTROPHE, MODIFIER LETTER APOSTROPHE, LEFT and RIGHT SINGLE QUOTATION MARK '''
    RE_PAT_APOST = '''['\u02bc\u2018\u2019]'''
    RE_APOST = regex.compile(RE_PAT_APOST)

    '''
    Receive the doubleClicked(modelindex) signal from the table view. This
    is handled here in the parent (not in the tableview) mainly because
    here we have access to the respect-case switch.
    
    The operation is to initiate a document Find for the letter on the row
    that was double-clicked. Usually it is a straight Find for that word. But
    if the word contains a hyphen or apostrophe, make the Find string a regex
    that finds all variations of those characters in those positions.
    '''
    def do_find(self,index):
        if index.column() != 0 :
            ''' the double-click wasn't on column 0, so get an index to column 0 '''
            index = index.sibling(index.row(),0)
        word = index.data(Qt.ItemDataRole.DisplayRole)
        QApplication.clipboard().setText(word)
        sw_rc = self.sw_case.isChecked()
        sw_rx = False # assume not-regex, whole word
        '''
        If the word contains quotes and/or apostrophes, replace each with
        a regex character-class that will find any at that position.
        '''
        work = self.RE_HYPHEN.sub(self.RE_PAT_HYPHEN, word)
        work = self.RE_APOST.sub(self.RE_PAT_APOST, work)
        '''
        Invoke the Find panel with the respect-case switch, and when the
        word is normal, the whole-word and not-regex switches. If the word
        has apostrophes or hyphens, pass not-whole-word and regex True.
        '''
        self.my_book.get_find_panel().find_this(
            work, case=sw_rc, word=(not sw_rx), regex=( work != word )
            )

    def _uic(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        '''
        Lay out the top row of controls: Refresh button, Respect Case
        checkbox, filter popup, and row-count display label.
        '''
        top_layout = QHBoxLayout()
        main_layout.addLayout(top_layout,0) # top row, no stretch
        self.refresh = QPushButton(
            _TR('Word panel refresh button',
                'Refresh') )
        self.refresh.setToolTip(
            _TR('Word panel refresh tooltip',
                'Clear the table and count all the words in the book again.' ) )
        top_layout.addWidget(self.refresh,0) # refresh hard left
        self.sw_case = QCheckBox(
            _TR('Word panel case switch name',
                'Respect &Case' ) )
        self.sw_case.setToolTip(
            _TR('Word panel case switch tooltip',
                'Sort uppercase and lowercase letters apart (ON) or together (OFF)' ) )
        top_layout.addWidget(self.sw_case,0) # checkbox next left
        self.popup = QComboBox()
        self.popup.addItems(FILTER_MENU_TEXT)
        self.popup.setToolTip(
            _TR('Word panel filter popup tooltip',
                'Choose special groups of words to show' ) )
        top_layout.addStretch(1) # central space left of popup
        top_layout.addWidget(self.popup,0)
        top_layout.addStretch(1) # push label hard right
        self.row_count = QLabel('0')
        self.row_count.setToolTip(
            _TR('Words panel row-count tooltip',
                'Number of rows in the table at this time' ) )
        top_layout.addWidget(self.row_count)
        row_count_label = QLabel(
            _TR('Words panel legend on row-count',
                'rows' ) )
        row_count_label.setToolTip( self.row_count.toolTip() )
        row_count_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        top_layout.addWidget(row_count_label)
        '''
        That completes the top row. Lay out the bottom with the
        word table left and good-word list right in a splitter.
        '''
        mid_layout = QSplitter()
        main_layout.addWidget(mid_layout,1) # with all the stretch
        ''' Create the table view. '''
        self.view = WordTableView(self, self.words, self.sw_case)
        self.view.setCornerButtonEnabled(False)
        self.view.setWordWrap(False)
        self.view.setAlternatingRowColors(True)
        self.view.sortByColumn( 0, Qt.SortOrder.AscendingOrder )
        ''' Create the table model and connect it to the view. '''
        self.model = WordTableModel(self.words, self)
        self.view.setModel(self.model)
        self.view.setSortingEnabled(True)
        ''' Put completed table view in splitter with max stretch. '''
        mid_layout.addWidget(self.view)
        mid_layout.setStretchFactor(0,2)
        '''
        Set up the goodwords list model/view. It doesn't need sorting
        or alternating colors.
        '''
        self.good_model = GoodModel(self.words, self)
        self.good_view = GoodView(self)
        self.good_view.setModel(self.good_model)
        self.good_view.setWordWrap(False)
        '''
        Put the good-list in a group-box so as to group it with its label.
        The splitter doesn't accept layouts, only widgets, but the groupbox
        doesn't accept widgets, only layouts. Sigh.
        '''
        gw_box = QGroupBox(
                _TR('Word panel good word list heading',
                    'Good Words')
                )
        gw_box.setToolTip(
            _TR( 'Good-words column tooltip',
                 'The good_words list: words that are always correctly spelled' ) )
        gw_vbox = QVBoxLayout()
        gw_vbox.addWidget(self.good_view,1)
        gw_box.setLayout( gw_vbox )
        ''' Add the good-words box to the splitter. '''
        mid_layout.addWidget(gw_box)
        mid_layout.setStretchFactor(1,1)
        ''' Divide the space 3:1 '''
        mid_layout.setSizes( [ 300, 150 ] )

        ''' Make a progress dialog (currently unused) '''
        #self.progress = utilities.make_progress(
            #_TR('Word-refresh progress bar title',
                #'Rebuilding the vocabulary' ), self)
        #self.progress.setAutoClose(False) # close it manually
        #self.progress.setAutoReset(False)
        #self.progress.reset()
        #self.progress.hide()
