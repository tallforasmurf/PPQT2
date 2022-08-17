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
__copyright__ = "Copyright 2013, 2014, 2015 David Cortesi"
__maintainer__ = "David Cortesi"
__email__ = "tallforasmurf@yahoo.com"

'''
                          paths.py

This somewhat minimal module records and makes available the
current paths to resources needed by the other modules.

At this time there are three:

    The "extras" path is where to find non-code items distributed
    with the program, for example Find macros and help.html.

    The "dicts" path is where to find specifically spelling
    dictionaries, when the user has dictionaries other than
    the ones distributed in "extras".

    The "loupe" path is where to find the executable program
    named bookloupe in this system. If it has not been set
    explicitly it is the null string.

The user sets these paths using the Preferences dialog. It must not permit
any to be set to an invalid path (unreadable or nonexistent -- see
check_path() below), but may permit a null string.

However a valid path in the settings could become inaccessible between
shutdown and startup. So we have to assume that the values in settings could
be null strings or could be invalid (which will be treated as null strings).

A null string or invalid extras path is "corrected" to the app's folder plus
'/extras' if that exists, or else to the CWD.

A null string for the dicts path is set to extras/dictionaries if that
exists, else left as the null string (no dicts available).


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

    get_loupe_path() returns the current selection for bookloupe
    or a null string if none.

    check_path(path) test that a path exists and is readable,
    returning True if so, else False.

    The following are called from the Preferences dialog:

    set_defaults() is called when initializing and from Preferences
    set_dicts_path()
    set_loupe_path()
    set_extras_path()

'''

import os
import sys
import logging
paths_logger = logging.getLogger(name='paths')
import constants as C

_DICTS = ''
_EXTRAS = ''
_LOUPE = ''


# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Validate a path as readable or executable. Note that os.access('',F_OK)
# returns False, a null string is not valid.

def check_path(path, executable=False):
    if executable :
        return os.access( path, os.F_OK ) and os.access( path, os.X_OK )
    # else not checking executable-ness only readability
    return os.access( path ,os.F_OK ) and os.access( path, os.R_OK )


# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Set the default paths as best we can based on fixed information.

def set_defaults():
    global _DICTS, _EXTRAS, _LOUPE
    # Default for the Loupe path is platform-dependent.
    if C.PLATFORM_IS_WIN :
        # TODO: where does bookloupe install on windows??
        candidate = ''
    else : # Mac, Linux likely location
        candidate = '/usr/local/bin/bookloupe'
    if not check_path(candidate, executable=True) :
        candidate = ''
    _LOUPE = str(candidate)
    # Default for the Extras path is our-folder/extras
    if hasattr(sys, 'frozen') : # bundled by pyinstaller/cxfreeze/pyqtdeploy?
        my_folder = os.path.dirname(sys.executable)
    else: # running from command line or an IDE
        my_folder = os.path.dirname(__file__)
    candidate = os.path.join(my_folder,'extras')
    if not check_path( candidate ) :
        # extras folder not found, fall back to CWD
        candidate = os.getcwd()
    _EXTRAS = str(candidate)
    # Default for dicts path is Extras/dictionaries, if it exists, else null
    candidate = os.path.join( _EXTRAS, 'dictionaries' )
    if not check_path( candidate ) :
        candidate = ''
    _DICTS = str(candidate)


# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Starting up: set the default paths based on our current environment,
# then load saved settings if they exist.

def initialize(settings):
    global _DICTS, _EXTRAS, _LOUPE
    paths_logger.debug('paths initializing')
    set_defaults()
    # Recover save bookloupe path if any, else the default.
    candidate = settings.value( "paths/loupe_path", _LOUPE )
    if not check_path(candidate,executable=True):
        candidate = '' # no-longer-valid path from settings
    _LOUPE = str(candidate)
    paths_logger.debug('initial loupe path is ' + _LOUPE)

    # Recover saved extras path if any, else leave the default.
    # The default from set_defaults is a valid path.
    candidate = settings.value( "paths/extras_path", _EXTRAS )
    if check_path(candidate):
        # extras_path from settings (or the default) is valid.
        _EXTRAS = str(candidate)
    # else extras from settings is no longer valid, leave default.
    paths_logger.debug('initial extras path is ' + _EXTRAS)

    # Recover the saved dicts path if any, else try to find
    # one in the newly-set Extras, else leave null.
    candidate = settings.value( "paths/dicts_path", _DICTS )
    if not check_path(candidate):
        # Either the saved path is no longer good, or _DICTS was
        # defaulted to null string. But possibly we just set a
        # new _EXTRAS, so try one more time.
        candidate = os.path.join( _EXTRAS, 'dictionaries' )
        if not check_path( candidate ) :
            candidate = ''
    _DICTS = str(candidate)
    paths_logger.debug('initial dicts path is ' + _DICTS)

def shutdown(settings):
    paths_logger.debug('paths saving loupe: ' + _LOUPE)
    settings.setValue("paths/loupe_path",_LOUPE)
    paths_logger.debug('paths saving extras: ' + _EXTRAS)
    settings.setValue("paths/extras_path",_EXTRAS)
    paths_logger.debug('paths saving dicts: ' + _DICTS)
    settings.setValue("paths/dicts_path",_DICTS)

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Create a global object that can send the signal
# PathsChanged('dict'/'extras'/'loupe'). Objects that want to know when the
# user changes path preferences, connect with paths.notify_me(my_slot)
#

from PyQt6.QtCore import ( pyqtSignal, QObject )

class PathSignaller(QObject):
    PathsChanged = pyqtSignal(str)
    def connect(self, slot):
        self.PathsChanged.connect(slot)
    def send(self,what):
        self.PathsChanged.emit(what)

_SIGNALLER = PathSignaller() # create one object of that class

def notify_me(slot):
    paths_logger.debug('Connecting PathsChanged signal to {}'.format(slot.__name__))
    _SIGNALLER.connect(slot)
def _emit_signal(what):
    paths_logger.debug('Emitting PathsChanged signal({})'.format(what) )
    _SIGNALLER.send(what)

# Return the current path to the extras. This should never be a null
# string although it might the fairly-useless cwd.

def get_extras_path():
    return str(_EXTRAS)

# Return the current path to dictionaries or a null string if none is
# currently known.

def get_dicts_path():
    return str(_DICTS)

# Return the current value of the bookloupe executable or a null string.

def get_loupe_path():
    return str(_LOUPE)

# Set some user-selected path. In each case assume the caller used
# check_path() first.

def set_loupe_path(path):
    global _LOUPE
    paths_logger.debug('setting loupe path to: ' + path)
    _LOUPE = str(path)
    _emit_signal('loupe')

def set_dicts_path(path):
    global _DICTS
    paths_logger.debug('setting dicts path to: ' + path)
    _DICTS = str(path)
    _emit_signal('dicts')

def set_extras_path(path):
    global _EXTRAS
    paths_logger.debug('setting extras path to: ' + path)
    _EXTRAS = str(path)
    _emit_signal('extras')