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
Unit test for chardata.py
'''
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Unit test module boilerplate stuff

import test_boilerplate as T
T.set_up_paths()

import metadata
import constants as C
import chardata
import logging

# In the following we use compressed json with no newlines
# or spaces. The metadata output has those but we compress
# them out before comparing.
import utilities # T.set_up_paths must have been called
def load_section(mgr, jsonbits):
    stream = utilities.MemoryStream()
    stream << '\n' # must start section with newline
    stream << jsonbits
    stream.rewind()
    mgr.load_meta(stream)
# read back a specified section to see that it contains exactly the input,
# modulo whitespace. We need to strip whitespace from the comparison also
# because .format can insert spaces into list repr's.
def strip_white(s):
    return s.replace('\n','').replace(' ','')
def check_section(mgr, section, jsonbits):
    stream = utilities.MemoryStream()
    mgr.write_section(stream, section)
    stream.rewind()
    received = stream.readAll()
    received = strip_white(received)
    expected = strip_white(jsonbits)
    t = (expected == received)
    if not t : # about to fail assertion in caller
        print('expected',expected)
        print('received',received)
    return t

T.make_app()
T.make_main()
# T.book is now a new-empty one. Get its edit model, char model, and meta manager
em = T.book.get_edit_model()
cd = T.book.get_char_model()
mm = T.book.get_meta_manager()
# load the em with minimal data
em.setPlainText('ABBCCC')
# do a refresh which loads the census
cd.refresh()
# read it out as metadata.
jpat_1 = '{{"{0}":{1}}}'
expect = jpat_1.format(C.MD_CC,'[["A",1],["B",2],["C",3]]')
assert check_section(mm,C.MD_CC,expect)
assert 3 == cd.char_count()
assert 'C' == cd.get_char(2)
assert ('B',2) == cd.get_tuple(1)

# Check error handling in get_tuple
etxt = 'Invalid chardata index'
assert ('?', 0) == cd.get_tuple(-4)
assert T.check_log(etxt,logging.ERROR)
assert ('?', 0) == cd.get_tuple(99)
assert T.check_log(etxt,logging.ERROR)
# check invalid section value
# note any call to chardata reader clears the census
etxt = 'CHARCENSUS metadata must be a list, ignoring all'
expect = jpat_1.format(C.MD_CC,'{"A":2}') # not a dict
load_section(mm,expect)
assert T.check_log(etxt,logging.ERROR)
assert 0 == cd.char_count()

# check bad values from metadata
etxt = 'Ignoring invalid CHARCENSUS chararacter '
expect = jpat_1.format(C.MD_CC,'[{"X":2}]') # item not a list
load_section(mm,expect)
assert T.check_log(etxt,logging.ERROR)
expect = jpat_1.format(C.MD_CC,'[["X",2,3]]') # item not k,n
load_section(mm,expect)
T.check_log(etxt,logging.ERROR)
expect = jpat_1.format(C.MD_CC,'[[5,"x"]]') # key not a str
load_section(mm,expect)
T.check_log(etxt,logging.ERROR)
expect = jpat_1.format(C.MD_CC,'[["xxx",5]]') # key not 1 char
load_section(mm,expect)
T.check_log(etxt,logging.ERROR)
expect = jpat_1.format(C.MD_CC,'[["X",2.2]]') # count not an int
load_section(mm,expect)
T.check_log(etxt,logging.ERROR)
expect = jpat_1.format(C.MD_CC,'[["X","Y"]]') # count not an int
load_section(mm,expect)
T.check_log(etxt,logging.ERROR)
expect = jpat_1.format(C.MD_CC,'[["X",["Y",3]]]') # count not an int
load_section(mm,expect)
T.check_log(etxt,logging.ERROR)
expect = jpat_1.format(C.MD_CC,'[["X",0]]') # count not >0
load_section(mm,expect)
T.check_log(etxt,logging.ERROR)

## testing refresh with a small and big document
#import timeit
#sb_path = os.path.join(files_path,'small_book.txt')
#sb = open(sb_path,'r',encoding='Latin-1')
#em.setPlainText(sb.read())
## naive: 0.730214225826785
## complicated: 0.20750655699521303
#print('starting')
#sb_time = timeit.timeit(cd.refresh, number=4)
#print(sb_time)