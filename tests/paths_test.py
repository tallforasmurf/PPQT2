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
Unit test for paths.py.
'''
import test_boilerplate as T
T.set_up_paths()
T.make_app()
import os
import logging
import constants as C
import paths
T.settings.clear()
# test readable folder
test_path = T.path_to_Files
assert paths.check_path(test_path)
# nonexistent file
assert not paths.check_path(os.path.join(test_path,'arglebargle'))
# file that has the read perms turned off
assert not paths.check_path(os.path.join(test_path,'unreadable.aff'))

paths.initialize(T.settings)

# with null settings, extras defaults to cwd = test_path
assert T.check_log('initial extras path is '+test_path ,logging.INFO)
assert paths.get_extras_path() == test_path
assert paths.get_dicts_path() == ''
# check assuming bookloupe is installed
if C.PLATFORM_IS_WIN:
    assert paths.get_loupe_path() == '' # TODO FIX WHEN KNOWN
else:
    assert paths.get_loupe_path() == '/usr/local/bin/bookloupe'
# point settings to an extras, expect dicts to follow
test_extras = os.path.join(T.path_to_Files,'extras')
T.settings.setValue("paths/extras_path", test_extras)
paths.initialize(T.settings)
assert T.check_log('initial extras path is '+test_extras ,logging.INFO)
assert paths.get_extras_path() == test_extras
test_dicts = os.path.join(test_extras,'dicts')
assert paths.get_dicts_path() == test_dicts
# Make sure that what we put into loupe, we get back
test_loupe = os.path.join(test_extras,'bookloupe.exe') # which doesn't exist
paths.set_loupe_path(test_loupe)
assert paths.get_loupe_path() == test_loupe
# test shutdown
T.settings.clear()
paths.shutdown(T.settings)
assert T.settings.value("paths/extras_path",'wrong') == test_extras
assert T.settings.value("paths/dicts_path",'wrong') == test_dicts
assert T.settings.value("paths/loupe_path",'wrong') == test_loupe
# set bad values because paths expects caller to verify validity
dummy_dicts = '/some/where/dicts'
paths.set_dicts_path(dummy_dicts)
dummy_extras = '/what/ever/extras'
paths.set_extras_path(dummy_extras)
dummy_loupe = 'nexist/pas/bookloupe'
paths.set_loupe_path(dummy_loupe)
assert paths.get_dicts_path() == dummy_dicts
assert paths.get_extras_path() == dummy_extras
assert paths.get_loupe_path() == dummy_loupe
# shut down with those bad values
paths.shutdown(T.settings)
# start up with bad values, expect defaults
paths.initialize(T.settings)
assert paths.get_extras_path() == test_path # bad path -> cwd
assert paths.get_dicts_path() == '' # bad path -> null
assert paths.get_loupe_path() == '' # bad path -> null
# Check sending of signal
sig_value = None
def catcher(what):
    global sig_value
    sig_value = what
paths.notify_me(catcher)
paths.set_extras_path('/somewhere/over/the/rainbow')
assert sig_value == 'extras'
paths.set_loupe_path('/somewhere/over/the/rainbow')
assert sig_value == 'loupe'
paths.set_dicts_path('/somewhere/over/the/rainbow')
assert sig_value == 'dicts'
