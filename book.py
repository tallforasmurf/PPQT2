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
from PyQt5.QtCore import QObject, QCoreApplication,QCryptographicHash
_TR = QCoreApplication.translate
from PyQt5.QtWidgets import QLabel # TODO eliminate when not needed

import utilities
import mainwindow
import metadata
import editdata
import editview
import worddata
import pagedata
import imageview
import dictionaries
import constants as C
import logging
import fonts

class Book(QObject):
    def __init__(self, sequence, the_main ):
        super().__init__(None)
        # Save our mainwindow ref and our unique sequence number
        self.mainwindow = the_main
        self.sequence = sequence
        # Create our dict of activity panel objects, used by the main
        # window when giving us the focus.
        self.panel_dict = mainwindow.PANEL_DICT.copy()
        # Set up a book-unique logging channel
        self.logger = logging.getLogger(name='book_'+str(self.sequence))
        # Create the spellchecker using the global default dictionary.
        # It may be recreated in _init_edit after we have a book path and
        # have possibly read dictionary info from metadata.
        self.dict_tag = dictionaries.get_default_tag()
        self._speller = dictionaries.Speller(self.dict_tag,
            dictionaries.get_dict_path() )
        self.edit_point_size = C.DEFAULT_FONT_SIZE
        self.edit_cursor = (0,0)
        self.bookname = ''
        self.book_folder = ''
        self.book_full_path = ''
        self.md_modified = False # see metadata_modified()
        # Initialize bookmarks, loaded from metadata later. The bookmarks
        # are indexed 1-9 (from control-1 to control-9 keys) but the list
        # has ten entries, entry 0 not being used.
        self.bookmarks = [None, None, None, None, None, None, None, None, None, None]
        #
        # Create the metadata manager and register to read and write the
        # items that are stored at this level: the last-set main dictionary
        # the cursor position at save, the point size at save, the bookmarks,
        # and the hash value of the saved document.
        #
        self.metamgr = metadata.MetaMgr()
        self.metamgr.register(C.MD_MD, self._read_dict, self._save_dict)
        self.metamgr.register(C.MD_CU, self._read_cursor, self._save_cursor)
        self.metamgr.register(C.MD_ES, self._read_size, self._save_size)
        self.metamgr.register(C.MD_BM, self._read_bookmarks, self._save_bookmarks)
        self.metamgr.register(C.MD_DH, self._read_hash, self._save_hash)
        #
        # Create the data model objects. These are private to the book.
        self.editm = editdata.Document(self) # document, to be initialized later
        self.pagem = pagedata.PageData(self) # page data
        self.wordm = worddata.WordData(self) # vocabulary data
        # TODO: notes, footnotes, bookloupe data
        #
        # Create the view objects that display and interact with the data models.
        # These need to be accessible to the main window so are stored in the
        # panel_dict. The edit view is created in _init_edit() after we have
        # loaded a document.
        #
        self.imagev = imageview.ImageDisplay(self) # keep a short reference
        self.panel_dict['Images'] = self.imagev
        # TODO other view objects, labels for placeholders
        self.panel_dict['Notes'] = QLabel(str(sequence)+'Notes') # notesview.NotesPanel(self)
        self.panel_dict['Find' ] = QLabel(str(sequence)+'Find') # findeview.FindPanel(self)
        self.panel_dict['Pages'] = QLabel(str(sequence)+'Pages') # pageview.PagePanel(self)
        self.panel_dict['Words'] = QLabel(str(sequence)+'Words') # wordview.WordPanel(self)
        self.panel_dict['Chars'] = QLabel(str(sequence)+'Chars') # charview.CharPanel(self)
        self.panel_dict['Fnote'] = QLabel(str(sequence)+'Fnote') # fnoteview.FnotePanel(self)
        self.panel_dict['Loupe'] = QLabel(str(sequence)+'Loupe') # loupeview.LoupePanel(self)
        self.panel_dict['tab_list'] = [
        (tabname, self.panel_dict[tabname]) for tabname in self.panel_dict['default']
            ]

        # End of __init__ however initialization continues here:

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # One of the following four methods is called by the main window after it
    # instantiates this object, to load it with data. Here is where Book
    # initialization is completed.

    # FILE>NEW: initialize for a new empty document. Pretty much everything
    # is set up for New already because all the models initialize to empty.
    # Sequence value is assigned by the main window when the Book is created,
    # use it here to make a unique "Untitled" value. Document status of
    # not-modified, because there's point in making user save an empty new
    # document.

    def new_empty(self):
        self.book_name = 'Untitled-{0}'.format(self.sequence)
        self.book_folder = ''
        self.book_full_path = ''
        self.editm.setModified(False)
        self.editv = editview.EditView(self, self.mainwindow.focus_me)

    # KNOWN BOOK: called to load a book that has a .meta file. Given:
    #   doc_stream  a FileBasedTextStream with the document text
    #   meta_stream a text stream (file or memory-based) with the metadata
    # Set modified status to False because we just loaded everything.

    def old_book(self, doc_stream, meta_stream):
        self.book_name = doc_stream.basename()
        self.book_folder = doc_stream.folderpath()
        self.book_full_path = doc_stream.fullpath()
        self.editm.setPlainText(doc_stream.readAll())
        self.metamgr.load_meta(meta_stream)
        self.editm.setModified(False)
        self.editv = editview.EditView(self, lambda: self.mainwindow.focus_me(self.sequence) )
        self.editv.set_cursor(self.editv.make_cursor(self.edit_cursor[0],self.edit_cursor[1]))
        if 0 < self.pagem.page_count():
            # we have a book with page info, wake up the image viewer
            self.imagev.set_path(book_folder)
            self.editv.Editor.cursorPositionChanged.connect(self.imagev.cursor_move)

    # FILE>OPEN a document that lacks an accompanying .meta file.
    #
    #   doc_stream  a FileBasedTextStream with the document data
    #   meta_stream None, or a memory stream derived from a Guiguts .bin file
    #   good_stream None, or a text stream of a good_words file
    #   bad_stream  None, or a text stream of a bad_words file
    # Set up as modified because the new metadata needs saving.
    # Create page metadata by scanning the text for page separators.
    # Default the cursor position to zero, in absence of metadata.

    def new_book(self, doc_stream, meta_stream, good_stream, bad_stream) :
        self.book_name = doc_stream.basename()
        self.book_folder = doc_stream.folderpath()
        self.book_full_path = doc_stream.fullpath()
        self.editm.setPlainText(doc_stream.readAll())
        self.editm.setModified(True)
        if meta_stream :
            # Process the Guiguts metadata for page info            
            self.metamgr.load_meta(meta_stream)
        else :
            # develop page info from separator lines in text
            self.pagem.scan_pages()
        # If there are good_words and bad_words streams, use the worddata
        # metadata readers to accept them.
        if good_stream:
            self.wordm.good_read(good_stream,C.MD_GW,'0','')
        if bad_stream :
            self.wordm.bad_read(bad_stream,C.MD_BW,'0','')
        # Create the visible editor, leaving cursor at 0.
        self.editv = editview.EditView(self, lambda: self.mainwindow.focus_me(self.sequence) )
        if 0 < self.pagem.page_count():
            # we have a book with page info, wake up the image viewer
            self.imagev.set_path(self.book_folder)
            self.editv.Editor.cursorPositionChanged.connect(self.imagev.cursor_move)

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # The only save function: called from main window with two streams
    # to be written. Note that we ASSUME any save will include a .meta
    # file. This is not a general purpose editor, if you use it for some
    # scratch file, you will get scratch.meta as well.
    def save_book(self, doc_stream, meta_stream):
        doc_stream << self.editm.toPlainText()
        self.metamgr.write_meta(meta_stream)
        self.editm.setModified(False)
        self.md_modified = False

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # The following functions are registered to the metatdata manager to read
    # and write metadata items that are kept at the Book level. We load the
    # book data into the editor before reading the metadata. This makes it
    # possible to establish the cursor value and bookmarks. (If the document
    # had not been read, the editor would not be able to set a cursor
    # position above zero.)
    #
    # This means that the v.1 {{ENCODING enc}} section was pointless; the
    # encoding of the file cannot be learned from that. So that old section is
    # ignored on input and not written on output.

    # Process the {{BOOKMARKS}} section. Each line is "x p a" where x is the
    # index in 1-9, and p/a are the cursor position and anchor. Note the
    # earliest versions of PPQT didn't save the anchor value, so watch for
    # that and duplicate the position.

    # refactor testing acceptable cursor position, for cpos an int
    def _test_cpos(self, cpos):
        return cpos >= 0 and cpos < self.editm.characterCount()

    def _read_bookmarks(self, stream, sentinel, v, parm):
        for line in metadata.read_to(stream,sentinel) :
            try:
                parts = line.split()
                if len(parts) == 2 : # old metadata file
                    parts.append(parts[1]) # duplicate pos as anchor
                [i,p,a] = parts # exception if not 3 items
                ix = int(i) # exception if not int
                if ix < 1 or ix > 9 :
                    raise ValueError
                cpos = int(p)
                canc = int(a)
                if self._test_cpos(cpos) and self._test_cpos(canc) :
                    self.bookmarks[ix] = self.editv.make_cursor(cpos,canc)
                else :
                    raise ValueError
            except:
                self.logger.error('Ignoring invalid bookmark position "'+line+'"')
    def _save_bookmarks(self, stream, section):
        stream << metadata.open_line(section)
        for ix in range(1,10):
            if self.bookmarks[ix] is not None:
                stream << '{0} {1} {2}\n'.format(
                    ix, self.bookmarks[ix].position(), self.bookmarks[ix].anchor() )
        stream << metadata.close_line(section)

    # Process {{CURSOR position anchor}}. Be suspicious of the coding as the
    # user might have (mis)edited it.

    def _read_cursor(self, stream, sentinel, v, parm):
        try:
            [p,a] = parm.split() # exception if wrong number of values
            cpos = int(p) # exception if not integer
            canc = int(a)
            if self._test_cpos(cpos) and self._test_cpos(canc) :
                self.edit_cursor = (cpos, canc)
            else :
                raise ValueError
        except:
            self.logger.error('Ignoring invalid cursor position "'+parm+'"')
    def _save_cursor(self, stream, section):
        parm = '{0} {1}'.format(self.edit_cursor[0],self.edit_cursor[1])
        stream << metadata.open_line(section,parm)

    # Process {{MAINDICT <dictag>}}. Look for dictag in the available tags
    # starting with the book path (if we are reading metadata, a book path
    # exists). If the tag exists at some level, make a new speller using it.

    def _read_dict(self, stream, sentinel, v, parm) :
        tag_dict = dictionaries.get_tag_list(self.book_folder)
        if parm in tag_dict :
            self.dict_tag = parm
            self._speller = dictionaries.Speller(parm,tag_dict[parm])
        else:
            self.logger.error(
                'Unable to open dictionary {0}, using default {1}'.format(parm,self.dict_tag))
    def _save_dict(self, stream, section):
        stream << metadata.open_line(section, self.dict_tag)

    # Process {{EDITSIZE int}}, new in v.2.
    def _read_size(self, stream, sentinel, v, parm) :
        try:
            s = int(parm)
            if s >= fonts.POINT_SIZE_MINIMUM and s <= fonts.POINT_SIZE_MAXIMUM :
                self.edit_point_size = s
                self.editv.font_change(True) # fake a font-change signal
            else :
                raise ValueError
        except:
            self.logger.error(
                'Ignoring invalid edit point size {0}'.format(parm) )
    def _save_size(self, stream, section) :
        stream << metadata.open_line(section, str(self.edit_point_size))

    # Process {{DOCHASH hashstring}}. The purpose of this is to detect when
    # by some error, the metadata file is not the same level as the text file,
    # for example if one was restored from backup and the other not.
    def _signature(self):
        # Calculate a hash signature of the current document and return
        # it as a string like "b'\\xde\\xad\\xbe\\xef...'"
        cuisineart = QCryptographicHash(QCryptographicHash.Sha1)
        cuisineart.reset()
        cuisineart.addData( self.editm.full_text() )
        return bytes(cuisineart.result()).__repr__()
    # Note in v.1 and Python 2.7, the result of __repr__ on a byte array was
    # a char string like '\xde\xad\xbe\xef...' but in v.2 and Python 3, the
    # result is b'\\xde\\xad\\xbe\\xef...' which does not compare equal
    # despite having the same bytes. So if reading a v.1 meta file, coerce it
    # to bytes. Since the user could have mucked with it, allow for errors.
    def _read_hash(self, stream, sentinel, v, parm) :
        if v < '2' :
            try:
                parm = bytes(parm,'Latin-1','ignore').__repr__()
            except :
                self.logger.error(
                'Could not convert dochash to bytes, ignoring dochash' )
                return
        # If the saved and current hashes now disagree, it is because the metadata
        # was saved along with a different book or version. Warn the user.
        if self._signature() != parm :
            utilities.warning_msg(
                text= _TR(
                    'Book object',
                    'Document and .meta files do not match!',
                    'Warning during File:Open'
                    ),
                info= _TR(
                    'Book object',
                    'Page breaks and other metadata will be wrong! Strongly recommend you not edit or save this book.',
                    'Warning during File:Open'
                    )
            )

    def _save_hash(self, stream, section) :
        # Calculate an SHA-1 hash over the current document and write it.
        stream << metadata.open_line(section, self._signature())

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # The following methods assist the editview to implement its context menu.
    #
    # User requests change of scanno file: Present a file dialog to select
    # one. The mechanics are in the utilities module. When that works, pass
    # the stream to the word-model to store.

    def ask_scanno_file(self):
        global _TR
        caption = _TR("EditViewWidget",
                "Choose a file of OCR error words to mark",
                "File dialog caption")
        scanno_stream = utilities.ask_existing_file(
            caption, self.editv, self.book_folder, None )
        if scanno_stream is not None :
            self.wordm.scanno_read(scanno_stream,C.MD_SC,0,None)
            return True
        return False

    # User requests change of dictionary: Get the list of available
    # tags and present them in a dialog. Contrary to the name, tag_list
    # is actually a dict, so pull out its keys for the dialog.
    def ask_dictionary(self) :
        global _TR
        tag_list = dictionaries.get_tag_list(self.book_folder)
        if 0<len(tag_list):
            # dictionaries knows about at least one tag, display it/them
            item_list = sorted(list(tag_list.keys()))
            current = 0
            if self.dict_tag in item_list:
                current = item_list.index(self.dict_tag)
            title = _TR("EditViewWidget",
                    "Primary dictionary for this book",
                    "Dictionary pop-up list title")
            explanation = _TR("EditViewWidget",
                    "Select the best dictionary for spell-checking this book",
                    "Dictionary pop-up list info")
            new_tag = utilities.choose_from_list(
                title, explanation,item_list, parent=self.editv, current=current)
            if (new_tag is not None) and (new_tag != self.dict_tag) :
                # a choice was made and it's different from before
                self.dict_tag = new_tag
                self._speller = dictionaries.Speller(
                    new_tag, tag_list[new_tag] )
                self.wordm.recheck_spelling(self._speller)
                return True
        else:
            # no known dictionaries, probably the Extras have not been
            # configured -- tell user.
            utilities.warning_msg(
                text= _TR("EditViewWidget",
                          "No dictionaries found",
                          "Dictionary request warning"),
                info= _TR("EditViewWidget",
                          "Perhaps the 'extras' folder is not defined?'",
                          "Dictionary request info")
                )
        return False

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # The following methods provide access to book info for other modules.

    # give access to the book name
    def get_book_name(self):
        return self.book_name
    # give access to the book folder path
    def get_book_folder(self):
        return self.book_folder
    # give access to the book canonical path
    def get_book_full_path(self):
        return self.book_full_path
    # give access to the panel dict
    def get_panel_dict(self):
        return self.panel_dict
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
    # give access to the Edit widget
    def get_edit_view(self):
        return self.editv
    # give access to the page data model
    def get_page_model(self):
        return self.pagem
    # give access to the spellcheck object
    def get_speller(self):
        return self._speller
    # give access to the word data model
    def get_word_model(self):
        return self.wordm
    # Note when metadata changes.
    def metadata_modified(self):
        self.md_modified = True
    # Answer the question, is a save needed?
    def get_save_needed(self):
        return self.md_modified or self.editm.isModified()
