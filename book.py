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
                          book.py

Defines a class for the Book object, which creates and maintains
all data that is unique to one book (edited document). This is an
astonishing amount of stuff that, in V1, was distributed throughout
the app as globals, specifically:

* paths to the book file, meta file, and images folder
* the current main (default) spell-check dictionary
* the current scannos file
* whether the editor should hilite scannos or spelling
* good-words, bad-words, the vocabulary and character censii
* the document itself and an editor on it
* the list of recent Find and Replace strings
...and etc

The book keeps a reference to the main window from which it
gets things like the list of available spelling dictionaries,
and the paths to them.

The Book instantiates the objects that hold and display all this
data, organized as *data and *view objects. When the keyboard focus
enters a book editview, the main window fetches all the other *view
objects and installs them in the relevant panels it displays.

Naming convention: xxxxm is a model, e.g. editm = editdata.Document
and xxxxxv is a view, e.g. wordv = wordview.WordPanel

provide document ref
provide metamanager ref
provide spellcheck ref

'''
from PyQt5.QtCore import QObject
import metadata
import editdata
import editview
import worddata
import spellcheck

class Book(QObject):
    def __init__(self, main_window): #TODO: API?
        super().__init__(main_window)
        #
        # Create the metadata manager
        #
        self.metamgr = metadata.MetaMgr()
        #
        # Create the objects that hold the document
        #
        self.editm = editdata.Document(self)
        # TODO self.editv = editview.Editor(self)
        # TODO: connect focus-in signal of editv to what?
        #
        # Create the spellchecker
        #
        # TODO from the main window get the list of available dicts
        #
        self.dict_paths = []
        self.speller = spellcheck.Speller(self)
        #
        # Create the objects that hold and display words data
        #
        self.wordm = worddata.WordData(self)
        # self.wordv = wordview.WordPanel(self)
        # TODO other init

    # give access to the Document object
    def get_edit_model(self):
        return self.editm
    # give access to the metadata manager
    def get_meta_manager(self):
        return self.metamgr
    # give access to the spellcheck object
    def get_speller(self):
        return self.speller