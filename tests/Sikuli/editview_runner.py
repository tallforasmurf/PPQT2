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
Unit test #2 for editview.py: run the window for Sikuli
'''
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Unit test module boilerplate stuff
#
# Assume we are nested somewhere within ppqt,
# find that and set up paths to ppqt/Tests, ppqt/Tests/Files,
# and ppqt/Tests/Sikuli
#
import sys
import os
path = os.path.realpath(__file__)
while 'ppqt' != os.path.basename(path):
    path = os.path.dirname(path)
sys.path.append(path) # allow imports of ppqt modules
path_to_Tests = os.path.join(path,'Tests')
path_to_Files = os.path.join(path_to_Tests,'Files')
path_to_Sikuli = os.path.join(path_to_Tests,'Sikuli')

# Create an app
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)
# Make the main window, the book needs it
import mainwindow
mw = mainwindow.MainWindow()
# Make a Book
import book
the_book = book.Book(mw)
# Load the book with our test book
from PyQt5.QtCore import QFile, QIODevice, QTextStream
path_to_sb = os.path.join(path_to_Files,'small_book.txt')
qfile = QFile(path_to_sb)
qfile.open(QIODevice.OpenModeFlag.ReadOnly)
doc_stream = QTextStream(qfile)
the_book.new_book(doc_stream, 'small_book.txt', path_to_Files)
# Load the words data with the vocabulary
the_book.wordm.refresh()
# put it on the screen
the_book.editv.show()
app.exec_()
