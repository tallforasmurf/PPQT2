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
my_path = os.path.realpath(__file__)
test_path = os.path.dirname(my_path)
ppqt_path = os.path.dirname(test_path)
sys.path.append(ppqt_path)
files_path = os.path.join(test_path, 'Files')
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)
app.setOrganizationName("PGDP")
app.setOrganizationDomain("pgdp.net")
app.setApplicationName("PPQT2")
from PyQt5.QtCore import QSettings
settings = QSettings()
settings.clear()
settings.setValue("paths/dicts_path",files_path)
settings.setValue("dictionaries/default_tag","en_GB")
import dictionaries
dictionaries.initialize(settings)

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
from PyQt5.QtCore import QObject, QSettings
import mainwindow
import metadata
import utilities
import constants as C
import worddata
import book
# load a list of one or more words as a metadata section
def load_section(mgr, section, wordlist, vers=None):
    stream = utilities.MemoryStream()
    if vers :
        stream << '{{VERSION '+vers+'}}\n'
    stream << metadata.open_line(section)
    for word in wordlist:
        stream.writeLine(word)
    stream << metadata.close_line(section)
    stream.rewind()
    mm.load_meta(stream)
# save metadata and verify that a section has ALL and ONLY
# the words in a list
def check_section(mgr, section, wordlist):
    stream = utilities.MemoryStream()
    mm.write_meta(stream)
    stream.rewind()
    while True:
        line = stream.readLine()
        if stream.atEnd(): break
        if line == metadata.open_string(section) : break
    assert (not stream.atEnd())
    saved = set()
    for line in metadata.read_to(stream, section):
        if section == C.MD_VL :
            line = line.split()[0]
        saved.add(line)
    assert saved == set(wordlist)

# Create a main window, which creates an untitled book
mw = mainwindow.MainWindow(settings)
# cheat and reach into the mainwindow and get that book
the_book = mw.open_books[0]
# access its word data manager and meta manager
wd = the_book.wordm
mm = the_book.metamgr
# -------- Test scanno read, test, and save
scannos = ['orio','arid','he','be']
load_section(mm, C.MD_SC, scannos)
for word in scannos:
    assert wd.scanno_test(word)
assert not(wd.scanno_test('and'))
check_section(mm, C.MD_SC, scannos)
assert (not wd.scanno_test('and'))
assert wd.scanno_test('arid')
# -------- test good-word read and save
goods = ['bon','bueno','spellfail','superb']
load_section(mm, C.MD_GW, goods)
check_section(mm, C.MD_GW, goods)

# -------- test bad-word read and save
bads = ['mal','horrid','deformed','buggy']
load_section(mm, C.MD_BW, bads)
check_section(mm, C.MD_BW, bads)

# --- log error on good in bad and bad in good
load_section(mm, C.MD_GW, ['horrid'])
assert check_log('good and bad words', logging.WARN)
load_section(mm, C.MD_BW, ['bueno'])
assert check_log('good and bad words', logging.WARN)

# --- test good- bad-words are additive but scannos replaces
load_section(mm, C.MD_GW, ['excellent'])
check_section(mm, C.MD_GW, goods+['excellent'])
load_section(mm, C.MD_BW, ['rotten'])
check_section(mm, C.MD_BW, bads+['rotten'])
scannos = ['bate','hate']
load_section(mm, C.MD_SC, scannos)
check_section(mm, C.MD_SC, scannos)

# --- test all the things that make word_read barf
load_section(mm, C.MD_VL, [' ']) # empty line
assert check_log('of word census list invalid',logging.WARN)
load_section(mm, C.MD_VL, ['whatever notaninteger notaset'])
assert check_log('of word census list invalid',logging.WARN)
load_section(mm, C.MD_VL, ['whatever 9 {6,syntaxerror'], '2')
assert check_log('of word census list invalid',logging.WARN)
load_section(mm, C.MD_VL, ['whatever 9 notaset'], '2')
assert check_log('of word census list invalid',logging.WARN)

# --- test addition of words
# bitset properties in v1
vocab = ['aaa', 'aab', 'aac']
load_section(mm, C.MD_VL, [vocab[0]+' 17 255'],'1')
assert wd.word_count() == 1
assert wd.word_at(0) == vocab[0]
(count, prop_set) = wd.word_info_at(0)
assert count == 17
assert worddata.MC in prop_set
assert worddata.ND in prop_set
assert worddata.HY in prop_set
assert worddata.AP in prop_set
assert worddata.XX in prop_set
load_section(mm, C.MD_VL, [vocab[1]+' 23 '+ str(prop_set).replace(' ','')],'2')
assert wd.word_count() == 2
assert wd.word_at(1) == vocab[1]
(count, prop_set2) = wd.word_info_at(1)
assert prop_set == prop_set2
assert count == 23
assert wd.word_count_at(1) == count
assert wd.word_props_at(1) == prop_set2
# check save format, can't use check_section
stream = utilities.MemoryStream()
mm.write_meta(stream)
stream.rewind()
while True:
    line = stream.readLine()
    if stream.atEnd(): break
    if line == metadata.open_string(C.MD_VL) : break
assert not stream.atEnd()
for line in metadata.read_to(stream,C.MD_VL):
    parts = line.split()
    assert parts[0] in vocab
    assert parts[1] in ("17","23")
    assert parts[2] == "{9,3,4,5,6}"

# exercise all branches of _add_token and _count, taking advantage of fact
# that a single-token meta line is passed to _add_token. Rather than try to
# control the index just use word_index
def test_props(word,props):
    load_section(mm, C.MD_VL, [word], '2')
    return check_props(word,props)
def check_props(word,props):
    w = word.split('/')[0] # drop alt tag if any
    j = wd.word_index(w)
    assert j >= 0
    ps = wd.word_props_at(j)
    return ps == props
assert test_props('lower',{worddata.LC})
assert test_props('UPPER',{worddata.UC})
assert test_props('Mixed',{worddata.MC})
assert test_props("man's",{worddata.LC,worddata.AP})
assert test_props("man\u02bcs",{worddata.LC,worddata.AP,worddata.XX})
assert test_props("1920s",{worddata.LC,worddata.ND,worddata.XX})
assert test_props("1920-29",{worddata.HY,worddata.ND})
assert test_props('xyxyx',{worddata.LC,worddata.XX})
assert test_props('bonjour/fr_FR',{worddata.LC,worddata.AD})
assert test_props('horrid',{worddata.LC,worddata.XX}) # badword
assert test_props('spellfail',{worddata.LC}) # goodword
# get into hyphenations now
assert test_props("mother-in-law",{worddata.LC,worddata.HY})
assert check_props("mother",{worddata.LC})
assert check_props("in",{worddata.LC})
assert check_props("law",{worddata.LC})
# check-spelling
assert (not wd.spelling_test('lower'))
assert wd.spelling_test('horrid')
# recheck-spelling
j = wd.word_index('Mixed')
ps = wd.word_props_at(j)
ps |= {worddata.XX}
wd.recheck_spelling(the_book.get_speller())
ps = wd.word_props_at(j)
assert worddata.XX not in ps
# testing refresh with a small "document"
doc = '''Now is the time
for all good men
to enjoy my mother-in-law's ph[oe]nix
'''
vocab = doc.split()
vocab.append('mother')
vocab.append('in')
vocab.append("law's")
doc += '''<span lang='fr_FR'>eau de mal de mer</span>.'''
vocab.append('mal')# n.b. "mal" is in bad-words so won't get /fr_FR
vocab.append('eau/fr_FR')
vocab.append('de/fr_FR')
vocab.append('mer/fr_FR')
editm = the_book.get_edit_model()
editm.setPlainText(doc)
wd.refresh()
check_section(mm,C.MD_VL,vocab)
# testing refresh with a small and big document
#import timeit
#fx_path = test_path+'/Files/'
#sb_path = fx_path+'small_book.txt'
#sb = open(sb_path,'r',encoding='Latin-1')
#editm.setPlainText(sb.read())
#sb_time = timeit.timeit(wd.refresh, number=1)
#print(sb_time)