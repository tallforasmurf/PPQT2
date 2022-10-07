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
                          pageview.py

Define a class PagePanel(QWidget) to implement the Pages panel.

The top row of the widget has three items:

  * A button Refresh that triggers recalculation of folio values
    down the table based on the current skip, start-at and add-1 values.
    Refresh is also used to load the table the first time, as this
    panel is created by the Book before the Book loads a document, thus
    we initially have no data to show at the time of creation.

  * A text field allows entry of a string to be inserted at every
    page boundary. In the string, %f is replaced with the folio value
    and %i with the scan image filename.

  * A button Insert cautions the user, then inserts the string at
    at every page boundary position.

Below the top row is a table with these columns:

0: Image scan filename, typically like 0002 but can be like index05
1: Folio format, shown as: Same, Arabic, ROMAN, roman
2: Folio action, shown as: Add 1, Skip, Set to:
3: Folio display value, for example 15 or xxvi
4: Proofer names as a comma-delimited list

Unlike tables in other panels this one cannot be sorted, it is built
in sequence and stays that way.

Class PageModel(QAbstractTableModel) has the usual table model method
overrides to supply data for display (drawn from the PageData object passed
to its __init__) and to supply column headers, row counts and so on.

Class PageTable(QTableView) implements the visible table and allows
editing via three custom item delegates, one for each of the folio
columns. The page table also handles a doubleclick in column 0, causing
the editor to jump to the top of the text for that scan image.

Class PagePanel(QWidget) defines the entire panel and initializes it.
'''
import constants as C
import logging
import fonts
import utilities
pageview_logger = logging.getLogger(name='pageview')

from PyQt6.QtCore import (
    Qt,
    QAbstractTableModel,
    QCoreApplication
    )
_TR = QCoreApplication.translate

from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout, QVBoxLayout,
    QHeaderView,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QStyledItemDelegate,
    QTableView,
    QWidget
    )

'''
Define constant values used by the Table Model
'''
COL_HEADERS = {
    0 : _TR('page data table column head',
            'Image', 'name of scan image file'),
    1 : _TR('page data table column head',
            'Format'),
    2 : _TR('page data table column head',
            'Action'),
    3 : _TR('page data table column head',
            'Folio'),
    4 : _TR('page data table column head',
            'Proofer Names')
}
COL_TOOLTIPS = {
    0 : _TR('page data table column tooltip',
           'Name of the scan image file for this page'),
    1 : _TR('page data table column tooltip',
           'Format of the folio on this page: arabic, roman, or same-as-above'),
    2 : _TR('page data table column tooltip',
           'Action to set the folio value for this page: set to N, add 1 to above, or skip'),
    3 : _TR('page data table column tooltip',
           'The folio (visible page number) for this page'),
    4 : _TR('page data table column tooltip',
           'Names of the PGDP users who worked on this page')
}
COL_ALIGNMENT = {
    0: Qt.AlignmentFlag.AlignRight,
    1: Qt.AlignmentFlag.AlignRight,
    2: Qt.AlignmentFlag.AlignLeft,
    3: Qt.AlignmentFlag.AlignRight,
    4: Qt.AlignmentFlag.AlignLeft
}
'''
Displayed names for the format codes, in sequence by C.FolioFormat*
Not translating these, intentionally.
'''
FORMAT_NAMES = [ 'Arabic', 'ROMAN', 'roman', '(same)' ]
# Names for the format actions, in sequence by 
'''
Displayed names for the folio format actions, see C.FolioRule*
Also not translated.
'''
ACTION_NAMES = [ 'Add 1', 'Set to:', 'Omit' ]

'''
Define the table model with all the usual table model support methods, drawing
data from the pagedata module. A reference to pagedata is obtained by the
PagePanel widged and passed in to init here.
'''
class PageTableModel(QAbstractTableModel):
    def __init__(self, pdata, parent=None):
        super().__init__(parent)
        self.pdata = pdata # Save reference to the pagedata database

    def columnCount(self,index):
        global COL_ALIGNMENT # just for its length
        if index.isValid() : return 0 # we don't have a tree here
        return len(COL_ALIGNMENT)

    def flags(self,index):
        if self.pdata.active() :
            ''' All table items are enabled '''
            f = Qt.ItemFlag.ItemIsEnabled
            '''
            Figure out if the queried column should be flagged editable. If
            asking about columns 1 & 2 (folio format and action), they are
            editable. Column 3 (folio display value) is only editable when
            the folio action for that row is "Set to:" -- which can only be
            the case when there is page data.
            ''' 
            c = index.column()
            if (c == 1) or (c == 2) :
                f |= Qt.ItemFlag.ItemIsEditable # cols 1-2 always editable
            elif (c == 3) and \
                 (self.pdata.folio_info(index.row())[0] == C.FolioRuleSet) :
                f |= Qt.ItemIsEditable
        else : f = Qt.ItemFlag.NoItemFlags
        return f

    def rowCount(self,index):
        if index.isValid() : return 0 # we don't have a tree here
        if self.pdata.active() :
            return self.pdata.page_count()
        return 1 # no data - have one, empty row

    def headerData(self, col, axis, role):
        global COL_ALIGNMENT, COL_HEADERS, COL_TOOLTIPS
        if (axis == Qt.Orientation.Horizontal) and (col >= 0):
            if role == Qt.ItemDataRole.DisplayRole : # wants actual text
                return COL_HEADERS[col]
            if (role == Qt.ItemDataRole.ToolTipRole) \
               or (role == Qt.ItemDataRole.StatusTipRole) :
                return COL_TOOLTIPS[col]
            if (role == Qt.ItemDataRole.TextAlignmentRole) :
                return COL_ALIGNMENT[col]
        return None # we don't do that whatever it was

    def data(self, index, role ):
        global COL_ALIGNMENT
        c = index.column()
        if (role == Qt.ItemDataRole.TextAlignmentRole) :
            return COL_ALIGNMENT[c]
        if (role == Qt.ItemDataRole.ToolTipRole) \
           or (role == Qt.ItemDataRole.StatusTipRole) :
            return COL_TOOLTIPS[c]
        r = index.row()
        if role == Qt.ItemDataRole.DisplayRole : # wants actual data
            if self.pdata.active() :
                '''
                The normal case: there exists good page data
                and we return the appropriate stuff for that column.
                '''
                [rule,fmt,val] = self.pdata.folio_info(r)
                if c == 0:
                    return self.pdata.filename(r)
                if c == 1:
                    return FORMAT_NAMES[fmt] # name for format code
                if c == 2:
                    return ACTION_NAMES[rule] # name for action code
                if c == 3: # return folio formatted per rule
                    return self.pdata.folio_string(r)
                if c == 4:
                    return ' '.join(self.pdata.proofers(r))
                return None # should never be reached
            else :
                '''
                The page model has not yet loaded metadata so there
                is nothing to display. Regardless we want to have one
                empty row of data so that column widths can be set.
                '''
                return '   '
        if (role == Qt.ItemDataRole.UserRole) :
            '''
            request is from a custom item delegate for the numeric value of a
            column, not the formatted string. This can only happen when a
            column is editable, which is only when there exists real data.
            '''
            [rule,fmt,val] = self.pdata.folio_info(r)
            if c == 1 : # format delegate
                return fmt
            if c == 2 : # action delegate
                return rule
            if c == 3 : # value delegate
                return val
            return None # should never occur
        # don't support other roles
        return None

    '''
    Slot that receives the signal when the Refresh button is clicked.
    Run through the page table and reset folio values based on the folio
    rules. This changes the numeric codes and values in the database.
    
    The call to begin/endResetModel causes the Qt code to re-fetch displayed
    items via data() above.
    '''
    def update_folios(self):
        self.beginResetModel()
        folio = 0
        for r in range(self.pdata.page_count()) :
            [rule,fmt,val] = self.pdata.folio_info(r)
            if rule == C.FolioRuleAdd1 :
                folio += 1
                self.pdata.set_folios(r, number=folio)
            elif rule == C.FolioRuleSet :
                folio = val
                self.pdata.set_folios(r, number=folio)
            else : # FolioRuleSkip
                assert rule == C.FolioRuleSkip
                # nothing to do
        self.endResetModel()

'''

Define a "custom delegate" for each of the three folio columns.

A custom delegate is an object that is created by the table to manage the
editing of a particular type of table cell. The delegate must implement 3
methods:

 - createEditor() returns a widget that the table view will position
   over the table cell to act as an editor. This widget, e.g. a
   combobox, provides the UI for editing this type of data.

 - setEditorData() initializes the editor widget with data to display
   (presumably, the current contents of the cell being edited).

 - setModelData() is called when editing is complete (indicated by
   a return key, and not cancelled as by Escape), to store
   possibly-changed data back to the model.

The init parameters are:

    parent, the individual table item over which the editor widget appears
    style, a QStyleOptionViewItem that we don't touch
    index, the model index of the edited item.

Custom delegate for column 1, the format code. Our editor is a combobox with
four types of folio format (three when called for row 0, where "Same" is not
permitted).
'''
class FormatDelegate(QStyledItemDelegate):
    ''' Create a combobox loaded with the names of the four formats '''
    def createEditor(self, parent, style, index):
        if index.column() != 1 : return None # should never happen
        cb = QComboBox(parent)
        ''' give it strong focus policy so it will get mouse events '''
        cb.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        ''' Add choices but do not provide "(same)" on row 0 '''
        cb.addItems(FORMAT_NAMES[:4 if index.row() else 3])
        return cb
    ''' Set the combobox to initially choose the current rule '''
    def setEditorData(self,cb,index):
        ''' get the value from this row of the table via data() '''
        fmt = index.data(Qt.ItemDataRole.UserRole)
        ''' make that row of the combobox active '''
        cb.setCurrentIndex(fmt)
    '''
    Return key on combobox; data may (or may not) be changed. We are
    helpfully given access to our data model. Reach in and use its pdata
    reference to pagedata to set the fmt value.
    '''
    def setModelData(self,cb,model,index):
        model.pdata.set_folios(index.row(), fmt = cb.currentIndex())

'''
Custom delegate for column 2, folio action rule. The editor is a combobox
with the three choices in it. Operation just like the above.
'''
class RuleDelegate(QStyledItemDelegate):
    def createEditor(self, parent, style, index):
        if index.column() != 2 : return None # should never happen
        cb = QComboBox(parent)
        cb.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        cb.addItems(ACTION_NAMES)
        return cb
    def setEditorData(self,cb,index):
        rule = index.data(Qt.ItemDataRole.UserRole) # get numeric code
        cb.setCurrentIndex(rule) # make that row active
    def setModelData(self,cb,model,index):
        model.pdata.set_folios(index.row(), rule = cb.currentIndex())

'''
Custom delegate for column 3, the folio value. Our editor widget is a
spinbox. This column is only flagged Editable when the Rule column is Set to
N (see flags() method, above). Thus we do not need to check the rule value.
'''
class FolioDelegate(QStyledItemDelegate):
    def createEditor(self, parent, style, index):
        if index.column() != 3 : return None # should never happen
        sb = QSpinBox(parent)
        sb.setFocusPolicy(Qt.StrongFocus)
        sb.setMaximum(2000) # arbitrary limit
        return sb
    def setEditorData(self,sb,index):
        sb.setValue(index.data(Qt.UserRole))
    def setModelData(self,sb,model,index):
        model.pdata.set_folios(index.row(), number = sb.value())

'''
Define the table view. The __init__ method disables word wrap and sorting,
and instantiates and assigns the three "delegates" for editing the folio
columns.
'''
class PageTableView(QTableView):
    def __init__(self, parent):
        super().__init__(parent)
        self.setCornerButtonEnabled(False)
        self.setWordWrap(False)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False)
        self.c1_delegate = FormatDelegate()
        self.setItemDelegateForColumn(1,self.c1_delegate)
        self.c2_delegate = RuleDelegate()
        self.setItemDelegateForColumn(2,self.c2_delegate)
        self.c3_delegate = FolioDelegate()
        self.setItemDelegateForColumn(3,self.c3_delegate)

    '''
    (Re-)Configure columns is called when the table is created
    or refreshed. We use the opportunity to set column widths.
    '''
    def configure_columns(self):
        hdr = self.horizontalHeader()
        ''' Size column 0, filename, to contents. '''
        hdr.setSectionResizeMode(0,QHeaderView.ResizeMode.ResizeToContents)
        '''
        Size columns 1 and 2 to 10 ens, based on the font in use by
        the header. This makes room for delegates.
        '''
        pix = hdr.fontMetrics().width("0123456789")
        hdr.resizeSection(1,pix)
        hdr.resizeSection(2,pix)
        '''
        Column 3, folio value, can be less as it is normally an arabic or
        roman number of not more than three digits.
        '''
        hdr.resizeSection(3,pix/2)
        ''' Let column 4, proofers, fill the rest of the frame '''
        hdr.setStretchLastSection(True)

'''
Define the Page Panel widget. Instantiate all the above, and hook up
the signals.
'''

class PagePanel(QWidget):
    def __init__(self, my_book):
        super().__init__(None)
        ''' save access to the Book '''
        self.my_book = my_book
        ''' save access to the PageData for the Book '''
        self.pdata = my_book.get_page_model()
        '''
        Take the UI setup out of line. This call creates the members
            self.refresh_button
            self.insert_button
            self.insert_text
            self.model: PageTableModel
            self.view: PageTableView
        '''
        self._uic()
        ''' Connect the double-clicked signal of the view '''
        self.view.doubleClicked.connect(self.go_to_row)
        ''' Connect the update button to the model's update method '''
        self.refresh_button.clicked.connect(self.do_refresh)
        ''' Connect the actual page model's signal on metadata-read '''
        self.pdata.PagesUpdated.connect(self.do_update)
        ''' Connect the insert button to our do_insert method '''
        self.insert_button.clicked.connect(self.do_insert)
        ''' Ask the fonts module to tell us if the mono font changes '''
        fonts.notify_me(self.font_change)
        # and that's page table setup.

    def font_change(self,boolean):
        if boolean : # mono font change
            self.insert_text.setFont( fonts.get_fixed() )

    '''
    Slot for the refresh button clicked signal. Call the model to do the
    actual update. Then call the view to set the widths of the columns.
    '''
    def do_refresh(self):
        self.model.update_folios()
        self.view.configure_columns()

    '''
    Slot for the PagesUpdated signal from the pagedata model, indicating we
    should refresh the table to show new values. We tell the table view to
    reset, which it does by fetching new data for all visible cells.
    '''
    def do_update(self):
        self.model.beginResetModel()
        self.model.endResetModel()
        self.view.configure_columns()

    '''
    
    This slot receives a double-click from the table view. The signal
    parameter is the index of the cell that was clicked.
    
    Double-clicks on columns 1 and 2 always, and column 3 sometimes, initiate
    editing with a custom delegate -- because those cells are flagged
    editable. The only double-clicks that come here are ones where the target
    was not editable, thus columns 0 and 4 and sometimes 3.    
    
    Get the position of the start of the page from the page data and ask the
    editor to center that text in its window.
    '''
    def go_to_row(self,index):
        p = self.pdata.position(index.row())
        self.my_book.get_edit_view().center_position(p)

    '''
    On the Insert button being pressed, make some basic sanity checks
    and get user go-ahead. Then insert the given text at the head of
    every page. This is a rarely-used service that permits inserting,
    for example, custom HTML at every page-boundary.
    '''
    def do_insert(self):
        ''' Copy the text and if it is empty, complain and exit.'''
        ins_text = self.insert_text.text()
        if 0 == len(ins_text) :
            utilities.warning_msg(
                _TR("Page Table warning message",
                    "No text to insert has been given"),
                _TR("Page Table warning message line 2",
                    "Write the text to insert in the field at the top."),
                self
            )
            return
        '''
        See how many pages are involved, which is just the ones that aren't
        marked skip. If no page info, or all are skip, complain and exit.
        '''
        n = 0
        for i in range( self.pdata.page_count() ):
            if self.pdata.folio_info(i)[0] != C.FolioRuleSkip :
                n += 1
        if n == 0 : # page table empty or all rows marked skip
            utilities.warning_msg(
                _TR("Page Table warning message",
                    "No pages to insert text into."),
                _TR("Page Table warning message line 2",
                    "No page information is known, or all folios are set to 'Omit'."),
                self
            )
            return
        ''' Get permission to do this significant operation. '''
        ok = utilities.ok_cancel_msg(
            _TR("Page Table permission request",
                "OK to insert the following string into %n pages?", n=n),
            ins_text, self)
        if ok :
            ''' get a cursor on the edit document. '''
            tc = self.my_book.get_edit_view().get_cursor()
            ''' Start a single undo-able operation on that cursor '''
            tc.beginEditBlock()
            '''
            Working from the end of the document backward, go to the
            top of each page and insert the string.
            '''
            for i in reversed( range( self.pdata.page_count() ) ) :
                [rule, fmt, val] = self.pdata.folio_info(i)
                if rule != C.FolioRuleSkip :
                    ''' Note the page's start position and set our work cursor to it '''
                    pos = self.pdata.position(i)
                    tc.setPosition(pos)
                    '''
                    Copy the insert string, replacing %f with this folio
                    and %i with the image filename.
                    '''
                    f_str = self.pdata.folio_string(i)
                    i_str = self.pdata.filename(i)
                    temp = ins_text.replace('%f',f_str).replace('%i',i_str)
                    ''' Insert that text at the position of the start of this page. '''
                    tc.insertText(temp)
                    '''
                    The insertion goes in ahead of the saved cursor position,
                    so the cursor now points after the inserted string --
                    effectively, the insert has gone to the end of the prior
                    page not the start of this one. Put the cursor for this
                    page back where it was, thus preceding the inserted text.                    
                    '''
                    self.pdata.set_position(i, pos)
            tc.endEditBlock() # wrap up the undo op

    def _uic(self):
        vbox = QVBoxLayout() # main layout
        hbox = QHBoxLayout() # top row layout
        self.refresh_button = QPushButton(
            _TR("button on Page table to update all folio values",
                "Refresh")
        )
        self.refresh_button.setToolTip(
            _TR("button on Page Table",
                "Update all folio values in the table to reflect any changes" )
        )
        self.insert_button = QPushButton(
            _TR("button on Page table to insert text at page boundaries",
                "Insert")
        )
        self.insert_button.setToolTip(
            _TR("button on Page Table",
                "Insert the text at the start of every page")
        )
        self.insert_text = QLineEdit()
        self.insert_text.setFont( fonts.get_fixed() )
        self.insert_text.setToolTip(
            _TR("text field on Page Table",
                "Text to insert at the start of every page. %f becomes the folio, %i becomes the image filename.")
        )
        hbox.addWidget(self.refresh_button,0)
        hbox.addWidget(self.insert_text,1) # text gets all available stretch
        hbox.addWidget(self.insert_button,0)
        vbox.addLayout(hbox, 0)
        self.model = PageTableModel(self.pdata,self)
        self.view = PageTableView(self)
        self.view.setModel(self.model)
        vbox.addWidget(self.view, 1)
        self.setLayout(vbox)
        # This completes UI initialization