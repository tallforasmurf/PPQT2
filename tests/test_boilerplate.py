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
Common boilerplate for test drivers:

  import test_boilerplate as T
  T.log_stream is the log
  T.check_log(text, level) to verify "text" appears in log at log-level
    e.g. assert T.check_log('message text',logging.ERROR)

  T.set_up_paths() to create T.path_to_Files, T.path_to_Tests, T.path_to_Sikuli
  T.make_app() to create globals T.app, T.settings
  T.make_main() to create T.main window object, T.book as "new"
  T.open(path,title) to make T.book open on real book
     path defaults to path_to_Files, title defaults to small_book.txt
'''
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QSettings
from PyQt5.QtCore import Qt,QPoint,QSize
import sys
import os
import logging
import io
log_stream = io.StringIO()
logging.basicConfig(stream=log_stream,level=logging.INFO)
def check_log(text, level):
    '''check that the log_stream contains the given text at the given level,
       and rewind the log, then return T/F'''
    global log_stream
    level_dict = {logging.DEBUG:'DEBUG',
                  logging.INFO:'INFO',
                  logging.WARN:'WARN',
                  logging.ERROR:'ERROR',
                  logging.CRITICAL:'CRITICAL'}
    log_data = log_stream.getvalue()
    x = log_stream.seek(0)
    x = log_stream.truncate()
    t = (1 < log_data.find(text)) & (-1 < log_data.find(level_dict[level]))
    if not t: print('log contains:\n',log_data) # about to fail an assertion
    return t

# Assume we are nested somewhere within ppqt,
# find that and set up paths to ppqt/Tests, ppqt/Tests/Files,
# and ppqt/Tests/Sikuli
path_to_Files = '.'
path_to_Tests = '.'
path_to_Sikuli = '.'

def set_up_paths():
    global path_to_Files,path_to_Sikuli,path_to_Tests
    _path = os.path.realpath(__file__)
    while 'ppqt' != os.path.basename(_path):
        _path = os.path.dirname(_path)
    sys.path.append(_path) # allow imports of ppqt modules
    path_to_Tests = os.path.join(_path,'Tests')
    path_to_Files = os.path.join(path_to_Tests,'Files')
    os.chdir(path_to_Files) # make that cwd
    path_to_Sikuli = os.path.join(path_to_Tests,'Sikuli')

# Create an app with minimal settings: dict path to Tests/Files
# and default dict en_US
app = None
settings = None
def make_app():
    global app, settings
    app = QApplication(sys.argv)
    app.setOrganizationName("PGDP")
    app.setOrganizationDomain("pgdp.net")
    app.setApplicationName("PPQT2")
    settings = QSettings()
    settings.clear()
    settings.setValue("paths/dicts_path",path_to_Files)
    settings.setValue("dictionaries/default_tag","en_US")
    settings.setValue("mainwindow/position",QPoint(50,50))

# Create the main window, have it open a test book and from it grab the
# book object. set_up_paths() must have been called.
main = None
book = None
def make_main():
    global main, book, settings
    from mainwindow import MainWindow
    main = MainWindow(settings)
    book = main.open_books[0]

def open_book(book_path=None, book_title=None, no_meta=False ):
    global main, book
    from utilities import path_to_stream
    _p = path_to_Files if book_path is None else book_path
    _b = 'small_book.txt' if book_title is None else book_title
    _f = os.path.join(_p,_b)
    if no_meta :
        import constants as C # set_up_paths must have been called by now
        _m = _f + '.' + C.METAFILE_SUFFIX
        if os.path.exists(_m) :
            os.remove(_m)
    _fbts = path_to_stream(_f)
    main._open(_fbts)
    book = main.open_books[main.focus_book]
