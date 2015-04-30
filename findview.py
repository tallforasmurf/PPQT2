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
                          findview.py

Create and manage the display of the Find panel.

This is a complex UI with many sub-parts and features.

The top row has the following check-boxes grouped in a horizontal box layout:

 [x] Respect Case [x] Whole Word [x] Regex [x] In Selection

Object name      Purpose

sw_respect_case  When checked, letter case is significant in both
                 normal and regular expression searches.

sw_whole_word    When checked, non-regex searches match to only
                 whole words. Disabled when Regex is checked;
                 the regex equivalent is to use explicit \b codes.

sw_regex         When checked, the find string is treated as a
                 regular expression, and replace operations are done
                 using regular expression syntax also. Disables the
                 Whole Word checkbox. Causes any input to the Find
                 input field to be checked for syntax and to get a
                 pink background to show invalid regex syntax.
                 Input to any Replace field is checked for syntax
                 and if bad (rare) gets a pink bg.

sw_in_range  While False, the find range is the whole document.
                 When toggled to True, if the current selection is
                 <100 characters, the user is warned and the switch
                 is set False. Otherwise the selection is set as the
                 range for find/replace. It is given a background color
                 so as to be visible.

(Note that version 1 had a Greedy checkbox; this is gone as the Python regex
support does not have a global greedyness flag. Use the '?' qualifier to
perform not-greedy searches: *?, +?, {m,n}?.)

Below this row is the Find text field with a recall button/menu:

 [>]  [ find text field ...]

The recall button pops up a menu containing the last 10 find unique find
strings from most to least recent. This includes only find strings that were
entered or edited by the user. Strings plugged in programatically are not
saved. The recall button, with its menu, is class RecallMenuButton.

The find text field is a custom QLineEdit class named FindRepEdit that:

* is monitored by a custom QValidator to make sure that any \n characters
  typed or pasted are only accepted into regexes (QTextDocument.find() does
  not support searching for, or across, newlines), and are shown visibly
  as '\n'.

* uses the mono font, tracks changes in that font, and allows font zoom.

* when sw_regex is true, checks each user edit and turns the background
  pink when the syntax is not correct.

Below this are four buttons in two groups of two:

  [Next] [Prior]          [First] [Last]

These implement searches:

Next:  Search forward from the end of the current selection. Fail
       at the end of the search range.

Prior: Search backward from the beginning of the current selection.
       Fail at the beginning of the search range.

First: Search forward from the start of the search range.

Last:  Search backward from the end of the search range.

Below these are three Replace fields. Each consists of a RecallMenuButton and
a FindRepEdit, followed by a command button:

  [>]  [ replace text ... ]  [Replace]

When Replace is clicked, if the current selection was set by a search, the
selected text is replaced, by regex if sw_regex is True. Then the replaced
text is selected. If there is no current selection, or the selection is not
the result of search, nothing is done and a beep is sounded. When a replace
is done, the replace string is saved in its RecallMenuButton.

To their right is a stack of three checkboxes that control replace
operations:

  [x] And Next
  [x] And Prior
  [x] ALL!

sw_and_next  After a successful replace, do a Next search

sw_and_prior After a successful replace, do a Prior search

sw_do_all  On clicking any Replace, initiate a global replace.

On global replace, the search text is applied throughout the current search
range and a list is made of all matches. The user is shown a warning dialog:

   OK to replace n occurrences of
    ...find text...
   With
    ...replace text...
   [OK] [CANCEL]

When OK is clicked, the replacements are done.

The bottom of the panel is occupied by 24 buttons in a grid array in a frame.
These are the user macro buttons, which can be saved or loaded to a text
file. They are defined as UserButton class.

Each UserButton stores the settings of certain switches, the find text field
and the replace text fields. When one is clicked, the UI controls are loaded
with the stored values. When one is ctl-clicked, the user is prompted for a
new label for the button, then the current values of the UI controls are
loaded into it.

The main window presents File > Load/Save Find Buttons commands. These are
implemented by calling here. This is separate from the book metadata system.
Loading user button definitions from, and saving them to, a text file is
a Version 1 feature that is retained and the same file format used. See
FindPanel.user_button_input() and .user_button_output().

The FindPanel constructor implements a metadata reader and writer to save and
load the contents of the four RecallMenuButtons and the current Userbutton
values into the book metadata, so the most recent search and replace patterns
and user button values are saved with the book. These operations use the
Version 2 JSON-based metadata system. See FindPanel._meta_read() and
._meta_write().

'''

from PyQt5.QtWidgets import(
    QAction,
    QCheckBox,
    QFrame,
    QGridLayout, QHBoxLayout, QVBoxLayout,
    QLineEdit,
    QMenu,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QWidget
)
from PyQt5.QtGui import(
    QColor,
    QIcon,
    QPalette,
    QTextCursor,
    QTextDocument,
    QValidator
)
from PyQt5.QtCore import QSize, QObject, pyqtSignal
from PyQt5.Qt import Qt, QCoreApplication
_TR = QCoreApplication.translate

import fonts
import utilities
import constants as C
import regex
import logging
find_logger = logging.getLogger(name='Find panel')

# Message texts for translation
NO_SELECTION = _TR(
    "Find panel In-Selection switch",
    "Selection is too small for searching - ignored"
    )
NO_SELECTION_INFO = _TR(
    "Find panel In-Selection switch",
    "Select at least 4 lines or 100 characters."
    )
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Global function to compile an RE with the flags we apply to all
# user regexes. If the compile throws an error the caller should catch it.
# case_switch is an instance of QCheckBox, the Respect Case switch.
#
def RE_Compile(string, case_switch, extra_flag = 0):
    flag = regex.MULTILINE | regex.DOTALL | regex.VERSION1 | extra_flag
    flag |= 0 if case_switch.isChecked() else regex.IGNORECASE
    return regex.compile( string, flag )

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# A RecallMenuButton is a QToolButton that pops up a menu of previously-used
# strings, based on a pushdown list of strings used by a related FindRepEdit
# object. The remember() method stores a new string in the list. It is called
# from the associated FindRepEdit, or from the parent FindPanel when loading
# strings from the metadata.
#
# When the ToolButton is pressed, the aboutToShow signal of the menu lets us
# fill the menu with QActions based on the stack of strings. When a menu item
# is chosen, we store the string as the text of the related FindRepEdit.
#

class RecallMenuButton(QToolButton):
    MAX_STRINGS = 10 # arbitrary limit

    def __init__(self, parent=None):
        super().__init__(parent)
        # Slot for the associated FindRepEdit widget which will
        # fill this in externally
        self.partner = None
        # The list of saved strings in the form of QActions.
        self.string_stack = [] # see remember()
        # Create our menu.
        self.setPopupMode(QToolButton.InstantPopup)
        self.my_menu = QMenu(self)
        self.my_menu.triggered.connect(self.menu_choice)
        # Create our look.
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setIcon(QIcon(':/recent-icon.png'))
        self.setMenu(self.my_menu)
        # Connect the menu's aboutToShow signal to our slot
        self.my_menu.aboutToShow.connect(self.fill_menu)
        # A disabled action to be in the menu when empty
        self.null_action = QAction('...empty...',self)
        self.null_action.setEnabled(False)

    # Clear the stack, used from metadata-reader to facilitate unit test.
    def clear(self):
        self.string_stack = []

    # When our menu is to pop-up, fill it with the saved actions.
    def fill_menu(self):
        self.my_menu.clear()
        for string in self.string_stack:
            self.my_menu.addAction(QAction(string,self.my_menu))
        if self.my_menu.isEmpty(): # apparently, the stack is empty!
            self.my_menu.addAction(self.null_action)

    # Called from our associated FindRepEdit when it acts on a user-edited
    # string. Push the string onto our stack in the form of a QAction that,
    # when triggered, calls menu_choice(). If it is already in the stack,
    # delete it so it moves to the top.
    def remember(self, new_string):
        new_stack = [old_string for old_string in self.string_stack if old_string != new_string]
        new_stack.insert(0,new_string)
        self.string_stack = new_stack[:self.MAX_STRINGS]

    # A menu item has been chosen. The menu action is passed with the
    # signal; set the text of that action in our partner.
    def menu_choice(self,chosen_action):
        self.partner.setText(chosen_action.text())
        self.partner.note_user(True)

    # Make our stack of strings available to the metadata writer.
    def stack_size(self):
        return len(self.string_stack)
    def get_string(self,n):
        return self.string_stack[n]

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# A specialized QLineEdit with the following changed or added features:
#
# By use of a special QValidator, it ensures that if a newline is entered
# (perhaps with a ctl-v paste?) it is converted to the two characters "\n" so
# as to be visible and useful to a regex. Note that a non-regex find cannot
# match to newlines anyway. If the regex switch is off, the search for "\n"
# will fail as it should, unless by chance there are those two characters in
# the text.
#
# The object keeps track of whether its contents have been edited by the
# user, or have merely been set by calling setText().
#
# For the Find edit only, whenever the text is changed for any reason, it
# checks the sw_regex switch (passed to its constructor) and if it is True,
# it validates the text as a regular expression. If the text is not a valid
# regex the background of the field is turned pink. This is disabled for the
# Replace edits, as there is no "compile" for a regex replace string.
#
# The object knows an associated RecallMenuButton (passed to the constructor)
# and provides a used() method which is called (e.g. by the Next button) when
# the field contents are actually used and should be saved for recall.
#

# Here is the custom QValidator which performs a single functions: fixing a
# literal newline, should one be pasted in.

class FindRepValidator(QValidator):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.partner = parent
    def validate(self,string,posn):
        n = string.count(u'\n')
        if n :
            string = string.replace(u'\n',u'\\n')
            posn += n
        self.partner.check_regex()
        return QValidator.Acceptable, string, posn

class FindRepEdit(QLineEdit):
    def __init__(self, my_recall, ref_to_find, sw_regex, sw_respect_case, parent=None):
        super().__init__(parent)
        # If this is a Replace, save pointer to the Find string.
        # If this is the Find string, save None.
        self.find_ref = ref_to_find
        # save reference to regex and case switches, and hook their
        # toggled signal to our check_regex slot.
        self.regex = None # the compiled regex for the current string
        self.match = None # result of last match on regex
        self.reverse = None # regex compiled with REVERSE
        # in any case, save the switches for quick access
        self.sw_regex = sw_regex # quick access to regex switch
        self.sw_respect_case = sw_respect_case # ..and case switch
        sw_regex.toggled.connect(self.check_regex)
        sw_respect_case.toggled.connect(self.check_regex)
        # save reference to associated RecallMenuButton and link it to me.
        self.my_recall = my_recall
        my_recall.partner = self
        # hook up to be notified of a change in font choice
        fonts.notify_me(self.font_change)
        self.font_change() # and set the current fixed font
        # allow changing background color
        self.setAutoFillBackground(True)
        # establish our validator
        self.setValidator(FindRepValidator(self))
        # switch to show input is by user action or not
        self.user_written = False
        # connect my textEdited signal to set the above switch true,
        # indicating that the current contents is user-created.
        self.textEdited.connect( lambda: self.note_user(True) )
        # Fiddle with the look
        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed)

    def note_user(self, flag):
        self.user_written = flag

    # Override .setText and .clear methods to clear the user_written switch.
    # .setText is called for a programmatic change of text, e.g. loading our
    # text from a menu or user button. So if you load this field by selecting
    # a prior string from the recall button, and don't edit it, it will not
    # be user-edited and if used, will not be pushed on the recall stack. But
    # if you edit the recalled string in any way, that string will be saved.
    def setText(self,string):
        self.note_user(False)
        super().setText(string)
    def clear(self):
        self.note_user(False)
        super().clear()

    # Method called by the FindPanel when our string has found a match.
    def content_used(self):
        if self.user_written :
            self.my_recall.remember(self.text())
            self.note_user(False)

    # Slot to receive font's notification of a change - reset to
    # chosen font at default size
    def font_change(self):
        self.setFont(fonts.get_fixed())
        self.setMinimumHeight( self.fontMetrics().lineSpacing() + 4 )

    # Change the background color of this lineEdit to pink and set
    # a diagnostic message as our tool-tip.
    def set_background_pink(self,diagnostic):
        palette = self.palette()
        palette.setColor( QPalette.Normal, QPalette.Base, QColor('Pink') )
        self.setPalette(palette)
        self.setToolTip(diagnostic)
    # Change the bacground color to white and clear our tooltip text.
    def set_background_white(self):
        palette = self.palette()
        palette.setColor( QPalette.Normal, QPalette.Base, QColor('White') )
        self.setPalette(palette)
        self.setToolTip('')

    # Check the validity of our current contents as a regular expression and
    # incidentally have that compiled regex ready to use. This is called from
    # the validator whenever the text changes (we want to be sure the
    # validator is finished before we do this work, so it isn't called
    # directly for our own textChanged signal). It is also called by the
    # toggled signal from either sw_regex or sw_respect_case.
    #
    # Note that when regex.compile raises an error, the str() value of the
    # error is a diagnostic. We put that in our tooltip.
    def check_regex(self):
        if self.sw_regex.isChecked() and self.find_ref is None :
            # This is the Find field and regex is on: check and save our regex
            self.match = None
            self.reverse = None
            try:
                self.regex = RE_Compile( self.text(), self.sw_respect_case )
                self.set_background_white()
            except regex.error as whatever:
                self.regex = None # shows that find text is invalid
                self.set_background_pink('error: '+str(whatever))
        else:
            # Regex not on, or this is a Replace field. Unfortunately it
            # is not possible to check a Replace string until there exists
            # a match object.
            self.regex = None
            self.set_background_white()


# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Class of the user-programmable push buttons. Each button can store the
# values of the fields of the upper part of the panel.
#
# The values are stored in the form of a Python dict with these keys:
#
# 'label'  : 'string'    label for the button
# 'tooltip': 'string'    tooltip for the button, can be longer than the label
# 'case'   : True/False  case switch
# 'word'   : True/False  whole word switch
# 'regex'  : True/False  regex switch
# 'find'   : 'string'    current find string in quotes
# 'rep1/2/3' : 'string'  current rep strings 1/2/3 in quotes
# 'andnext' : True/False  +Next replace switch
# 'andprior' : True/False  +Prior replace switch
# 'all'    : True/False replace all switch
#
# Note that in version 1 we also supported 'insel':T/F and 'greedy':T/F. In
# version 2 we ignore these on input and do not write them on output.
#
# The button constructor takes the __repr__ string of a dict as argument
# and converts it to a dict if it can. See .load_dict() for requirements.
#
# When the button is clicked, the normal QPushButton.clicked signal goes to
# FindPanel where the dict values stored in the clicked button are queried
# and used to set the fields of the panel. When the button is right-clicked
# (Mac: ctl-clicked), we generate the user_button_ctl_click signal. This
# is also handled in the FindPanel, where the user is queried for a new
# label for the button, and the current widget values are written in this
# button's dict.
#
# The stored dict can be converted with its __repr__ method to a string
# for saving buttons to a file or to metadata.
#
import ast

class UserButton(QPushButton):
    user_button_ctl_click = pyqtSignal()

    model_dict = {'label':'(empty)', 'tooltip':None,'find':None,
                  'rep1':None, 'rep2':None, 'rep3':None,
                  'case':None, 'word':None, 'regex':None,
                  'andnext':None, 'andprior':None, 'all':None}
    model_types = {'label':type(''), 'tooltip':type(''),'find':type(''),
                   'rep1':type(''), 'rep2':type(''), 'rep3':type(''),
                   'case':type(False), 'word':type(False), 'regex':type(False),
                   'andnext':type(False), 'andprior':type(False), 'all':type(False)}

    def __init__(self, init_dict=None, parent=None):
        super().__init__(parent)
        self.setCheckable(False) # supposedly the default
        self.setContextMenuPolicy(Qt.PreventContextMenu) # we handle right-click
        # load either the given dictionary or go with the model
        if init_dict is None :
            self.udict = UserButton.model_dict.copy()
            self.setText(self.udict['label'])
            self.setToolTip('')
        else :
            self.load_dict(init_dict)

    # Return True when this button has anything loaded. The signal is that
    # the button label is not (empty).
    def is_active(self):
        return self.udict['label'] != UserButton.model_dict['label']

    # Trap a right-click or control-click and pass it as a signal to the
    # parent FindPanel. It will query the user for a new button label and
    # load our dict from the present find fields. Note originally we used
    # contextMenuEvent to generate this signal which should be the same, but
    # it elicited some funny behavior from Qt so we went to plain
    # mouseReleaseEvent.
    def mouseReleaseEvent(self,event):
        if 2 != int(event.button()) : # right- or control-click
            event.ignore()
            super(UserButton, self).mouseReleaseEvent(event)
        else:
            event.accept()
            self.user_button_ctl_click.emit()

    # Subroutine to load this button's values from a Python string that purports
    # to be the Python __repr__ of a dictionary.
    #
    # This is called during initialization, or when loading user Buttons from
    # a file or metadata. Since the dict string might be user-edited, we
    # treat it with suspicion. We require it to be a valid Python literal
    # form of a dict type. It must have an entry 'label':'string' with a
    # reasonable length of 'string'. Other entries are optional but each key
    # must exist in our model dict and have either True/False or a string
    # value. If any test fails we leave our existing dict alone.
    #
    def  load_dict(self,dictrepr):
        try:
            # Validate dictrepr as being strictly a literal dictionary: ast
            # will throw ValueError if it isn't a good literal and only a literal,
            # thus avoiding possible code injection.
            err = 'Not a valid dict literal'
            # The compiler chokes on literal tabs so replace with spaces.
            literal = ast.literal_eval(dictrepr.replace(u'\t',u' '))
            # Check its keys against model_dict. If it isn't a dict,
            # the .keys() call raises an error.
            ok_dict = UserButton.model_dict.copy()
            for key in literal.keys():
                err = 'bad value for '+key
                if key in ok_dict :
                    if literal[key] is not None :
                        if type(literal[key]) != UserButton.model_types[key]:
                            raise ValueError
                        if isinstance(literal[key],str) and len(literal[key]) > 512 : # cap possible strings
                            raise ValueError
                        # Correct type and reasonable length, use it
                        ok_dict[key] = literal[key]
                    else: # input is None, leave that field at None
                        continue
                else : # key not in model_dict, ignore it...
                    continue # ...probably 'greedy' or 'insel'..
            # Make sure it included a valid label key
            if 'label' not in literal :
                err = 'no label value in the input'
                raise ValueError
            # all good, go ahead and use it
            self.udict = ok_dict
            self.setText(ok_dict['label'])
            if 'tooltip' in ok_dict:
                self.setToolTip(ok_dict['tooltip'])
            else :
                self.setToolTip('')
        except:
            # some error raised, go to minimum default
            find_logger.error(err)
            find_logger.error(dictrepr)

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Finally, the class of a FindPanel itself.
#

class FindPanel(QWidget):
    USER_BUTTON_MAX = 24 # how many user buttons to instantiate
    USER_BUTTON_ROW = 4 # how many to put in a row of the grid
    SEARCH_BACKWARD = 1 # search control flags: Last, Prior
    SEARCH_LIMIT = 2    # First, Last
    # Characters that need to be escaped when treating an ordinary
    # string as a regex.
    RE_MAGIC_CHARS = regex.compile('([\[\]\(\)\*\.\?\+])')

    def __init__(self, my_book, parent=None):
        super().__init__(parent)
        # save access to the book, from which we get the editor and metadata
        # manager. Get references to the edit view and edit model.
        self.book = my_book
        self.editv = my_book.get_edit_view()
        self.editm = my_book.get_edit_model()
        # True while the current edit selection is the result of find
        self.selection_by_find = False
        # Register to read and write metadata class MD_FP, for its
        # format see _meta_read below.
        self.book.get_meta_manager().register(
            C.MD_FR, self._meta_read_rb, self._meta_write_rb )
        self.book.get_meta_manager().register(
            C.MD_FU, self._meta_read_ub, self._meta_write_ub )
        # Lay our UI out -- code at the end of the module.
        # This creates the objects:
        #    Checkboxes,
        # self.sw_respect_case
        # self.sw_whole_word
        # self.sw_regex
        # self.sw_in_range
        # self.sw_and_next
        # self.sw_and_prior
        # self.sw_do_all
        #    Find text field and four related pushbuttons
        # self.find_field
        # self.find_first
        # self.find_next
        # self.find_prior
        # self.find_last
        #    Multiple items
        # self.recall_buttons: 4 RecallMenuButtons [find, rep1, rep2, rep3]
        self.recall_buttons = [None,None,None,None]
        # self.replace_fields: 3 FindRepEdits [None, rep1, rep2, rep3]
        self.replace_fields = [None,None,None,None]
        # self.do_replace: 3 buttons in [None, rep1, rep2, rep3]
        self.do_replace = [None, None, None, None]
        # self.user_buttons: a list of 24 UserButtons
        self.user_buttons = []
        self._uic() # Make all the above.
        # Now hook up signals.
        # Connect a change in Regex to modify Whole Word.
        self.sw_regex.stateChanged.connect(self.regex_change)
        # Connect changes in And Next and And Prior
        self.sw_and_next.stateChanged.connect(self.andnext_change)
        self.sw_and_prior.stateChanged.connect(self.andprior_change)
        # Connect a change of In Selection to insel_change
        self.sw_in_range.stateChanged.connect(self.insel_change)
        # Connect the four do-search buttons to the do_search method
        # passing a 2-bit code to distinguish each.
        self.find_first.clicked.connect(
            lambda : self.start_search(FindPanel.SEARCH_LIMIT)
            )
        self.find_last.clicked.connect(
            lambda : self.start_search(FindPanel.SEARCH_BACKWARD+FindPanel.SEARCH_LIMIT)
            )
        self.find_prior.clicked.connect(
            lambda : self.start_search(FindPanel.SEARCH_BACKWARD)
            )
        self.find_next.clicked.connect( lambda : self.start_search(0) )
        # Also connect find_field's returnPressed to do a "next".
        self.find_field.returnPressed.connect( lambda : self.start_search(0) )
        # Connect the three do-replace buttons to replace_click().
        for j in [1,2,3] :
            self.do_replace[j].clicked.connect( self.replace_click )
        # Connect the actual editor's selectionChanged signal to a
        # slot where we note the selection is no longer our work.
        self.editv.get_actual_editor().selectionChanged.connect( self.edit_selection_change )
        # Connect its editFindKey signal to our edit_key_press method.
        self.editv.get_actual_editor().editFindKey.connect( self.edit_key_press )
        # Run through the user buttons and connect their clicked signals all
        # to user_button_click, and their user_button_ctl_click to user_button_load.
        for j in range(FindPanel.USER_BUTTON_MAX):
            self.user_buttons[j].clicked.connect(
                self.user_button_click )
            self.user_buttons[j].user_button_ctl_click.connect(
                self.user_button_load )
    # End of __init__

    # Come here when the state of the And Next or And Prior switch
    # changes. If one is "on" make sure the other is "off".
    def andnext_change(self,state):
        if state:
            self.sw_and_prior.setChecked(False)
    def andprior_change(self,state):
        if state:
            self.sw_and_next.setChecked(False)

    # Come here when the state of Regex changes. Disable or enable the Whole
    # Word switch because Whole Word doesn't apply to regex search.
    def regex_change(self,state):
        self.sw_whole_word.setEnabled(not state)

    # Come here when the editview changes its selection. We need this in order
    # to know, when Replace is requested, that the current selection is or is not
    # the result of a find.
    def edit_selection_change(self):
        self.selection_by_find = False

    # Come here when the editview traps a key event in the set C.KEYS_FIND.
    # Convert the signal into actions. The argument is the OR of event
    # modifiers and event key value, used in constants.py as a key signature
    # for quick lookup.
    def edit_key_press(self,kkey):
        if   kkey == C.CTL_F or kkey == C.CTL_SHFT_F :
            # ^f means, focus to Find panel, ^F means, with current selection
            # Make sure our panel is visible, focus in Find text,
            # with existing text selected for easy replacement.
            if not self.isVisible() :
                self.book.make_me_visible(self)
            self.find_field.setFocus(Qt.ShortcutFocusReason)
            self.find_field.selectAll()
            if kkey == C.CTL_SHFT_F :
                # Put the currently selected text in the Find field
                txt = self.editv.get_cursor().selectedText()
                # If it contains \n's, the FindRepEdit will fix them.
                # However if regex is set, and the text contains regex
                # magic characters, they need to be escaped.
                if self.sw_regex.isChecked() :
                    txt = FindPanel.RE_MAGIC_CHARS.sub('\\\\\\1',txt)
                self.find_field.setText(txt)
        elif kkey == C.CTL_G : # ^g == find Next
            self.start_search(0) # find forward
        elif kkey == C.CTL_SHFT_G : # ^G == find Prior
            self.start_search(FindPanel.SEARCH_BACKWARD)
        elif kkey == C.CTL_EQUAL : # ^= means, replace only
            self.start_replace(1,False,False,False)
        elif kkey == C.CTL_T : # ^t means, replace and find next
            self.start_replace(1,True,False,False)
        elif kkey == C.CTL_SHFT_T : # ^T means, replace and find prior
            self.start_replace(1,False,True,False)
        else :
            # Should not occur, log it
            find_logger.error('Unknown keystroke sent to find: {0}'.format(kkey))

    # Methods related to setting the valid range for searching. The current
    # range within which searching is done is defined by the selection of a
    # cursor managed by editview. Normally it is the whole document. When the
    # In Selection switch goes False->True, we have the editor set the range
    # to its current selection, provided that is large enough.
    #
    # Come here when the state of the In Selection switch changes.
    # Check that the current edit cursor has a selection of at least
    # 100 characters or 4 lines (arbitrary) and if so, set that as
    # the search range.
    def insel_change(self,state):
        if not state :
            # gone from on to off, clear range
            self.editv.clear_find_range()
            return
        # switch changed from off to on, check current selection
        tc = self.editv.get_cursor() # copy of edit cursor
        a = tc.selectionStart()
        z = tc.selectionEnd()
        ba = self.editm.findBlock(a)
        bz = self.editm.findBlock(z)
        if (100 > (z-a)) and ( 4 > ( bz.blockNumber() - ba.blockNumber() ) ):
            # selection nonexistent or too small, complain
            utilities.warning_msg(NO_SELECTION,NO_SELECTION_INFO,self)
            # following generates a recursive call to this method
            self.sw_in_range.setChecked(False)
            return
        self.editv.set_find_range()

    # Public method used by the Char and Word census panels to initiate a
    # search for a word or character. The arguments are:
    # * what: string to find
    # * case: boolean to set Respect Case
    # * word: boolean to set Whole Word
    # * regex: boolean to set Regex switch
    # * repl: optional replace string for rep 1
    #
    def find_this(self, what, case=False, word=False, regex=False, repl=None):
        self.find_field.setText(what)
        self.find_field.note_user(False) # don't push to recall list
        self.sw_respect_case.setChecked(case)
        self.sw_whole_word.setChecked(word)
        self.sw_regex.setChecked(regex)
        if repl : # is not None, set that string
            self.replace_fields[1].setText(repl)
            self.replace_fields[1].note_user(False)
        self.book.make_me_visible(self)
        self.start_search(FindPanel.SEARCH_LIMIT) # do a First

    # Execute one of the four do-search buttons. flag has SEARCH_LIMIT for
    # First and Last and SEARCH_BACKWARD for Last and Prior. Here we choose
    # the correct starting position and call real_search to execute one find.
    #
    # We choose starting positions so as to NOT find overlapping matches.
    # In choosing the start position we assume a find-range has been set, but
    # if it has not, the range cursor selects the whole document anyway.
    #
    # If a match is found, display that with editv.center_this(). If not,
    # beep and leave the edit cursor unchanged.

    def start_search(self, flag):
        # Begin with the position of the current selection, often the result
        # of a previous match. Search goes forward or backward from there.
        start_tc = self.editv.get_cursor()
        # Get the find range, usually the whole document but maybe less.
        range_tc = self.editv.get_find_range()
        if flag & FindPanel.SEARCH_LIMIT :
            # Doing First or Last, start at the limit of the range.
            if flag & FindPanel.SEARCH_BACKWARD :
                pos = range_tc.selectionEnd() # backward from the end
            else :
                pos = range_tc.selectionStart() # forward from the top
        else :
            # Doing Next or Prior, start from one end of the current
            # selection, adjusted to the top or bottom of the range.
            # These tests do not ensure the start point is inside the
            # range, but if they leave it outside the range, it was
            # such that no in-range hit was possible in any case.
            if flag & FindPanel.SEARCH_BACKWARD :
                pos = min( range_tc.selectionEnd(),
                           start_tc.selectionStart() )
            else : # forward
                pos = max( range_tc.selectionStart(),
                           start_tc.selectionEnd() )
        start_tc.setPosition(pos) # clears any selection
        # Look for a match, forward or backward from start_tc.
        find_tc = self.real_search( start_tc, flag & FindPanel.SEARCH_BACKWARD )
        # If find_tc has a selection, there was a match. However it could
        # fall wholly or in part, outside the range.
        if find_tc.hasSelection() and \
           find_tc.selectionStart() >= range_tc.selectionStart() and \
           find_tc.selectionEnd() <= range_tc.selectionEnd() :
            # We have a match inside the search range.
            self.find_field.content_used() # remember a successful use
            self.editv.center_this(find_tc) # make sure it is visible
            self.selection_by_find = True # ok to do a replace on it
        else :
            utilities.beep()

    # Actually perform a find. This is called either from start_search above
    # for a single find, or from replace_all below to find each possible
    # search target. start_tc is a cursor marking the starting position,
    # and flag is zero or SEARCH_BACKWARD. Also depends on the whole-word,
    # respect-case, and regex switches.

    def real_search(self, start_tc, flag):
        global RE_Compile
        if not self.sw_regex.isChecked() :
            # normal string search: apply the QTextDocument.find() method
            # passing our respect-case, whole-word and direction flags
            flags = QTextDocument.FindFlags(0)
            if (flag & FindPanel.SEARCH_BACKWARD) :
                flags |= QTextDocument.FindBackward
            if self.sw_respect_case.isChecked() :
                flags |= QTextDocument.FindCaseSensitively
            if self.sw_whole_word.isChecked() :
                flags |= QTextDocument.FindWholeWords
            find_tc = self.editm.find(self.find_field.text(),start_tc,flags)
        else :
            find_tc = start_tc # assume failure
            fp = self.find_field # short reference to FindRepEdit
            re = fp.regex # short reference to its regex
            if re : # is not None, the find text is a valid regex
                # Is this a reverse search?
                if flag & FindPanel.SEARCH_BACKWARD :
                    if fp.reverse is None :
                        # re was compiled for forward, compile a version
                        # for reverse, and save it in case we do this again
                        fp.reverse = RE_Compile(fp.text(), self.sw_respect_case, regex.REVERSE)
                    re = fp.reverse
                # re is now compiled appropriately for the direction
                text = self.editm.full_text() # get the whole document
                if flag & FindPanel.SEARCH_BACKWARD :
                    # reverse search begins at "endpos"
                    fp.match = re.search(text,0,start_tc.position())
                else : # forward search begins at "pos" argument
                    fp.match = re.search(text,start_tc.position())
                if fp.match : # is not None, we have a match
                    (a, z) = fp.match.span()
                    find_tc.setPosition(a)
                    find_tc.setPosition(z, QTextCursor.KeepAnchor)
        return find_tc

    # Execute one of the three do-replace buttons. Sample the current
    # state of the and-next, and-prior and do-all checkboxes and pass
    # them, with the button number, to start_replace.
    def replace_click(self,useless_boolean):
        rb = self.sender()
        self.start_replace(self.do_replace.index(rb),
                           self.sw_and_next.isChecked(),
                           self.sw_and_prior.isChecked(),
                           self.sw_do_all.isChecked() )

    # Execute the Replace action for a particular button 1, 2, or 3, and with
    # particular values for and-next and-prior and do_all. This method can be
    # called from replace_click above, or from a keystroke. Thus the key
    # action for ctl-t passes True for andnext, while shift-ctl-t passes True
    # for andprior.

    def start_replace(self, button, and_next, and_prior, do_all ):
        if do_all :
            # Global-replace is a whole different thing. Go do that.
            self.do_global_replace(button)
            return
        # Single replace: If the current selection is not the result of
        # a preceding Find, beep and do nothing.
        if not self.selection_by_find :
            utilities.beep()
            return
        # The current edit selection is the result of a Find. Proceed.
        tc = self.editv.get_cursor() # access to current selection
        pa = tc.selectionStart() # save index of start of selection
        rb = self.replace_fields[button] # quick ref to the button
        rb.content_used() # push current value on the recall list
        if not self.sw_regex.isChecked() or (self.find_field.match is None) :
            # Current selection does not need regex-style replacement,
            # so just replace it with the contents of the Rep button.
            tc.insertText(rb.text())
        else :
            # Current selection was (presumably) created by our current
            # regex. Since the selection hasn't changed, the match object
            # in find_field is still valid, so use it to generate the
            # replacement string. This is where we find out about a mistake
            # in the Replacement string syntax.
            try:
                new_text = self.find_field.match.expand( rb.text() )
                tc.insertText(new_text)
            except regex.error as whatever:
                diagnostic = str(whatever)
                utilities.warning_msg(
                    _TR( 'Find panel error in Replace text',
                         'Error in Replace text' ),
                    diagnostic, self )
                # the text was not inserted, so just exit
                return
            except IndexError as whatever:
                diagnostic = str(whatever)
                utilities.warning_msg(
                    _TR( 'Find panel error in Replace text',
                         'Error in Replace text' ),
                    diagnostic, self)
                return
        # Either of those insertText() calls left the cursor
        # without a selection and positioned at the end of the insert.
        # Reselect back to start so the inserted text is selected.
        # Besides being convenient, this properly positions the cursor
        # in case we are doing and_prior.
        tc.setPosition(pa, QTextCursor.KeepAnchor)
        self.editv.set_cursor(tc)
        if and_next :
            self.start_search(0)
        elif and_prior :
            self.start_search(FindPanel.SEARCH_BACKWARD)

    # Execute global replace. Here we are going to take advantage of the
    # excellent regex.finditer(string,pos,endpos) method to generate all
    # matches. If the current search is not already a regex, make it one by
    # escaping all regex magic characters in the find pattern. In the replace
    # pattern we only escape backslashes, because only "\#" and "\g<#>" are
    # supported in replace strings.
    #
    # Collect all the match objects in the search range in a list. (We have
    # to collect them all before doing the replace because we need the count
    # of matches to show the user.)
    #
    # When the user says go, we run backward through the list (from end of
    # document toward the top) converting each match to a cursor, and
    # replacing the selected text with the expanded match. This is all done
    # under an undo macro so it is a single undo.

    def do_global_replace(self, button):
        r_pattern = self.replace_fields[button].text()
        f_pattern = self.find_field.text()
        # prepare the "blah with blarg" before we possibly mung the texts
        info_with = f_pattern + _TR(
            "replace <string> with <string>",
            " with " ) + r_pattern
        if self.sw_regex.isChecked() :
            rex = self.find_field.regex
            if rex is None : # bad regex syntax
                utilities.beep()
                return
        else : # not a regex pattern, make it one.
            if f_pattern == '' : # empty pattern, not good for global find!
                utilities.beep()
                return
            # escape any magic chars in the rep and search patterns
            r_pattern = r_pattern.replace('\\','\\\\')
            f_pattern = FindPanel.RE_MAGIC_CHARS.sub('\\\\\\1',f_pattern)
            rex = regex.compile(f_pattern, (regex.M | 0 if self.sw_respect_case.isChecked else regex.I))
        range_tc = self.editv.get_find_range()
        full_text = self.editm.full_text()
        # In one statement get a match for every hit in the range.
        mlist = [ m for m in rex.finditer(full_text,range_tc.selectionStart(),range_tc.selectionEnd())]
        count = len(mlist)
        if 0 == count : # no hits
            utilities.beep()
            return
        # Tell the user how many hits we found and ask for permission.
        msg = _TR(
            "Global replace",
            "OK to replace %n occurences of",n=count
            )
        info_with = _TR(
            "replace <string> with <string>",
            "\nwith\n"
            )
        info_msg = self.find_field.text().__repr__() + info_with + self.replace_fields[button].text().__repr__()
        if not utilities.ok_cancel_msg(msg,info_msg,self) :
            return
        # Do the deed.
        find_tc = self.editv.get_cursor()
        find_tc.beginEditBlock() # start single-undo macro
        for j in reversed(range(count)):
            m = mlist[j]
            find_tc.setPosition(m.end())
            find_tc.setPosition(m.start(),QTextCursor.KeepAnchor)
            find_tc.insertText(m.expand(r_pattern))
        find_tc.endEditBlock()


    # Come here when any UserButton is clicked. The argument is a boolean
    # that we don't care about. All user buttons connect here; we find out
    # which one with the sender() method.
    #
    # If the button has defined contents, move its dict values into our
    # actual widgets. Some dict may be None, meaning, no change.
    #
    # As in V1, these values will NOT go in the recall stack for their
    # find/rep field. (The .setText method clears the note_user flag.) This
    # could be argued either way. The user can always recover the find/rep
    # string by hitting the userbutton again. OTOH, you might set things up
    # from a button but then want to alternate between that find string and a
    # different one and the recall button would be convenient for that.
    #
    # In V1 we set all switches to False and then let the udict values turn
    # them on. In V2 we permit a userbutton (loaded from a file) to have None
    # values, meaning leave the widget alone.

    def user_button_click(self,useless_boolean):
        ub = self.sender()
        if not ub.is_active(): return
        d = ub.udict
        if d['case'] is not None :
            self.sw_respect_case.setChecked(d['case'])
        if d['word'] is not None :
            self.sw_whole_word.setChecked(d['word'])
        if d['regex'] is not None :
            self.sw_regex.setChecked(d['regex'])
        if d['andnext'] is not None :
            self.sw_and_next.setChecked(d['andnext'])
        if d['andprior'] is not None :
            self.sw_and_prior.setChecked(d['andprior'])
        if d['all'] is not None :
            self.sw_do_all.setChecked(d['all'])
        if d['find'] is not None :
            self.find_field.setText(d['find'])
            # self.find_field.note_user(True) to make it eligible for recall
        if d['rep1'] is not None :
            self.replace_fields[1].setText(d['rep1'])
        if d['rep2'] is not None :
            self.replace_fields[2].setText(d['rep2'])
        if d['rep3'] is not None :
            self.replace_fields[3].setText(d['rep3'])

    # Come here when any UserButton gets a control-click. Prompt the user for
    # a new button label, and if one is given, load our current widget values
    # into the button's dict. Use direct access to the button's udict. Could
    # add a nice set-you method to UserButton but why?
    def user_button_load(self):
        ub = self.sender()
        d = ub.udict
        label = d['label'] if ub.is_active() else ''
        ubno = self.user_buttons.index(ub) + 1
        title = _TR(
            "Find panel user button load",
            "Loading button %n",n=ubno)
        caption = _TR(
            "Find panel user button load",
            "Enter a short label for button %n", n=ubno)
        label = utilities.get_string(title,caption,self,label)
        if label is None : # Cancel was clicked, make no change
            return
        # A null label string (hit Delete and then OK) means, clear the button
        if len(label) == 0:
            d = UserButton.model_dict.copy()
            ub.setText(d['label']) # puts (empty) in the button
            ub.setToolTip('')
            return
        # A non-null label means, load the dictionary with current data
        d.clear()
        d['label'] = str(label)
        ub.setText(label)
        ub.setToolTip('')
        d['case'] = self.sw_respect_case.isChecked()
        d['word'] = self.sw_whole_word.isChecked()
        d['regex'] = self.sw_regex.isChecked()
        d['andnext'] = self.sw_and_next.isChecked()
        d['andprior'] = self.sw_and_prior.isChecked()
        d['insel'] = self.sw_in_range.isChecked()
        d['all'] = self.sw_do_all.isChecked()
        d['find'] = self.find_field.text()
        d['rep1'] = self.replace_fields[1].text()
        d['rep2'] = self.replace_fields[2].text()
        d['rep3'] = self.replace_fields[3].text()

    # Functions to load and save user buttons to/from streams.
    # The mainwindow manages the File > Load/Save Find Buttons
    # including preparation of UTF-8 file streams.

    def user_button_input(self, stream):
        start_def = regex.compile('\s*(\d+)\s*:\s*\{')
        while not stream.atEnd():
            line = stream.readLine().strip()
            m = start_def.match(line)
            if m : # is not None we have a possible definition 17 : {
                but_no = int(m.group(1)) # guaranteed numeric by the regex
                # Special feature: button 99 means use highest empty button
                if but_no == 99 :
                    for i in reversed(range(FindPanel.USER_BUTTON_MAX)) :
                        if not self.user_buttons[i].is_active() :
                            but_no = i
                            break
                    # if loop ends with no hit, all buttons are active,
                    # and but_no remains 99 and will fail the next test.
                if (but_no >= 0) and (but_no < FindPanel.USER_BUTTON_MAX):
                    line = line[len(m.group(0))-1: ] # drop 17 : but keep {
                    while True:
                        if line.endswith('}') :
                            break
                        if stream.atEnd():
                            break
                        else:
                            line +=' '
                            line += stream.readLine().strip()
                    # line now contains from { to }, pass to button to
                    # validate and load, setting label and tooltip.
                    ub = self.user_buttons[but_no]
                    ub.load_dict(line) # always sets label
                # else not valid button-number - ignore it
            # else doesn't start with "n:{" - blank? comment? just skip it
        # end of file

    UB_BOILERPLATE = '''#
# Saved user-buttons from the Find panel. Each button definition starts with
# a number that says what button to set. The button numbers go from 0 (upper
# left button) to 23 (lower right button). Or use 99 to mean, the unused
# button with the highest number. The button number is followed by a colon.
#
# Next comes a Python dictionary { key:value, key:value...}. Each key is a
# string such as 'find' or 'regex' that names a part of the Find panel.
# Each value is either True, False, or a 'quoted string'. In a quoted string,
# every backslash must be doubled!
#
# The only required key is 'label'. Its value is a string that is the label
# on the button. Use the 'tooltip' key to give an explanation that pops up
# when the mouse is over the button.
'''
    def user_button_output(self, stream):
        # in start_def, {{ is doubled because format() is used on it
        start_def = '{0}: {{\t' # first line starts "button# : {\t"
        item_str = '\t{0} : {1}' # each item is "\tkey : repr"
        sep_str = ',\n' # comma, newline between items
        end_def = '\n}\n\n' # last line is "\n}" and two newlines
        stream << FindPanel.UB_BOILERPLATE
        for i in range(FindPanel.USER_BUTTON_MAX) :
            ub = self.user_buttons[i]
            if ub.is_active() :
                d = ub.udict
                stream << start_def.format(i)
                items = [
                    item_str.format(key.__repr__(),d[key].__repr__())
                    for key in sorted(d.keys()) ]
                stream << sep_str.join(items)
                stream << end_def

    # Functions to read and write the FINDPANEL metadata sections,
    # which are new in V2 (in V1 these items were saved in settings).
    #
    # The output of a writer is a single Python value. For MD_FR, the recall
    # buttons, it is a dict { "n" : [ str9, str8... ],...} for "n" in "0123"
    # and the strings being the recall stack strings. The strings are listed
    # in reverse order so that when they are read back, they are pushed onto
    # the recall stack in the correct order.

    def _meta_write_rb(self, sentinel):
        rbd = dict()
        for j in [0,1,2,3] :
            sl = []
            for k in reversed(range(self.recall_buttons[j].stack_size())) :
                sl.append(
                    self.recall_buttons[j].get_string(k)
                )
            rbd[str(j)] = sl
        return rbd

    # To read back the recall button metadata, we apply some sanity
    # checks because we permit user editing.

    def _meta_read_rb(self, sentinel, value, version):
        try:
            for (rbx, sl) in value.items() : # exception if not a dict
                try:
                    rbn = int(rbx) # exception if not numeric
                    self.recall_buttons[rbn].clear()
                    if len(sl) > RecallMenuButton.MAX_STRINGS : raise ValueError
                    for s in sl : # exception if not an iterable
                        if not isinstance(s, str) : raise ValueError
                        self.recall_buttons[rbn].remember(s) # exception if not in 0-3
                except : # some problem with rbx/sl
                    find_logger.error(
                        'Ignoring invalid FIND_RB {}:{}'.format(rbx,sl)
                        )
        except : # value does not support items()
            find_logger.error(
                'FIND_RB metadata is not a dict value'
                )

    # For MD_FU, the user buttons, the output is a dict { "n" : ubdict,...}
    # that is, one item per user button whose value is that buttons dict.

    def _meta_write_ub(self,sentinel):
        ubd = dict()
        for j in range(FindPanel.USER_BUTTON_MAX):
            if self.user_buttons[j].is_active() :
                ubd[str(j)] = self.user_buttons[j].udict
        return ubd

    # To read back the user button metadata we look for stupid errors in
    # the top-level value. However, the user button itself has a detailed
    # error-checker for the string repr of a dict, so we convert the dict
    # to a string and let the button do the checking.

    def _meta_read_ub(self,sentinel,value,version):
        if isinstance(value,dict):
            for (ubx, ubd) in value.items() :
                try :
                    ubn = int(ubx) # exception if not numeric
                    if not isinstance(ubd, dict) : raise ValueError
                    self.user_buttons[ubn].load_dict(ubd.__repr__())
                except :
                    find_logger.error(
                        'Ignoring invalid FIND_UB entry headed '+ubx
                        )
        else :
            find_logger.error(
                'FIND_UB metadata value not a dict, ignoring it'
                )

    def _uic(self):
        # Make the widgets and lay them out. Signals are connected
        # later on in __init__. Translate the button titles and tooltips.
        #
        # To put widgets in a frame, the frame must be the parent of the
        # layout that contains them. This frame is for the find controls, 4
        # checkboxes, the find text, and four go-buttons.
        frame_find = QFrame()
        frame_find.setFrameShape(QFrame.Panel)
        frame_find.setFrameShadow(QFrame.Raised)
        frame_find.setLineWidth(3)
        box_find = QVBoxLayout(frame_find)
        box_find.setContentsMargins(4,2,4,2)
        # Make the Respect Case switch.
        self.sw_respect_case = QCheckBox(
            _TR('Find panel checkbox','Respect Case','refers to letter case')
            )
        self.sw_respect_case.setToolTip(
            _TR('Find panel checkbox','When checked, "A" is different from "a"','button tooltip')
            )
        # Make the Whole Word switch.
        self.sw_whole_word = QCheckBox(
            _TR('Find panel checkbox','Whole Word')
            )
        self.sw_whole_word.setToolTip(
            _TR('Find panel checkbox','When checked, only whole words can be found','button tooltip')
            )
        # Make the Regex switch. Do not attempt to translate "regex".
        self.sw_regex = QCheckBox('Regex') # don't translate regex
        self.sw_regex.setToolTip(
            _TR('Find panel checkbox','When checked, the find and replace patterns are treated as regular expressions.','button tooltip')
            )
        # Make the In Selection switch.
        self.sw_in_range = QCheckBox(
            _TR('Find panel checkbox','In Range')
            )
        self.sw_in_range.setToolTip(
            _TR('Find panel checkbox','When checked, search and replace are restricted to a chosen block of text.','button_tooltip')
            )
        # Make the recall button for the Find text. Save its reference as [0] in
        # the list of four recall buttons.
        self.recall_buttons[0] = RecallMenuButton()
        self.recall_buttons[0].setToolTip(
            _TR('Find panel','Show the ten most recent entries in the Find text','tooltip')
            )
        # Make the edit field for the Find. Its constructor needs access to the
        # related recall button and to switches that affect parsing regexes.
        self.find_field = FindRepEdit(
            self.recall_buttons[0], None, self.sw_regex, self.sw_respect_case )
        self.find_field.setToolTip(
            _TR('Find panel','Enter the text to be matched. Pink color means a "regex" has incorrect syntax.')
            )
        # Make the First, Next, Prior and Last buttons, translating their names
        # and tooltips.
        self.find_first = QPushButton(
            _TR('Find panel button','First')
            )
        self.find_first.setToolTip(
            _TR('Find panel button','Find the first match in the document or selection','tooltip')
            )
        self.find_next = QPushButton(
            _TR('Find panel button','Next','Name of find-next button used later')
            )
        self.find_next.setToolTip(
            _TR('Find panel button','Find the next match to the right in the document or selection','tooltip')
            )
        self.find_prior = QPushButton(
            _TR('Find panel button','Prior','Name of find-prior button used later')
            )
        self.find_prior.setToolTip(
            _TR('Find panel button','Find the next match to the left in the document or selection','tooltip')
            )
        self.find_last = QPushButton(
            _TR('Find panel button','Last')
            )
        self.find_last.setToolTip(
            _TR('Find panel button','Find the last match in the document or selection','tooltip')
            )

        # Arrange the switches compressed to the left in a row.
        box_switches = QHBoxLayout()
        box_switches.setContentsMargins(4,2,4,2)
        box_switches.addWidget(self.sw_respect_case)
        box_switches.addWidget(self.sw_whole_word)
        box_switches.addWidget(self.sw_regex)
        box_switches.addWidget(self.sw_in_range)
        box_switches.addStretch() # compress to the left
        # Arrange the popup and find text in a row with the text maximized.
        box_find_text = QHBoxLayout()
        box_find_text.setContentsMargins(4,2,4,2)
        box_find_text.addWidget(self.recall_buttons[0], 0)
        box_find_text.addWidget(self.find_field, 1)
        # Arrange the four go-buttons in two groups of two
        box_4_buttons = QHBoxLayout()
        box_4_buttons.setContentsMargins(4,2,4,2)
        box_4_buttons.addWidget(self.find_first)
        box_4_buttons.addWidget(self.find_next)
        box_4_buttons.addStretch() # make a gap in the middle
        box_4_buttons.addWidget(self.find_prior)
        box_4_buttons.addWidget(self.find_last)
        # Stack those three groups in the framed vbox.
        box_find.addLayout(box_switches,0)
        box_find.addLayout(box_find_text,1)
        box_find.addLayout(box_4_buttons,0)

        # Create and lay out the replace objects within a frame.
        frame_reps = QFrame()
        frame_reps.setFrameShape(QFrame.Box)
        #frame_reps.setFrameShadow(QFrame.Plain)
        #frame_reps.setLineWidth(2)

        box_reps = QHBoxLayout(frame_reps)
        box_reps.setContentsMargins(4,2,4,2)

        # Create three recall popups and store them in recall_buttons[1:3],
        # three Replace fields linked to those popups and stored in
        # replace_fields[1:3], and three Replace buttons in do_replace[1:3].
        # Arrange each group in a row and stack them in a vbox layout.
        box_3_reps = QVBoxLayout()
        box_3_reps.setContentsMargins(4,2,4,2)
        for j in [1,2,3] :
            box_1_rep = QHBoxLayout()
            box_1_rep.setContentsMargins(4,2,4,2)
            self.recall_buttons[j] = RecallMenuButton()
            self.recall_buttons[j].setToolTip(
                _TR('Find panel',
                    'Show the ten most recent entries in Replace field {0}'.format(j),'tooltip')
                )
            self.replace_fields[j] = FindRepEdit(
                self.recall_buttons[j], self.find_field, self.sw_regex, self.sw_respect_case )
            self.replace_fields[j].setToolTip(
                _TR('Find panel','Enter text to replace the the last text matched.','tooltip')
                )
            self.do_replace[j] = QPushButton(
                _TR('Find panel','Replace','button that commands a replacement to happen')
                )
            self.do_replace[j].setToolTip(
                _TR('Find panel','Text that was matched is replaced with the text in Replace field {0}'.format(j),'tooltip')
                )
            self.do_replace[j].setSizePolicy(QSizePolicy.Minimum,QSizePolicy.Fixed)
            self.do_replace[j].setMaximumHeight(30)

            box_1_rep.addWidget(self.recall_buttons[j],0)
            box_1_rep.addWidget(self.replace_fields[j],1)
            box_1_rep.addWidget(self.do_replace[j],0)
            box_3_reps.addLayout(box_1_rep)

        # Make three checkboxes that modify replacements, and stack them in a vbox.
        self.sw_and_next= QCheckBox(
            _TR('Find panel checkbox','+Next')
            )
        self.sw_and_next.setToolTip(
            _TR('Find panel checkbox','When checked, after any Replace, Find the Next match to the right',
                '"Next" == name of find-next button')
            )
        self.sw_and_prior = QCheckBox(
            _TR('Find panel checkbox','+Prior')
            )
        self.sw_and_prior.setToolTip(
            _TR('Find panel checkbox','When checked, after any Replace, Find the Prior match to the left',
                '"Prior" == name of find-prior button')
            )
        self.sw_do_all = QCheckBox(
            _TR('Find panel checkbox','ALL!')
            )
        self.sw_do_all.setToolTip(
            _TR('Find panel checkbox','When checked, replace every matching text in the document or selection')
            )
        box_3_sws = QVBoxLayout()
        box_3_sws.setContentsMargins(4,2,4,2)
        box_3_sws.addWidget(self.sw_and_next)
        box_3_sws.addWidget(self.sw_and_prior)
        box_3_sws.addStretch() # space ALL! away from the others
        box_3_sws.addWidget(self.sw_do_all)
        # Put box_3_reps and box_3_sws in a row. This completes frame_reps.
        box_reps.addLayout(box_3_reps,1)
        box_reps.addLayout(box_3_sws,0)

        # Make the array of 24 User buttons. Initially we have no userdict
        # string for initializing them so they go in with (empty) contents.
        # The metadata reader may load some of them later.
        frame_user = QFrame()
        frame_user.setFrameShape(QFrame.Box)
        #frame_user.setFrameShadow(QFrame.Sunken)
        #frame_user.setLineWidth(3)
        grid_user = QGridLayout(frame_user)
        for i in range(FindPanel.USER_BUTTON_MAX):
            btn = UserButton()
            self.user_buttons.append(btn)
            grid_user.addWidget(btn,
                int(i/FindPanel.USER_BUTTON_ROW), int(i%FindPanel.USER_BUTTON_ROW)
                )

        # Create the total panel layout of three boxes stacked.
        vb1 = QVBoxLayout()
        vb1.addWidget(frame_find,0)
        vb1.addWidget(frame_reps,0)
        vb1.addStretch()
        vb1.addWidget(frame_user,0)
        self.setLayout(vb1)