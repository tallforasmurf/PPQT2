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
* user-set "bookmark" locations 0-9
* the collection of "facts" about the book, author, title etc.
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

One Book is created from the main window (mainwindow.py) on the File>New
and File>Open menu actions. The main window keeps track of all books and
handles switching the focus between them.

Naming convention: xxxxm is a model, e.g. editm = editdata.Document and
xxxxxv is a view, e.g. wordv = wordview.WordPanel

'''
from PyQt6.QtCore import QObject, QCoreApplication,QCryptographicHash
_TR = QCoreApplication.translate

import utilities
import paths
import dictionaries
import constants as C
import fonts
import mainwindow
import metadata
import chardata
import charview
import editdata
import editview
import findview
import fnotdata
import fnotview
import imageview
#import loupeview
import noteview
import pagedata
import pageview
import worddata
import wordview
import logging

class Book(QObject):
    def __init__(self, sequence, the_main ):
        super().__init__(None)
        '''
        Save a reference to the mainwindow and our unique sequence number
        '''
        self.mainwindow = the_main
        self.sequence = sequence
        '''
        Set up a book-unique logging channel
        '''
        self.logger = logging.getLogger(name='book_'+str(self.sequence))
        '''
        Create the spellchecker based on the global default dictionary. It
        may be recreated when we have a book path and/or read a preferred
        dict tag from metadata.
        '''
        self.dict_tag = dictionaries.get_default_tag()
        self._speller = dictionaries.Speller(self.dict_tag,
            paths.get_dicts_path() )
        '''
        Connect to the paths signal so we find out about a change in the
        dicts path.
        '''
        paths.notify_me(self.path_change_slot)
        '''
        Initialize slots for info about our book. They are filled in when
        the mainwindow calls new_empty(), old_book(), or new_book() below.
        '''
        self.edit_point_size = C.DEFAULT_FONT_SIZE
        self.edit_cursor = (0,0)
        self.book_name = ''
        self.book_folder = ''
        self.book_full_path = ''
        self.last_find_button_path = ''
        '''
        Initialize the metadata-modified flag, see metadata_modified()
        '''
        self.md_modified = 0
        '''
        Initialize bookmarks, loaded from metadata later. The bookmarks are
        indexed 1-9 (from control-1 to control-9 keys) but the list has ten
        entries, entry 0 not being used.
        '''
        self.bookmarks = [None, None, None, None, None, None, None, None, None, None]
        '''
        Initialize the book-facts dict in case none is read from metadata.
        '''
        self.book_facts = {
            "Title" : "?",
            "Author" : "?",
            "Publication date" : "1???",
            "Language" : "English" }
        '''
        Create the metadata manager (explained at length in metadata.py).
        Then register to read and write the metadata sections that are stored
        at this level: the last-set main dictionary, the cursor position at
        save, the edit point size at save, the bookmarks, the hash value of
        the saved document, and the book_facts dictionary.
        '''
        self.metamgr = metadata.MetaMgr()
        self.metamgr.register(C.MD_MD, self._read_dict, self._save_dict)
        self.metamgr.register(C.MD_CU, self._read_cursor, self._save_cursor)
        self.metamgr.register(C.MD_ES, self._read_size, self._save_size)
        self.metamgr.register(C.MD_BM, self._read_bookmarks, self._save_bookmarks)
        self.metamgr.register(C.MD_DH, self._read_hash, self._save_hash)
        self.metamgr.register(C.MD_BI, self._read_facts, self._save_facts)
        '''
        Create the data model objects. These are private to the book.
        '''
        self.editm = editdata.Document(self) # document, to be initialized later
        self.pagem = pagedata.PageData(self) # page data
        self.charm = chardata.CharData(self) # character data
        self.wordm = worddata.WordData(self) # vocabulary data
        self.fnotm = fnotdata.FnoteData(self) # footnote data
        '''
        Create our dict of activity panel objects, used by the main window
        when giving this book the focus. See mainwindow.py for details.
        '''
        self.panel_dict = mainwindow.PANEL_DICT.copy()
        '''
        Create the view objects that display and interact with the data
        models. These need to be accessed by the main window for the focus_me
        operation, as the book gets and loses focus, so they are stored in
        the panel_dict.
        '''
        self.editv = editview.EditView(self, lambda: self.mainwindow.focus_me(self.sequence) )
        self.imagev = imageview.ImageDisplay(self) # keep a short reference
        self.panel_dict['Images'] = self.imagev
        self.panel_dict['Notes'] = noteview.NotesPanel(self)
        self.panel_dict['Find' ] = findview.FindPanel(self)
        self.panel_dict['Chars'] = charview.CharView(self)
        self.panel_dict['Words'] = wordview.WordPanel(self) # wordview.WordPanel(self)
        self.panel_dict['Pages'] = pageview.PagePanel(self) # pageview.PagePanel(self)
        self.panel_dict['Fnote'] = fnotview.FnotePanel(self) # fnotview.FnotePanel(self)
        #self.panel_dict['Loupe'] = loupeview.LoupeView(self)
        self.panel_dict['tab_list'] = [
        (tabname, self.panel_dict[tabname]) for tabname in self.panel_dict['default']
            ]

        '''
        End of __init__(), however initialization continues here:
        '''

    '''
    One of the following three methods is called by the main window after
    it instantiates this object, to load it with data. Here is where Book
    initialization is completed.

    FILE>NEW: initialize for a new empty document. Pretty much everything is
    set up for New already, because all the data models initialize to empty.
    The sequence value is assigned by the main window when the Book is
    created; use it here to make a unique "Untitled" value. Document status
    in the edit model is left not-modified, because there's no point in
    making the user save an empty new document.
    '''
    def new_empty(self):
        self.book_name = 'Untitled-{0}'.format(self.sequence)
        self.editv.book_renamed(self.book_name)
        self.book_folder = ''
        self.book_full_path = ''
        self.editm.setModified(False)
    '''
    KNOWN BOOK: called to load a book that has previously been saved by
    this program, and thus has a .meta file. Input is
    
    * doc_stream, a FileBasedTextStream with the document text
    
    * meta_stream, a text stream (file or memory-based) with the metadata
    
    Record the various file name items. Load the edit model from the
    stream. Create the edit view before reading the metadata, because if it
    has a point-size, we need somewhere to set it.
    
    Set modified status to False because we just loaded everything.
    
    n.b. this can also be called with a book that is the output of a 
    Translator, created by translating from PP format to e.g. HTML.
    '''
    def old_book(self, doc_stream, meta_stream):
        self.book_name = doc_stream.filename()
        self.editv.book_renamed(self.book_name)
        self.book_folder = doc_stream.folderpath()
        self.book_full_path = doc_stream.fullpath()
        self.editm.setPlainText(doc_stream.readAll())
        meta_message = self.metamgr.load_meta(meta_stream)
        if meta_message :
            # Problem with json decoding of metadata file, warn the user
            m1 = _TR('error opening book',
                     'Error decoding the metadata file, metadata lost')
            m2 = _TR('error opening book, details',
                     'Recommend you close the book without saving and investigate the following:')
            utilities.warning_msg( m1, m2+'\n'+meta_message, parent= self.mainwindow )
        self.hook_images()
        # Everything loaded from a file, clear any mod status
        self.md_modified = 0
        self.editm.setModified(False)
        # Set the edit cursor to a saved location
        tc = self.editv.make_cursor(self.edit_cursor[0],self.edit_cursor[1])
        self.editv.center_this( tc )
    '''
    FILE>OPEN of a document that lacks an accompanying .meta file. Input:
    
    * doc_stream: a FileBasedTextStream with the document data
    
    * good_stream: None, or a text stream of a good_words file
    
    * bad_stream: None, or a text stream of a bad_words file
    
    Create page-boundary metadata by scanning the text for page separators.
    Default the cursor position to zero. Make a new speller dictionary just
    in the unlikely case that this new book folder has a local copy of the
    same dictionary tag as the global default we already set up. Set up as
    modified because all the new metadata needs saving.

    Finally, check to see if the loaded document has any Unicode
    Replacement characters. If so, it is very likely a Latin-1 doc loaded
    as UTF-8. We could try to fix that, e.g. by rewinding the doc_stream
    and re-reading it with a different codec, but (a) at this point we
    don't know what codec was used; (b) maybe it's not Latin-1 either, maybe
    it's windows codepage crap; (c) the same problem likely affects the
    good- and bad-words files too. So just warn the user.
    
    '''
    def new_book(self, doc_stream, good_stream, bad_stream) :
        self.book_name = doc_stream.filename()
        self.editv.book_renamed(self.book_name)
        self.book_folder = doc_stream.folderpath()
        self.book_full_path = doc_stream.fullpath()
        self.editm.setPlainText(doc_stream.readAll())
        self.editm.setModified(True)
        # If there are good_words and bad_words streams, call the worddata
        # metadata reader functions directly to accept them.
        if good_stream:
            self.wordm.good_file(good_stream)
        if bad_stream :
            self.wordm.bad_file(bad_stream)
        self.pagem.scan_pages() # develop page metadata if possible
        self.hook_images() # set up display of scan images if possible
        self.editv.set_cursor(self.editv.make_cursor(0,0)) # cursor to top
        self._speller = dictionaries.Speller( self.dict_tag, self.book_folder )
        '''
        Check the loaded text for \ufffd "replacement" chars indicating
        mis-decoding of the file. We do this by calling the edit model to do
        a Find for the replacement symbol. The returned value is an edit cursor
        which .isNull() when nothing was found.
        '''
        findtc = self.editm.find( C.UNICODE_REPL, position=0 )
        if not findtc.isNull() :
            m1 = _TR( 'File:Open finds bad encoding',
                      'This document contains at least one Unicode Replacement Character!'
                      )
            m2 = _TR( 'File: Open finds bad encoding',
'''This indicates it was read with the wrong encoding!
See the Help file under "File Encodings and File Names"
The first bad character is at ''',
                        'integer follows this') + str( findtc.position() )
            utilities.warning_msg( m1, m2, self.mainwindow )


    '''
    A wee bit of code factored out of new_book and old_book so the
    translator can use it. Activate the page image viewer if the
    book has page images and page boundary metadata.
    '''
    def hook_images(self) :
        if self.pagem.active():
            # we have a book with page info, wake up the image viewer
            self.imagev.set_path(self.book_folder)
            self.editv.Editor.cursorPositionChanged.connect(self.imagev.cursor_move)

    '''
    Give the book a new name and/or file path. Input is a FileBasedTextStream
    from which we can get the file name and path info. Set the book modified.
    
    This is called from the main window File Save-As action. It will be
    followed by a call to save_book().
    '''
    def rename_book(self, doc_stream):
        self.book_name = doc_stream.filename()
        self.book_folder = doc_stream.folderpath()
        self.book_full_path = doc_stream.fullpath()
        self.editv.book_renamed(self.book_name)
        self.md_modified = True

    '''
    
    The only save function: called from main window with two streams to be
    written. Note that we ASSUME any save will include a .meta file. (PPQT
    is not a general purpose editor, if you use it for some scratch file,
    you will get scratch.meta as well.)
    
    After writing the data into the streams, we call the flush() method. This
    returns False if the operation is unsuccessful, presumably due to an I/O
    error of some type. flush() is the main operation, in fact the close()
    method ignores errors on flush and clears error status. The files will be
    closed when mainwindow._save() exits.
    '''
    def save_book(self, doc_stream, meta_stream):
        doc_stream << self.editm.toPlainText()
        output_ok = doc_stream.flush()
        if not output_ok :
            doc_stream.show_error( 'saving', self.mainwindow )
        else :
            self.metamgr.write_meta(meta_stream)
            output_ok = meta_stream.flush()
            if not output_ok :
                meta_stream.show_error( 'saving metadata', self.mainwindow )
        if output_ok :
            self.editm.setModified(False)
            self.md_modified = False
            self.editv.mod_change_signal(False)
        return output_ok

    '''
    The following functions are registered to the metatdata manager to read
    and write metadata items that are kept at the Book level. We load the
    book data into the editor before reading the metadata. This makes it
    possible to establish the cursor value and bookmarks. (If the document
    had not been read, the editor would not be able to set a cursor
    position other than zero.)

    refactor testing for acceptable cursor position, for cpos an int
    '''
    def _test_cpos(self, cpos):
        return cpos >= 0 and cpos < self.editm.characterCount()
    '''
    Process the {"BOOKMARKS": [[x,p,a],...] } section. The save value is a
    list of lists [x,p,a] where x is the index in 1-9, and p, a are the
    cursor position and anchor. (In other words, a bookmark can include a
    non-empty selection.)
    
    As with all metadata, we guard against user tinkering with the .meta
    file, by suspecting everything.
    '''
    def _read_bookmarks(self, sentinel, value, version):
        try:
            for [x,p,a] in value : # unpacking error if not [ [x,p,a],...]
                try:
                    ix = int(x) # exception if not numeric
                    if ix < 1 or ix > 9 :
                        raise ValueError
                    cpos = int(p) # further exceptions if not numerics
                    canc = int(a)
                    if self._test_cpos(cpos) and self._test_cpos(canc) :
                        self.bookmarks[ix] = self.editv.make_cursor(cpos,canc)
                    else :
                        raise ValueError
                except:
                    self.logger.error( 'Ignoring invalid bookmark metadata {}'.format([x,p,a]) )
        except: # unpacking error only
            self.logger.error( 'BOOKMARKS metadata not valid, some bookmarks ignored.' )

    def _save_bookmarks(self, section):
        ret = [ ]
        for ix in range(1,10):
            if self.bookmarks[ix] is not None:
                ret.append([ix, self.bookmarks[ix].position(), self.bookmarks[ix].anchor()])
        return ret

    '''
    Process {"CURSOR: [position, anchor]}. Be suspicious of the coding.
    self.edit_cursor was initialized to (0,0), so just leave it if problems.
    '''
    def _read_cursor(self, sentinel, value, version):
        try:
            [p,a] = value # exception if wrong number of values
            cpos = int(p) # exceptions if not integer
            canc = int(a)
            if self._test_cpos(cpos) and self._test_cpos(canc) :
                self.edit_cursor = (cpos, canc)
            else :
                raise ValueError
        except:
            self.logger.error('Ignoring invalid cursor position {}'.format(value))

    def _save_cursor(self, section):
        return self.editv.get_cursor_val() # json converts tuple to list

    '''
    Process {"MAINDICT": <dictag>}. Look for dictag in the available tags
    starting with the book path (if we are reading metadata, a book path
    exists). If the tag exists at some level, make a new speller using it.
    The tag might not be available, either because the user mistyped it,
    or because the dictionary path isn't set right, or other reasons.
    In that case log an error and stay with the current default.
    '''
    def _read_dict(self, sentinel, value, version) :
        tag_dict = dictionaries.get_tag_list(self.book_folder)
        try:
            dict_path = tag_dict[value] # index error if value not a known tag
            speller = dictionaries.Speller(value,dict_path)
            if not speller.is_valid() :
                raise ValueError
            # we have a valid dictionary tag and spellcheck object
            self.dict_tag = value
            self._speller = speller
        except:
            self.logger.error(
                'Unable to open default dictionary {0}, using default {1}'.format(value,self.dict_tag))
    def _save_dict(self, section):
        return self.dict_tag

    '''
    Process {"EDITSIZE" : int}, current edit point size (new in v.2.)
    '''
    def _read_size(self, sentinel, value, version) :
        try:
            s = int(value) # error if not numeric
            if s >= fonts.POINT_SIZE_MINIMUM and s <= fonts.POINT_SIZE_MAXIMUM :
                self.edit_point_size = s
                self.editv.font_change(True) # fake a font-change signal
            else :
                raise ValueError
        except:
            self.logger.error(
                'Ignoring invalid edit point size {0}'.format(value) )

    def _save_size(self, section) :
        return self.edit_point_size

    '''
    Process {"DOCHASH": b'hash_string_in_hex'}. The purpose of storing a hash
    of the document text in the metadata file is to detect when by some
    error, the metadata file relates to a different version of the book, as
    for example if one was restored from backup and the other not.
    
    Calculate a hash signature of the current document and return
    it as a string like "b'\\xde\\xad\\xbe\\xef...'" 
    '''
    def _signature(self):
        cuisineart = QCryptographicHash(QCryptographicHash.Algorithm.Sha1)
        cuisineart.reset()
        text = self.editm.full_text()
        cuisineart.addData( text.encode() )
        return bytes(cuisineart.result())
    '''
    Compare what should be a byte-string to the hash of the book text that we
    have already loaded.
    '''
    def _read_hash(self, sentinel, value, version) :
        if self._signature() != value :
            self.logger.error('Doc hash in metadata does not match book contents')
            utilities.warning_msg(
                text= _TR(
                    'Book object',
                    'Document and .meta files do not match!',
                    'Warning during File:Open'
                    ),
                info= _TR(
                    'Book object',
                    'Page breaks and other metadata may be wrong! Strongly recommend you not edit or save this book.',
                    'Warning during File:Open'
                    ),
                parent= self.mainwindow
            )
    '''
    Calculate an SHA-1 hash over the current document and write it to the
    metadata. The old SHA1 hash is perfectly adequate for this, security is
    not the issue.
    '''
    def _save_hash(self, section) :
        return self._signature()
    '''
    Process {"BOOKINFO": { "Title":"Whatever", etc... } } The facts about the
    book are stored as a dict with user-defined keys and values, see
    edit_book_facts(). On save, just write the existing dict.
    '''
    def _save_facts(self, section) :
        return self.book_facts
    '''
    On load, take some trouble to make sure it is a dict with only string
    keys and values.
    '''
    def _read_facts(self, sentinel, value, version) :
        if type(value) == type(self.book_facts) :
            self.book_facts = dict()
            for (key, arg) in value.items() :
                if type(key) == type('x') and type(arg) == type(key) :
                    self.book_facts[key] = arg
                else :
                    self.logger.error( 'Keys and values in BOOKINFO must be strings,' )
                    self.logger.error( '  Ignoring {} : {}'.format(key,arg) )
        else :
            self.logger.err( 'BOOKINFO is not a dictionary, ignoring it')

    '''
    The following methods assist the editview to implement its context menu.
    
    TODO: why then aren't they in editview.py?
    
    User requests change of scanno file. Use the utilities module to present
    a file dialog to select one. When that works, pass the stream to the
    word-model to store.
    '''
    def ask_scanno_file(self):
        caption = _TR("EditViewWidget",
                "Choose a file of OCR error words to mark",
                "File dialog caption")
        scanno_stream = utilities.ask_existing_file(
            caption, self.editv, self.book_folder, None )
        if scanno_stream is not None :
            self.wordm.scanno_file(scanno_stream)
            return True
        return False
    '''
    User requests change of dictionary: Get the list of available tags
    and present them in a dialog. Contrary to the name, tag_list is actually
    a dict, so pull out its keys for the dialog.
    '''
    def ask_dictionary(self) :
        tag_list = dictionaries.get_tag_list(self.book_folder)
        if 0<len(tag_list):
            '''
            dictionaries knows about at least one tag, display it/them
            with the current tag, if any, highlighted.
            '''
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
            new_tag = utilities.choose_from_list(
                title, explanation,item_list, parent=self.editv, current=current)
            if (new_tag is not None) and (new_tag != self.dict_tag) :
                '''
                A choice was made and it's different from before. Create a
                new Speller based on the chosen tag. Then force the vocabulary
                model to recheck the spelling of the whole book.
                '''
                self.dict_tag = new_tag
                self._speller = dictionaries.Speller(
                    new_tag, tag_list[new_tag] )
                self.wordm.recheck_spelling(self._speller)
                return True
        else:
            '''
            No known available dictionary tags. Probably the Extras have
            not been configured -- tell user.
            '''
            utilities.warning_msg(
                text= _TR("EditViewWidget",
                          "No dictionaries found",
                          "Dictionary request warning"),
                info= _TR("EditViewWidget",
                          "Perhaps the 'extras' folder is not defined?'",
                          "Dictionary request info")
                )
        return False
    '''
    User requests to edit facts about the book. Present a dialog containing a
    plain text edit primed with what we know about those facts. When edit
    completes, if not cancelled, update our book facts dict.
    '''
    def edit_book_facts(self) :
        starting_text = ''
        for (key, arg) in self.book_facts.items() :
            starting_text += '{} : {}\n'.format(key,arg)
        response = utilities.show_info_dialog(
                _TR("Edit View Book Facts Dialog Title",
'''Enter facts about the book such as Title or Author.\n
Each line must have a key such as Title, a colon, then a value.'''),
                self.editv, starting_text )
        if response : # is not None, there is some text
            self.book_facts = dict() # this changes metadata, no matter what is input
            for line in response.split('\n') :
                if line.strip() : # is not empty,
                    try :
                        '''
                        This raises an exception if the line does not have exactly
                        one colon, resulting in exactly two split parts. Note the
                        format could still be wrong e.g. "  :  " or such but in any
                        case the split parts are strings hence valid dict keys and
                        values even if nonsensical.
                        '''
                        (key, arg) = line.split(':')
                        self.book_facts[key.strip()] = arg.strip()
                    except :
                        utilities.warning_msg(
                            _TR("Edit book-facts dialog warning message",
                                "Each line must have a key, a colon, and a value. Ignoring:"),
                            "'{}'".format(line) )
                # else skip empty line
            self.metadata_modified(True, C.MD_MOD_FLAG)
        # else Cancel - do nothing

    '''
    When the dicts path changes, recreate our speller. A change in dicts path
    might not mean a change in the spell check because we might be getting
    the dict for this book from its own folder. But make the change in case.
    It will show up next time words gets refreshed.
    '''
    def path_change_slot(self, what_path):
        if what_path == 'dicts' :
            self._speller = dictionaries.Speller(
                self.dict_tag, self.book_folder)
    '''
    Note when metadata changes its modified state. Each module that stows
    metadata may have its own bit-flag, so that type of metadata can change
    in either directions, unmodified->modified and (on ^z) or
    modified->unmodified. See constants MD_MOD_*. Currently only Notes uses
    this ability.
    '''
    def metadata_modified(self, state, flag):
        previous = self.md_modified
        self.md_modified |= (state * flag)
        self.md_modified &= 255 - (flag * (not state))
        if previous != self.md_modified:
            self.editv.mod_change_signal(True)
    '''
    Answer the question, is a save needed?
    '''
    def get_save_needed(self):
        return (0 != self.md_modified) or self.editm.isModified()

    '''
    Make one of our panels visible. Just pass the requesting widget
    on to the main window.
    '''
    def make_me_visible(self,widg):
        self.mainwindow.make_tab_visible(widg)

    '''
    The following methods provide access to book info for other modules.

    give access to the book name
    '''
    def get_book_name(self):
        return self.book_name
    ''' give access to the book folder path '''
    def get_book_folder(self):
        return self.book_folder
    ''' give access to the book canonical path '''
    def get_book_full_path(self):
        return self.book_full_path
    '''
    give access to the last find-button load/save path
    If find-buttons have not been specifically saved already, the
    default path is the book path.
    '''
    def get_last_find_button_path(self):
        p = self.book_full_path
        if self.last_find_button_path : # is not null
            p = self.last_find_button_path
        return p
    ''' note a find-button path actually used to return next time '''
    def set_last_find_button_path(self, path):
        self.last_find_button_path = str(path)
    ''' give access to the panel dict '''
    def get_panel_dict(self):
        return self.panel_dict
    ''' give access to the last-set edit font size '''
    def get_font_size(self):
        return self.edit_point_size
    def save_font_size(self, size):
        self.edit_point_size = size
    ''' give access to the metadata manager '''
    def get_meta_manager(self):
        return self.metamgr
    ''' give access to the Document model object '''
    def get_edit_model(self):
        return self.editm
    ''' give access to the Edit widget '''
    def get_edit_view(self):
        return self.editv
    ''' give access to the page data model '''
    def get_page_model(self):
        return self.pagem
    ''' give access to the spellcheck object '''
    def get_speller(self):
        return self._speller
    ''' give access to the char data model '''
    def get_char_model(self):
        return self.charm
    ''' give access to the word data model '''
    def get_word_model(self):
        return self.wordm
    ''' give access to the footnote data model '''
    def get_fnot_model(self):
        return self.fnotm
    ''' give access to the words panel (mostly for test) '''
    def get_word_panel(self):
        return self.panel_dict['Words']
    ''' give access to the Find panel object (test, also editview) '''
    def get_find_panel(self):
        return self.panel_dict['Find']
    ''' give access to the Char panel mostly for test '''
    def get_char_panel(self):
        return self.panel_dict['Chars']
    ''' give access to the Loupe panel mostly for test '''
    #def get_loupe_panel(self):
        #return self.panel_dict['Loupe']
    ''' give access to the page panel mostly for test '''
    def get_page_panel(self):
        return self.panel_dict['Pages']
    ''' give access to the Footnotes panel mostly for test '''
    def get_fnot_panel(self):
        return self.panel_dict['Fnote']
    ''' give access to the book_facts, for translators '''
    def get_book_facts(self):
        return self.book_facts
