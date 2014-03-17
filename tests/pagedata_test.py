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
Unit test for pagedata.py
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
# load a list of one or more lines as a metadata section
def load_section(mgr, section, line_list, vers=None):
    stream = metadata.MemoryStream()
    if vers :
        stream << '{{VERSION '+vers+'}}\n'
    stream << metadata.open_line(section)
    for line in line_list:
        stream.writeLine(line)
    stream << metadata.close_line(section)
    stream.rewind()
    mm.load_meta(stream)
# dump all metadata and look at a specified section to see
# that it contains ALL but ONLY the lines in a list.
def check_section(mgr, section, line_list):
    stream = metadata.MemoryStream()
    mm.write_meta(stream)
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

# add .. dir to sys.path so we can import ppqt modules which
# are up one directory level
import sys
import os
my_path = os.path.realpath(__file__)
test_path = os.path.dirname(my_path)
ppqt_path = os.path.dirname(test_path)
sys.path.append(ppqt_path)
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
from PyQt5.QtCore import QObject
import mainwindow
import metadata
import constants as C
import book
import pagedata

mw = mainwindow.MainWindow()
the_book = book.Book(mw)
pagem = the_book.get_page_model()
mm = the_book.metamgr
# Load the document with known text
editm = the_book.get_edit_model()
doc = '''A12345678
B12345678
C12345678
D12345678'''
editm.setPlainText(doc)
# Load page metadata corresponding to those lines
# Note pf X contains \u2002
pagemats = '''0 A \pf0\pf1\pf\u2002A\pf3\pf4 1 0 1
10 B \pf0\pf1\pf\u2002B\pf3\pf4 0 0 2
20 C \pf0\pf1\pf\u2002C\pf3\pf4 0 0 3
30 D \pf0\pf1\pf\u2002D\pf3\pf4 0 0 4'''.split('\n')
load_section(mm, C.MD_PT, pagemats)
assert pagem.active()
assert pagem.page_count() == 4
assert pagem.filename(0) == 'A'
assert pagem.filename(3) == 'D'
assert pagem.filename(4) == ''
assert pagem.proofers(0)[2] == 'pf A'
assert pagem.proofers(3)[2] == 'pf D'
assert pagem.proofers(4) == []
assert pagem.folios(0)[0] == C.FolioRuleSet
assert pagem.folios(3)[0] == C.FolioRuleAdd1
assert pagem.folios(3)[2] == 4
pagem.set_folios(3,rule=C.FolioRuleSet,nbr=9)
assert pagem.folios(3)[2] == 9
assert pagem.folios(3)[0] == C.FolioRuleSet
pagem.set_folios(2,fmt=C.FolioFormatUCRom)
assert pagem.folios(2) == [C.FolioRuleAdd1,C.FolioFormatUCRom,3]
line_list = '''0 A \pf0\pf1\pf\u2002A\pf3\pf4 1 0 1
10 B \pf0\pf1\pf\u2002B\pf3\pf4 0 0 2
20 C \pf0\pf1\pf\u2002C\pf3\pf4 0 1 3
30 D \pf0\pf1\pf\u2002D\pf3\pf4 1 0 9'''.split('\n')
check_section(mm, C.MD_PT, line_list)
# force various errors in read_pages and check logging
# wrong number of items
load_section(mm, C.MD_PT, ['0 A \pf0\pf1\pf\u2002A\pf3\pf4 1 0'])
assert check_log('invalid line of page metadata:',logging.ERROR)
load_section(mm, C.MD_PT, ['0 A \pf0\pf1\pf\u2002A\pf3\pf4 1 0 9 9'])
assert check_log('invalid line of page metadata:',logging.ERROR)
# page offset off the end of the document or negative
load_section(mm, C.MD_PT, ['100000 A \pf0\pf1\pf\u2002A\pf3\pf4 0 0 0'])
assert check_log('invalid line of page metadata:',logging.ERROR)
load_section(mm, C.MD_PT, ['-1 A \pf0\pf1\pf\u2002A\pf3\pf4 0 0 0'])
assert check_log('invalid line of page metadata:',logging.ERROR)
# Load the document from an actual book and scan it.
# Purely for test purposes, re-call the __init__ function to
# clear the existing data.
pagem.__init__(the_book)
assert not pagem.active()

fx_path = test_path+'/Files/'
sb_path = fx_path+'small_book.txt'
sb = open(sb_path,'r',encoding='Latin-1')
editm.setPlainText(sb.read())
pagem.scan_pages()
assert pagem.active()
# following depends on contents of small_book.txt:
# 27 pages, last proofer list ends in bazongas!
# note it has one line of text preceding page 1.
assert pagem.page_count() == 27
assert pagem.filename(26) == '027'
assert pagem.proofers(26)[3] == 'bazongas!'
# Test basics of page_index()
assert pagem.page_index(0) is None
pz = editm.lastBlock().position() + editm.lastBlock().length() - 2
p1 = editm.findBlockByLineNumber(1).position()
for j in range(p1) :
    assert pagem.page_index(j) is None
assert pagem.page_index(p1) == 0
assert pagem.page_index(pz) == 26
# time a bunch of calls to page_index using a sequence of
# random positions in p1..pz that have some locality of reference.
import timeit
import random
def jumper():
    global pagem,pz,p1
    hops = random.sample(range(200),20) # 20 little moves
    jumps = random.sample(range(pz-p1),50) # 50 bigger moves
    for J in jumps:
        for H in hops:
            x = pagem.page_index(J+H)
#pi_time = timeit.timeit(jumper,number=10)
#print(pi_time)
# time to execute 10,000 calls: 0.073 sec, or 0.0000073 sec/call,
# or 7usec call. This will do at least for now.
