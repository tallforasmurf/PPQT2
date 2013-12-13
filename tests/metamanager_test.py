from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from PyQt4.QtCore import QTextStream, QString
import os
import sys
path = os.path.realpath(__file__)
path = os.path.dirname(path)
path = os.path.dirname(path)
sys.path.append(path)
import metamanager
#check that only VERSION is installed so far
assert 1 == len(metamanager.SectionDict)
assert 'VERSION' in metamanager.SectionDict
#test utilities
assert u'{{FOO}}' == metamanager.open_string(u'FOO',None)
assert u'{{FOO BAR}}' == metamanager.open_string(u'FOO',u'BAR')
assert u'{{/FOO}}' == metamanager.close_string(u'FOO')
# test reading, writing of VERSION, incidentally ignoring blank lines
# garbage and leading and trailing spaces. When making a text stream
# from a string, be sure to keep a reference to the string until finished
# or you crash python.
string = QString('''
  garbage


   {{VERSION      5      }}
 mo gobbaj

''')
stream = QTextStream(string)
metamanager.load_meta(stream)
dbg = metamanager.Version_read
assert metamanager.Version_read == u'5'
string = QString()
stream = QTextStream(string)
metamanager.write_meta(stream)
stream.seek(0)
line = stream.readLine()
assert unicode(line) == u'{{VERSION 2}}'
# Force execution of unknown_rdr and unknown_wtr
# Nothing we can assert about, use breakpoint to check
string = QString('''{{NOTDEFINED}}\nignored line\n{{/NOTDEFINED}}\n''')
stream = QTextStream(string)
metamanager.load_meta(stream)
# When we read it back we should get nothing but version
string = QString()
stream = QTextStream(string)
metamanager.write_meta(stream)
stream.seek(0)
line = stream.readLine()
assert unicode(line) == u'{{VERSION 2}}'

# Test registration and invocation of a reader and writer
sentinel = u'FOOBAR'
data = 'one-line-of-data'
called = 0
def t_rdr(qts, section, vers, parm):
    global sentinel, called, data
    assert section == sentinel
    assert vers == '5' # from earlier test
    assert len(parm) == 0 # no parm value
    n = 1
    for line in metamanager.read_to(qts, section) :
        assert n == 1
        n += 1
        assert line == data
    called = 1
def t_wtr(qts,section):
    global called
    qts << metamanager.open_string(section,None) + u'\n'
    qts << data + u'\n'
    qts << metamanager.close_string(section) + u'\n'
    called = 2

metamanager.register(sentinel, t_rdr, t_wtr)

expected = u'{{'+sentinel+u'}}\n'+data+'\n{{/'+sentinel+'}}\n'
string = QString(expected)
stream = QTextStream(string)
metamanager.load_meta(stream)
assert called == 1
string = QString()
stream = QTextStream(string)
metamanager.write_meta(stream)
assert called == 2
stream.seek(0L)
line = stream.readLine()
assert unicode(line) == u'{{VERSION 2}}'
line = unicode(stream.readAll())
assert line == expected
