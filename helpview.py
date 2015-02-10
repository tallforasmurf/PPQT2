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
                          helpview.py

Create and manage the display of the Help file.

One object of class HelpWidget is created by the main window the first time
the user selects File>Show Help. The object initializes a window containing
only a QWebView, and populates it with either the distributed ppqt2help.html
file, or with a default text explaining how to open that file.

The window title is set to "PPQT Help Viewer".

Note: Using QWebView rather than the newer QWebEngineView because the older
web engine is adequate to display a manual. As of Qt5.4, the WebEngine does
not support the FindFlag FindWrapsAroundDocument, which is kind of important.
If some later version of Qt adds that to WebEngine and deprecates WebView the
change is very simple to make.

If the user closes the help widget, control comes to the closeEvent()
slot. The event is ignored, meaning the widget is not closed. However,
it calls self.hide() so that the widget becomes invisible.

Each time the user selects File>Show Help, the main window calls the
object's setVisible(True) method, making it appear if it was hidden.
It reappears at the same place and size as when it was 'closed'.

The widget traps key events only to look for the Find, Find-Next, and
Find-prior keys. It implements a simple Find dialog using
utilities.get_find_string.

'''
import paths # for extras path
import utilities # for get_find_string
import constants as C
import os # for access, path.join
# no need for logging
from PyQt5.QtCore import QCoreApplication, QUrl
_TR = QCoreApplication.translate
from PyQt5.QtWidgets import QWidget, QHBoxLayout
from PyQt5.QtWebKitWidgets import QWebPage, QWebView

# TODO : find a way to get this translated.
DEFAULT_HTML = '''
<h1>PPQT Help Viewer</h1>
<p>This is not the real help text!
The <i>real</i> Help text is very helpful.
It is stored in a file named <b><tt>ppqt2help.html</tt></b>.
That file should be in the "Extras" folder distributed with PPQT.
</p><p>
Please choose <b>File : Preferences...</b> to open the Preferences dialog.
</p><p>
In that dialog, set the correct path to the "Extras" folder.
If the ppqt2help file is in that folder, it will appear here.
</p><p>
If the ppqt2help file is not in the Extras folder, you need to find it
and put it there.
</p>
'''
class HelpWidget(QWidget) :

    def __init__( self ) :
        super().__init__() # no parent; we are a standalone window
        # Set window title to translated value
        self.setWindowTitle(
            _TR( "title of help viewer window", "PPQT Help Viewer" ) )
        # Initialize saved geometry, see showEvent()
        self.last_shape = None
        # Initialize find string, see find_action().
        self.find_text = None
        # Create our complete layout consisting of a web page.
        self.view = QWebView()
        hb = QHBoxLayout()
        hb.addWidget(self.view)
        self.setLayout(hb)
        # Look for the help text file and load it if found.
        self.html_path = None # assume the worst
        self.load_html( paths.get_extras_path() )
        if self.html_path is None :
            # The first try to load the help text failed. Load default text
            # and set up for a signal when the Extras path changes.
            self.view.setHtml( DEFAULT_HTML )
            paths.notify_me( self.path_change )

    # Called during initialization and, if not successful then, called when
    # the extras path changes to try again. Sets self.html_path when
    # successful.

    def load_html( self, extras_path ) :
        html_path = os.path.join( extras_path , 'ppqt2help.html' )
        if os.access( html_path, os.R_OK ) :
            # it exists, load it and save self.html_path
            try :
                f = None # in case open fails, define f
                f = open( html_path, 'r', encoding='UTF-8' )
                base_url = QUrl.fromLocalFile( os.path.join(extras_path,'sphinx') + os.path.sep )
                self.view.setHtml( f.read(), base_url )
                self.html_path = html_path # show we are good now
            except :
                pass # just silently fail :-(
            finally :
                if f : f.close()

    # Slot to receive the pathChanged signal from the paths module. That
    # signal is given when any of the standard paths are changed. If we are
    # still looking for ppqt2help.html, try again to load the file. Don't
    # bother testing to see if it was extras that changed, just do it.

    def path_change( self, code ) :
        if self.html_path is None :
            self.load_html( paths.get_extras_path() )

    def closeEvent( self, event ) :
        self.last_shape = self.saveGeometry()
        event.ignore()
        self.hide()
        return super().closeEvent(event)

    def showEvent( self, event ) :
        if self.last_shape : # is not None
            self.restoreGeometry( self.last_shape )

    # Handle keypress events for ^f ^g

    def keyPressEvent( self, event ) :
        kkey = int( int(event.modifiers()) & C.KEYPAD_MOD_CLEAR) | int(event.key() )
        if kkey == C.CTL_F :
            event.accept()
            self.find_action()
        elif kkey == C.CTL_G :
            event.accept()
            self.find_next_action()
        elif kkey == C.CTL_SHFT_G :
            event.accept()
            self.find_prior_action()
        else :
            super().keyPressEvent(event)

    # Methods for a basic Find operation. Other modules e.g. noteview have a
    # custom Edit menu with Find/Next as menu actions. Here we do not support
    # any editing actions, so support Find/Next/Prior only via keystrokes.
    #
    # Use the simple find dialog in utilities to get a string to look for.
    # Initialize the dialog with up to 40 chars of the current selection. If
    # the user clicks Cancel in the Find dialog, self.find_text is None; if
    # the user just clears the input area and clicks OK the find_text is an
    # empty string. In either case do nothing.
    #
    # Following a successful find, the found text is selected in the view, so
    # if you do ^f again without disturbing that selection, that text is back
    # in the dialog to be used or replaced. So ^f+Enter is the same as ^g.

    FIND_NORMAL = QWebPage.FindWrapsAroundDocument
    FIND_PRIOR = QWebPage.FindWrapsAroundDocument | QWebPage.FindBackward


    def find_action(self):
        prep_text = self.view.selectedText()[:40]
        self.find_text = utilities.get_find_string(
            _TR('Help viewer find dialog','Text to find'),
            self, prep_text)
        if self.find_text : # is not None nor an empty string
            self._do_find( self.FIND_NORMAL )

    # For ^g Find Next, if there is no active find-text pretend that ^f was
    # hit. If there was a prior search, repeat the search.
    def find_next_action(self):
        if self.find_text : # is not None nor an empty string
            self._do_find( self.FIND_NORMAL )
        else :
            self.find_action()

    # for ^G Find Prior, same as for ^g but backward.
    def find_prior_action(self):
        if self.find_text :
            self._do_find( self.FIND_PRIOR )
        else :
            self.find_action()

    # The actual search, factored out of the above actions. Because the
    # search wraps around, if it fails, it fails, and that's that.

    def _do_find( self, find_flags ) :
        if not self.view.page().findText( self.find_text, find_flags ):
            utilities.beep()
