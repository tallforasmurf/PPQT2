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
                         editview.py

Defines a class for the edit object, which implements the user
access to a document for editing, based on QPlainTextEdit.

Gets its data (QPlainTextDocument) from the Book object.

Implements all keyboard actions (ctl-F, etc) in the editor. Implements the
syntax highlighter that colors scannos and spelling errors. Calls on a
WordData object to identify scannos and spelling errors.

'''
