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
Unit test for utilities.py. Originally it wasn't going to need a unit test
driver, just using it from mainwindow would be enough, but it has
acquired a lot of behavior.
'''
import test_boilerplate as T
T.set_up_paths()
import constants as C
import os
import logging
file_exists = os.path.join(T.path_to_Files,'en_US.aff') # existing file
file_nexiste = os.path.join(T.path_to_Files,'fubar') # not existing file
file_unreadable = os.path.join(T.path_to_Files,'unreadable.txt') # has mode 0222
dir_name = os.path.join(T.path_to_Files,'pngs') # existing dir
import utilities
# The following incidentally test class key_dependent_default
assert utilities.file_is_accessible(file_exists)
assert not utilities.file_is_accessible(dir_name)
assert not utilities.file_is_accessible(file_nexiste)
assert not utilities.file_is_accessible(file_unreadable)
assert ('en_US.aff',T.path_to_Files) == utilities.file_split(file_exists)
assert ('pngs',T.path_to_Files) == utilities.file_split(dir_name)
assert ('en_US.aff', T.path_to_Files) == utilities.file_split('en_US.aff')
assert len(utilities._FI_DICT) == 5
# Not much to test in MemoryStream other than added methods
memstream = utilities.MemoryStream()
THETA = 'Θ'
STRING = THETA+'foobar!'
memstream.writeLine(STRING)
assert (len(STRING)+1)*2 == memstream.pos()
memstream.rewind()
assert memstream.readLine() == STRING
# n.b. it does no good to check .pos() now, it is a bytes offset
# on a unicode stream. useless...
memstream.rewind()
assert memstream.pos() == 0
assert memstream.readAll() == STRING + '\n'
# FBTS gets used a lot. Check base functionality
from PyQt5.QtCore import QFile
qfile_exists = QFile(file_exists)
fbts = utilities.FileBasedTextStream(qfile_exists)
assert fbts.basename() == 'en_US'
assert fbts.filename() == 'en_US.aff'
assert fbts.folderpath() == T.path_to_Files
assert fbts.fullpath() == file_exists
fbts = None
# Now check various methods that create FBTS
# Successful opens with default and explicit codecs
flatin = os.path.join(T.path_to_Files,'en-common-ltn.txt')
fbts = utilities.path_to_stream(flatin)
assert fbts.basename() == 'en-common-ltn'
assert b'ISO-8859-1' == fbts.codec().name()
fbts = None
futf8 = os.path.join(T.path_to_Files,'en-common-utf.txt')
fbts = utilities.path_to_stream(futf8)
assert b'UTF-8' == fbts.codec().name()
fbts = None
fbts = utilities.path_to_stream(futf8,encoding='KOI8-R')
assert b'KOI8-R' == fbts.codec().name()
# Unsuccessful opens
fbts = utilities.path_to_stream(file_nexiste)
assert fbts is None
assert T.check_log('Request for nonexistent input file',logging.ERROR)
fbts = utilities.path_to_stream(file_unreadable)
assert fbts is None
assert T.check_log('Error 5 (Permission denied) opening file unreadable',logging.ERROR)
# Existing file dialog - file dialogs require an App and a parent window
# or python will crash
T.make_app()
T.make_main()
T.main.show()
fbts = utilities.ask_existing_file('PRESS CANCEL',parent=T.main,starting_path=T.path_to_Files)
assert fbts is None
fbts = utilities.ask_existing_file('SELECT unreadable.txt',parent=T.main,starting_path=T.path_to_Files)
assert fbts is None
fbts = utilities.ask_existing_file('SELECT en-common-ltn.txt',parent=T.main,starting_path=T.path_to_Files)
assert fbts.basename() == 'en-common-ltn'
assert b'ISO-8859-1' == fbts.codec().name()
# This should get the alphabetically last, en_US.dic
fb2 = utilities.related_file(fbts,'en_US.*',encoding='KOI8-R')
assert fb2.filename() == 'en_US.dic'
assert fb2.codec().name() == 'KOI8-R'
fb3 = utilities.path_to_stream(os.path.join(T.path_to_Files,'z-ut-test.suffix'))
assert fb3 is not None
fb4 = utilities.related_suffix(fb3,C.METAFILE_SUFFIX,'KOI8-R')
assert fb4 is not None
assert fb4.filename() == 'z-ut-test.suffix.'+C.METAFILE_SUFFIX
assert fb4.codec().name() == 'KOI8-R'
fb5 = utilities.file_less_suffix(fb4)
assert fb5 is not None
assert fb5.filename() == fb3.filename()

f_foo = 'test_junk.foo'
f_bar = 'test_junk.foo.bar'
foo_path = os.path.join(T.path_to_Files,f_foo)
if os.path.isfile(foo_path):
    os.remove(foo_path)
bar_path = os.path.join(T.path_to_Files,f_bar)
if os.path.isfile(bar_path):
    os.remove(bar_path)
fbfoo = utilities.path_to_output(foo_path)
assert fbfoo.filename() == f_foo
fbfoo.writeLine('some data')
assert os.path.isfile(foo_path)
fbbar = utilities.related_output(fbfoo,'bar')
assert fbbar.filename() == f_bar
fbbar.writeLine('some data')
assert os.path.isfile(bar_path)

# Message routines
utilities.info_msg('About to beep', 'When you dismiss this message')
utilities.beep()
assert utilities.ok_cancel_msg('Did you hear a beep?', 'OK for yes, Cancel for no',parent=T.main)
utilities.warning_msg('This is a warning','the very last warning',parent=T.main)
assert utilities.save_discard_cancel_msg('Click SAVE','no parent argument')
assert not utilities.save_discard_cancel_msg('Click DISCARD (dont save?)','does have parent',parent=T.main)
assert utilities.save_discard_cancel_msg('Click CANCEL','no parent') is None
result = utilities.get_find_string('Press CANCEL',T.main,prepared='preptext')
assert result is None
preptext = 'REPLACE-WITH-FOO'
result = utilities.get_find_string('Press Find',T.main,prepared=preptext)
assert result==preptext

# to_roman, to_alpha
assert 'mmmmcmxcix' == utilities.to_roman(4999)
assert 'i' == utilities.to_roman(1)
assert 'XIV' == utilities.to_roman(14, lc=False)
emsg = 'Invalid number for roman numeral'
assert '????' == utilities.to_roman(5000)
assert T.check_log(emsg,logging.ERROR)
assert '????' == utilities.to_roman(0)
assert T.check_log(emsg,logging.ERROR)
assert 'A' == utilities.to_alpha(1, lc=False)
assert 'zzy' == utilities.to_alpha(18277)
emsg = 'Invalid number for alpha conversion'
assert '???' == utilities.to_alpha(0)
assert T.check_log(emsg,logging.ERROR)
assert '???' == utilities.to_alpha(18279, lc=False)
assert T.check_log(emsg,logging.ERROR)


T.main.close()
T.app.quit()
os.remove(foo_path)
os.remove(bar_path)



# idle a bit after quit to let garbage be collected
from PyQt5.QtTest import QTest
QTest.qWait(300)

