# PPQT Version 2

This is a major rewrite of PPQT to achieve certain goals.

(May 2014) This project is currently in early stages of development. If you are interested in the details of programming with Qt, PyQt and Python 3, you may enjoy following my blog at thispageintentionally.blogspot.com where I write about what I'm learning as I code. 

## What Is PPQT?

See github.com/tallforasmurf/PPQT, where PPQT Version 1 (V1) is described:

PPQT (Post-processing in Python and Qt) is an integrated application meant to assist the volunteers who post-process etexts prepared at Distributed Proofreaders (PGDP.net). It provides a text editor that integrates a number of features useful during post-processing, including display of the book's scanned pages, regular expression find/replace, spellcheck, pagination, footnoting, and html preview.

## License

PPQT is Copyright(C) 2013, 2014 David Cortesi (tallforasmurf@yahoo.com)
 
License (GPL-3.0) :
    PPQT is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You can find a copy of the GNU General Public License in the file
    COPYING.TXT included in the distribution of this program, or see:
    <http://www.gnu.org/licenses/>.

PPQT makes use of PyQt5, Qt5, Hunspell, and PyInstaller, all available for nonprofit use under one form of the GPL or another.

## Features

Features are basically the same as PPQT, with these additions:

1. Is based on Qt5 and PyQt5 under Python 3.3,
gaining some features and greater
stability. (V1 uses Qt4 and PyQt4 under Python 2.7)

2. Adds several whizzy GUI features such as being able to
drag edit panels out to be independent windows.

3. Multiple documents (books) can be edited at the same time (V1
allowed only one document at a time). Support for multiple documents
forces changes in almost every module; many things that were
global resources have to be localized to the document.

4. Adds further support for automated detection of OCR errors
as provided by older tools such as "Gutcheck".

5. Adds further support for HTML with automated validation, making
HTML validation easier.

6. Numerous smaller user interface changes and improvements
remove minor restrictions.

