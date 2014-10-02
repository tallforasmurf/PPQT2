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
                          loupeview.py

Define a class LoupePanel(QWidget) to implement the Loupe panel.

The panel's central feature is LoupeTableView(QTableView) drawing its data
from a LoupeTableModel(QAbstractTableModel). The table has three columns,
Line#, Column#, and Message. The table can be sorted but requires no special
sort/filter proxy.

Double-clicking a row causes the edit panel to jump to the line and column
of the message.

Above the table is a Refresh button. No other controls for now (although
some type of filtration may be added).

The real Table Model is in this module (there is no loupedata.py, unlike
other panels) because it is quite simple.

Initially the model has no data and rowcount() returns 0 so the table is
empty. When the Refresh button is clicked, the table model is reset and then:

1, if a path to the bookloupe executable is not known, the user is
   asked to specify one. If that fails, nothing is done.

2, with the executable known, the current edit document is written to a
   temporary file. subprocess.popen is used to launch bookloupe with the
   temp file as input.

3, the bookloupe output is captured as a list of tuples (line#, col#, message).

The table model reset completes and the rowcount() and data() methods allow
the table to be built. The default sort is by line# descending, that is, the
message for the highest line number is at the top. The user can go through
the document from bottom up and editing will not disturb the lineation.

'''

import logging
loupeview_logger = logging.getLogger(name='loupeview')
import subprocess
import regex
import utilities
import paths
from PyQt5.QtCore import (
    Qt,
    QAbstractTableModel,
    QCoreApplication,
    QSortFilterProxyModel
    )
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QTableView,
    QWidget
    )
_TR = QCoreApplication.translate
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
#
# Class of our table model. Overrides the standard methods:
# flags : return Qt.itemIsEnabled.
# columnCount : return the number of columns (3)
# rowCount : return number of message tuples in the message_list
# headerData : return the column header name or tooltip string.
# data : return the actual data, or various helpful info about a column.
#
COL_HEADS = {
    0 : _TR('Loupe table column head, keep it short','Line#'),
    1 : _TR('Loupe table column head, keep it short','Col#'),
    2 : _TR('Loupe table column head','Diagnostic message')
    }
COL_TOOLTIPS = {
    0: _TR('Loupe table column tooltip', 'Document line number where error was found' ),
    1: _TR('Loupe table column tooltip', 'Column in line where error was found or 0 if not known' ),
    2: _TR('Loupe table column tooltip', 'Description of the error that was found in this line')
}
COL_ALIGNMENT = {
    0: Qt.AlignRight,
    1: Qt.AlignRight,
    2: Qt.AlignLeft
    }
# Regex to get parts out of a bookloupe message, for example
#    Line 1 column 26 - Query standalone 1:
#  match group 1 == '1'
#  match group 3 == '26'
#  match group 4 == 'Query standalone 1'
#    Line 81 - Mismatched singlequotes?
#  match group 1 == '81'
#  match group 3 == None
#  match group 4 == 'Mismatched singlequotes?'
# Other messages: no match

MSGREX = regex.compile('Line\s(\d+)(\s+column\s+(\d+))?\s+-\s+(\w.+)')

class LoupeModel(QAbstractTableModel):
    def __init__(self, my_book, parent):
        super().__init__(parent)
        self.my_book = my_book # for access to edit data
        self.message_tuples = list() # where we keep messages

    def rowCount(self, index):
        if index.isValid() : return 0 # we don't have a tree here
        return len(self.message_tuples)

    def columnCount(self, index):
        global COL_HEADS
        if index.isValid() : return 0 # we don't have a tree here
        return len(COL_HEADS) # i.e., 3

    def flags(self, index):
        return Qt.ItemIsEnabled

    def headerData(self, col, axis, role):
        global COL_HEADS, COL_TOOLTIPS
        if (axis == Qt.Horizontal) and (col >= 0):
            if role == Qt.DisplayRole : # wants actual text
                return COL_HEADS[col]
            elif (role == Qt.ToolTipRole) or (role == Qt.StatusTipRole) :
                return COL_TOOLTIPS[col]
        return None # whatever, we don't do that

    def data(self, index, role ):
        global COL_ALIGNMENT, COL_TOOLTIPS
        if role == Qt.DisplayRole : # wants actual data
            (line_no, col_no, msg) = self.message_tuples[index.row()]
            if 0 == index.column() :
                return format(line_no,' >5')
            elif 1 == index.column() :
                return format(col_no,' >3')
            else:
                return msg
        elif (role == Qt.TextAlignmentRole) :
            return COL_ALIGNMENT[index.column()]
        elif (role == Qt.ToolTipRole) or (role == Qt.StatusTipRole) :
            return COL_TOOLTIPS[index.column()]
        # don't support other roles
        return None
    # OK, the money method. Generate the data to show by invoking bookloupe
    # in a subprocess. Actual refresh in a subroutine so on any error we just
    # return, and the endResetModel will still happen.
    def refresh(self):
        self.beginResetModel()
        # Clear out existing data so if the call fails, table is empty
        self.message_tuples = list()
        self._real_refresh()
        self.endResetModel()
    def _real_refresh(self):
        # Make sure we have access to the bookloupe executable
        bl_path = paths.get_loupe_path()
        if not bl_path : # path is null string
            bl_path = utilities.ask_executable(
                _TR('File-open dialog to select bookloupe',
                    'Select the bookloupe executable file'), parent)
            if bl_path is None : # user selected non-executable
                utilities.warning_msg(
                    _TR('Error choosing bookloupe file',
                        'That is not an executable file.') )
                return
            if 0 == len(bl_path) : # user pressed Cancel
                return
            paths.set_loupe_path(bl_path)
        # bl_path is an executable, continue
        # create a temp file containing the book contents
        fbts = utilities.temporary_file()
        fbts << self.my_book.get_edit_model().full_text()
        fbts.rewind() # forces a flush()
        # create the bookloupe command
        command = [bl_path,'-e','-s','-l','-m','-v', fbts.fullpath()]
        # run it, capturing the output as a byte stream
        try:
            bytesout = subprocess.check_output( command, stderr=subprocess.STDOUT )
        except subprocess.CalledProcessError as CPE :
            msg1 = _TR('bookloupe call returns error code',
                    'Bookloupe execution ended with an error code')
            msg1 += ' '
            msg1 += str(CPE.returncode)
            msg2 = _TR('header for end of output string',
                       'Last part of bookloupe output:' )
            msg2 += '\n'
            msg2 += CPE.output[:-100].decode('UTF-8','replace')
            utilities.warning_msg( msg1, msg2, self.parent())
            return # leaving message_tuples empty
        # convert the bytes to unicode. bookloupe's message templates are
        # just ASCII but they can include quoted characters of any set.
        charsout = bytesout.decode(encoding='UTF-8',errors='replace')
        # convert the stream to a list of lines.
        linesout = charsout.split('\n')
        # process the lines into tuples in our list.
        for line in linesout :
            m = MSGREX.search(line)
            if m : # was matched
                lno = int(m.group(1))
                cno = 0 if m.group(3) is None else int(m.group(3))
                msg = m.group(4)
                self.message_tuples.append( (lno, cno, msg) )
        # and that's refresh. On exit, fbts is trashed which closes
        # and deletes the temporary file.

class LoupeView(QWidget):
    def __init__(self, book, parent=None):
        self.my_book = book
        super().__init__(parent)
        # Do the messy part of laying out the panel out of line.
        # This creates the members,
        #  self.refresh QPushButton
        #  self.view QTableView
        #  self.model LoupeModel
        #  self.proxy QSortFilterProxyModel
        #
        self._uic()
        # hook up the Refresh signal
        self.refresh.clicked.connect(self.do_refresh)
        # hook up the doubleclicked signal
        self.view.doubleClicked.connect(self.go_to_line)

    # On click of Refresh, get new data and reset table props.
    def do_refresh(self):
        self.model.refresh()
        self.view.resizeColumnsToContents()
        self.view.horizontalHeader().setStretchLastSection(True)
        self.view.setSortingEnabled(True)

    # On double-click of row, tell the editor to go to that line and column.
    # Get the line number by getting the displayed data from column 0 of the
    # target row.
    def go_to_line(self, index):
        if index.column() != 0 :
            # dblclick on some column other than 0. We need a reference to
            # column 0, and we get it from the index.
            index = index.sibling(index.row(),0)
        line_num = int( index.data(Qt.DisplayRole) )
        # get a column number the same way
        index = index.sibling(index.row(),1)
        col_num = int( index.data(Qt.DisplayRole) )
        # Tell the editor to go to this line
        edview = self.my_book.get_edit_view()
        edview.go_to_line_number(line_num)
        # If we have a nonzero column number, move to that
        if col_num > 0 :
            (pos, anchor) = edview.get_cursor_val()
            edview.show_position(pos+col_num)

    def _uic(self):
        # create the refresh button left-aligned
        top_hbox = QHBoxLayout()
        self.refresh = QPushButton(
            _TR('Loupe refresh button','Refresh') )
        top_hbox.addWidget(self.refresh,0)
        top_hbox.addStretch(1)
        # create the table model
        self.model = LoupeModel(self.my_book,self)
        # create the minimal sort proxy
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.model)
        # create the table view and connect it to the proxy-model.
        self.view = QTableView(self)
        self.view.setModel(self.proxy)
        # Table view has simple column sorting enabled, no proxy
        # needed. If we add filtering we must use a sortfilterproxy
        # instead, see charview for an example.
        self.view.setSortingEnabled(True)
        self.view.setCornerButtonEnabled(False)
        self.view.setWordWrap(False)
        self.view.setAlternatingRowColors(False)
        # Add view to the layout with all stretch
        vbox = QVBoxLayout()
        vbox.addLayout(top_hbox,0)
        vbox.addWidget(self.view,1)
        self.setLayout(vbox)
