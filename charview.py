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
                          charview.py

Here we define classes to implement the Chars panel.

CharModel(QAbstractTableModel) interfaces to chardata.py to get the actual
data, and also supplies such user-visible items as column headers and
tooltips, which need to be translated and localized. It calls on the Python
standard module unicodedata for character class names and character names.

CharSortFilter(QSortFilterProxyModel) implements a sort/filter proxy
based on a test function set by the parent.

CharView(QWidget) implements a panel consisting of a top row containing
a Refresh button the left, and a filter combobox on the right.

Pressing Reset causes a call to chardata.py to reload the census of
characters, and a redisplay of the table afterward. The combo box offers the
user a choice of displaying all characters, or only non-ASCII characters, or
only non-Latin-1 characters.

Below and filling the rest of the widget is a 6-column table headed (in English)

 * Symbol, the character symbol
 * Value, the character value in hex
 * Count, the number of times it appears in the document
 * Entity, the HTML named or numeric entity value
 * Category, a unicode category in words.
 * Name, official unicode name for that character

'''
import constants as C
import unicodedata
from PyQt6.QtCore import (
    Qt,
    QAbstractTableModel,
    QCoreApplication,
    QSortFilterProxyModel
    )
_TR = QCoreApplication.translate
from PyQt5.QtWidgets import (
    QWidget,
    QComboBox,
    QVBoxLayout,
    QPushButton,
    QTableView
    )
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Dictionary to translate Unicode category abbreviations such as "Sc"
# returned by unicodedata.category() to phrases such as "Symbol, currency".
# The key is lowercased because we don't trust unicodedata to be 100%
# consistent with the unicode standard names.
#
# Not making any attempt to translate these, as unicode.org doesn't.

UC_CAT_EXPAND = {
    'cc' : 'Other, Control',
    'cf' : 'Other, Format',
    'cn' : 'Other, Not Assigned',
    'co' : 'Other, Private Use',
    'cs' : 'Other, Surrogate',
    'lc' : 'Letter, Cased',
    'll' : 'Letter, Lowercase',
    'lm' : 'Letter, Modifier',
    'lo' : 'Letter, Other',
    'lt' : 'Letter, Titlecase',
    'lu' : 'Letter, Uppercase',
    'mc' : 'Mark, Spacing Combining',
    'me' : 'Mark, Enclosing',
    'mn' : 'Mark, Nonspacing',
    'nd' : 'Number, Decimal Digit',
    'nl' : 'Number, Letter',
    'no' : 'Number, Other',
    'pc' : 'Punctuation, Connector',
    'pd' : 'Punctuation, Dash',
    'pe' : 'Punctuation, Close',
    'pf' : 'Punctuation, Final quote ',
    'pi' : 'Punctuation, Initial quote ',
    'po' : 'Puntuation, Other',
    'ps' : 'Punctuation, Open',
    'sc' : 'Symbol, Currency',
    'sk' : 'Symbol, Modifier',
    'sm' : 'Symbol, Math',
    'so' : 'Symbol, Other',
    'zl' : 'Separator, Line',
    'zp' : 'Separator, Paragraph',
    'zs' : 'Separator, Space'
}

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Dictionaries of translated column header strings, column tool-tip strings,
# and column text alignment. Key is the column number 0..5.

COL_HEADERS = {
    0 : _TR('character table column head',
            'Symbol'),
    1 : _TR('character table column head',
            'Value'),
    2 : _TR('character table column head',
            'Count'),
    3 : _TR('character table column head',
            'Entity'),
    4 : _TR('character table column head',
            'Unicode category'),
    5 : _TR('character table column head',
            'Unicode name')
}
COL_TOOLTIPS = {
    0: _TR('char. table column tooltip',
           'Character symbol'),
    1: _TR('char. table column tooltip',
           'Numeric value in hexadecimal'),
    2: _TR('char. table column tooltip',
           'Number in the document'),
    3: _TR('char. table column tooltip',
           'HTML/XML Entity code'),
    4: _TR('char. table column tooltip',
           'Unicode category'),
    5: _TR('char. table column tooltip',
           'Official Unicode character name')
}
COL_ALIGNMENT = {
    0: Qt.AlignHCenter,
    1: Qt.AlignRight,
    2: Qt.AlignRight,
    3: Qt.AlignLeft,
    4:Qt.AlignLeft,
    5:Qt.AlignLeft
}

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Define the table model, implementing those methods required to make an
# abstract table, concrete:
#
# flags : the base class returns Qt.itemIsSelectable|Qt.itemIsEnabled.
# columnCount : return the number of columns (6, but not hard-coded)
# rowCount : return number of chars in the database
# headerData : return the column header name or tooltip string.
# data : return the actual data, or various helpful info about a column.

class CharModel(QAbstractTableModel):
    def __init__(self, chardata, parent):
        super().__init__(parent)
        self.chardata = chardata # save access to CharData object

    def columnCount(self,index):
        global COL_HEADERS
        if index.isValid() : return 0 # we don't have a tree here
        return len(COL_HEADERS)

    def rowCount(self,index):
        if index.isValid() : return 0 # we don't have a tree here
        return self.chardata.char_count()

    def headerData(self, col, axis, role):
        global COL_HEADERS, COL_TOOLTIPS, COL_ALIGNMENT
        if (axis == Qt.Horizontal) and (col >= 0):
            if role == Qt.DisplayRole : # request for actual text
                return COL_HEADERS[col]
            if (role == Qt.ToolTipRole) or (role == Qt.StatusTipRole) :
                return COL_TOOLTIPS[col]
            if (role == Qt.TextAlignmentRole) :
                return COL_ALIGNMENT[col]
        return None # whatever you said, we don't have it

    def data(self, index, role ):
        global UC_CAT_EXPAND, COL_ALIGNMENT, COL_TOOLTIPS
        (char, count) = self.chardata.get_tuple(index.row())
        if role == Qt.DisplayRole : # request for actual data
            if 0 == index.column():
                return char
            elif 1 == index.column():
                return '0x{0:04x}'.format(ord(char))
            elif 2 == index.column():
                return count
            elif 3 == index.column():
                if char in C.NAMED_ENTITIES :
                    return '&' + C.NAMED_ENTITIES[char] + ';'
                else:
                    return '&#{0:d};'.format(ord(char))
            elif 4 == index.column():
                return UC_CAT_EXPAND[unicodedata.category(char).lower()]
            else: # assuming column is 5, unicode name
                return unicodedata.name(char,'no name?').title()
        elif (role == Qt.TextAlignmentRole) :
            return COL_ALIGNMENT[index.column()]
        elif (role == Qt.ToolTipRole) or (role == Qt.StatusTipRole) :
            if index.column() < 5 :
                return COL_TOOLTIPS[index.column()]
            # For column 5, the tooltip is the name string, because a narrow
            # column may not expose the entire name any other way.
            return unicodedata.name(char,'no name?').title()
        # Sorry, we don't support other roles
        return None

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Define the sort/filter proxy, used by the table view to sort and filter
# the rows to be displayed. We don't re-implement the sort() method, that
# just goes to the default which sorts columns on their character values
# as returned by the data() method above.
#
# We do implement filterAcceptsRow(). This tests the given row's character
# value in a Lambda expression selected by the user. The lambdas are defined
# in this class, and the current lambda is selected upon an activated(row)
# signal from the filter combobox.

class CharFilter(QSortFilterProxyModel):
    def __init__(self, chardata, parent):
        super().__init__(parent)
        self.chardata = chardata # save pointer to the chardata object
        self.lambda_all = lambda char : True
        self.lambda_not_ascii = lambda char : (ord(char) > 126) or (ord(char) < 32)
        self.lambda_not_latin = lambda char : (ord(char) > 255) or (not (ord(char) & 0x60))
        self.test = self.lambda_all

    # To implement filterAcceptsRow we take the row number and go to the
    # database to get that character. We pass the character into one of the
    # above lambda expressions and return that result, True for accept and
    # False for reject.

    def filterAcceptsRow(self, row, parent_index):
        return self.test(self.chardata.get_char(row))

    # The parent calls this slot to set the test lambda when the user chooses
    # one. It is up to the parent widget to cause a redisplay of the table.

    def set_filter(self, row):
        if row == 1 : self.test = self.lambda_not_ascii
        elif row == 2 : self.test = self.lambda_not_latin
        else : self.test = self.lambda_all

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Define the CharView object that is displayed in the Chars panel.
#
class CharView(QWidget):
    def __init__(self, my_book):
        super().__init__(None) # no parent, the tabset will parent us later
        # save access to the book and other important objects.
        self.my_book = my_book
        self.chardata = my_book.get_char_model()
        self.findpanel = my_book.get_find_panel()
        # Instantiate our layout and subwidgets. This creates:
        # self.view, QTableView
        # self.refresh, QPushButton
        # self.popup, QComboBox
        self._uic()
        # Set up the table model/view. Pass to the model a pointer
        # to the view so it can query the row under the mouse.
        self.model = CharModel(self.chardata,self)
        #Interpose a sort filter proxy between the view and the model.
        self.proxy = CharFilter(self.chardata,self)
        self.proxy.setSourceModel(self.model)
        self.view.setModel(self.proxy)
        # Hook up some signals.
        # Connect the double-click signal to find_this.
        self.view.doubleClicked.connect(self.find_this)
        # Connect the CharsLoaded from the chardata object to our slot.
        self.chardata.CharsLoaded.connect(self.chars_loaded)
        # Connect the popup activated signal to our slot.
        self.popup.activated.connect(self.new_filter)
        # Connect the refresh button clicked signal to refresh below
        self.refresh.clicked.connect(self.do_refresh)
        # Connect the modelReset signal to our slot.
        self.model.modelReset.connect(self.set_up_view)

    # Slot to receive doubleClicked(index) from the table view, and
    # convert that into a Find for that character.
    def find_this(self, index):
        repl = None
        if index.column() == 3 :
            # doubleclick was in the HTML entity column. Put the entity
            # string from column 3 in the replace-1 field
            repl = index.data(Qt.DisplayRole)
        if index.column() != 0 :
            # dblclick on some column other than 0. We need a reference to
            # column 0, and we get it from the index.
            index = index.sibling(index.row(),0)
        what = index.data(Qt.DisplayRole) # get the character as a string
        # Call for a find with respect case on, whole word and regex off
        self.findpanel.find_this(what,case=True,word=False,regex=False,repl=repl)

    # Slot to receive the CharsLoaded() signal from the chardata module
    # (metadata has been loaded). Reset the table model.
    def chars_loaded(self):
        self.model.beginResetModel()
        self.model.endResetModel()

    # Slot to receive the activated(row) signal from the filter popup. Set
    # the filter and reset the table model.
    def new_filter(self,row):
        self.model.beginResetModel()
        self.proxy.set_filter(row)
        self.model.endResetModel()

    # Slot to receive the clicked() signal from the Refresh button.
    # Warn the table model that things be changing, then call the
    # database to do a new census, then finish the table reset.
    def do_refresh(self):
        self.model.beginResetModel()
        self.chardata.refresh()
        self.model.endResetModel()

    # Slot to receive the modelReset() signal from the table model, emitted
    # after the endResetModel() call. Set some features of our table view
    # that we can't set until some data has been loaded.
    def set_up_view(self):
        self.view.resizeColumnsToContents()
        self.view.horizontalHeader().setStretchLastSection(True)
        self.view.resizeRowsToContents()
        self.view.setSortingEnabled(True)

    # Do all the fiddly UI stuff out of line.
    def _uic(self):
        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)
        topLayout = QHBoxLayout()
        topLayout.setContentsMargins(0,0,0,0)
        mainLayout.addLayout(topLayout,0)
        # Lay out the refresh button and filter popup
        self.refresh = QPushButton(
            _TR('Button to reload all data in char panel',
                'Refresh')
            )
        topLayout.addWidget(self.refresh,0)
        topLayout.addStretch(1) # push filters to the right
        self.popup = QComboBox()
        # Set choices in popup, must match to the lambdas
        # defined in CharFilter.set_filter()
        self.popup.addItem(
            _TR('char panel: show all characters',
                'All')
        )
        self.popup.addItem(
            _TR('char panel: show non-ascii characters',
                'not 7-bit')
        )
        self.popup.addItem(
            _TR('char panel: show non-latin-1',
                'not Latin-1')
        )
        topLayout.addWidget(self.popup,0)
        # Set up the table view, the actual visible table
        self.view = QTableView()
        self.view.setCornerButtonEnabled(False)
        self.view.setWordWrap(False)
        self.view.setAlternatingRowColors(True)
        mainLayout.addWidget(self.view,1) # give it all the stretch
        # end of _uic()
