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
    def __init__(self, primary_tag, dict_path_dict ):
        self.primary_tag = primary_tag
        self.dict_path_dict = dict_path_dict
        self.primary_dictionary = None
        self.alt_dictionary = None
        self.alt_tag = None
        # TODO make primary dict now

    # Called by the book when the user chooses a new default
    # dictionary: if it is a change, get rid of the old and
    # make a new one.
    def new_primary_dict(self, primary_tag):
        if primary_tag != self.primary_tag :
            self.primary_dictionary = None
            # TODO make new primary dictionary

    def make_a_dict(self, tag):
        # TODO: implement
        return None

    def check(word, alt_tag = None):
        if alt_tag : # is not None:
            if alt_tag != self.alt_tag :
                self.alt_dictionary = None
            if self.alt_dictionary is None:
                self.alt_dictionary = self.make_a_dict(alt_tag)
                self.alt_tag = alt_tag
            dict_to_use = self.alt_dictionary
        else :
            dict_to_use = self.primary_dictionary
        if dict_to_use :
            return True #TODO
        else:
            return True