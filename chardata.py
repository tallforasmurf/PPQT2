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

Characters are stored as the keys in a sorteddict. The value of each is a
list of [count,category] where count is tallied during a census and category
is the unicode category such as "Ll" for "Letter_Lowercase", as returned by
unicodedata.category().

char_read() is registered with the metadata manager to read the CHARCENSUS
section of a metadata file, and initialice the char dict. The info on these
lines can differ between version-1 and -2 metadata, see comments below.

During a Save, the metamanager calls the method char_save() to write the
current census as metadata, passing a text stream to write into.

The Chars panel calls char_count() to size its table. It calls char_at(n) for
the nth character value, and char_val_at(n) to get a tuple of (count,
category) for the nth char. These access the dict by way of a KeysView or
ValuesView respectively to attain O(1) speed.

'''


# The character list. New items go in with a value (count) of 0
# and category "Other_NotAssigned".
self.chars = sorteddict()
self.char.setdefault([0,'Cn'])
# Key and Values views on the chars dict for indexed access.
self.chars_kview = self.chars.KeysView()
self.chars_vview = self.chars.ValuesView()
self.metamgr.register('CHARCENSUS', self.char_read, self.char_save)


#
# 4. Load a character census from a metadata file. The line format is "X
# count category", but since the user can edit the file we only require
# the count to be non-negative (i.e. if you don't know the count, put in
# 0). Also the user can't be relied upon to get the category right; and
# moreover the category code of version 1 is an integer and now we want
# the 2-character string; so just ignore the category token if present.
#
def char_read(self, stream, v, sentinel) :
    for line in self.metamgr.read_to(stream, sentinel):
        parts = line.split()
        try :
            char = parts[0]
            count = int(parts[1])
            if (len(char) != 1) or (count < 0) :
                raise ValueError
        except whocares :
            worddata_logger.WARN('invalid CHARCENSUS line "'+line+'" ignored')
            char = None
        if char : # X is one char, count is non-negative int
            count = min(1,count) # in case it was zero, make nonzero
            cat = unicodedata.category(char)
            self.chars[char] = [count, cat]
#
# 4. Save the character table, each as CHAR count
# in v1 we also saved the unicode category but there's no
# point, it saves no time to read it back as opposed to
# just generating it on input.
#
def char_save(self, stream, sentinel) :
    stream << metadata.open_string(sentinel)
    for char in self.chars :
        count = self.chars[char][0]
        stream << char + ' ' + str(count)
        stream << '\n'
    stream << metadata.close_string(sentinel)
# The following methods are used by the Chars panel.
#
#  Get the count of chars in the census.
#
def char_count(self):
    return len(self.chars)
#
#  Get the nth char, or its count. Guard against bad indices.
#
def char_at(self,n):
    try:
        return self.chars_kview[n]
    except its_always_something:
        return ('?')
def char_count_at(self, n):
    try:
        return self.chars_vview[n]
    except whatever:
        return(0)
