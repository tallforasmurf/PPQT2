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
                          paths.py

This somewhat minimal module records and makes available the
current paths to resources needed by the other modules.

At this time there are two:

    The "extras" path is where to find non-code items distributed
    with the program, for example Find macros and help.html.

    The "dicts" path is where to find specifically spelling
    dictionaries, when the user has dictionaries other than
    the ones distributed in "extras".

NOTE: Through Preferences the user sets these two paths independently.
Preferences will not permit either to be set to an invalid path (unreadable
or nonexistent -- see check_path() below) but will permit a null string.
Moreover a valid path could *become* inaccessible between shutdown and
startup.

So we have to assume that the values in settings could be null strings and
could be invalid (which will be treated as null strings).

A null string for the extras path is "corrected" to the app's folder plus
'/extras', or to the CWD if that is not readable.

A null string for the dicts path is set to extras/dicts if that exists, else
left as the null string (no dicts available).


The following functions are offered:

    initialize(settings) is called by mainwindow.py as the
    first step in setting up. It gets the last-set paths from the
    settings (which might be empty in a new installation) and
    applies the above policies.

    shutdown(settings) called at shutdown to save the latest
    path selections in the settings.

    get_dicts_path() returns the current selection for dictionaries
    if any, or ''
    
    get_extras_path() returns the current selection for extras.

    check_path(path) test that a path exists and is readable,
    returning True if so, else False.
    
    set_dicts_path()
    set_extras_path() are called from the Preferences dialog TODO.

'''

import os
import sys
import logging
paths_logger = logging.getLogger(name='paths')

_DICTS = ''
_EXTRAS = ''

# Note os.access('',F_OK) returns False

def check_path(path):
    return os.access( path ,os.F_OK ) and os.access( path, os.R_OK )

def initialize(settings):
    global _DICTS, _EXTRAS
    paths_logger.debug('paths initializing')
    candidate = settings.value("paths/extras_path",'')
    if check_path(candidate):
        _EXTRAS = candidate
    else :
        # extras_path is not in the settings (maybe a new installation?) or
        # is not a valid path. Set it to a default based on the location of
        # this app, which we get different ways depending on whether we are
        # running in development or bundled by pyinstaller. TODO: is
        # pyqtdeploy the same? (probably not)
        if hasattr(sys, 'frozen') : # bundled by pyinstaller?
            my_folder = os.path.dirname(sys.executable)
        else: # running from command line or an IDE
            my_folder = os.path.dirname(__file__)
        candidate = os.path.join(my_folder,'extras') 
        if check_path( candidate) :
            _EXTRAS = candidate
        else:
            # couldn't find extras, default it to cwd
            _EXTRAS = os.getcwd()
    # At this point we have a non-null valid path string in _EXTRAS
    # Now examine the dicts path similarly.
    candidate = settings.value("paths/dicts_path",'')
    if check_path(candidate):
        _DICTS = candidate
    else :
        # Empty or invalid path string for dicts_path, try to 
        # 'correct' it to extras/dicts if that exists.
        candidate = os.path.join( _EXTRAS, 'dicts' )
        if check_path( candidate ) :
            _DICTS = candidate
        else :
            # Nope, don't see extras/dicts. Just in case the 
            # settings contained a non-null bad path, make it null
            _DICTS = ''
    paths_logger.debug('initial extras path is ' + _EXTRAS)
    paths_logger.debug('initial dicts path is ' + _DICTS)

def shutdown(settings):
    global _DICTS, _EXTRAS
    
    paths_logger.debug('paths saving extras: ' + _EXTRAS)
    settings.setValue("paths/extras_path",_EXTRAS)
    paths_logger.debug('paths saving dicts: ' + _DICTS)
    settings.setValue("paths/dicts_path",_DICTS)

# Return the current path to the extras. This should never be a null
# string although it might the fairly-useless cwd.

def get_extras_path():
    global _EXTRAS
    return str(_EXTRAS)

# Return the current path to dictionaries or a null string if none is
# currently known.

def get_dicts_path():
    global _DICTS
    return str(_DICTS)

# Set a user-selected Dicts path or Extras path from the Preferences.
# Assume the caller used check_path() first.

def set_dicts_path(path):
    global _DICTS   
    paths_logger.debug('setting dicts path to: ' + path)
    _DICTS = str(path)

def set_extras_path(path):
    global _EXTRAS    
    paths_logger.debug('setting extras path to: ' + path)    
    _EXTRAS = str(path)