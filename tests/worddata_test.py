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
Unit test for worddata.py
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
    return (-1 < log_data.find(text)) & (-1 < log_data.find(level_dict[level]))

# add .. dir to sys.path so we can import ppqt modules which
# are up one directory level
import sys
import os
path = os.path.realpath(__file__)
path = os.path.dirname(path)
path = os.path.dirname(path)
sys.path.append(path)
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
from PyQt5.QtCore import QObject
import metadata
import constants as C
import worddata
import book
fake_main_window = QObject()
the_book = book.Book(fake_main_window)
wd = the_book.wordm
mm = the_book.metamgr
# Test scanno read, test, and save
words = ['orio','arid','he','be']
stream = metadata.MemoryStream()
stream << metadata.open_line(C.MD_SC)
for word in words:
    stream.writeLine(word)
stream << metadata.close_line(C.MD_SC)
stream.rewind()
mm.load_meta(stream)
for word in words:
    assert wd.scanno_test(word)
assert not(wd.scanno_test('and'))
stream = metadata.MemoryStream()
mm.write_meta(stream)
stream.rewind()
while True:
    line = stream.readLine()
    if stream.atEnd(): break
    if line == metadata.open_string(C.MD_SC) : break
assert (not stream.atEnd())
for line in metadata.read_to(stream, C.MD_SC):
    assert line in words
# test good-word read and save
words = ['bon','bueno','rad','superb']
stream = metadata.MemoryStream()
stream << metadata.open_line(C.MD_GW)
for word in words:
    stream.writeLine(word)
stream << metadata.close_line(C.MD_GW)
stream.rewind()
mm.load_meta(stream)
stream = metadata.MemoryStream()
mm.write_meta(stream)
stream.rewind()
while True:
    line = stream.readLine()
    if stream.atEnd(): break
    if line == metadata.open_string(C.MD_GW) : break
assert (not stream.atEnd())
for line in metadata.read_to(stream, C.MD_GW):
    assert line in words

