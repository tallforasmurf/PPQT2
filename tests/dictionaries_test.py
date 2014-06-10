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
Unit test for dictionaries.py
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
# Create an app and empty settings
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)
import constants as C
app.setOrganizationName("PGDP")
app.setOrganizationDomain("pgdp.net")
app.setApplicationName("PPQT2")
from PyQt5.QtCore import QSettings
settings = QSettings()
settings.setValue("dictionaries/path",files_path)
settings.setValue("dictionaries/default_tag","en_GB")
import dictionaries
dictionaries.initialize(settings)
assert files_path == dictionaries.get_dict_path()
assert 'en_GB' == dictionaries.get_default_tag()

# There are 3 dicts in Tests/Files:
expect_tags = ['en_US','en_GB','fr_FR']
tag_list = dictionaries.get_tag_list('')
for tag in expect_tags:
    assert tag in tag_list
assert len(expect_tags) == len(tag_list.keys())
# Create a mismatched dic/aff pair
dic_path = os.path.join(files_path,'foobar.dic')
open(dic_path,'w')
tag_list = dictionaries.get_tag_list('')
assert check_log(".dic but not",logging.ERROR)
os.remove(dic_path) # clean up Files
aff_path = os.path.join(files_path,'foobar.aff')
open(aff_path,'w')
tag_list = dictionaries.get_tag_list('')
assert check_log(".aff but not",logging.ERROR)
os.remove(aff_path) # clean up Files
# "skipping" should appear if we check a path twice
tag_list = dictionaries.get_tag_list(files_path)
assert check_log("Skipping",logging.INFO)
# Check the spellcheck object part
SP = dictionaries.Speller("en_US",dictionaries.get_dict_path())
assert SP.check('raspberry',None)
assert not SP.check('bazongas',None)
assert SP.check('framboise','fr_FR')
assert not SP.check('bazongas','fr_FR')
# nonexistent alt tag
assert SP.check('bazongas','de_DE')
