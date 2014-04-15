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
* filename of the book
* font size in use in the editor
* user-selected highlight color for scannos
* user-selected highlight method for spellcheck
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

The Book instantiates the objects that hold and display all this data,
organized as *data and *view objects. When the keyboard focus enters a book
editview, the book is notified by a signal; it then asks the main window to
display all the other *view objects and install them in the relevant panels
it displays.

Naming convention: xxxxm is a model, e.g. editm = editdata.Document and
xxxxxv is a view, e.g. wordv = wordview.WordPanel

provide document ref
provide metamanager ref
provide spellcheck ref

'''
from PyQt5.QtCore import QObject, QCoreApplication
_TR = QCoreApplication.translate
from PyQt5.QtCore import QTextStream
import metadata
import editdata
import editview
import worddata
import pagedata
import dictionaries
import constants as C

class Book(QObject):
    def __init__(self, main_window): #TODO: API?
        super().__init__(main_window)
        #
        self.main_window = main_window
        #
        self.edit_point_size = C.DEFAULT_FONT_SIZE
        self.bookname = '' # set during New or load
        self.book_path = ''
        self.image_path = '' # set during load
        # Initialize bookmarks, loaded from metadata later
        self.bookmarks = [None, None, None, None, None, None, None, None, None]
        #
        # Create the metadata manager
        #
        self.metamgr = metadata.MetaMgr()
        # TODO: register to save and load dictionary tag from metadata
        # TODO: register to save and load spellcheck and scanno colors!
        # TODO: register to save and load editor font size
        # TODO: register to save and load editor position cursor
        # TODO: register to save and load bookmarks
        #
        # Create a document, it will be initialized later.
        self.editm = editdata.Document(self)
        #
        # Create the spellchecker using the default dictionary as it is now.
        # It is recreated when (or if) we read a dictionary info in metadata.
        #
        self.dict_tag = dictionaries.get_default_tag()
        self._speller = dictionaries.Speller(
            dictionaries.get_default_tag(),
            dictionaries.get_dict_path() )
        #
        # Create the pagedata model and its clients
        #
        self.pagem = pagedata.PageData(self)
        # self.pagev = pageview.PagePanel(self) TODO
        #
        # Create the objects that hold and display words data
        #
        self.wordm = worddata.WordData(self)
        # self.wordv = wordview.WordPanel(self)
        # TODO other init like images panel

    # The following four methods are called by the main window
    # after it instantiates this object, to load it with data.

    # FILE>NEW: initialize for a new empty document. Pretty much everything
    # is set up for New already because all the models initialize to empty.
    # Sequence argument is maintained by the main window to make a unique
    # "Untitled" value. Set status of un-modified, no point in making user
    # save an empty new document.

    def new_empty(self,sequence):
        self._init_edit(doc_stream=None,
                        book_name='Untitled-{0}'.format(sequence))

    # FILE>OPEN an unknown document, one without metadata of any kind.
    #   doc_stream  a QTextStream with the document data
    #   book_name   filename string
    #   book_path  absolute path to book, where there might
    #       be a folder of pngs, or maybe not.
    # Set up as modified because the new metadata needs saving.
    # Default cursor position to zero, in absence of metadata.

    def new_book(self, doc_stream, book_name, book_path) :
        self._init_edit( doc_stream, book_name, book_path, modified=True )
        self.pagem.scan_pages()
        # TODO init image panel

    # KNOWN BOOK: called to load a book that has a .meta file. Given:
    #   doc_stream  a QTextStream with the document text
    #   meta_stream a QTextStream with the metadata
    #   book_name   filename string
    #   image_path  absolute path string to a folder of pngs, or None
    # Set modified status to False because we just loaded everything.

    def old_book(self,doc_stream, meta_stream, book_name, book_path):
        pass #TODO

    # GG BOOK: called to load a book that has a Guiguts .bin file.
    #   doc_stream  a QTextStream of the document text
    #   bin_stream  a QTextStream of the Guiguts .bin file
    #   book_name   filename string
    #   image_path  absolute path string to a folder of pngs, or None
    # Set modified status to True because all the metadata is new.

    def gg_book(self,doc_stream, bin_stream, book_name, image_path):
        pass #TODO

    # After implementing one of the above operations, initialize the
    # edit document and edit view.
    def _init_edit(self,
                   doc_stream=None,
                   book_name='',
                   book_path=None,
                   modified=False,
                   cursor_pos=0):
        self.book_name = book_name
        self.book_path = book_path
        if doc_stream: # that is, if not File>New
            self.editm.setPlainText(doc_stream.readAll())
        self.editm.setModified(modified)
        self.editv = editview.EditView(self)
        self.editv.show_position(cursor_pos)
        # TODO: connect focus-in signal of editv to what?
        # TODO: create Images view using book-path
        # TODO: create Notes view

    # User requests change of scanno file: Present a file dialog
    # to select one. The mechanics are in main_window. When that
    # works, pass the stream to the word-model to store.
    def ask_scanno_file(self):
        global _TR
        caption = _TR("EditViewWidget",
                "Choose a file of OCR error words to mark",
                "File dialog caption")
        scanno_stream = self.main_window.ask_existing_file(
            caption, self.editv, self.book_path, None )
        if scanno_stream is not None :
            self.wordm.scanno_read(scanno_stream,C.MD_SC,0,None)
            return True
        return False

    # User requests change of dictionary: Get the list of available
    # tags and present them in a dialog. Contrary to the name, tag_list
    # is actually a dict, so pull out its keys for the dialog.
    def ask_dictionary(self) :
        global _TR
        tag_list = dictionaries.get_tag_list(self.book_path)
        item_list = sorted(list(tag_list.keys()))
        current = 0
        if self.dict_tag in item_list:
            current = item_list.index(self.dict_tag)
        title = _TR("EditViewWidget",
                "Primary dictionary for this book",
                "Dictionary pop-up list")
        explanation = _TR("EditViewWidget",
                "Select the best dictionary for spell-checking this book",
                "Dictionary pop-up list")
        new_tag = self.main_window.choose_from_list(
            title, explanation,item_list, parent=self.editv, current=current)
        if (new_tag is not None) and (new_tag != self.dict_tag) :
            # a choice was made and it's different from before
            self.dict_tag = new_tag
            self._speller = dictionaries.Speller(
                new_tag, tag_list[new_tag] )
            self.wordm.recheck_spelling(self._speller)
            return True
        return False

    # give access to the book name
    def get_book_name(self):
        return self.book_name
    # give access to the book path
    def get_book_path(self):
        return self.book_path
    # give access to the last-set edit font size
    def get_font_size(self):
        return self.edit_point_size
    def save_font_size(self, size):
        self.edit_point_size = size
    # give access to the metadata manager
    def get_meta_manager(self):
        return self.metamgr
    # give access to the Document object
    def get_edit_model(self):
        return self.editm
    # give access to the page data model
    def get_page_model(self):
        return self.pagem
    # give access to the spellcheck object
    def get_speller(self):
        return self._speller
    # give access to the word data model
    def get_word_model(self):
        return self.wordm

    # Note when metadata changes and needs save
    # TODO implement
    def metadata_modified(self):
        pass