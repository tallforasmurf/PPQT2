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
Unit test #1 for findview.py: exercise RecallButton and UserButton
using metadata, checking all error conditions. This fully exercises
the metadata reader/writers, the UserButton dict validation, and
the RecallButton internal operation.
'''
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Unit test module boilerplate stuff
import logging
import test_boilerplate as T
T.set_up_paths()
T.make_app()
T.make_main()

import metadata
import constants as C
import utilities # T.set_up_paths must have been called
# In the following we use compressed json with no newlines
# or spaces. The metadata output has those but we compress
# them out before comparing.
import json
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
def get_section(mgr, section):
    stream = utilities.MemoryStream()
    mgr.write_section(stream, section)
    stream.rewind()
    return stream.readAll()

# For simple, predictable json do a comparison with whitespace stripped
def check_section(mgr, section, jsonbits):
    received = get_section(mgr, section)
    received = strip_white(received)
    expected = strip_white(jsonbits)
    t = (expected == received)
    if not t : # about to fail assertion in caller
        print('expected',expected)
        print('received',received)
    return t

# For less simple, get the value of the returned json
def get_section_value(mgr, section):
    return json.loads( get_section(mgr, section) )

json_1 = '{{"{0}":{1}}}' # no quote on value
json_2 = '{{"{0}":"{1}"}}' # value in quotes

# Get the metadata manager for the book
mdmgr = T.book.get_meta_manager()

# Get a reference to the Find widget
fp = T.book.get_find_panel()

# Testing RecallMenuButton by loading the Find one with strings
# and getting them back via metadata.
rbd = { 3: [], 2: [], 1: [], 0 : [
    'String_with_no_blanks',
    'String  with  lotsa blanks   and extra spaces',
    'String mit unicode ∑∞' ]
    }
jd = { C.MD_FR : rbd }
load_section(mdmgr,json.dumps(jd))
xd = get_section_value(mdmgr, C.MD_FR)
assert 1 == len(xd)
assert C.MD_FR in xd
xbd = xd[C.MD_FR]
for (k,v) in xbd.items():
    assert rbd[int(k)] == v

# Check errors by loading bad stuff and checking the log
errmsg = 'FIND_RB metadata is not a dict value'
jd = { C.MD_FR : [0,'not a dict'] }
load_section(mdmgr,json.dumps(jd))
assert T.check_log(errmsg,logging.ERROR)
errmsg = 'Ignoring invalid FIND_RB'
# non-integer button number
jd = { C.MD_FR : { 'X' : ['list','of','strings'] } }
load_section(mdmgr,json.dumps(jd))
assert T.check_log(errmsg,logging.ERROR)
# list too long
jd = { C.MD_FR : { 0 : ['1','2','3','4','5','6','7','8','9','A','B'] } }
load_section(mdmgr,json.dumps(jd))
assert T.check_log(errmsg,logging.ERROR)
# not an iterable
jd = { C.MD_FR : { 0 : 9} }
load_section(mdmgr,json.dumps(jd))
assert T.check_log(errmsg,logging.ERROR)
# not a string
jd = { C.MD_FR : { 0 : ['str',9]} }
load_section(mdmgr,json.dumps(jd))
assert T.check_log(errmsg,logging.ERROR)
# Test a recall button by loading it with 10 items,
# then an eleventh, and read it back to see if the 10th
# is gone.
sl = ['0','1','2','3','4','5','6','7','8','9']
rbd = { 0 : sl}
jd = { C.MD_FR : rbd }
load_section(mdmgr,json.dumps(jd))
fp.recall_buttons[0].remember('a')
xd = get_section_value(mdmgr, C.MD_FR)
xbd = xd[C.MD_FR]
xl = xbd['0']
assert xl == sl[1:] + ['a']


# Now validate the UserButton check code by calling user_button_input with
# the repr of a dict with problems.
def push_ub(fpanel, butno, udict):
    stream = utilities.MemoryStream()
    stream << '{} : {}'.format(butno,udict)
    stream.rewind()
    fpanel.user_button_input(stream)

emsg = 'Not a valid dict literal'
ubd = "{,,}" # should fail literal_eval
push_ub(fp, 1, ubd)
assert T.check_log(emsg,logging.ERROR)
ubd = set([1,2]) # valid literal not a dict
push_ub(fp, 1, ubd)
assert T.check_log(emsg,logging.ERROR)
emsg = 'no label value in the input'
ubd = { 'find' : 'foo' }
push_ub(fp, 1, ubd)
assert T.check_log(emsg,logging.ERROR)
emsg = 'bad value for '
ubd = {'label':'(empty)', 'tooltip':None,'find':None,
              'rep1':None, 'rep2':None, 'rep3':None,
              'case':None, 'word':None, 'regex':None,
              'andnext':None, 'andprior':None, 'all':None}
ubd['label'] = 1
push_ub(fp, 1, ubd)
assert T.check_log(emsg+'label',logging.ERROR)
ubd['label'] = 'foo'
ubd['tooltip'] = 1
push_ub(fp, 1, ubd)
assert T.check_log(emsg+'tooltip',logging.ERROR)
ubd['tooltip'] = 'foo'
ubd['andnext'] = 'False'
push_ub(fp, 1, ubd)
assert T.check_log(emsg+'andnext',logging.ERROR)
ubd['andnext'] = True
ubd['find'] = '''
 123456789 123456789 123456789 123456789 123456789
 123456789 123456789 123456789 123456789 123456789
 123456789 123456789 123456789 123456789 123456789
 123456789 123456789 123456789 123456789 123456789
 123456789 123456789 123456789 123456789 123456789
 123456789 123456789 123456789 123456789 123456789
 123456789 123456789 123456789 123456789 123456789
 123456789 123456789 123456789 123456789 123456789
 123456789 123456789 123456789 123456789 123456789
 123456789 123456789 123456789 123456789 123456789
and a couple for good measure'''
push_ub(fp, 1, ubd)
assert T.check_log(emsg+'find',logging.ERROR)

# Load good dict and get it back
ubd['find']='Find text'
ubd['rep1']='Rep1 text'
ubd['rep2']='Rep2 text'
ubd['rep3']='Rep3 text'
ubd['case']=True
ubd['word']=True
ubd['regex']=True
ubd['andnext']=True
ubd['andprior']=True # wrong, but no check
ubd['all']=True
push_ub(fp,1,ubd)
stream = utilities.MemoryStream()
fp.user_button_output(stream)
stream.rewind()
while not stream.atEnd():
    line = stream.readLine()
    if not line.startswith('#') : break
assert line.startswith("1:")
drep = line[2:]
while not stream.atEnd():
    drep += stream.readLine()
drep = drep.replace(u'\t',u' ')
drep = drep.strip()
import ast
xbd = ast.literal_eval(drep)
for (k, v) in xbd.items():
    assert ubd[k] == v

# we have checked out FindPanel.user_button_input, .user_button_output,
# and UserButton.load_dict(). Now check out FindPanel._meta_write_ub
# and ._meta_read_ub. Format is { "FIND_UB" : { "n" : {udict},...} }

udud = { "label" : "FOOBAR", "tooltip" : "FLUBBER", "find" : "Find" }
ud = { "1" : udud }
jd = { "FIND_UB" : ud }
load_section(mdmgr,json.dumps(jd))
xd = get_section_value(mdmgr, C.MD_FU)
xud = xd[C.MD_FU]
xudud = xud["1"]
for (k,v) in udud.items():
    assert v == xudud[k]
assert True