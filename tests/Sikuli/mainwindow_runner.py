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
Unit test for mainwindow.py -- this mainwindow_runner.py
Invoked from Sikuli to get the window up.
This lives in ppqt/Tests/Sikuli but does a chdir to
ppqt/Tests/Files
'''
import logging
logging.basicConfig(level=logging.INFO)
import sys
import os
files_path = '/Users/dcortes1/Dropbox/David/PPQT/V2/ppqt/Tests/Files'
os.chdir(files_path)
ppqt_path = '/Users/dcortes1/Dropbox/David/PPQT/V2/ppqt'
sys.path.append(ppqt_path)
# Create an app and empty settings
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)
import constants as C
app.setOrganizationName("PGDP")
app.setOrganizationDomain("pgdp.net")
app.setApplicationName("PPQT2")
from PyQt5.QtCore import QSettings
settings = QSettings()

import mainwindow
from PyQt5.QtCore import Qt,QPoint,QSize
settings.clear()
settings.setValue("mainwindow/position",QPoint(0,0))
mw = mainwindow.MainWindow(settings)

mw.show()
app.exec_()

# idle a bit after quit to let garbage be collected
from PyQt5.QtTest import QTest
QTest.qWait(200)













#app.quit()


#mw = None
#mwp = mw.pos()
#mws = mw.size()
#mwmid = QPoint(mwp.x()+mws.width()/2, mwp.y()+mws.height()/2)

# trash mw before the app or there is a race and sip crashes
#mw = None
#app.exec_()

