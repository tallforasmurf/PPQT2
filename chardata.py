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
of this class is created by the Book as part of opening or creating a file.
It acts as the real data model for the Chars panel (charview.py). However, it
is not based on QAbstractTableModel, because that class also has to provide
user-visible strings such as column headers and tooltips, and these are more
appropriately defined in the charview module.

    Storing Characters

Characters are stored as the keys in a dict, with the count of the character
as the value of the key. The count is tallied during a census. (In an earlier
version the type "sorteddict" was used, but that type has been withdrawn and
now an ordinary dict is used, since Python 3.7 dicts promise to preserve the
insertion sequence of data. We have to make sure when building the dict, that
insertion sequence is also character-value sequence.

The char_read() method is registered with the metadata manager to read the
CHARCENSUS section of a metadata file, and initializes the char dict as it
was when the file was saved.

During a Save, the metamanager calls the method char_save() to write the
current census as metadata, passing a text stream to write into.

The QAbstractTableModel in charview.py calls char_count() to size its table.
It calls get_tuple(n) for a tuple of (char, count) for the value and count of
the nth character in the sorted sequence.

The Chars panel calls refresh() when the user clicks that button, causing us
to rip through the whole document counting the characters and to rebuild the
dict.
'''
import metadata
import constants as C
import logging
cd_logger = logging.getLogger(name='Char Data')
from PyQt6.QtCore import QObject, pyqtSignal

class CharData(QObject):
    # Define the signal we emit when we have loaded new data
    CharsLoaded = pyqtSignal()

    def __init__(self,my_book):
        super().__init__()
        # Save access to the Book, from which we learn the metadata
        # manager and the edit data model.
        self.my_book = my_book
        # The character list as a dict {'x':count}.
        self.census = dict()
        # Key and Value views on the census dict, so that we can get
        # the nth character from the sorted list.
        self.k_view = None # supplied during refresh
        self.v_view = None
        # Register to handle metadata.
        self.my_book.get_meta_manager().register(C.MD_CC, self.char_read, self.char_save)

    '''    
    Report the count of characters, used by charview to size the table. The
    returned value can be 0 after opening a document with no metadata and
    before a call to refresh().
    '''
    def char_count(self):
        return len(self.census)

    '''
    Return only the character at position j, saving a little time for the
    sort filter. Assume this is never called except from the data() method
    of the table managed by charview.py, hence j will never be invalid.
    '''
    def get_char(self, j):
        return self.k_view[j]

    '''
    Return the tuple(unichar, count ) at position j of the sorted sequence of
    characters. Be a little suspicious of the caller.
    '''
    def get_tuple(self,j):
        try :
            return (self.k_view[j], self.v_view[j])
        except :
            cd_logger.error('Invalid chardata index {0}'.format(j))
            return ('?',0)

    '''
    Build a new census. The current self.census may be empty, for example
    after opening a document with no metadata and clicking Refresh for the
    first time. Or, we may already have a loaded it, from metadata or a prior
    refresh. There is no value in trying to preserve an existing census; in
    all cases we build a new one by counting all the characters in the text.
    
    Since 3.7, Python dicts preserve insertion sequence. We want the dict to
    be in alphabetic sequence, so that self.census[0] or self.k_view[0] is
    the alphabetically first character in the book. If the dict is built from
    a scan over the book text, self.census[0] is instead, the first character
    seen in the text (insertion order).
    
    So we build a scrap census dict in book text order as we scan the text.
    Then, in one large dict comprehension, create self.census in alpha order.
    '''
    
    def refresh(self):
        editm = self.my_book.get_edit_model()
        work = dict() # temp dict
        self.census = None # free up some space
        self.k_view = None # also don't want these updating while
        self.v_view = None # ..we load self.census
        # rip through text counting all chars
        for line in editm.all_lines() :
            for char in line :
                count = work.get(char,0)
                work[char] = count+1
        # now, sort dat dict
        self.census = {
            char:work[char] for char in work.keys().sort()
            }
        # Create the views for fast access
        self.k_view = self.census.keys()
        self.v_view = self.census.values()
        # Reach back to the Book object and turn on the modified flag.
        self.my_book.metadata_modified(C.MD_MOD_FLAG,True)

    '''   
    Pass the character census entire to be written to the metadata file. See
    metadata.py for the interface.
    
    Previously we used the now-obsolete sorteddict for the census, and that
    could not be serialized by json.dumps(), so we converted it to a list.
    Now we are using a normal dict, which json.dumps can serialize, we can
    just return self.census and be done with it.
    
    '''
    def char_save(self, sentinel) :
        return self.census
    
    '''
    Load the character census from a metadata file. See metadata.py for the
    function signature. The input value should be a dict, a previous
    self.census, see char_save() above. It could be an empty dict if the user
    saved a new file before ever refreshing the char count.
    
    The user can edit metadata so we dare trust nothing. We check every entry
    to make sure the key is a single char and the value is an int>0. Bad
    values are logged and not saved.
    
    Also we ought not assume the metadata items are in alpha order. After all
    if the user diddled with the file they might have inserted a character
    into the dict out of sequence. However this is extremely unlikely, so
    rather than check for this, or go through the work of sorting what is
    almost certainly an already-sorted dict, we ignore it. In this unlikely
    event the display of characters will have an out-of-order value until the
    next time it is refreshed.
    '''

    def char_read(self, sentinel, value, version) :
        cd_logger.debug('Loading CHARCENSUS metadata')
        self.census.clear()
        self.v_view = None
        self.k_view = None
        if isinstance(value,dict) :
            for (letter,count) in value.items() :
                try:
                    if isinstance(letter,str) \
                    and (1 == len(letter)) \
                    and isinstance(count,int) \
                    and (count > 0) :
                        self.census[letter] = count                        
                    else :
                        raise ValueError
                except :
                    cd_logger.error(
                        'Ignoring invalid CHARCENSUS entry {}'.format([letter,count])
                    )
            # Emit a Qt signal that will cause the visible table to be refreshed
            self.CharsLoaded.emit()
        else :
            cd_logger.error('CHARCENSUS metadata must be a dict, ignoring all')
        # in any case, recreate views on possibly empty dict
        self.k_view = self.census.keys()
        self.v_view = self.census.values()
