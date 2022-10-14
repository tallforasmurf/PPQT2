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

Characters are stored as the keys in a SortedDict, self.vocab. The count of
the character is the value of the key. The data are tallied during a census.
The main reason we are still using SortedDict is that "view object" on a
SortedDict can be indexed (the standard dictionary view objects cannot). This
allows us to index into the sequence of keys, to return the character for a
given row of the table.

The Chars panel calls refresh() when the user clicks that button, causing us
to rip through the whole document counting the characters and to rebuild the
dict and two views on it.

The QAbstractTableModel in charview.py calls char_count() to size its table.
It calls get_tuple(n) for a tuple of (char, count) for the value and count of
the nth character in the sorted sequence.

During a Save, the metamanager calls the method char_save() to write the
current census as metadata, passing a text stream to write into.

The char_read() method is registered with the metadata manager to read the
CHARCENSUS section of a metadata file, and initializes the char dict as it
was when the file was saved. Thus when a book is re-opened the census is 
already built.
'''
import metadata
import constants as C
from sortedcontainers import SortedDict
import logging
cd_logger = logging.getLogger(name='Char Data')
from PyQt6.QtCore import QObject, pyqtSignal

class CharData(QObject):
    # Define the signal we emit when we have loaded new data
    CharsLoaded = pyqtSignal()

    def __init__(self,my_book):
        super().__init__()
        '''
        Save access to the Book, from which we learn the metadata
        manager and the edit data model.
        '''
        self.my_book = my_book
        '''
        Initialize the character census as a SortedDict {'x':count},
        initially empty (so char_count() returns 0)
        '''
        self.census = SortedDict()
        '''
        Key and Value views on the census dict, so that we can get
        the nth character from the sorted list.
        '''
        self.k_view = self.census.keys()
        self.v_view = self.census.values()
        ''' Register to handle metadata. '''
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
    
    '''
    
    def refresh(self):
        editm = self.my_book.get_edit_model()
        self.census = SortedDict() # garbage collect existing dict
        work = self.census # save a few dict lookups
        self.k_view = None # also don't want these updating while
        self.v_view = None # ..we load self.census
        ''' Rip through text counting all chars. '''
        for line in editm.all_lines() :
            for char in line :
                count = work.get(char,0)
                work[char] = count+1
        ''' Create the views for fast access '''
        self.k_view = self.census.keys()
        self.v_view = self.census.values()
        ''' Reach back to the Book object and turn on the modified flag.
        The metadata needs saving. '''
        self.my_book.metadata_modified(C.MD_MOD_FLAG,True)

    '''
    Pass the character census entire to be written to the metadata file. See
    metadata.py for the interface. Metadata is written using json.dumps(),
    which handles the SortedDict perfectly well, as a dict.
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
    
    Also we need not assume the metadata items are in alpha order. After all
    if the user diddled with the file they might have inserted a character
    into the dict out of sequence. However we need to convert the ordinary
    dict returned by json.loads(), into a SortedDict anyway. So proper
    alpha sequence will be restored automatically.
    '''

    def char_read(self, sentinel, value, version) :
        cd_logger.debug('Loading CHARCENSUS metadata')
        ''' release existing census values for garbage collection '''
        self.census = SortedDict()
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
