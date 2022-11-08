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
import logging
import sys
import os
import test_boilerplate as T
T.set_up_paths()
T.make_app()
T.settings.clear()

# Initialize paths to Tests/Files/extras/dicts (from paths_test)
import paths
test_extras = os.path.join(T.path_to_Files,'extras')
T.settings.setValue("paths/extras_path", test_extras)
test_dicts = os.path.join(test_extras,'dictionaries')
paths.initialize(T.settings)
paths.set_extras_path(test_extras)
paths.set_dicts_path(test_dicts)
import dictionaries
T.settings.setValue("dictionaries/default_tag",'en_GB')
dictionaries.initialize(T.settings)
assert 'en_GB' == dictionaries.get_default_tag()

# There are 3 dicts in Tests/Files/extras/dictionaries: en_US, en_GB, fr_FR
# There is one more in Tests/Files/extras, de_DE

expect_tag_list = {'en_US':test_dicts,'en_GB':test_dicts,'fr_FR':test_dicts,'de_DE':test_extras}
tag_list = dictionaries.get_tag_list()
for (tag,path) in expect_tag_list.items():
    assert tag in tag_list
    assert tag_list[tag] == expect_tag_list[tag]

# cause T.path_to_Files to have mismatched foobar.dic
dic_path = os.path.join(T.path_to_Files,'foobar.dic')
f = open(dic_path,'w')
f.close()
tag_list = dictionaries.get_tag_list(T.path_to_Files)
assert T.check_log(".dic but not",logging.ERROR)
os.remove(dic_path) # clean up Files
# cause T.path_to_Files to have mismatched foobar.aff
aff_path = os.path.join(T.path_to_Files,'foobar.aff')
f = open(aff_path,'w')
f.close()
tag_list = dictionaries.get_tag_list(T.path_to_Files)
assert T.check_log(".aff but not",logging.ERROR)
os.remove(aff_path) # clean up Files

# "skipping" should appear if we check a path twice
tag_list = dictionaries.get_tag_list(test_dicts)
assert T.check_log("Skipping",logging.DEBUG)

# Check the spellcheck object: bad input makes not is_valid
# and all words are ok
SP = dictionaries.Speller("xx_YY",paths.get_dicts_path())
assert T.check_log('bad dictionary path',logging.ERROR)
assert not SP.is_valid()
assert SP.check('neenerneener',None)
SP = None # get rid of that object

SP = dictionaries.Speller("en_US",paths.get_dicts_path())
assert SP.is_valid()
assert SP.check('raspberry',None)
assert not SP.check('bazongas',None)
assert SP.check('framboise','fr_FR')
assert not SP.check('bazongas','fr_FR')
# nonexistent alt tag produces True
assert SP.check('bazongas','en_AU')
