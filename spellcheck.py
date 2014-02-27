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
                          SPELLCHECK.PY

Defines the class of objects that provide spellcheck via hunspell.

One of these is created for each open Book because the
default dict is different per book.

Receives a list of available dicts from the Book.

Implements check(word, alt-tag=None) method used by worddata.py
to check spelling in a default or alternate dictionary.

If there is no active main dictionary or the alt-dictionary cannot
be created, return True, in other words, we do not see misspellings
unless we actually can check them.

'''

# THIS IS A STUB TODO see v1 pqSpell.py
class Speller(object):
    def __init__(self, my_book):
        self.book = my_book
        # TODO get main dict tag from book
        # TODO instantiate a dictionary for it
        # TODO get list of available dicts from book


    def check(word, alt_tag = None):
        return True
