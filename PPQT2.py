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
                          PPQT.PY
Top level module of PPQT version 2.

Performs all non-GUI global initialization of the application.
Initiates mainwindow.py. Waits for completion.
'''
'''
Locations for settings values:
Linux: $HOME/.config/PGDP/PPQT2.conf
Mac OSX: $HOME/Library/Preferences/com.PGDP.PPQT2.plist
Windows (registry): HKEY_CURRENT_USER\Software\PGDP\PPQT2

'''
import logging
import io
log_stream = io.StringIO()
logging.basicConfig( stream=log_stream, level=logging.INFO )

from PyQt5.QtWidgets import QApplication
import sys

the_app = QApplication( sys.argv )
the_app.setOrganizationName( "PGDP" )
the_app.setOrganizationDomain( "pgdp.net" )
the_app.setApplicationName( "PPQT2" )

from PyQt5.QtCore import QSettings
the_settings = QSettings()

from mainwindow import MainWindow
the_main_window = MainWindow( the_settings )
the_main_window.show()
the_app.exec_()
