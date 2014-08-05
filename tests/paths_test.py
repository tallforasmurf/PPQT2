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

import io
log_stream = io.StringIO()
import logging
logging.basicConfig(stream=log_stream,level=logging.DEBUG)
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
files_path = os.path.join(test_path,'Files')
ppqt_path = os.path.dirname(test_path)
sys.path.append(ppqt_path)
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)
app.setOrganizationName("PGDP")
app.setOrganizationDomain("pgdp.net")
app.setApplicationName("PPQT2")
from PyQt5.QtCore import QSettings
settings = QSettings()
import constants as C
import paths

assert paths.check_path(test_path)
assert not paths.check_path(os.path.join(test_path,'arglebargle'))
assert not paths.check_path(os.path.join(files_path,'unreadable.aff'))

settings.clear()
paths.initialize(settings)
# with null settings, extras defaults to cwd = test_path
check_log('initial extras path is '+test_path ,logging.DEBUG)
assert paths.get_extras_path() == test_path
assert paths.get_dicts_path() == ''
# point settings to an extras, expect dicts to follow
test_extras = os.path.join(files_path,'extras')
settings.setValue("paths/extras_path", test_extras)
paths.initialize(settings)
check_log('initial extras path is '+test_extras ,logging.DEBUG)
assert paths.get_extras_path() == test_extras
test_dicts = os.path.join(test_extras,'dicts')
assert paths.get_dicts_path() == test_dicts
# test shutdown
settings.clear()
paths.shutdown(settings)
assert settings.value("paths/extras_path",'wrong') == test_extras
assert settings.value("paths/dicts_path",'wrong') == test_dicts
# operate the pref sets
dummy_dicts = '/some/where/dicts'
paths.set_dicts_path(dummy_dicts)
dummy_extras = '/what/ever/extras'
paths.set_extras_path(dummy_extras)
assert paths.get_dicts_path() == dummy_dicts
assert paths.get_extras_path() == dummy_extras
# shut down with bad values
paths.shutdown(settings)
# start up with bad values, look for defaults
paths.initialize(settings)
assert paths.get_extras_path() == test_path
assert paths.get_dicts_path() == ''
