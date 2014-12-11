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
                          fnotview.py

Define a class to implement the Fnote (Footnotes) panel. This is the
View/Controler corresponding to the Data Model of fnotdata.py.

The view consists of:

At the top, three buttons:

  [Refresh]  left-justified; right-justified:  [Renumber] [Move to Zones]

The bulk of the panel consists of a six-column table of
   Key   Class   Anchor line   Note line   Note Length   Text

An array of six popup menus (QComboBox) which relate the six classes
of Key (ABC/IVX/abc/ivx/123/*¤§) to a "number stream" of some class.

(Note version 1 had two more actions, ASCII Cvt and HTML Cvt, but
these operations are now delegated to translators.)

'''

import fnotdata
import utilities
from PyQt5.QtCore import (
    Qt,
    QAbstractTableModel,
    QCoreApplication
    )
_TR = QCoreApplication.translate
from PyQt5.QtGui import (
    QBrush,
    QColor
    )
from PyQt5.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QItemDelegate,
    QLabel,
    QPushButton,
    QSpacerItem,
    QTableView,
    QVBoxLayout,
    QWidget,
    )

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Assorted global constants used in this module.
#
# Assume KeyClass_xxx names defined in fnotdata.
#
# Class names for display in the table, indexed by fnotdata constants.
key_class_names = {
    fnotdata.KeyClass_IVX : 'IVX',
    fnotdata.KeyClass_ABC : 'ABC',
    fnotdata.KeyClass_ivx : 'ivx',
    fnotdata.KeyClass_abc : 'abc',
    fnotdata.KeyClass_123 : '123',
    fnotdata.KeyClass_sym : '*\u00A4\u00A7'
    }

# Number-stream names as a list in KeyClass* order, except that the
# KeyClass_sym position is used to mean, don't renumber. Used to load the
# stream comboboxes.

stream_names = [
    'I, II, .. M',
    'A, B, ..ZZZ',
    'i, ii, .. m',
    'a, b, ..zzz',
    '1, 2, ..999',
    'no renumber'
    ]

# Constants for table head values
COL_HEADS = {
    0 : _TR('Footnote table column head', 'Key' ),
    1 : _TR('Footnote table column head', 'Class' ),
    2 : _TR('Footnote table column head', 'Anchor\nline'),
    3 : _TR('Footnote table column head', 'Note\nline'),
    4 : _TR('Footnote table column head', 'Note\nlength'),
    5 : _TR('Footnote table column head', 'Note text')
    }
COL_TOOLTIPS = {
    0 : _TR('Footnate table column tooltip', 'Number or symbol of this footnote'),
    1 : _TR('Footnate table column tooltip', 'Type of key: alpha, roman number, arabic number, symbol'),
    2 : _TR('Footnate table column tooltip', 'Line number where [key] appears'),
    3 : _TR('Footnate table column tooltip', 'Line number of [Footnote key:'),
    4 : _TR('Footnate table column tooltip', 'Number of lines in the [Footnote...]'),
    5 : _TR('Footnate table column tooltip', 'Text of the first line of the note')
    }
COL_ALIGNMENT = {
    0 : Qt.AlignCenter,
    1 : Qt.AlignCenter,
    2 : Qt.AlignRight,
    3 : Qt.AlignRight,
    4 : Qt.AlignRight,
    5 : Qt.AlignLeft
    }
# Amount of text to display in the last column
# TODO: can we compute this from the header???
MAX_NOTE_TEXT = 40
# Values that make us display a matched note with a green background
SUSPICIOUS_NOTE_SIZE = 10
SUSPICIOUS_NOTE_DISTANCE = 50

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Implement a concrete table model by subclassing Abstract Table Model. The
# data served is obtained from an FnoteData object which is passed here by
# FnotePanel when it creates the model.
#

class FnoteTableModel(QAbstractTableModel):
    def __init__(self, model, parent):
        super().__init__(parent)
        # save access to FnoteData database
        self.data = model
        # items of last row requested in data()
        self.last_row = None # index of row
        self.brush_for_row = None # background color brush
        self.note_line = None
        self.anchor_line = None
        self.note_size = None
        # Greate the brushes for painting the background of good,
        # questionable, and bad (unmatched) rows.
        self.white_brush = QBrush(QColor('transparent'))
        self.pink_brush = QBrush(QColor('lightpink'))
        self.green_brush = QBrush(QColor('palegreen'))

    def columnCount(self,index):
        global COL_HEADS
        if index.isValid() : return 0 # we don't have a tree here
        return len(COL_HEADS)

    # Flags: at one time I considered making column editable so the user
    # could change the Key value in the table, but decided against it, on the
    # grounds that the user shouldn't be fiddling with keys on a
    # one-at-a-time basis, but only use the renumbering tool.
    def flags(self,index):
        return Qt.ItemIsEnabled

    def rowCount(self,index):
        if index.isValid() : return 0 # we don't have a tree here
        return self.data.count()

    def headerData(self, column, axis, role):
        global COL_HEADS, COL_TOOLTIPS
        if ( axis == Qt.Horizontal ) and ( column >= 0 ):
            if role == Qt.DisplayRole : # wants actual text
                return COL_HEADS[column]
            if (role == Qt.ToolTipRole) or (role == Qt.StatusTipRole) :
                return COL_TOOLTIPS[column]
        return None # we don't do that, whatever it is

    # This method is called whenever the table view wants to know practically
    # anything about the visible aspect of a table cell. The row & column are
    # in the index, and what it wants to know is expressed by the role.
    #
    # We trust QTableView to only ask for rows that exist, and we assume
    # that it asks for all columns of one row before going on to the next.
    # However it is not clear at what point it asks for the Background
    # so we set aside the correct brush the first time it asks for a row.

    def data(self, index, role ):
        row = index.row()
        col = index.column()
        if row != self.last_row :
            self.last_row = row
            self.brush_for_row = self.white_brush # be optimistic
            self.note_line = self.data.note_line(row)
            self.anchor_line = self.data.anchor_line(row)
            self.note_size = self.data.note_size(row)
            if (self.anchor_line is None) or (self.note_line is None) :
                # unmatched anchor or note, show in pink
                self.brush_for_row = self.pink_brush
            elif (self.note_size > SUSPICIOUS_NOTE_SIZE) \
                 or SUSPICIOUS_NOTE_DISTANCE \
                           <= ( self.note_line - self.anchor_line ) :
                self.brush_for_row = self.green_brush
        # Now, what was it you wanted?
        if role == Qt.DisplayRole : # wants actual data
            if   col == 0 : return self.data.key(row)
            elif col == 1 : return key_class_names[self.data.key_class(row)]
            elif col == 2 : return self.anchor_line
            elif col == 3 : return self.note_line
            elif col == 4 : return self.note_size
            else : return self.data.note_text(row, MAX_NOTE_TEXT)
        elif (role == Qt.TextAlignmentRole) :
            return COL_ALIGNMENT[col]
        elif (role == Qt.ToolTipRole) or (role == Qt.StatusTipRole) :
            return COL_TOOLTIPS[col]
        elif (role == Qt.BackgroundRole) or (role == Qt.BackgroundColorRole):
            return self.brush_for_row
        # don't support other roles
        return None

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Define the class of the Footnote panel, based on a QWidget.
#
class FnotePanel(QWidget):
    def __init__(self, my_book) :
        super().__init__(None) # parentage supplied by tab bar
        # save reference to my book.
        self.book = my_book
        # set up access to the fnotdata object
        self.data = my_book.get_fnot_model()
        # set up access to the edit panel for our book
        self.edit_view = my_book.get_edit_view()
        # The lengthy process of setting up this moderately complicated
        # widget is out of line. _uic() creates the following members
        # and lays them out:
        #
        # self.refresh_button      QPushButton
        # self.renumber_button        "
        # self.move_button            "
        # self.table               FnoteTableModel
        # self.view                QTableView
        # self.pick_IVX            QComboBox
        # self.pick_ABC               "
        # self.pick_ivx               "
        # self.pick_abc               "
        # self.pick_123               "
        # self.pick_sym               "
        #
        self._uic()
        # Set up a list of stream-choice comboboxes in Key-class order.
        # To decide which stream to use for a given key:
        #   j = self.stream_menus[key-class].currentIndex()
        self.stream_menus = [
            self.pick_IVX,
            self.pick_ABC,
            self.pick_ivx,
            self.pick_abc,
            self.pick_123,
            self.pick_sym]
        # Set up the number streams from which we generate new numbers.
        #    To get the next value from stream j:
        # self.streams[j]+=1; key=self.stream_lambdas[j](self.streams[j])
        self.number_streams = [ 0, 0, 0, 0, 0, 0 ]
        self.stream_lambdas = [
            lambda n : utilities.to_roman( n, False ),
            lambda n : utilities.to_alpha( n, False ),
            lambda n : utilities.to_roman( n, True ),
            lambda n : utilities.to_alpha( n, True ),
            lambda n : str(n),
            lambda n : None
            ]
        # Connect the various signals that are flashing about here.
        # Connect any click on the table to our clicked slot:
        self.view.clicked.connect(self.table_click)
        # Four of the menus have special rules, connect their signals
        # to where the rules are enforced:
        self.pick_IVX.activated.connect(self.IVX_pick)
        self.pick_ABC.activated.connect(self.ABC_pick)
        self.pick_ivx.activated.connect(self.ivx_pick)
        self.pick_abc.activated.connect(self.abc_pick)
        # Connect the action buttons.
        self.refresh_button.clicked.connect(self.do_refresh)
        self.renumber_button.clicked.connect(self.do_renumber)
        self.move_button.clicked.connect(self.do_move)
        # Connect FootNotesLoaded from the model to our table_reset
        self.data.FootNotesLoaded.connect(self.table_reset)

    #-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # Slots that handle signals from UI elements.
    #
    # The following four slots are for the ambiguous classes, to make sure
    # that contradictory choices are not made.

    # If the user sets the IVX stream to the same as the ABC stream or to
    # no-renumber, fine. Otherwise the user is asserting there are valid
    # IVX Keys, and in that case, ABC needs to be no-renumber.

    def IVX_pick(self, pick):
        if (pick == self.pick_ABC.currentIndex()) or (pick == 5) : return
        self.pick_ABC.setCurrentIndex(5)

    # If the user sets the ABC stream to anything but no-renumber, that is
    # an assertion that there are valid ABC keys, and therefore keys that
    # are classified IVX need to use the same stream.

    def ABC_pick(self, pick):
        if pick != 5 :
            self.pick_IVX.setCurrentIndex(pick)

    # And similarly for the lowercase versions.
    def ivx_pick(self, pick):
        if (pick == self.pick_abc.currentIndex()) or (pick == 5) : return
        self.pick_abc.setCurrentIndex(5)

    def abc_pick(self, pick):
        if pick != 5 :
            self.pick_ivx.setCurrentIndex(pick)

    # This is the slot for a click anywhere in the tableview. Click is on:
    #
    # * column 0 or 1 (key or class) we jump to the Anchor line, unless we
    #   are on that line, in which case jump to the Note line (ping-pong).
    #
    # * column 2 (Anchor line) we jump to the Anchor line.
    #
    # * column 3, 4, 5 (Note line, size, or text) jump to the Note line.
    #
    # In each case, to "jump" means, set the document cursor to the reftc or
    # the notetc, making the ref or note the current selection.
    #
    # In all cases, watch out for unmatched Anchors and Notes.

    def table_click(self, index) :
        row = index.row()
        col = index.column()
        if col > 2 : # column 3 4 or 5
            target_line = self.data.note_line( row )
        else : # column 0 1 or 2
            target_line = self.data.anchor_line( row )
        if col < 2 and target_line == self.edit_view.get_line() :
            # cannot get here if target_line is None
            target_line = self.data.note_line( row ) # but now it might be
        if target_line is None : # unmatched Anchor
            utilities.beep()
            return
        self.edit_view.go_to_line( target_line )

    # Doing a refresh just means, call the data model's refresh method. It
    # will emit a FootNotesLoaded signal which we handle in table_reset.

    def do_refresh(self):
        self.data.refresh(
            utilities.make_progress(
                _TR('Title of footnote refresh progress bar',
                    'Finding all footnotes'),self)
            )

    # When the data model in fnotdata reads a metadata section, or when
    # it performs a refresh operation, it emits FootNoteData and we
    # make our visible table redraw itself.

    def table_reset(self):
        self.model.beginResetModel()
        self.model.endResetModel()
        # Adjust column widths. Although a roman-numeral key can be very
        # wide, almost every real Key is one or at most 2 chars. Key class is
        # only 3 characters (key_class_names). Anchor Line and Note Line are
        # numbers less than 6 digits and Note Length is less than 4 digits.
        # So, size first five columns to 5 or 7ens. Make the last column fill
        # the remaining space.
        hdr = self.view.horizontalHeader()
        pix5 = hdr.fontMetrics().width("99999")
        pix7 = hdr.fontMetrics().width("9999999")
        hdr.resizeSection(0,pix5)
        hdr.resizeSection(1,pix5)
        hdr.resizeSection(2,pix7)
        hdr.resizeSection(3,pix7)
        hdr.resizeSection(4,pix7)
        # Let column 5, note text, fill the rest of the frame
        hdr.setStretchLastSection(True)

    # In version 1, before doing a move or renumber, we checked to see
    # if there had been any editing since the last refresh, and did a
    # refresh if so. But the actual refresh goes fast enough that we
    # are just going to do the refresh, and not try to figure out if
    # we really need to.

    # subroutine to refresh (since some mismatches might have been fixed
    # since the last one), check for unmatched notes, and if there are any,
    # issue an error message and return False.

    def _can_we_do_this(self):
        self.do_refresh()
        m = self.data.mismatches()
        if (m) :
            emsg = _TR(
                'Footnote panel error message',
                'Cannot do this action when there are unmatched Anchors and Notes.'
                )
            expl = _TR(
                'Footnote panel info message',
                'There are %n unmatched Anchors and Notes.',n=m)
            utilities.warning_msg(emsg,expl,self)
        return m == 0

    def do_renumber(self):
        if not self._can_we_do_this() : return
        # clear the number streams
        self.streams = [ 0, 0, 0, 0, 0, 0]
        # Tell the table model that things are gonna change
        self.model.beginResetModel()
        # create a working cursor and start an undo macro on it.
        worktc = self.edit_view.get_cursor()
        worktc.beginEditBlock()
        # Do the actual work inside a try-finally block so as to be sure
        # that the Edit Block is ultimately closed.
        try :
            for j in range(self.data.count()):
                old_key = self.data.key(j)
                old_class = self.data.key_class(j)
                # Get the index of the stream that has been chosen for
                # this class of key
                stream_index = self.stream_menus[old_class].currentIndex()
                # Increment that stream (if the choice is 5, no-renumber,
                # the increment is harmless)
                self.streams[stream_index] += 1
                # Format the current stream value based on the selected stream.
                # When stream_index is 5, the result is None. If the stream
                # has become too high, the to_roman or to_alpha function might
                # return '???' but will not generate an exception.
                new_key = self.stream_lambdas[stream_index](self.streams[stream_index])
                # in the rare event that produced "oe" or "OE", skip to the next
                # (wonder if this is ever executed in real use?)
                if (new_key is not None) and (new_key.lower() == 'oe') :
                    self.streams[stream_index] += 1
                    new_key = self.stream_lambdas[stream_index](self.streams[stream_index])
                # If new_key is None, we make no change to this note.
                # Otherwise, make the change.
                if new_key is not None :
                    self.data.set_key(j, new_key, worktc)
            # end of for j in range of keys
        finally:
            worktc.endEditBlock
    # end of do_renumber

    # For do_move, first make sure there are no mismatches. Then
    # have the database look for footnote zones. If it finds at least 1,
    # tell it to go ahead and do the move.

    def do_move(self):
        if not self._can_we_do_this() : return
        nzones = self.data.find_zones()
        if nzones == 0 :
            emsg = _TR(
                'Footnote panel error message',
                'Cannot move footnotes until footnote zones have been defined')
            expl = _TR(
                'Footnote panel explanation',
                'A Footnote zone is defined by "/F" and "F/" lines.' )
            utilities.warning_msg(emsg,expl,self)
            return
        self.data.move_notes()

    #-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # Set-up functions for initializing the UI elements.

    # convenience functions to shorten the code of setting up 6 similar menus.
    # make a combobox loaded with the stream names and set to a particular one.
    def _make_cb(self, default, text) :
        cb = QComboBox()
        cb.addItems(stream_names)
        cb.setCurrentIndex(default)
        tt = _TR( 'Footnote panel popup menus',
                 'Choose the format to use when renumbering Note Keys such as:',
                 'will be followed by e.g. "[A]" or "[5]"' )
        cb.setToolTip(tt+text)
        return cb
    # combine a combobox with a label in an hbox
    def _make_pair(self, cb, caption):
        hb = QHBoxLayout()
        hb.addWidget( QLabel(caption) )
        hb.addWidget(cb)
        return hb

    def _uic(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        # make a horizontal layout of [Refresh       Renumber Move]
        top_box = QHBoxLayout()
        # make the Refresh button with translated text
        self.refresh_button = QPushButton(
            _TR('Footnote panel Refresh button', 'Refresh') )
        self.refresh_button.setToolTip(
            _TR('Footnote panel Refresh button',
                'Scan the book to find all footnotes and match them to their anchors' ) )
        top_box.addWidget(self.refresh_button,0)
        top_box.addStretch(1) # push next two buttons to the right
        # Make the Renumber button
        self.renumber_button = QPushButton(
            _TR('Footnote panel Renumber button', 'Renumber') )
        self.renumber_button.setToolTip(
            _TR('Footnote panel Renumber button',
                'Renumber all footnotes using the styles chosen in the menus below') )
        top_box.addWidget(self.renumber_button,0)
        # Make the Move button
        self.move_button = QPushButton(
            _TR('Footnote panel Move-to-zones button','Move to Zones') )
        self.move_button.setToolTip(
            _TR('Footnote panel Move button',
                'Move all footnotes into zones marked /F ... F/' ) )
        top_box.addWidget(self.move_button,0)
        # Put that row of buttons at the top of the panel
        main_layout.addLayout(top_box,0)
        # Create the table, a very basic one, no sorting etc.
        self.model = FnoteTableModel(self.data, self)
        self.view = QTableView()
        self.view.setModel(self.model)
        self.view.setCornerButtonEnabled(False)
        self.view.setWordWrap(False)
        self.view.setAlternatingRowColors(False)
        self.view.setSortingEnabled(False)
        main_layout.addWidget(self.view,1) # Table gets all the stretch
        # Create the six combo boxes. Initialize both IVX and ABC to
        # the ABC stream and ivx and abc to the abc.
        self.pick_IVX = self._make_cb(fnotdata.KeyClass_ABC, '[II]')
        self.pick_ABC = self._make_cb(fnotdata.KeyClass_ABC, '[B]' )
        self.pick_ivx = self._make_cb(fnotdata.KeyClass_abc, '[vi]')
        self.pick_abc = self._make_cb(fnotdata.KeyClass_abc, '[b]' )
        self.pick_123 = self._make_cb(fnotdata.KeyClass_123, '[2]' )
        self.pick_sym = self._make_cb(fnotdata.KeyClass_sym, '[§]' )
        # Create a 2x3 grid layout and put a label:combobox in each cell
        grid = QGridLayout()
        grid.addLayout( self._make_pair( self.pick_ABC, key_class_names[1] ), 0, 0)
        grid.addLayout( self._make_pair( self.pick_IVX, key_class_names[0] ), 1, 0)
        grid.addLayout( self._make_pair( self.pick_abc, key_class_names[3] ), 0, 1)
        grid.addLayout( self._make_pair( self.pick_ivx, key_class_names[2] ), 1, 1)
        grid.addLayout( self._make_pair( self.pick_123, key_class_names[4] ), 0, 2)
        grid.addLayout( self._make_pair( self.pick_sym, key_class_names[5] ), 1, 2)
        # Put the grid in an hbox with stretch on each side to center it
        gridhb = QHBoxLayout()
        gridhb.addStretch(1)
        gridhb.addLayout(grid,0)
        gridhb.addStretch(1)
        # Add that row to the main layout
        main_layout.addLayout(gridhb)
        # End of _uic