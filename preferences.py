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
            preferences.py

The Preferences dialog gives the user the ability to choose the following:

    The path to the bookloupe executable

    The path to the extras folder

    The path to a folder of spellcheck dictionaries

    The preferred default spellcheck language (dictionary)

    The monospaced font for the editor

    The text format used to highlight the current line

    The text format used to highlight a limited Find range

    The text format used to highlight detected scannos

    The text format used to highlight words that fail spellcheck

The UI to choose each item is presented in a narrow rectangle, and the
rectangles are stacked in a pile. Below them is a text display area where a
detailed explanation of each preference is shown. As the mouse hovers over
each preference choice it displays its explanation at the bottom of the
dialog.

At the bottom are four buttons:

    Apply : applies any changes made since the dialog was opened.

    Cancel : closes the dialog and does not apply any changes

    OK : performs Apply, then closes the dialog

    Set Defaults : sets all preferences to reasonable default values and does Apply

'''
import paths
import fonts
import colors
import dictionaries
import utilities

import os

from PyQt6.QtCore import pyqtSignal, QCoreApplication

from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout
)
from PyQt6.QtGui import (
    QColor,
    QPalette,
    QBrush,
    QTextCharFormat
)
#from PyQt6.QtCore import QCoreApplication

_TR = QApplication.translate

'''

Since the preference choices are all similar in many ways, they are coded as
subclasses of the following base class, ChoiceWidget(QGroupBox), which
creates the look of the basic rectangle with a title line. It implements the
mouse-over behavior of changing color and setting self.explanation into
self.explainer. Creates self.layout for contents.

Each subclass must:
* pass its title string
* pass its explainer, a widget that supports setText()
* set self.explanation to explain itself
* implement self.apply() to install the current values
* implement self.reset() to get the established values and display them

'''
class ChoiceWidget(QGroupBox):
    def __init__( self, title, explainer ) :
        super().__init__( title, None )
        self.explainer = explainer
        self.explanation = ''
        self.setLayout( QHBoxLayout() )
        # Compress the stack vertically
        self.layout().setContentsMargins( 0,5,0,5 )
        # Figure out a slightly darker color for mouse-over
        self.normal_color = self.palette().color(
            QPalette.ColorGroup.Normal, QPalette.ColorRole.Window)
        self.mouse_color = self.normal_color.darker(110)
        # allow changing background color
        self.setAutoFillBackground(True)
        self.setFlat(True)

    def enterEvent( self, event ) :
        palette = self.palette()
        palette.setColor(
            QPalette.ColorGroup.Normal, QPalette.ColorRole.Window, self.mouse_color )
        self.setPalette(palette)
        self.explainer.setText(self.explanation)

    def leaveEvent( self, event ) :
        palette = self.palette()
        palette.setColor(
            QPalette.ColorGroup.Normal, QPalette.ColorRole.Window, self.normal_color )
        self.setPalette(palette)
        #self.explainer.setText('') # leave it in place until changed by another

    # Called when the Apply button is clicked.
    def apply( self ) :
        pass

    # Called when the Defaults button is clicked, and when initializing.
    # Reset your displayed value to the current established setting.
    def reset( self ) :
        pass

'''
Choose the editor font: basic ChoiceWidget plus ComboBox of available
fixed-pitch fonts.
'''
class ChooseFixedFont( ChoiceWidget ) :
    def __init__( self, explainer ) :
        super().__init__( _TR( 'Preference item title line',
                               'Choose a monospaced font for the Editor' ),
                          explainer )
        self.fcb = QComboBox()
        self.fcb.addItems( fonts.list_of_good_families() )
        self.fcb.textActivated.connect( self.choice_made )
        self.layout().addWidget(self.fcb)
        self.reset() # set the current font
        self.explanation = _TR( 'Preference item details',
'''Select the font to use in the Edit panel. Choose a monospaced font that shows a clear difference 1/l and 0/O, and that has a wide selection of Unicode characters. Good choices are Cousine and Liberation Mono.

When you select a font from the menu, that font is applied to this window. To apply it to the Edit panel, click Apply.''')
        self.reset()

    def choice_made(self, family) :
        self.choice = family
        qf = fonts.font_from_family( family )
        self.explainer.setFont(qf)

    def reset(self) :
        self.choice = fonts.get_fixed().family()
        self.fcb.setCurrentText( self.choice )

    def apply(self) :
        fonts.set_fixed( fonts.font_from_family( self.choice ) )

'''
Choose the default dictionary tag, used when opening a new book. A basic
ChoiceWidget with a combobox containing the available dict tags. Signs up
to get the pathsChanged signal and reloads the combo box when the dicts or
extras paths change.
'''

class ChooseDefaultDict( ChoiceWidget ):
    def __init__( self, explainer ) :
        super().__init__( _TR( 'Preference item title line',
                               'Choose the spellcheck dictionary for any new book' ),
                          explainer )
        self.dcb = QComboBox()
        self.layout().addWidget(self.dcb)
        self.dcb.textActivated.connect( self.choice_made )
        self.reset() # load the combobox
        paths.notify_me( self.path_changed )
        self.explanation = _TR( 'Preference item details',
'''Choose the spell-check dictionary to be used when a book is opened for the first time.

If the list is empty or the dictionary that you want is not shown, you may need to choose the path to the dictionaries folder, above, and click Apply.

You can change the dictionary for any book by right-clicking in its Edit panel.''' )

    def choice_made( self, dic_tag ) :
        self.choice = dic_tag

    def path_changed( self, which ):
        # some path preference changed; if "dicts", reload the menu
        if which == "dicts" :
            self.reload_menu()

    def reload_menu( self ) :
        # refresh the combobox with the available tags.
        dict_dict = dictionaries.get_tag_list()
        self.dcb.clear()
        self.dcb.addItems( list( dict_dict.keys() ) )
        self.dcb.setCurrentText ( self.choice )

    def reset(self) :
        self.choice = dictionaries.get_default_tag()
        self.reload_menu()

    def apply(self):
        dictionaries.set_default_tag( self.choice )

'''
Parent class for the three choose-a-path classes. Display a lineedit and a
browse button. On end-edit, check the line-edit contents for validity as a
path according to a criterion, and if not valid turn the field pink and
beep. When editing resumes, clear the pink color.

Subclass must:
* pass criterion, one of os.F_OK, os.R_OK, or os.X_OK
* implement browse to respond to the Browse button click
* in reset(), check self.path_valid
'''
class PathChoice(ChoiceWidget):
    def __init__( self, criterion, title, explainer ) :
        super().__init__( title, explainer )
        self.criterion = criterion
        self.path_edit = QLineEdit()
        self.path_valid = True
        self.path_edit.textChanged.connect( self.path_working )
        self.path_edit.editingFinished.connect( self.check_path )
        self.browse_button = QPushButton(
            _TR('Path preference button', 'Browse' ) )
        self.browse_button.clicked.connect( self.browse )
        self.layout().addWidget( self.path_edit, 1 )
        self.layout().addWidget( self.browse_button, 0 )

    ''' Change the color of the background of the path_edit.'''
    def set_path_color( self, color_name ) :
        p = self.path_edit.palette()
        p.setColor(
            QPalette.ColorGroup.Normal, QPalette.ColorRole.Window, QColor( color_name ) )
        self.path_edit.setPalette(p)

    '''
    Return pressed (or focus-out) on the path line-edit. Check for
    validity per the criterion. If it is not valid, mark it so.
    '''
    def check_path( self ) :
        if os.access( self.path_edit.text(), self.criterion ) :
            return
        if self.path_edit.text() : # is not null
            utilities.beep()
            self.path_valid = False
            self.set_path_color( 'Pink' )

    '''
    User is editing the path string. If we had marked it invalid (above),
    clear that indication and make its background white again.
    '''
    def path_working( self ) :
        if self.path_valid : return
        self.path_valid = True
        self.set_path_color('White')

    '''
    User wants to browse for a path. The subclass must implement
    this by calling a utilities dialog with a specific caption.
    '''
    def browse(self) :
        pass

'''
Choose path to bookloupe executable.
'''

class ChooseLoupe( PathChoice ) :
    def __init__( self, explainer ):
        super().__init__( os.X_OK,
                          _TR( 'Preference item title line',
                               'Enter the path to the Bookloupe program' ),
                          explainer )
        self.explanation = _TR( 'Preference item details',
'''When you click Refresh in the Loupe panel, PPQT executes the program you specify here.

Enter the path to the bookloupe program file. If you have not installed bookloupe, leave this blank.''')
        self.reset() # load initial value in path_edit

    def browse( self ) :
        p = utilities.ask_executable(
            _TR( 'Browse dialog for bookloupe',
                 'Choose the bookloupe executable program' ),
            self, self.path_edit.text() )
        if p : # p is not None and not a null string
            self.path_edit.setText(p)

    def reset( self ) :
        p = paths.get_loupe_path()
        self.path_edit.setText( p )

    def apply( self ) :
        if self.path_valid :
            paths.set_loupe_path( self.path_edit.text() )

'''
Choose the "extras" folder
'''
class ChooseExtras( PathChoice ) :
    def __init__( self, explainer ):
        super().__init__( os.F_OK,
                          _TR( 'Preference item title line',
                               'Enter the path to the "extras" folder' ),
                          explainer )
        self.explanation = _TR( 'Preference item details',
'''The "extras" folder contains useful files distributed with PPQT. It is the place where PPQT looks first when loading Find Buttons. It is the second or third place where PPQT looks for spelling dictionaries, after the book folder and dictionary folder.

The "extras" folder is found in the PPQT folder when it is downloaded, but you may move it anywhere.''' )
        self.reset() # load initial value in path_edit

    def browse( self ) :
        p = utilities.ask_folder(
            _TR( 'Browse dialog for extras',
                 'Choose the extras folder' ),
            self, self.path_edit.text() )
        if p : # p is not a null string
            self.path_edit.setText(p)

    def reset( self ) :
        p = paths.get_extras_path()
        self.path_edit.setText( p )

    def apply( self ) :
        if self.path_valid :
            paths.set_extras_path( self.path_edit.text() )

'''
Choose the "dicts" folder
'''

class ChooseDicts( PathChoice ) :
    def __init__( self, explainer ) :
        super().__init__(  os.F_OK,
                           _TR( 'Preference item title line',
                                'Enter the path to a folder of spell-check dictionaries' ),
                           explainer )
        self.explanation = _TR( 'Preference item details',
'''A spell-check dictionary is a pair of files with names like en_GB.dic and en_GB.aff, or fr_FR.dic and fr_FR.aff.

When PPQT needs to perform spell-checking, it looks for a dictionary first in the folder for the current book, then in this folder, last in the "extras" folder.

Some dictionaries are distributed with PPQT in the folder extras/dictionaries, but you may move that folder anywhere.''' )
        self.reset() # fill initial value

    def browse( self ) :
        p = utilities.ask_folder(
            _TR( 'Browse dialog for extras',
                 'Choose a folder of spell-check dictionary files' ),
            self, self.path_edit.text() )
        if p : # p is not a null string
            self.path_edit.setText(p)

    def reset( self ) :
        p = paths.get_dicts_path()
        self.path_edit.setText( p )

    def apply( self ) :
        if self.path_valid :
            paths.set_dicts_path( self.path_edit.text() )

'''
Classes to help implement the four character-format choices.

Swatch is a clickable color patch. It emits a signal "clicked" on mouse
release. It offers a set_color method.
'''

class Swatch(QLabel):
    clicked = pyqtSignal()
    def __init__(self, parent=None ):
        super().__init__( '   ', parent )
        self.qc = QColor('White')
        self.setMinimumHeight(24)
        self.setMinimumWidth(24)
        self.setMaximumHeight(24)
    def set_color( self, qc ) :
        self.qc = qc
        self.setStyleSheet( 'background: '+qc.name() )
    def mouseReleaseEvent( self, event ) :
        self.clicked.emit()

'''
Sample is a read-only QTextEdit that displays the appearance of
some QTextCharFormat.
'''
class Sample(QTextEdit):
    def __init__( self, parent=None ) :
        super().__init__(parent)
        self.setReadOnly( True )
        self.setMaximumHeight(26)
        self.document().setPlainText('Normal highlighted normal.')
        self.cursor = self.document().find('highlighted')
    def change_format( self, qtcf ) :
        self.cursor.setCharFormat( qtcf )

'''
Parent class of four choose-format widgets. Builds on ChoiceWidget to add
a combobox for underline styles, a Swatch and a Sample.

When the Swatch is clicked, query the user for a color choice. When the
color or combobox changes, update the sample to show the effect.

underline styles 0..6 for loading the combobox.
'''

UNDERLINE_NAMES = {
    QTextCharFormat.UnderlineStyle.NoUnderline : 'No underline',
    QTextCharFormat.UnderlineStyle.SingleUnderline : 'Single',
    QTextCharFormat.UnderlineStyle.DashUnderline : 'Dash',
    QTextCharFormat.UnderlineStyle.DotLine : 'Dotted',
    QTextCharFormat.UnderlineStyle.DashDotLine : 'Dash-Dot',
    QTextCharFormat.UnderlineStyle.DashDotDotLine : 'Dash-dot-dot',
    QTextCharFormat.UnderlineStyle.WaveUnderline : 'Wave'
}
UNDERLINE_VALUES = list(UNDERLINE_NAMES.keys())
class FormatChoice( ChoiceWidget ) :
    # combobox value
    def __init__( self, title, explainer ) :
        super().__init__( title, explainer )
        #Current color and line style are kept in this QTextCharFormat
        self.text_format = QTextCharFormat()
        # Set up the underline menu
        self.ul_menu = QComboBox()
        self.ul_menu.addItems( list( UNDERLINE_NAMES.values() ) )
        self.ul_menu.currentIndexChanged.connect(self.ul_change)
        self.layout().addWidget( self.ul_menu, 0 )
        # Set up the color swatch
        self.swatch = Swatch( self )
        self.layout().addWidget( self.swatch, 0 )
        self.swatch.clicked.connect( self.color_change )
        # Set up the text sample
        self.sample = Sample()
        self.layout().addWidget( self.sample )
        self.reset() # set widgets to current value
    '''
    Combine the underline choice and swatch color into a QTextCharFormat.
    '''
    def make_format( self, ul_index, qc ) :
        qtcf = QTextCharFormat()
        style = UNDERLINE_VALUES[ul_index]
        qtcf.setUnderlineStyle( style )
        if style == QTextCharFormat.UnderlineStyle.NoUnderline :
            qtcf.setBackground(QBrush(qc))
        else :
            qtcf.setUnderlineColor(qc) # underline color gets a QColor
            qtcf.clearBackground()
        return qtcf
    '''
    Parse self.text_format and display it in the swatch and combobox.
    '''
    def show_format( self ) :
        un = self.text_format.underlineStyle()
        if un == QTextCharFormat.UnderlineStyle.NoUnderline :
            qc = self.text_format.background().color()
        else :
            qc = self.text_format.underlineColor()
        self.swatch.set_color( qc )
        self.ul_menu.setCurrentIndex( un.value )
        self.sample.change_format(self.text_format)
    '''
    Handle a change in selection of the underline popup
    '''
    def ul_change( self, index ) :
        self.text_format = self.make_format( index, self.swatch.qc )
        self.show_format()
    '''
    Handle a click on the color swatch. Show the color dialog. After it
    ends, the Preferences dialog will be behind the main window. Why? Who
    knows! But raise it back up to visibility.
    '''
    def color_change(self) :
        qc = colors.choose_color(
            _TR('Browse dialog for color preference',
                'Choose a color for highlighting'),
            self.swatch.qc )
        BIG_FAT_KLUDGE.raise_()
        if qc is not None :
            self.text_format = self.make_format( self.ul_menu.currentIndex(), qc )
            self.show_format()

'''
Choose the Scanno highlight.
'''
class ChooseScanno( FormatChoice ) :
    def __init__( self, explainer ) :
        super().__init__( _TR( 'Preference item title line',
                               'Choose a highlight style for "scanno" words' ),
                          explainer )
        self.explanation = _TR( 'Preference item details',
'''In the Edit panel, right-click to turn on marking of "scanno" words (probable OCR errors). The words will be highlighted as shown.

When you choose "No Underline" the text is marked with a colored background. When you choose one of the underline styles, the words are marked with a colored underline. Click the color sample to choose a different color.''')

        self.reset() # load initial text format

    def reset( self ) :
        self.text_format = colors.get_scanno_format()
        self.show_format()

    def apply( self ) :
        colors.set_scanno_format( self.text_format )
        QCoreApplication.processEvents() # force change to be visible

'''
Choose the Spellcheck highlight.
'''
class ChooseSpellcheck( FormatChoice ) :
    def __init__( self, explainer ) :
        super().__init__( _TR( 'Preference item title line',
                               'Choose a highlight style for words that fail spellcheck' ),
                          explainer )
        self.explanation = _TR( 'Preference item details',
'''In the Edit panel, right-click to turn on marking of words that fail spellcheck. The words will be highlighted as shown.

When you choose "No Underline" the text is marked with a colored background. When you choose one of the underline styles, the words are marked with a colored underline. Click the color sample to choose a different color.''')
        self.reset() # load initial text format

    def reset( self ) :
        self.text_format = colors.get_spelling_format()
        self.show_format()

    def apply( self ) :
        colors.set_spelling_format( self.text_format )
        QCoreApplication.processEvents() # force change to be visible        

'''
Choose the Find-range highlight.
'''

class ChooseFindRange( FormatChoice ) :
    def __init__( self, explainer ) :
        super().__init__( _TR( 'Preference item title line',
                               'Choose a highlight style for a limited Find range' ),
                          explainer )
        self.explanation = _TR( 'Preference item details',
'''In the Find panel, use the "In Selection" switch to limit Find and Replace operations to a range of text. The range of text is highlighted as shown.

When you choose "No Underline" the text is marked with a colored background. When you choose one of the underline styles, the words are marked with a colored underline. Click the color sample to choose a different color.''')

        self.reset() # load initial text format

    def reset( self ) :
        self.text_format = colors.get_find_range_format( )
        self.show_format()

    def apply( self ) :
        colors.set_find_range_format( self.text_format )
        QCoreApplication.processEvents() # force change to be displayed

# Choose the Current-line highlight.

class ChooseCurrentLine( FormatChoice ) :
    def __init__( self, explainer ) :
        super().__init__( _TR( 'Preference item title line',
                               'Choose a highlight style for the current line' ),
                          explainer )
        self.explanation = _TR( 'Preference item details',
'''In the Edit panel PPQT puts a highlight on the current line to make it easier to find the cursor.The usual highlight is a very pale yellow, but you may change that here.

When you choose "No Underline" the text is marked with a colored background. When you choose one of the underline styles, the words are marked with a colored underline. Click the color sample to choose a different color.''')
        self.reset() # load initial text format

    def reset( self ) :
        self.text_format = colors.get_current_line_format( )
        self.show_format()

    def apply( self ) :
        colors.set_current_line_format( self.text_format )
        QCoreApplication.processEvents() # force change to be visible        

BIG_FAT_KLUDGE = None

'''

**Finally**, the actual PreferencePanel object.

'''
class PreferenceDialog(QDialog):
    def __init__( self, parent=None ):
        global BIG_FAT_KLUDGE
        super().__init__( parent )
        # put a reference to this dialog where FormatChoice.color_change()
        # can get at it.
        BIG_FAT_KLUDGE = self
        # Create our layout, a stack of bricks.
        vb = QVBoxLayout()
        # Create the "explainer", a QTextEdit. It must be passed
        # to each widget.
        xp = QTextEdit()
        # Create the choice widgets in order top to bottom. Store references
        # to them in a list for convenience executing Reset and Apply.
        self.widgets = []
        self.widgets.append( ChooseLoupe( xp ) )
        self.widgets.append( ChooseExtras( xp ) )
        self.widgets.append( ChooseDicts( xp ) )
        self.widgets.append( ChooseDefaultDict( xp ) )
        self.widgets.append( ChooseFixedFont( xp ) )
        self.widgets.append( ChooseScanno( xp ) )
        self.widgets.append( ChooseSpellcheck( xp ) )
        self.widgets.append( ChooseFindRange( xp ) )
        self.widgets.append( ChooseCurrentLine( xp ) )
        for w in self.widgets :
            vb.addWidget( w, 0 )
        # Make our row of four buttons, Defaults, Cancel, Apply, OK
        bb = QHBoxLayout()
        bb.setContentsMargins(0,0,0,0)
        #
        self.defaults_button = QPushButton( _TR( 'Preferences set-defaults button', 'Defaults' ) )
        self.defaults_button.setToolTip( _TR( 'Preferences set-defaults button',
                    'Restore the original default preferences for all choices.' ) )
        self.defaults_button.clicked.connect( self.do_defaults )
        bb.addWidget( self.defaults_button )
        #
        self.cancel_button = QPushButton( _TR( 'Preferences cancel button', 'Cancel' ) )
        self.cancel_button.setToolTip( _TR( 'Preferences cancel button',
                    'Close this dialog and apply no changes.' ) )
        self.cancel_button.clicked.connect( self.do_cancel )
        bb.addWidget( self.cancel_button )
        #
        self.apply_button = QPushButton( _TR( 'Preferences apply button', 'Apply' ) )
        self.apply_button.setToolTip( _TR( 'Preferences apply button',
                    'Apply all choices and make them effective.' ) )
        self.apply_button.clicked.connect( self.do_apply )
        bb.addWidget( self.apply_button )
        #
        self.ok_button = QPushButton( _TR( 'Preferences ok button', 'OK' ) )
        self.ok_button.setToolTip( _TR( 'Preferences ok button',
                    'Apply all choices, then close this dialog.' ) )
        self.ok_button.clicked.connect( self.do_ok )
        bb.addWidget( self.ok_button )
        #
        vb.addLayout(bb, 0)
        #
        vb.addWidget( xp, 1 )
        self.setLayout( vb )
        # invoke reset on every choice, to load it with the current values.
        self.do_reset()

    # Call every choice to load up the current settings.
    def do_reset(self) :
        for w in self.widgets :
            w.reset()

    # Call the settings modules to reset to factory defaults, then reload.
    def do_defaults(self) :
        fonts.set_defaults()
        colors.set_defaults()
        paths.set_defaults()
        self.do_reset()

    def do_cancel(self) :
        self.done(0)

    def do_apply(self) :
        for w in self.widgets :
            w.apply()

    def do_ok(self) :
        self.do_apply()
        # do_apply() can generate signals which are connected to methods of
        # our children. Make sure they are delivered before ending. A 0.25
        # second wait should be enough...
        self.done(0)
