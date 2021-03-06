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

                          CHARDATA.PY

Defines a class for storing the counts of characters in a document. An object
of this class is created by the book when a file is created or opened. It
acts as the real data model for the Chars panel (charview.py). However, it is
not based on QAbstractTableModel, because that class also has to provide
user-visible strings such as column headers and tooltips, and these are more
appropriately defined in the charview module.

    Storing Characters

Characters are stored as the keys in a sorteddict. The value of each is its
count as tallied during a census.

char_read() is registered with the metadata manager to read the CHARCENSUS
section of a metadata file, and initializes the char dict. The info on these
lines can differ between version-1 and -2 metadata, see comments below.

During a Save, the metamanager calls the method char_save() to write the
current census as metadata, passing a text stream to write into.

The QAbstractTableModel in charview calls char_count() to size its table. It
calls get_tuple(n) for a tuple of (char, count) for the value and count of
the nth character in the sorted sequence. Access to the nth char is by way of
sorteddict KeyView and ValueView which promis attain O(1) time.

The Chars panel calls refresh() when that button is clicked, causing us
to rip through the whole document counting the characters.
'''
from sortedcontainers import SortedDict
import metadata
import constants as C
import logging
cd_logger = logging.getLogger(name='Char Data')
from PyQt5.QtCore import QObject, pyqtSignal

class CharData(QObject):
    # Define the signal we emit when we have loaded new data
    CharsLoaded = pyqtSignal()

    def __init__(self,my_book):
        super().__init__()
        # Save access to the book, from which we learn the metadata
        # manager and the edit data model.
        self.my_book = my_book
        # The character list as a dict 'x':count.
        self.census = SortedDict()
        # Key and Values views on the census dict for indexed access.
        self.k_view = None # supplied in char_read() or refresh()
        self.v_view = None
        # Register to handle metadata.
        self.my_book.get_meta_manager().register(C.MD_CC, self.char_read, self.char_save)

    # Report the count of characters, used by charview to size the table.
    # The returned value can be 0 after opening a document with no metadata
    # and before a call to refresh().
    def char_count(self):
        return len(self.census)

    # Return only the character at position j, saving a little time
    # for the sort filter. Assuming this is never called except from
    # the data() method of the table, hence j will never be invalid.
    def get_char(self, j):
        return self.k_view[j]

    # Return the tuple( unichar, count ) at position j of the sorted sequence
    # of characters. Be a little suspicious of the caller.
    def get_tuple(self,j):
        try :
            return (self.k_view[j], self.v_view[j])
        except :
            cd_logger.error('Invalid chardata index {0}'.format(j))
            return ('?',0)

    # Build a new census. The current census may be empty, for example after
    # opening a document with no metadata and clicking Refresh for the first
    # time. However, once a census has been built, later refresh calls only
    # change the counts, and possibly add or subtract a few characters.
    #
    # For performance' sake we do what worddata does: if a census exists, set
    # all existing counts to zero, run the census, then delete any items with
    # zero-counts.
    def refresh(self):
        editm = self.my_book.get_edit_model()
        c = self.census # save a few lookups
        if len(c) : # something in the dict now
            self.v_view = None # discard values view
            # clear all existing counts to 0
            for char in self.k_view:
                c[char] = 0
            self.k_view = None # don't maintain keys view
            # Count every char in the document
            for line in editm.all_lines() :
                for char in line :
                    n = self.census.setdefault(char,0)
                    c[char] = n+1
            # recreate the keys view
            self.k_view = c.keys()
            # List the chars that are no longer there and delete them
            mtc = [char for char in self.k_view if c[char] == 0 ]
            for char in mtc :
                del c[char]
            # recreate the values view
            self.v_view = c.values()
        else : # empty dict; k_view and v_view are None
            for line in editm.all_lines() :
                for char in line :
                    n = c.setdefault(char,0)
                    c[char] = n+1
            # Create the views for fast access
            self.k_view = c.keys()
            self.v_view = c.values()
        self.my_book.metadata_modified(C.MD_MOD_FLAG,True)

    # Load a character census from a metadata file. The input value should be
    # a list [ ["X",count]... ], see char_save() below. However the user can
    # edit metadata so we trust nothing. We check every entry to make sure
    # the key is a single char and the value is an int>0.

    def char_read(self, sentinel,value,version) :
        self.census.clear()
        self.v_view = None
        self.k_view = None
        if isinstance(value,list) :
            for item in value :
                try:
                    if isinstance(item,list) \
                    and 2 == len(item) :
                        (key, count) = item
                    else :
                        raise ValueError
                    if isinstance(key,str) \
                    and (1 == len(key)) \
                    and isinstance(count,int) \
                    and (count > 0) :
                        self.census[key] = count
                    else :
                        raise ValueError
                except :
                    cd_logger.error(
                        'Ignoring invalid CHARCENSUS chararacter {}'.format(item) )
            # Restore the views for fast access
            self.k_view = self.census.keys()
            self.v_view = self.census.values()
            self.CharsLoaded.emit()
        else :
            cd_logger.error('CHARCENSUS metadata must be a list, ignoring all')

    # Save the character table as a list [ ["X",count]... ] for all unicode
    # values "X" in the census. We cannot simply return self.census because
    # JSON does not know how to serialize a SortedDict. We cannot simply return
    # dict(self.census) although that would work, because the serialized version
    # is not in sorted order -- the JSON serializer reproduces the dict in hash
    # key sequence. This would make it difficult to impossible for a user to edit
    # the metadata. So we peel off the items in sorted order and make a list.
    # There's not much time lost because on input (above) we have to check the
    # validity of every item anyway.

    def char_save(self, sentinel) :
        l = [ [key,value] for (key, value) in self.census.items() ]
        return l