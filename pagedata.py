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

                          PAGEDATA.PY

Defines a class to store info extracted from page boundary lines. Acts as the
Data Model for pageview.py, which displays the page table with user controls.
Defines some constants used by pagedata and pageview.

Created by a Book object. Registers page_load and page_save methods
to read/write {{PAGETABLE}} metadata section.

'''

# These values are used to encode folio controls for the
# Page/folio table.
FolioFormatArabic = 0x00
FolioFormatUCRom = 0x01
FolioFormatLCRom = 0x02
FolioFormatSame = 0x03 # the "ditto" format
FolioRuleAdd1 = 0x00
FolioRuleSet = 0x01
FolioRuleSkip = 0x02

# Each .meta page info is a list of 6 items, specifically
# 0: page start offset, 1: png# string, 2: prooferstring,
# 3: folio rule, 4: folio format, 5: folio number
