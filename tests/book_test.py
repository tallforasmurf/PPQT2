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
Unit test for book.py - assume normal function is adequately tested
by mainwindow.sikuli - here exercise only the log and error messages.
'''
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Unit test module boilerplate stuff
#
# set up logging to a stream
import io
log_stream = io.StringIO()
import logging
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
    ret = (-1 < log_data.find(text)) & (-1 < log_data.find(level_dict[level]))
    if not ret:
        print('expected:',text)
        print('actual:',log_data)
    return ret
# add .. dir to sys.path so we can import ppqt modules which
# are up one directory level
import sys
import os
my_path = os.path.realpath(__file__)
test_path = os.path.dirname(my_path)
files_path = os.path.join(test_path,'Files')
ppqt_path = os.path.dirname(test_path)
sys.path.append(ppqt_path)
from PyQt5.QtWidgets import QApplication, QWidget
app = QApplication(sys.argv)
app.setOrganizationName("PGDP")
app.setOrganizationDomain("pgdp.net")
app.setApplicationName("PPQT2")
from PyQt5.QtCore import QSettings
settings = QSettings()
# load a list of one or more lines as a metadata section
import metadata
import utilities
import mainwindow

import book

import dictionaries
settings = QSettings()
settings.clear()
settings.setValue("paths/dicts_path",files_path)
settings.setValue("dictionaries/default_tag","en_GB")
import dictionaries
dictionaries.initialize(settings)

def load_section(mgr, section, line_list, vers=None):
    stream = utilities.MemoryStream()
    if vers :
        stream << metadata.open_line(C.MD_V, vers)
    stream << metadata.open_line(section)
    for line in line_list:
        stream.writeLine(line)
    stream << metadata.close_line(section)
    stream.rewind()
    mgr.load_meta(stream)
# dump all metadata and look at a specified section to see
# that it contains ALL but ONLY the lines in a list.
def check_section(mgr, section, line_list):
    stream = utilities.MemoryStream()
    mgr.write_meta(stream)
    stream.rewind()
    while True:
        line = stream.readLine()
        if stream.atEnd(): break
        if line == metadata.open_string(section) : break
    assert (not stream.atEnd())
    saved = set()
    for line in metadata.read_to(stream, section):
        saved.add(line)
    assert saved == set(line_list)
# load a one-line metadata section
def load_single(mgr, section, parm, vers=None):
    stream = utilities.MemoryStream()
    if vers :
        stream << metadata.open_line(C.MD_V, vers)
    stream << metadata.open_line(section,parm)
    stream.rewind()
    mgr.load_meta(stream)
def check_single(mgr, section, parm):
    stream = utilities.MemoryStream()
    mgr.write_meta(stream)
    stream.rewind()
    txt = stream.readAll()
    assert (section+' '+parm) in txt


mmw = mainwindow.MainWindow(settings)
# mainwindow opens a new-empty book, peek into it and grab a ref.

the_book = mmw.open_books[0]
# Put a little text in it so cursors are valid.
em = the_book.get_edit_model()
text = '''1. Now is the time
2. For all good bits
3. To come to the aid
4. Of their byte.
'''
em.setPlainText(text)
# the book has now registered its metadata rdrs/wtrs.
# we can invoke those indirectly by calling its meta manager
# for load_meta and write_meta.
# test all md readers
m = the_book.get_meta_manager()
import constants as C
s = C.MD_DH
# enable the next line to test warning message
load_single(m, s, 'DEADBEEF')
# test conversion of v1 parm
load_single(m, s, '\xc6\xd59\xf62,\x0cV\x7f\xe0\x11\xa8%\x19\xf1\xf8\xa7\x05\xf6\xc7', vers='0')
# test v2 parm format
load_single(m, s, b'\xc6\xd59\xf62,\x0cV\x7f\xe0\x11\xa8%\x19\xf1\xf8\xa7\x05\xf6\xc7', vers='2')
check_single(m, s, b'\xc6\xd59\xf62,\x0cV\x7f\xe0\x11\xa8%\x19\xf1\xf8\xa7\x05\xf6\xc7'.__repr__())

s = C.MD_MD
load_single(m, s, 'en_US')
check_single(m, s, 'en_US')
load_single(m, s, 'ukrainian')
assert check_log('Unable to open default dictionary ukrainian',logging.ERROR)
s = C.MD_ES
load_single(m, s, '18')
check_single(m, s, '18')
e = 'Ignoring invalid edit point size '
p = '100'
load_single(m, s, p)
assert check_log(e+p,logging.ERROR)
p = '2'
load_single(m, s, p)
assert check_log(e+p,logging.ERROR)
p = 'asdf'
load_single(m, s, p)
assert check_log(e+p,logging.ERROR)
s = C.MD_CU
p = '5 5'
load_single(m, s, p)
check_single(m, s, p)
e = 'Ignoring invalid cursor position metadata "'
p = 'x 5'
load_single(m, s, p)
assert check_log(e+p+'"',logging.ERROR)
p = '5 x'
load_single(m, s, p)
assert check_log(e+p+'"',logging.ERROR)
p = '-2 5'
load_single(m, s, p)
assert check_log(e+p+'"',logging.ERROR)
p = '1000 1000'
load_single(m, s, p)
assert check_log(e+p+'"',logging.ERROR)
# bookmarks n.b. the bookmarks list is not cleared but accumulates
s = C.MD_BM
l = ['1 1 1']
load_section(m, s, l)
check_section(m, s, l)
l = ['1 2 3','2 3']
load_section(m, s, l)
check_section(m, s, ['1 2 3','2 3 3'])
l = ['1 2 3','2 3 4','3 4 5','4 5 6','5 6 7','6 7 8','7 8 9','8 9 10','9 10 11']
load_section(m, s, l)
check_section(m, s, l)
e = 'Ignoring invalid bookmark metadata "'
l = ['0 2 3']
load_section(m, s, l)
assert check_log(e+l[0]+'"',logging.ERROR)
l = ['99 2 3']
load_section(m, s, l)
assert check_log(e+l[0]+'"',logging.ERROR)
l = ['1 2 3 4']
load_section(m, s, l)
assert check_log(e+l[0]+'"',logging.ERROR)
l = ['1 1000 2']
load_section(m, s, l)
assert check_log(e+l[0]+'"',logging.ERROR)
