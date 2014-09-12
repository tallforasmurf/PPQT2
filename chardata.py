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

                          CHARDATA.PY

Defines a class for storing the counts of characters in a document.
An object of this class is created by the book when a file is created
or opened. It acts as the data model for the Chars panel (charview.py).

    Storing Characters

Characters are stored as the keys in a sorteddict. The value of each is its
count as tallied during a census.

char_read() is registered with the metadata manager to read the CHARCENSUS
section of a metadata file, and initializes the char dict. The info on these
lines can differ between version-1 and -2 metadata, see comments below.

During a Save, the metamanager calls the method char_save() to write the
current census as metadata, passing a text stream to write into.

The Chars panel calls char_count() to size its table. It calls get_tuple(n)
for a tuple of (char, count) for the value and count of the nth char, which
accesses the dict by way of an ValueView to attain O(1) speed.

The Chars panel calls refresh() when that button is clicked, causing us
to rip through the whole document counting the characters.
'''
from blist import sorteddict
import metadata
import logging
cd_logger = logging.getLogger(name='Char Data')
from PyQt5.QtCore import QObject

class CharData(QObject):
    def __init__(self,my_book):
        super().__init__()
        # Save access to the book, from which we learn the metadata
        # manager and the edit data model.
        self.my_book = my_book
        # The character list as a dict 'x':count.
        self.census = sorteddict()
        # Key and Values views on the census dict for indexed access.
        self.k_view = None # supplied in char_read() or refresh()
        self.v_view = None
        # Register to handle metadata.
        self.my_book.get_meta_manager().register('CHARCENSUS', self.char_read, self.char_save)

    # Report the count of characters, used by charview to size the table.
    # The returned value can be 0 after opening a document with no metadata
    # and before a call to refresh().
    def char_count(self):
        return len(self.census)

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
    # For now we do the naive thing and just build the census completely from
    # scratch on every call. However it may be worth recoding to do what
    # worddata does: if a census exists, set all existing counts to zero, run
    # the census, then delete any items with zero-counts. This would avoid
    # rebuilding the KeysView and ValuesView, and any other apparatus
    # sorteddict might maintain behind the scenes.
    def refresh(self):
        editm = self.my_book.get_edit_model()
        c = self.census # save a few lookups
        if len(c) : # something in the dict now
            self.v_view = None # discard values view
            for char in self.k_view:
                c[char] = 0
            self.k_view = None # don't update that
            for line in editm.all_lines() :
                n = self.census.setdefault(char,0)
                c[char] = n+1
            self.k_view = c.keys()
            mtc = [char for char in self.k_view if c[char] == 0 ]
            for char in mtc :
                del c[char]
            self.v_view = c.values()
        else : # empty dict; k_view and v_view are None
            for line in editm.all_lines() :
                for char in line :
                    n = c.setdefault(char,0)
                    c[char] = n+1
            # Restore the views for fast access
            self.k_view = c.keys()
            self.v_view = c.values()

    # Load a character census from a metadata file. The V1 line format is
    # "X count category", X a unicode character and count and category
    # are integers. However the user can edit metadata so we trust nothing.
    # We only require the count to be non-negative (i.e. if you don't know
    # the count, put in 0). Also the user can't be relied upon to get the
    # category right; and moreover the category code in version 1 was an
    # integer and now we want the 2-character string; so just ignore the
    # category token if present.

    def char_read(self, stream, sentinel,v,p) :
        self.census.clear()
        self.v_view = None
        self.k_view = None
        for line in metadata.read_to(stream, sentinel):
            parts = line.split()
            try :
                char = parts[0]
                count = int(parts[1]) # can raise IndexError or ValueError
                if (len(char) != 1) or (count < 0) :
                    raise ValueError
            except :
                cd_logger.error('invalid CHARCENSUS line "'+line+'" ignored')
                continue
            count = min(1,count) # in case it was zero, make nonzero
            if char in self.census :
                cd_logger.warn('"'+char+'" appears more than once in metadata')
                continue
            self.census[char] = count
        # Restore the views for fast access
        self.k_view = self.census.keys()
        self.v_view = self.census.values()

    # Save the character table as "X count". In v1 we also saved the unicode
    # category but there's no point, it saves no time to read it back as
    # opposed to just generating it on input.
    def char_save(self, stream, sentinel) :
        stream << metadata.open_line(sentinel)
        for char in self.census :
            count = self.census[char]
            stream << char + ' ' + str(count) + '\n'
        stream << metadata.close_string(sentinel)
