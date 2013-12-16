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
                          FNOTDATA.PY

Defines a class to store the footnote info of one Book. Acts as the Data Model
for fnotview.py which displays footnote data and offers user controls.

Methods fnote_load and fnote_save() are registered to read/write footnote
metadata.

Books with version 1 metadata and new books don't have that metadata. So can
also be (re-)initialized from the Refresh button of the Fnote panel which
calls method refresh(), which scans the book and loads footnote data.

TBS: What services this affords to fnotview.py.

TBS: Where we put the functions that modify the book text,
renumbering and moving footnotes. Which object owns the
renumber streams?

'''