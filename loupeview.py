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
                          loupeview.py

Define a class LoupePanel(QWidget) to implement the Loupe panel.

The panel's central feature is LoupeTableView(QTableView) drawing its data
from a LoupeTableModel(QAbstractTableModel). The table has three columns,
Line#, Column#, and Message. The table can be sorted by clicking on the
heading of column 1 (Line#) or column 3 (message); clicking on the head of
column 2 is treated the same as column 1. The sort is done locally, not
using a QSortFilterProxyModel.

Double-clicking a row causes the edit panel to jump to the line and column
of the message.

Above the table is a Refresh button. Beside it are four checkboxes that
control the -p, -l, -s and -v command line switches.

The real Table Model is in this module (there is no loupedata.py, unlike
other panels) because it is quite simple.

Initially the model has no data and rowcount() returns 0 so the table is
empty. When the Refresh button is clicked, the table model is reset and then:

1, if a path to the bookloupe executable is not known, the user is
   asked to specify one. If that fails, nothing is done.

2, with the executable known, the current edit document is written to a
   temporary file. subprocess.popen is used to launch bookloupe with the
   temp file as input.

3, the bookloupe output is captured as a list of tuples (line#, col#, message),
   where line# and col# are formatted strings, right-justified with leading
   spaces -- instead of ints. This facilitates display and making sort keys.

The table model reset completes and the rowcount() and data() methods allow
the table to be built. The default sort is by line# descending, that is, the
message for the highest line number is at the top. The user can go through
the document from bottom up and editing will not disturb the lineation.

'''

import logging
loupeview_logger = logging.getLogger(name='loupeview')
import subprocess
import regex
from sortedcontainers import SortedDict
import utilities
import paths
from PyQt5.QtCore import (
    Qt,
    QAbstractItemModel,
    QAbstractTableModel,
    QCoreApplication,
    QSortFilterProxyModel
    )
from PyQt5.QtWidgets import (
    QCheckBox,
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
        # save access to parent's four command line switches
        self.sw_l = parent.switch_l
        self.sw_p = parent.switch_p
        self.sw_s = parent.switch_s
        self.sw_v = parent.switch_v
        self.sw_x = parent.switch_x
        self.my_book = my_book # for access to edit data
        self.message_tuples = list() # where we keep messages
        self.sort_col = 0 # default sort on column 1..
        self.sort_dir = Qt.DescendingOrder # ..descending
        self.sort_vector = [] # sort indirection list

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
            col = index.column()
            sort_row = self.sort_vector[ index.row() ]
            line_col_msg_tuple = self.message_tuples[ sort_row ]
            return line_col_msg_tuple[ col ]
        elif (role == Qt.TextAlignmentRole) :
            return COL_ALIGNMENT[index.column()]
        elif (role == Qt.ToolTipRole) or (role == Qt.StatusTipRole) :
            return COL_TOOLTIPS[index.column()]
        # don't support other roles
        return None

    # Instead of using a QSortFilterProxyModel, which has a fatal performance
    # bug that makes sorting a table of more than a few hundred rows just
    # impossibly slow, we do our own sort. When the table view detects a
    # click on a column head, it calls its model's sort() method passing
    # a column number and a direction.
    #
    # We use a SortedDict to achieve sorting. The dict key is a sort key,
    # and the value is the index in self.message_tuples. When the values
    # are read out in sorted order, they give us the indexes of the data in
    # sort sequence.
    #
    # When col==0 or 1, line # sort, the key is "line#+col#". When col==2,
    # the key is "msg+line#".
    #
    # When the sort order is descending, we have to read out the vector
    # reversed() to make a list of indexes in descending order.

    def sort( self, col, order ) :
        self.sort_vector = []
        if 0 == len(self.message_tuples) : # nothing to do
            return
        self.layoutAboutToBeChanged.emit([],QAbstractItemModel.VerticalSortHint)
        sorted_dict = SortedDict()
        for j in range( len( self.message_tuples ) ) :
            line_col_msg_tuple = self.message_tuples[ j ]
            if col==2 :
                key = line_col_msg_tuple[2]+line_col_msg_tuple[0]
            else :
                key = line_col_msg_tuple[0]+line_col_msg_tuple[1]
            sorted_dict[key] = j
        if order == Qt.AscendingOrder :
            self.sort_vector = sorted_dict.values()
        else :
            self.sort_vector = [ j for j in reversed( sorted_dict.values() ) ]
        self.layoutChanged.emit([],QAbstractItemModel.VerticalSortHint)

    # OK, the money method. Generate the data to show by invoking bookloupe
    # in a subprocess. Actual refresh in a subroutine so on any error we just
    # return, and the endResetModel will still happen.
    def refresh(self):
        self.beginResetModel()
        # Clear out existing data so if the call fails, table is empty
        self.message_tuples = list()
        self._real_refresh()
        self.endResetModel()
        self.sort( self.sort_col, self.sort_dir )

    def _real_refresh(self):
        # Make sure we have access to the bookloupe executable
        bl_path = paths.get_loupe_path()
        if not bl_path : # path is null string
            bl_path = utilities.ask_executable(
                _TR('File-open dialog to select bookloupe',
                    'Select the bookloupe executable file'), self.parent() )
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
        command = [bl_path,'-d','-e','-t','-m']
        # line-end check is disabled by -l
        if not self.sw_l.isChecked() : command.append( '-l' )
        if self.sw_p.isChecked() : command.append( '-p' )
        if self.sw_s.isChecked() : command.append( '-s' )
        if self.sw_v.isChecked() : command.append( '-v' )
        if self.sw_x.isChecked() : command.append( '-x' )
        command.append( fbts.fullpath() )
        loupeview_logger.info('executing'+' '.join(command))
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
            msg2 += CPE.output[-100:].decode('UTF-8','replace')
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
            if m : # was matched, so is not None,
                lno = format( int(m.group(1)), ' >6' )
                c = 0 if m.group(3) is None else int(m.group(3))
                cno = format( c, ' >3' )
                msg = m.group(4)
                self.message_tuples.append( (lno, cno, msg) )
        loupeview_logger.info('loupeview total of {} items'.format(len(self.message_tuples)))
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
        #  self.switch_l, switch_p, switch_s, switch_v
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
        top_hbox.addStretch()
        self.switch_l = QCheckBox("No-CR")
        self.switch_l.setToolTip(
            _TR( "Loupeview command switch tooltip",
                 "Permit the 'No CR' message." ) )
        self.switch_p = QCheckBox("Quotes")
        self.switch_p.setToolTip(
            _TR( "Loupeview command switch tooltip",
                 "Require quotes to be closed in the same paragraph." ) )
        self.switch_s = QCheckBox("SQuotes")
        self.switch_s.setToolTip(
            _TR( "Loupeview command switch tooltip",
                 "Treat single-quote (apostrophes) like double quotes." ) )
        self.switch_v = QCheckBox("Verbose")
        self.switch_v.setToolTip(
            _TR( "Loupeview command switch tooltip",
                 "Enable many detailed messages." ) )
        self.switch_x = QCheckBox("Relaxed")
        self.switch_x.setToolTip(
            _TR( "Loupeview command switch tooltip",
                 "Omit some detailed tests." ) )
        top_hbox.addWidget(self.switch_p)
        top_hbox.addWidget(self.switch_s)
        top_hbox.addWidget(self.switch_v)
        top_hbox.addWidget(self.switch_x)
        top_hbox.addWidget(self.switch_l)
        # create the table model
        self.model = LoupeModel(self.my_book,self)
        # create the table view, initialized for sorting
        self.view = QTableView(self)
        self.view.setSortingEnabled(True)
        self.view.setCornerButtonEnabled(False)
        self.view.setWordWrap(False)
        self.view.setAlternatingRowColors(False)
        # connect the view to the model
        self.view.setModel(self.model)
        # Add view to the layout with all stretch
        vbox = QVBoxLayout()
        vbox.addLayout(top_hbox,0)
        vbox.addWidget(self.view,1)
        self.setLayout(vbox)
