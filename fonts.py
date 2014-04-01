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
            fonts.py
Font resource for PPQT2.

TODO: figure out how to package liberation mono as a resource,
and install it in the font db if it isn't there.

This module is imported by mainwindow on startup, when it calls
initialize(). The services offered are designed so that other widgets
don't have to know about the QFont/QFontInfo API.

    initialize() creates a font database and identifies the
        user's preferred monospaced and general fonts
        from saved settings if any.

    choose_font() puts up a font-choice dialog for fixed or general
        and stores the choice. If it is a change, the fontChanged
        signal is emitted.

    get_fixed() returns the QFont for the selected monospaced font
        at a specified or default size.

    get_general() returns the QFont for the selected general font
        at a specified or default size.

    TODO: FIGURE OUT BEST API FOR SCALE +/- points? abs % (of what)
    scale() scales the size of a font up or down and returns the
        modified QFont.

    get_size() returns the integer size of a QFont (presumably,
        for saving in one's settings?)

    shutdown() saves current font choices in the settings.
'''
import logging
fonts_logger = logging.getLogger(name='fonts')

from PyQt5.QtGui import (QFont, QFontInfo, QFontDatabase)

font_db = QFontDatabase()
qf_general = font_db.systemFont(QFontDatabase.GeneralFont)
families = font_db.families()
libmono = [family for family in families if 'Liberation Mono' in family]
couriermono = [family for family in families if 'Courier New' in family]
if libmono :
    qf_mono = font_db.font(libmono[0],'Regular',16)
    dbg = qf_mono.family()
elif couriermono :
    qf_mono = font_db.font(couriermono[0],'Regular',16)
else:
    qf_mono = font_db.systemFont(QFontDatabase.FixedFont)

def initialize(settings):
    fonts_logger.debug('Fonts initializing')

def get_fixed(point_size=16):
    return qf_mono

def get_general(point_size=16):
    return qf_general

def get_size(qf):
    return qf.pointSize()

def scale(qf, pct) :
    fonts_logger.error('Unimplemented:scale')
    return qf

def choose_font(mono=True, parent=None):
    fonts_logger.error('Unimplemented:choose_font')
    return qf_mono if mono else qf_general

def shutdown():
    fonts_logger.error('Unimplemented:shutdown')
