# PPQT Version 2

This is a major rewrite of PPQT to achieve certain goals.

(July 2015) This project is substantially complete.

## What Is PPQT?

PPQT (Post-processing in Python and Qt) is an integrated application
meant to assist the volunteers who post-process etexts prepared at
Distributed Proofreaders (PGDP.net).
It provides a text editor that integrates a number of features useful
during post-processing, including display of the book's scanned pages,
regular expression find/replace, spellcheck, pagination, footnoting and
use of the volunteer-built text-inspector "bookloupe".

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

PPQT makes use of PyQt5, Qt5, Hunspell, and PyInstaller, all available
for nonprofit use under one form of the GPL or another.

## Features

Features are basically the same as PPQT version 1, with these additions:

1. Is based on Qt5.4 and PyQt5.4 under Python 3.4, gaining some features and
greater stability. (V1 uses Qt4 and PyQt4 under Python 2.7)

2. Multiple documents (books) can be edited at the same time (V1 allowed only
one document at a time). Support for multiple documents forced changes in
almost every module; many things that were global resources have to be
localized to the document.

3. The metadata file stored with each book has a new format based on JSON.

4. Numerous smaller user interface changes and improvements removed minor
restrictions and made the user experience better.

## Translators

A major conceptual change was applied as a result of discovering that a multitude
(well, two) new text markup styles were being used in DP: Ppgen in the U.S. and Fpgen
by DP Canada. Each of those incompatible markups was the head of a toolchain that
fed into batch utilities to generate HTML, EPUB and such end-formats.

Besides these, there are several markups (such as AsciiDoc) that accomplish the
same thing: feeding a batch toolchain to create other book formats.

PPQT V1, following its model Guiguts, provided built-in conversion to
formatted ASCII and to HTML. This is no longer a sustainable design because
it would put PPQT in direct competition with at least two other toolchains,
and at a disadvantage because those toolchains already handle EPUB, MOBI, and
PDF, which PPQT did not (and which I have no interest in coding).

So PPQT V2 does not provide built-in conversion to ASCII or HTML. Instead it
provides a clean, comprehensible interface to any number of Translators. A
Translator is an independent module (dynamically loaded by PPQT) that takes a
well-formatted DP book as input, and produces a new version marked up by some
other convention -- such as HTML, or Ppgen. The new version opens as a new
document in PPQT for editing.

It is my intent that other people supply Translators. I have written and
included two example Translators, one for HTML and one for ASCII. (Thus PPQT
V2 actually does support conversion to those forms, but in code that can be
easily changed or replaced.)

Support for Translators is in this repository in the folder extras/xlt_dev.
The documentation for the API is TranslatorAPI.html. skeleton.py is a
skeleton basis for a new Translator. testing.py is a simple translator that
writes a document showing all the API inputs it received.
