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
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

import metadata # things to test
import utilities # MetaStream
#test utilities
assert u'{{FOO}}' == metadata.open_string(u'FOO',None)
assert u'{{FOO BAR}}' == metadata.open_string(u'FOO',u'BAR')
assert u'{{/FOO}}' == metadata.close_string(u'FOO')
assert u'{{FOO BAR}}\n' == metadata.open_line(u'FOO',u'BAR')
assert u'{{/FOO}}\n' == metadata.close_line(u'FOO')
# test section re
import re
m = metadata.re_sentinel.match('  {{FOO}}  ')
assert m.group(1) == 'FOO'
assert m.group(2) == ''
m = metadata.re_sentinel.match('{{FOO Babaloo 6}}')
assert m.group(1) == 'FOO'
assert m.group(2).strip() == 'Babaloo 6'

# Create a metamgr object we can work with.

MGR = metadata.MetaMgr()

# test reading, writing of VERSION, incidentally ignoring blank lines
# garbage and leading and trailing spaces.

mstream = utilities.MemoryStream()
mstream << '''
  garbage


   {{VERSION      5      }}
 mo gobbaj

'''
mstream.rewind()
MGR.load_meta(mstream)
# Did the manager get the version value?
assert MGR.version_read == '5'
# Should be no log output yet
x = log_stream.getvalue()
assert len(x) == 0

# Test writing metadata, which will be only VERSION
mstream = utilities.MemoryStream()
MGR.write_meta(mstream)
mstream.rewind()
line = mstream.readLine()
assert line == u'{{VERSION 2}}'
# Test reading bad VERSION w/ log output
mstream = utilities.MemoryStream()
mstream << '{{VERSION   }}'
mstream.rewind()
MGR.load_meta(mstream)
assert check_log('no parameter: assuming 1',logging.WARN)

# Force execution of unknown_rdr and unknown_wtr
# expecting warning log msgs
mstream = utilities.MemoryStream()
mstream << '''
{{NOTDEFINED}}
ignored line
{{/NOTDEFINED}}
'''
mstream.rewind()
f = log_stream.seek(0)
f = log_stream.truncate()
MGR.load_meta(mstream)
assert check_log('No reader registered for',logging.ERROR)

# When we read it back we should get nothing but version 2
mstream = utilities.MemoryStream()
MGR.write_meta(mstream)
mstream.rewind()
line = mstream.readLine()
assert line == u'{{VERSION 2}}'
assert mstream.atEnd()

# Test registration and invocation of a reader and writer
sentinel = u'FOOBAR'
data = 'one-line-of-data'
called = 0
def t_rdr(qts, section, vers, parm):
    global sentinel, called, data
    assert section == sentinel
    assert vers == '1' # version_read default from prior error test
    assert len(parm) == 0 # no parm value
    n = 1
    for line in metadata.read_to(qts, section) :
        assert n == 1
        n += 1
        assert line == data
    called = 1
def t_wtr(qts,section):
    global called
    qts << metadata.open_line(section,None)
    qts << data + u'\n'
    qts << metadata.close_line(section)
    called += 1

MGR.register(sentinel, t_rdr, t_wtr)

mstream = utilities.MemoryStream()
expected = '{{'+sentinel+'}}\n'+data+'\n{{/'+sentinel+'}}\n'
mstream << expected
mstream.rewind()

# test write_meta which writes VERSION and all defined sections
MGR.load_meta(mstream)
assert called == 1
mstream = utilities.MemoryStream()
MGR.write_meta(mstream)
assert called == 2
mstream.rewind()
line = mstream.readLine()
assert line == u'{{VERSION 2}}'
line = mstream.readAll()
assert line == expected

# test write_section which does not write VERSION
mstream = utilities.MemoryStream()
MGR.write_section(mstream, sentinel)
mstream.rewind()
line = mstream.readAll()
assert line == expected

# Test registration errors, expecting log lines
# duplicate registration
MGR.register(sentinel, t_rdr, t_wtr)
assert check_log('duplicate metadata registration ignored',logging.WARN)
# non-string section name
MGR.register(2, t_rdr, t_wtr)
assert check_log('sentinel not a string value',logging.ERROR)
# non-function rdr/wtr
MGR.register(sentinel, MGR, t_wtr)
assert check_log('rdr/wtr not function types',logging.ERROR)
