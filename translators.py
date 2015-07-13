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
            Translators.py

This module contains all the machinery for finding, loading, and invoking
Translators.

In concept a Translator is a module that accepts the text of a document that
is marked up in accord with the DP Formatting Guidelines (possibly extended
as described in the Suggested Workflow document) and returns a new text that
is marked up according to some different convention, for example HTML.

In practice, a Translator is a file of Python code located in the Translators
folder of the Extras folder. It is loaded into Python at startup, and its
name is put in a submenu of the File menu. When the user chooses that menu
action, the Translator is executed according to the API documented below,
producing a new document that is added to the set being edited.

The methods available are:

    build_xlt_menu( mainwindow, menu_handler )

        Called from the Main window at startup. Finds all available
        Translators, loads them, builds a submenu with their names and
        returns it. menu_handler is a reference to a slot (an executable,
        probably a method of the main window) to receive the triggered
        signal of each QAction in the submenu. mainwindow is used as the
        parent argument when presenting an error dialog.

        Each QAction in the submenu is loaded with a data() value that
        is returned to the next function.

    xlt_book( book, xlt_info )

        Called from the Main window when one of the Translators is selected
        from the submenu built above. The book is a Book object from which
        we can get the document text and metadata. xlt_info is whatever
        build_xlt_menu put as the data() of the menu QAction (in fact, an
        index into _XLT_NAMESPACES). When translation is successful, a new
        Book object is returned with the translated contents. If it fails,
        None is returned.

'''

import logging
xlt_logger = logging.getLogger(name='Translator Support')

from PyQt5.QtCore import QCoreApplication
_TR = QCoreApplication.translate

import os
import types
import regex
import json
import paths
import utilities
import xlate_utils as XU
import constants as C

from PyQt5.QtWidgets import (
    QAction,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget
    )

import importlib.machinery

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Set up the Translators sub-menu by looking at all files in the Translators
# folder of the Extras folder. If a file is readable and has the .py suffix,
# attempt to load it into a namespace (this executes its code).
#
# Examine the loaded namespace for a MENU_NAME global which is a string of
# reasonable length. If there is none, the namespace is ignored (and will
# eventually be trashed). Use the MENU_NAME value for as the visible name of
# that action of the submenu.
#
# Verify the namespace contains global functions initialize(), translate(),
# and finalize().
#
# Keep a permanent list of the accepted namespaces as they are loaded. This
# ensures they will not go out of scope and be lost. The "data" stored in a
# submenu action is the index of the matching namespace in this list.

_XLT_NAMESPACES = []

def build_xlt_menu( mainwindow, slot ):

    # Create the submenu but assume it will be empty.
    submenu = QMenu(
        _TR( 'Name of Translators submenu', 'Translators...' ) )
    submenu.setToolTip(
        _TR( 'Translators submenu tooltip',
             'Available Translators in extras/Translators folder' ) )
    submenu.setEnabled( False )

    # Form the path to extras/Translators and try to get a list
    # of all files in it. If it doesn't exist or isn't a dir,
    # we get an error.
    xlt_dir = os.path.join( paths.get_extras_path(), 'Translators' )
    try :
        xlt_files = os.listdir( xlt_dir )
    except Exception as E:
        # this error is logged but not displayed to the user as its
        # only effect is an empty, disabled submenu.
        xlt_logger.error( 'Unable to load any Translator modules')
        xlt_logger.error( str(E) )
        xlt_files = []

    # Check every file in extras/Translators as a possible Translator
    for candidate in xlt_files :

        # Form the full path
        candidate_path = os.path.join( xlt_dir, candidate )

        # Is it readable?
        if not os.access( candidate_path, os.R_OK ) : continue

        # Is it a python source? (Not supporting .pyc just now)
        if not candidate.endswith('.py') : continue

        # Create a loader object - this throws no exceptions
        xlt_logger.info( 'Loading translator module '+candidate )
        xlt_loader = importlib.machinery.SourceFileLoader(
            os.path.splitext( candidate )[0], candidate_path )

        # Try the actual load, which executes the code and can throw
        # exceptions either directly from the loader, or uncaught exceptions
        # thrown by the loaded code. If any exceptions, skip it.
        xlt_logger.info( 'Executing translator into namespace '+candidate )
        try:
            xlt_namespace = xlt_loader.load_module()
        except Exception as E :
            # This error is only logged. It is of interest only to the
            # coder of a Translator wondering why it doesn't appear.
            xlt_logger.error( 'Error loading or executing Translator {}:'.format(candidate) )
            xlt_logger.error( str(E) )
            continue

        # The loaded module should have a MENU_NAME which is a string
        xlt_name = getattr( xlt_namespace, 'MENU_NAME', False )
        if not isinstance(xlt_name, str) :
            xlt_logger.error('Translator {} has no MENU_NAME string'.format(candidate) )
            continue

        # The MENU_NAME should be of reasonable length for a menu item
        if ( len( xlt_name ) > 16 ) or ( len( xlt_name ) < 3 ) :
            xlt_logger.error('Translator {} MENU_NAME too long or too short'.format(candidate) )
            continue

        # The loaded module should offer global functions initialize() and
        # translate(). If not, log an error.

        xlt_fun = getattr( xlt_namespace, 'initialize', False )
        if not isinstance( xlt_fun, types.FunctionType ):
            xlt_logger.error('Translator {} lacks initialize() member'.format(candidate) )
            continue
        xlt_fun = getattr( xlt_namespace, 'translate', False )
        if not isinstance( xlt_fun, types.FunctionType ) :
            xlt_logger.error('Translator {} lacks translate() member'.format(candidate) )
            continue
        xlt_fun = getattr( xlt_namespace, 'finalize', False )
        if not isinstance( xlt_fun, types.FunctionType ) :
            xlt_logger.error('Translator {} lacks finalize() member'.format(candidate) )
            continue
        # OK, we are going to trust it. Save the namespace for use later.
        xlt_index = len( _XLT_NAMESPACES )
        _XLT_NAMESPACES.append( xlt_namespace )

        # Build the menu action with the given name and an optional tooltip.
        action = submenu.addAction( xlt_namespace.MENU_NAME )
        action.setToolTip( getattr( xlt_namespace, 'TOOLTIP', '' ) )

        # Save the index to the namespace as the menu action's data()
        action.setData( xlt_index )

        # Connect the action to the slot provided
        action.triggered.connect( slot )

        # The menu is not going to be empty, so make it enabled
        submenu.setEnabled( True )

    # end for candidate in xlt_files
    return submenu


# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Translate one book using a chosen translator. Translation proceeds in
# six steps.
#
# One, if the selected Translator has an OPTION_DIALOG, build it and display
# it. If the user clicks OK, store the chosen values back into the namespace
# for reference. If CANCEL, return an error.
#
# Two, parse the current document and verify its structure. In the course of
# parsing, build a list of WorkUnit objects to represent the document. If the
# document structure fails the parse, display an error to the user and exit.
#
# Three, call the Translator's initialize() method. We know it exists, but
# we do not know if its signature is appropriate, and anyhow it might have
# a bug, so we call it in a try, and fail the translation on error.
#
# Four, create an iterator over the list of work units and pass it to the
# translate() function to deal with. Again, the signature might be wrong or
# it might throw other exceptions, so guard it in a try.
#
# Five, call the Translator's finalize() method, guarding as necessary.
#
# Six, complete building a new book from the Translator's output data
# and return it.
#

def xlt_book( source_book, xlt_index, main_window ) :
    global WORK_UNITS

    # Get the namespace of the chosen Translator, based on the index saved in
    # the menu action.
    xlt_namespace = _XLT_NAMESPACES[ xlt_index ]
    menu_name = getattr( xlt_namespace, 'MENU_NAME' )
    xlt_logger.info('Translating {}: {}'.format(xlt_index, menu_name) )

    # If it has an option dialog, now is the time to run it. If the
    # user clicks Cancel, we are done.
    dialog_list = getattr( xlt_namespace, 'OPTION_DIALOG', None )
    if dialog_list :
        answer = _run_dialog( dialog_list, menu_name, main_window )
        if not answer :
            xlt_logger.error('User cancelled option dialog for', menu_name)
            return None

    # Perform the document parse. If it succeeds, the list of work units is
    # ready. If it fails, a message has been shown to the user and we exit.
    WORK_UNITS = []
    if not _do_parse( source_book, main_window ) :
        return None

    # Initialize the translator. Create three streams. Collect the book facts
    # dict. Make a page boundary offset list filled with -1. Pass all that to
    # the initialize function to store.

    prolog = utilities.MemoryStream()
    body = utilities.MemoryStream()
    epilog = utilities.MemoryStream()
    book_facts = source_book.get_book_facts()
    source_page_model = source_book.get_page_model()
    page_list = []
    if source_page_model.active() :
        page_list = [ -1 for x in range( source_page_model.page_count() ) ]

    try:
        result = xlt_namespace.initialize( prolog, body, epilog, book_facts, page_list )
    except Exception as e :
        m1 = _TR( 'Translator throws exception',
                  'Unexpected error initializing translator' ) + ' ' + menu_name
        m2 = str(e)
        utilities.warning_msg( m1, m2, main_window )
        xlt_logger.error('Exception from {}.initialize()'.format(menu_name))
        xlt_logger.error(m2)
        return None
    if not result : return None

    # The translator is initialized, so call its translate() passing our
    # event_generator(), below.

    try:
        event_iterator = event_generator( source_page_model, source_book.get_edit_model() )
        result = xlt_namespace.translate( event_iterator )
    except Exception as e :
        m1 = _TR( 'Translator throws exception',
                  'Unexpected error in translate() function of') + ' ' + menu_name
        m2 = str(e)
        utilities.warning_msg( m1, m2, main_window )
        xlt_logger.error('Exception from {}.translate()'.format(menu_name))
        xlt_logger.error(m2)
        return None
    if not result : return None

    # Translating over, finalize it.

    try:
        result = xlt_namespace.finalize( )
    except Exception as e :
        m1 = _TR( 'Translator throws exception',
                  'Unexpected error in finalize() function of') + ' ' + menu_name
        m2 = str(e)
        utilities.warning_msg( m1, m2, main_window )
        xlt_logger.error('Exception from {}.finalize()'.format(menu_name))
        xlt_logger.error(m2)
        return None
    if not result : return None

    # Now put it all together as a Book. First, have mainwindow create a
    # New book and display it.

    new_book = main_window.do_new()

    # Get an edit cursor and use it to insert all the translated text.

    new_edit_view = new_book.get_edit_view()
    qtc = new_edit_view.get_cursor()
    prolog.rewind()
    qtc.insertText( prolog.readAll() )
    body.rewind()
    qtc.insertText( body.readAll() )
    epilog.rewind()
    qtc.insertText( epilog.readAll() )

    # Position the file at the top.

    new_edit_view.go_to_line_number( 1 )

    # Read relevant metadata sections from the source book and install them
    # on the new book. metadata.write_section() gets a specific section.
    # metadata.load_meta() doesn't care if the stream is a single section
    # or a whole file.

    source_mgr = source_book.get_meta_manager()
    new_mgr = new_book.get_meta_manager()

    new_book.book_folder = source_book.book_folder # base folder
    _move_meta( source_mgr, new_mgr, C.MD_BW ) # badwords
    _move_meta( source_mgr, new_mgr, C.MD_FR ) # find memory
    _move_meta( source_mgr, new_mgr, C.MD_FU ) # find userbuttons
    _move_meta( source_mgr, new_mgr, C.MD_GW ) # goodwords
    _move_meta( source_mgr, new_mgr, C.MD_MD ) # main dictionary
    _move_meta( source_mgr, new_mgr, C.MD_NO ) # notes
    if source_page_model.active() and page_list[0] > -1 :
        # It looks as if the translator did update the page offset list. Get
        # the source page metadata and modify it. (Note the original design
        # was to just transfer the old page metadata the way we transfer the
        # other types, above, then use pagedata.set_position() to set the new
        # positions. HOWEVER there is a possibility that the new book is
        # shorter than the old one, in which case pagedata.read_pages() would
        # see some of the (old) positions as invalid, and would discard some
        # of the final rows. So we get the metadata; translate it back to
        # python; modify it in place with the new positions which are
        # presumably all valid for the new book; convert it to json and feed
        # that to the new book. If the translator messed up any of those
        # positions, there will be log messages.
        stream = utilities.MemoryStream()
        source_mgr.write_section( stream, C.MD_PT )
        stream.rewind()
        pdata = json.loads( stream.readAll() )
        plist = pdata['PAGETABLE']
        for j in range( len( plist ) ) :
            plist[j][0] = page_list[j]
        stream = utilities.MemoryStream()
        stream << json.dumps( pdata )
        stream.rewind()
        new_mgr.load_meta( stream )
        new_book.hook_images()


# Get one section's json from the source, and load it into the target.

def _move_meta( from_mgr, to_mgr, section ) :
    stream = utilities.MemoryStream()
    from_mgr.write_section( stream, section )
    stream.rewind()
    to_mgr.load_meta( stream )
    stream.rewind()




# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#
#        option dialog implementation
#
# _run_dialog: Check the validity of OPTION_DIALOG. If it is not a list
# of Dialog_Item objects, log an error and return False.
#
# When the list is ok, build a list of the widgets described in it. We can
# keep the list as a global because we only do one Translate command at a
# time, and we destroy all the built widgets before exiting.
#
# Next build a QDialog containing those widgets in a stack. The Checkbox
# widget has its own label, but the other types need to be put into a
# horizontal layout with their labels in front.
#
# Run the dialog and return True if the user clicked OK, or False for Cancel.
#

DIALOG_LIST = []

def _run_dialog( dialog_list, menu_name, main_window ):

    global DIALOG_LIST

    # Do basic validation: is OPTION_DIALOG a list of Dialog_Items?
    # If it is an empty list, return True, accept the dialog.
    # The try/except catches the error of it not being a list.
    try:
        for j, item in enumerate( dialog_list ) :
            if not isinstance( item, XU.Dialog_Item ) :
                raise TypeError
    except :
        xlt_logger.error( '{} OPTION_DIALOG not a list of Dialog_Items'.format( menu_name ) )
        return False
    if 0 == len( dialog_list ) :
        xlt_logger.info( '{} OPTION_DIALOG is empty list, accepting'.format( menu_name ) )
        return True

    # dialog_list is a list of at least one Dialog_Item. Build the widgets
    # and store (item,widget) in DIALOG_LIST. The widgets are also loaded
    # from the item.result members.
    for item in dialog_list :
        DIALOG_LIST.append( ( item, _make_widget( item ) ) )

    # Create the dialog, centered over the main window
    dialog = QDialog( main_window )
    buttons = QDialogButtonBox( QDialogButtonBox.Ok | QDialogButtonBox.Cancel )
    buttons.accepted.connect( dialog.accept )
    buttons.rejected.connect( dialog.reject )

    # Stack up the requested widgets, each in an HBoxLayout
    vbox = QVBoxLayout()
    for ( item, widget ) in DIALOG_LIST :
        vbox.addLayout( _make_layout( item, widget ) )

    # Add the OK/Cancel buttons and finish the dialog
    vbox.addWidget( buttons )
    dialog.setLayout( vbox )

    # Display the modal dialog and get a result. If OK is clicked, unload
    # the widget values into their dicts so the Translator can query them.
    answer = dialog.exec_()
    if answer == QDialog.Accepted :
        for ( item, widget ) in DIALOG_LIST :
            _unload_widget( item, widget )

    # Destroy the dialog and free all the widgets before exiting.
    dialog = None
    DIALOG_LIST = []
    return answer == QDialog.Accepted

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Given one Dialog_Item from an OPTION_DIALOG list, build the thing it
# describes and load it with data from the result member.

def _make_widget( item ) :

    if item.kind == 'checkbox' :
        # Checkbox is just that
        widget = QCheckBox( item.label )
        if item.result is not None :
            widget.setChecked( bool( item.result ) )

    elif item.kind == 'string' :
        # String is a Line-Edit
        widget = QLineEdit()
        if item.result is not None :
            widget.setText( item.result )

    elif item.kind == 'number' :
        # Number is a SpinBox with optional min/max
        widget = QSpinBox()
        if item.minimum is not None :
            widget.setMinimum( item.minimum )
        if item.maximum is not None :
            widget.setMaximum( item.maximum )
        if item.result is not None :
            widget.setValue( item.result )

    elif item.kind == 'choice' :
        # Choice is a QGroupBox with some number of radio buttons in a stack
        widget = QGroupBox()
        widget.setFlat( True )
        widget.setTitle( item.label )
        vbl = QVBoxLayout()
        for id, (lbl, tip) in enumerate( item.choices ) :
            button = QRadioButton( lbl )
            button.setToolTip( tip )
            button.setChecked( id == item.result )
            vbl.addWidget( button )
        widget.setLayout( vbl )

    else : # item.kind == 'error'
        # Put in a label "Error in definition"
        widget = QLabel( 'Error in definition' )

    widget.setToolTip( item.tooltip )

    return widget

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Given a dialog item and the widget built from it, create an hbox layout
# with the label appropriately positioned. A Checkbox item already has
# its label.

def _make_layout( item, widget ) :
    hbox = QHBoxLayout()
    if item.kind in ['number','string'] :
        hbox.addWidget( QLabel( item.label ) )
    hbox.addWidget( widget )
    return hbox

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Given a dialog item and the widget built from it, unload the widget's
# current value (presumably set by the user) back into the result member of
# the item. The value is easy to get except for the choice, where we have to
# ask the groupbox for its list of children and poll them.

def _unload_widget( item, widget ) :
    if item.kind == 'checkbox' :
        item.result = widget.isChecked()
    elif item.kind == 'string' :
        item.result = widget.text()
    elif item.kind == 'number' :
        item.result = widget.value()
    elif item.kind == 'choice' :
        # the list returned is the vboxlayout followed by the radio
        # buttons in the order added to the layout.
        buttons = widget.children()[1:] # ignore the layout
        for j, button in enumerate( buttons ):
            if button.isChecked() :
                item.result = j
                break
    else: # error
        item.result = None

#         End of option dialog code.
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#
#         document parsing implementation
#
# The following elaborate and sophisticated (if I do say so) machinery allows
# a formal definition of the structure of a DP document as augmented by my
# rules. The syntax definition is in dpdocsyntax.g. This is processed by the
# YAPPS2 parser generator to produce dpdocsyntax.py, which contains
# DPDOCScanner, a token scanner, and DPDOC, the generated parser.
#
# While doing the parse we generate Work Units which will be fed into the
# selected Translator as Events. When the parse succeeds we know the document
# structure is valid with all blocks properly nested and closed.
#

def _do_parse( book, mainwindow ) :
    global WORK_UNITS
    import yapps_runtime

    edit_model = book.get_edit_model()
    scanner = DocScanner( edit_model.all_lines() )
    parser = dpdocsyntax.DPDOC( scanner )
    good_parse = False
    try:
        x = parser.goal()
        good_parse = True
    except yapps_runtime.SyntaxError as s:
        m1 = _TR('Checking document structure',
                 'Document structure error around line') + ' {}'
        m2 = 'Processing {}\n{}'.format( s.context.rule, s.msg )
        utilities.warning_msg(
            m1.format(s.pos[2]), info=m2, parent=mainwindow )
    except Exception as e:
        m1 = _TR('Checking document structure',
                 'Unknown error parsing document')
        m2 = str(e)
        xlt_logger.error(m1)
        xlt_logger.error(m2)
        utilities.warning_msg( m1, info=m2, parent=mainwindow )
    # whatever, clean up if there is a failure.
    if not good_parse :
        WORK_UNITS = []
    return good_parse

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Define a WorkUnit. One is created for each non-empty line of the document
# and eventually gets fed to the Translator as an Event.

class WorkUnit( object ) :
    __slots__ = ['lnum','tok','text','stuff']
    def __init__ ( self, lnum, tok, text ) :
        self.lnum = lnum # actual line number in document
        self.tok = tok   # the parser token or later, event code
        self.text = text # full text of the line
        self.stuff = { 'F':0, 'L':0, 'R':0 }
    def __repr__( self ) :
        # __repr__ used only in testing
        return '''WorkUnit( lnum={}, tok="{}", text="{}" )'''.format(
            self.lnum, self.tok, self.text )
    def copy( self ) :
        return WorkUnit(self.lnum, self.tok, '')

WORK_UNITS = [] # units appended in the scanner.grab_input()
HEAD_UNIT = None # last HEAD2/3 unit appended, see check_head below.

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Small functions called out of the parser at special transitions in the
# parse. These are named in the grammer file dpdocsyntax.g, and so they
# are also named in dpdocsyntax.DPDOC. However they are not available
# in that namespace until we insert them.

def open_para():
    global WORK_UNITS, HEAD_UNIT
    '''
    last work unit was a LINE which starts a Paragraph, need to insert a
    POPEN action ahead of it. If this is also the paragraph that starts
    a heading, stick a copy of the LINE's text into it.
    '''
    unit = WORK_UNITS[-1].copy()
    unit.tok = XU.Events.OPEN_PARA
    WORK_UNITS.insert( len(WORK_UNITS)-1, unit)
    if HEAD_UNIT :
        if HEAD_UNIT.text == '' :
            HEAD_UNIT.text = WORK_UNITS[-1].text

SAVED_CLOSE = None
def close_para():
    global WORK_UNITS, SAVED_CLOSE
    '''
    end of para, append a PCLOSE action.
    '''
    unit = WORK_UNITS[-1].copy()
    unit.tok = XU.Events.CLOSE_PARA
    WORK_UNITS.append(unit)
    if SAVED_CLOSE :
        WORK_UNITS.append(SAVED_CLOSE)
        SAVED_CLOSE = None

def open_head():
    global WORK_UNITS, HEAD_UNIT
    '''
    an EMPTY has been scanned, a head will be recognized.
    add an empty work unit as a place-holder.
    '''
    unit = WORK_UNITS[-1].copy()
    WORK_UNITS.append(unit)
    HEAD_UNIT = unit

def close_head(level):
    global WORK_UNITS, HEAD_UNIT
    '''
    modify the work unit created by open_head() to reflect the type of head
    just scanned, HEAD2 or HEAD3; and append a close-head unit.
    '''
    HEAD_UNIT.tok = str(level)
    unit = HEAD_UNIT.copy()
    unit.tok = str(level+2)
    WORK_UNITS.append(unit)
    HEAD_UNIT = None

def check_head() :
    global WORK_UNITS
    '''
    a HEAD2/3 has just closed in the context of a footnote
    landing zone. If it was a Head2 (Chapter) throw an
    exception; that is a no-no.
    '''
    if HEAD_UNIT.tok != '3' :
        raise SyntaxError

def close_note() :
    global WORK_UNITS
    '''
    A "]" has been parsed ending a Sidenote, Footnote or Illustration.
    Push a work unit to that effect. Get the line number from the
    previous work unit. If it has already happened, don't repeat it.
    '''
    if WORK_UNITS[-1].tok != ']' :
        unit = WorkUnit( WORK_UNITS[-1].lnum, ']', '' )
        WORK_UNITS.append( unit )

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Import the code generated by YAPPS as a namespace. Insert into that
# namespace the names of the above functions.

import dpdocsyntax
dpdocsyntax.open_para = open_para
dpdocsyntax.close_para = close_para
dpdocsyntax.open_head = open_head
dpdocsyntax.close_head = close_head
dpdocsyntax.check_head = check_head
dpdocsyntax.close_note = close_note

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Globals needed to perform "tokenization" of the lines of the document.
# (c.f. https://docs.python.org/dev/library/re.html#writing-a-tokenizer)
# The following tuples are ( match-group-name, match-expression ).
#
# The combined regex will be matched against a single line, so ^$ have
# their normal meanings.

TOKEN_RXS = [
    ( 'EMPTY',  r'^\s*$'           ),
    ( 'XOPEN',  r'^/[X\*]'         ),
    ( 'XCLOSE', r'^[X\*]/'         ),
    ( 'ROPEN',  r'^/R'             ),
    ( 'RCLOSE', r'^R/'             ),
    ( 'COPEN',  r'^/C'             ),
    ( 'CCLOSE', r'^C/'             ),
    ( 'TOPEN',  r'^/T'             ),
    ( 'TCLOSE', r'^T/'             ),
    ( 'POPEN',  r'^/P'             ),
    ( 'PCLOSE', r'^P/'             ),
    ( 'NOPEN',  r'^/F'             ),
    ( 'NCLOSE', r'^F/'             ),
    ( 'QOPEN',  r'^/Q'             ),
    ( 'QCLOSE', r'^Q/'             ),
    ( 'UOPEN',  r'^/U'             ),
    ( 'UCLOSE', r'^U/'             ),
    ( 'FOPEN',  r'^\[Footnote\s+[^:]+:' ), # only recognize valid fnotes
    ( 'IOPEN',  r'^\[Illustration' ),
    ( 'SOPEN',  r'^\[Sidenote'     ),
    ( 'TBREAK', r'^\s*\<\s*tb\s*\>|(\s*\*){5}' ),
    ( 'LINE',   r'^.'              ) # i.e., none of the above
]

# Combine the above as alternatives in a single regex. The combined
# expression will always produce a match, to the EMPTY or LINE expressions if
# nothing else. The group name of the matching expression is in the lastgroup
# member of the match object.

TOKEN_EXPR = '|'.join(
    '(?P<{0}>{1})'.format(*pair) for pair in TOKEN_RXS
)
TOKEN_X = regex.compile( TOKEN_EXPR )

# This dictionary maps the regex match group name into a single character to
# feed the parser. The parser will recognize it as a "token" of the same name,
# see the dpdocsyntax.g file.

TOKEN_VALUE = {
    'EMPTY'  : 'E',
    'XOPEN'  : 'X',
    'XCLOSE' : 'x',
    'ROPEN'  : 'R',
    'RCLOSE' : 'r',
    'COPEN'  : 'C',
    'CCLOSE' : 'c',
    'TOPEN'  : 'T',
    'TCLOSE' : 't',
    'POPEN'  : 'P',
    'PCLOSE' : 'p',
    'NOPEN'  : 'N',
    'NCLOSE' : 'n',
    'QOPEN'  : 'Q',
    'QCLOSE' : 'q',
    'UOPEN'  : 'U',
    'UCLOSE' : 'u',
    'IOPEN'  : 'I',
    'FOPEN'  : 'F',
    'SOPEN'  : 'S',
    'TBREAK' : '%',
    'LINE'   : 'L'
    }

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Override the YAPPS scanner with our own code to generate one character
# per line of the document. It is initialized with the editdata.all_lines
# iterator from the Book.

class DocScanner( dpdocsyntax.DPDOCScanner ) :
    # recognize head of a footnote isolating the Key
    fnrex = regex.compile( r'\[Footnote\s+([^:]+):\s*' )
    # recognize head of illo, isolate one or two filenames
    ilrex = regex.compile( r'\[Illustration:((\w+\.\w+)(\|(\w+\.\w+))?)?\s*' )
    # recognize head of sidenote
    snrex = regex.compile( r'\[Sidenote:\s*' )
    # recognize one column spec on a /T line, being very forgiving. This accepts
    # such as l, 9C, 25rclTB, etc.
    tbrex = regex.compile( r'[0-9lcrTBC]+' )
    tbdig = regex.compile( r'[0-9]+' ) # extract first group of digits if any
    tbhor = regex.compile( r'[lrc]' ) # extract first horizontal char if any
    tbver = regex.compile( r'[TBC]' ) # extract first vertical char if any

    def __init__( self, iterator ):
        self.iterator = iterator
        self.line_number = 0
        self.find_bracket = False
        super().__init__('')

    nfrex = regex.compile( r'F\w*:\s*(\d+)' )
    def _find_first( self, unit ) :
        mob = self.nfrex.search(unit.text)
        if mob :
            unit.stuff['F'] = int( mob.group(1) )

    nlrex = regex.compile( r'L\w*:\s*(\d+)' )
    def _find_left( self, unit ) :
        mob = self.nlrex.search(unit.text)
        if mob :
            unit.stuff['L'] = int( mob.group(1) )

    nrrex = regex.compile( r'R\w*:\s*(\d+)' )
    def _find_right( self, unit ) :
        mob = self.nrrex.search(unit.text)
        if mob :
            unit.stuff['R'] = int( mob.group(1) )

    def grab_input( self ) :
        global SAVED_CLOSE
        if self.pos < len( self.input ) :
            return # some pushed tokens to read still
        # parser needs another token.
        self.pos = 0
        self.line_number += 1

        # TODO at this point get file offset and find out if it hits a
        # different scan image, and if so, insert a pagebreak work unit
        # Maybe need to deal in text blocks instead of lines?

        try:
            # Get the next document line. If this is unit test, iterator is
            # stringIo and returns strings with newlines. If it is real life,
            # there should be no whitespace at the end of a line anyway.
            line = next(self.iterator).rstrip()
        except StopIteration :
            # No more lines to process, so...
            self.input = '$' # ..deliver the END token
            return # parser should never call back

        # Extract the meaning of the received line.
        mob = TOKEN_X.match(line) # cannot fail
        assert mob is not None # something has to match

        # Store the parser token representing this line's contents
        # for the parser to read.

        tok = TOKEN_VALUE[ mob.lastgroup ]
        self.input = tok

        # If it is an empty line, we are done; we do not make WorkUnits for
        # empty lines.
        if tok == 'E' : return

        # Not an empty line, so make a work unit.
        unit = WorkUnit( self.line_number, tok, line )

        # If starting a bracketed group, set the switch for "looking for a
        # closing bracket". Remove boilerplate from the line text, and put
        # optional items in the stuff dict. Put the group-opening unit on
        # the WORK_UNITS list and continue with a Line unit.
        if tok in 'FIS' :
            self.find_bracket = True
            open_unit = unit.copy() # make an F/I/S unit with no text.
            WORK_UNITS.append( open_unit )
            self.input += 'L' # token input is FL, IL, or SL
            unit.tok = 'L' # second unit is a LINE
            if tok == 'F' :
                # remove [Footnote A: from LINE, save "A" in OPEN stuff
                hob = self.fnrex.match(line)
                open_unit.stuff['key'] = hob.group(1)
            elif tok == 'I' :
                # remove [Illustration:, put optional filenames in OPEN
                hob = self.ilrex.match(line)
                open_unit.stuff['image'] = hob.group(2) # filename or None
                open_unit.stuff['hires'] = hob.group(4) # filename or None
                # Illustration only: put line text in I unit for use in alt=
                open_unit.text = line[ hob.end(): ].replace(']','')
            else : # tok == 'S'
                hob = self.snrex.match(line)
            # remove whatever boilerplate was matched above
            unit.text = line[ hob.end(): ]

        # If starting a group markup, implement default F/L/R values and read
        # any on the line.
        elif tok == 'X' :
            unit.stuff['F'] = 2
            self._find_first( unit )
        elif tok == 'R' :
            self._find_right( unit )
        elif tok == 'C' :
            unit.stuff['F'] = 2
            self._find_first( unit )
            self._find_right( unit )
        elif tok in 'PQ' :
            unit.stuff['F'] = 2
            unit.stuff['R'] = 2
            self._find_first( unit )
            self._find_left( unit )
            self._find_right( unit )
        elif tok == 'U' :
            unit.stuff['F'] = 2
            unit.stuff['L'] = 4
            self._find_first( unit )
            self._find_left( unit )
            self._find_right( unit )

        # Entering a table, process the table column values and save in stuff.
        elif tok == 'T' :
            cols = []
            for tob in self.tbrex.finditer(line[2:]) :
                colspec = tob.group(0)
                xob = self.tbdig.search(colspec)
                cw = 0
                if xob : cw = int(xob.group(0))
                ch = None
                xob = self.tbhor.search(colspec)
                if xob : ch = xob.group(0)
                cv = None
                xob = self.tbver.search(colspec)
                if xob : cv = xob.group(0)
                cols.append( [cw, ch, cv] )
            unit.stuff['columns'] = cols

        # If looking for the end of a bracket-group and this line ends in
        # ']', drop the bracket from the line text passed to the Translator,
        # and push the E and ] tokens for the parser. (The E closes any
        # paragraph that might be working; the ] closes the group.)
        if self.find_bracket :
            if line.endswith(']') :
                if line.strip() == ']' and WORK_UNITS[-1].tok != 'L' :
                    # they ended the block with e.g. a quote and a bracket
                    # on a line by itself.
                    self.input = self.input[:-1] + ']' # make input ], possibly F] or I]
                    unit.tok = ']'
                else :
                    self.input += 'E]' # make input LE], possibly FLE]
                    unit.text = unit.text[:-1] # clear bracket from text
                # either way, no mo brackets expected
                self.find_bracket = False

        # OK, this is a kludge. If this is a close-quote or close-list, push
        # an extra E ahead of it. This will close any PARA that might be
        # open, so the user does not have to remember to put a blank line
        # ahead of every Q/ or U/. However, we also want to append the
        # QCLOSE/UCLOSE work unit we just built, but only after the PCLOSE is
        # pushed by close_para() above.
        if tok in 'qu' and WORK_UNITS[-1].tok =='L' :
            # closing a quote or list with a paragraph working.
            self.input = 'E' + tok # input is Eq or Eu
            SAVED_CLOSE = unit # QCLOSE/UCLOSE unit deferred
        else :
            WORK_UNITS.append( unit )

    def get_pos( self ) :
        return ( '', 1, self.line_number )

# End of document-parsing code
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#
#         "Event" generator
#
# The following generator function yields a sequence of Events based on the
# contents of WORK_UNITS above.
#
# An Event is a tuple (code, text, stuff, lnum) which in most cases is just
# the contents of a WorkUnit. We have to make the following modifications.
#
# 1, in a no-flow section we have to recreate any blank lines because those
# are not saved by the parser.
#
# 2, The F/L/R values in work units are only set on the containers XCRPUQ
# and some of these can be nested, although nesting is uncommon and never deep.
# So we keep a little pushdown list of container work units and replicate
# the top one's F/L/R into every non-container unit.
#
# 3, the close-bracket-group token ']' needs to be expanded into CLOSE_FNOTE,
# CLOSE_SNOTE, or CLOSE_ILLO. These bracket groups cannot be nested, so we
# just note the prior open-token and lowercase it to make the close-token.
#
# 4, if the pagedata is active we note when the position of a line (textblock)
# exceeds the start of the next page and generate a pagebreak event.
#
# 5, on finding a Table, break it down into separate events. This is
# raw-ther complex.

def event_generator( page_model, edit_model ) :
    global WORK_UNITS

    # When the actual lnum of a unit exceeds expect_lnum, and we are in a
    # no-flow section, we need to generate blank lines to fill in.
    in_no_flow = False
    expect_lnum = 1
    # Stack of container work units. Almost never gets more than 2 deep.
    stack = [ WorkUnit(0,XU.Events.LINE, '') ] # outermost context F/L/R
    # The "bracket" group (fnote, snote, illo) last seen, to be closed
    # when a ']' token appears.
    last_bracket = None
    # The index of the next scan image, if any, and the position at which it
    # starts in the source document. If there are no scan images, store a
    # start position that will never be reached.
    next_scan = 0
    scan_limit = page_model.page_count()
    next_scan_starts = page_model.position(0) if page_model.active() else int( 2**31 )
    # If in a table, all LINEs get special treatment.
    in_table = False
    columns = []

    for unit in WORK_UNITS :

        code = unit.tok
        text = unit.text
        stuff = unit.stuff
        lnum = unit.lnum

        # In the following we are allowing for the not-uncommon event where
        # there are multiple pages with the same offset. If we run off the
        # end of the list, position() returns None, and the >= returns False.
        while edit_model.line_starts( lnum ) >= next_scan_starts :
            yield ( XU.Events.PAGE_BREAK, '',
                    {'page':next_scan, 'folio':page_model.folio_string(next_scan) }, lnum )
            next_scan += 1
            next_scan_starts = page_model.position( next_scan ) if next_scan < scan_limit else int( 2**31 )

        if in_table :
            # Only two codes can happen in a table, "t" and LINE
            if code == 't' :
                in_table = False
                yield ( code, '', stuff, lnum )
                continue # save a nesting level
            if 0 == len(columns) :
                # table cols were not defined on /T line, and this is the
                # first LINE after. Determine column widths and emit the /T
                # that we just skipped.
                stile_pos = text.find('|')
                while stile_pos > 0 :
                    columns.append( (stile_pos, None, None) )
                    stile_pos = text.find( '|', stile_pos+1 )
                stuff['columns'] = columns
                yield( 'T', '/T', stuff, lnum-1 )
            # Table columns are defined, parse the current line expecting
            # len(columns) stiles and emit a row, cell and line events.
            yield ( XU.Events.OPEN_TROW, text, {}, lnum )
            j = len(columns) # number of stiles expected
            col_start = 0
            stile_pos = text.find('|')
            while j :
                cell_text = text[col_start:stile_pos] if stile_pos != -1 else ''
                yield ( XU.Events.OPEN_TCELL, '', {}, lnum )
                yield ( XU.Events.LINE, cell_text, {}, lnum )
                yield ( XU.Events.CLOSE_TCELL, '', {}, lnum )
                col_start = stile_pos + 1
                stile_pos = text.find('|', col_start )
                j -= 1
            code = XU.Events.CLOSE_TROW
            text = ''

        elif code == 'T' : # not in table, should we be?
            in_table = True
            columns = stuff['columns']
            if 0 == len( columns ) :
                # table cols not defined on /T, defer to the next event
                continue

        if code in 'XCRPUQ' :
            stack.append( unit )
        else:
            if code in 'xcrpuq' :
                stack.pop()
        if len(stack) > 1 :
            # in a container, copy the parent FLR
            container_stuff = stack[-1].stuff
            stuff['F'] = container_stuff['F']
            stuff['L'] = container_stuff['L']
            stuff['R'] = container_stuff['R']

        if code in 'FSI' :
            last_bracket = code.lower()

        if code == ']' :
            code = last_bracket

        if not in_no_flow :
            in_no_flow = code in 'XCRP'
        else :
            in_no_flow = not code in 'xcrp'

        while in_no_flow and expect_lnum < lnum :
            yield( XU.Events.LINE, '', stuff, expect_lnum )
            expect_lnum += 1

        yield ( code, unit.text, stuff, lnum )
        expect_lnum = lnum + 1


if __name__=='__main__':

    DOC9 = '''There is never a heading at the top of a document.




This Chapter Features a List


There has to be a line after a head.

/U
* Item one

* Item two
U/
'''

    import io
    import yapps_runtime
    DOCFILE = io.StringIO( initial_value = DOC9 )
    scanner = DocScanner( DOCFILE )
    parser = dpdocsyntax.DPDOC( scanner )
    try:
        x = parser.goal()
    except yapps_runtime.SyntaxError as s:
        print( 'Document structure error around line {}'.format(s.pos[2]) )
        print( 'Processing', s.context.rule )
        print( s.msg )
    #except Exception as e:
        #print('Other error')
        #print(e)

    for unit in WORK_UNITS :
        print( unit )
    DOC8 = '''
This keys a footnote[*].

[Footnote *: Begins with a para.

/P
has a poem
P/
/T
has | a | Table
T/
/Q
Has a quote which has

/Q
Another quote

Q/
Q/

And a closing para.]
'''
    DOC7 = '''

[Illustration: this figure has it all,
including this 2-line para

/P
n a little peom
P/
/T r5 l60 rB8
whatever | asdf | asdf
T/
/Q First:4 Right:4
/C
asdf
C/
Q/
]

'''

    DOC6 = '''
/Q
/Q
para in a quote

/C
center ina  qutoe
C/

/R
right in a quote
R/

/P
peom in a qutoe
P/
Peom ends

Q/

Q/

'''

    DOC5 = '''

/Q
para in a quote

/C
center ina  qutoe
C/

/R
right in a quote
R/

/P
peom in a qutoe
P/
Peom ends

Q/

'''

    DOC4 = '''
This paragraph is followed by a figure.

[Illustration: <sc>Fig.</sc> 3: pair of bvd's]

[Illustration:fig4.png <sc>Fig.</sc> 4: a jock strap]

[Illustration:fig5.png|fig5.jpg <sc>Fig.</sc>5: Socks.]

'''

    DOC3 = '''
[Sidenote: exercise notes]

This paragraph is followed by footnotes[B] and[C].

[Footnote B: this footnote is all on one line]

[Footnote C: this foontote
extends to
3 lines]

'''

    DOC2 = '''
/C
Centered Paragraph.
C/

/R
Right aligned text
R/

/P
Twas Brillig,
   and the slithy toves,
Did gyre and gymbal
   in the wabe
P/

'''

    DOC0 = '''

/X
foobar
X/
'''

    DOC1 = '''
Opening Paragraph!




TABLE OF CONTENTS


Just a paragraph pair
of graphs

Another paragraph, gee
we could get to like this.


SUBHEAD, Y'ALL!

Afterhead paragraph.




CHAPtER DOS

In which Doris gets her offs.


Post chapter paragraph.
'''
