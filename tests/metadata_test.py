import os
import sys
# add .. dir to sys.path so we can import the modules
path = os.path.realpath(__file__)
path = os.path.dirname(path)
path = os.path.dirname(path)
sys.path.append(path)
import metadata # things to test and incidentally, MemoryStream
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
# garbage and leading and trailing spaces. When making a text stream
# from a bytearray, be sure to keep a reference to it until finished
# or you crash python.
mstream = metadata.MemoryStream()
mstream << '''
  garbage


   {{VERSION      5      }}
 mo gobbaj

'''
mstream.rewind()
MGR.load_meta(mstream)

# Did the manager get the version value?
assert MGR.version_read == '5'
# Test writing metadata, which will be only VERSION
mstream = metadata.MemoryStream()
MGR.write_meta(mstream)
mstream.rewind()
line = mstream.readLine()
assert line == u'{{VERSION 2}}'
# Force execution of unknown_rdr and unknown_wtr
# Nothing we can assert about, use breakpoint to check
mstream = metadata.MemoryStream()
mstream << '''
{{NOTDEFINED}}
ignored line
{{/NOTDEFINED}}
'''
mstream.rewind()
MGR.load_meta(mstream)
# When we read it back we should get nothing but version
mstream = metadata.MemoryStream()
MGR.write_meta(mstream)
mstream.rewind()
line = mstream.readLine()
assert line == u'{{VERSION 2}}'

# Test registration and invocation of a reader and writer
sentinel = u'FOOBAR'
data = 'one-line-of-data'
called = 0
def t_rdr(qts, section, vers, parm):
    global sentinel, called, data
    assert section == sentinel
    assert vers == '5' # version_read from earlier test
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

mstream = metadata.MemoryStream()
expected = '{{'+sentinel+'}}\n'+data+'\n{{/'+sentinel+'}}\n'
mstream << expected
mstream.rewind()

MGR.load_meta(mstream)
assert called == 1
mstream = metadata.MemoryStream()
MGR.write_meta(mstream)
assert called == 2
mstream.rewind()
line = mstream.readLine()
assert line == u'{{VERSION 2}}'
line = mstream.readAll()
assert line == expected
