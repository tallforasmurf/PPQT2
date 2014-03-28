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
                          mainwindow.py

Create and manage the main window, menus, and toolbars.
This code manages app-level global resources for example
  * the path(s) to user resources (the V1 "extras")
  * tags and paths to available spellcheck dicts
  * fonts (by way of initializing the font module)
  * the Help file and its display panel

Within the main window it creates the widgets that display the various
"view" objects.

Instantiates and manages multiple Book objects.

Support the user action of dragging a panel out of the tab-set to be an
independent window, or vice-versa.

'''
from PyQt5.QtWidgets import QMainWindow
import fonts

# TEMP TODO REMOVE vv
import os
temp_path = os.path.dirname(__file__)
# REMOVE ^^

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        # initialize our font db
        fonts.initialize()

        # TODO get default spell dict from settings
        self.default_dic_tag = "en_US"
        # TODO develop a dict of available dic-tags,
        #       key is tag, value is path to containing folder
        self.dictionary_paths = {'en_US':temp_path}