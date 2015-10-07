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
__version__ = "1.0.0"
__author__  = "David Cortesi"
__copyright__ = "Copyright 2015 David Cortesi"
__maintainer__ = "David Cortesi"
__email__ = "tallforasmurf@yahoo.com"

DOCSTRING = '''
This program reads the metadata from a book saved by PPQT 2.0.
It writes a .bin file with some metadata compatible with Guiguts.
Example:

    python3 meta2bin.py very_good_book.utf

It looks for very_good_book.utf.ppqt (the PPQT2 metadata file).

It writes a new file very_good_book.utf.bin containing the Page
Boundary metadata as you set it using the PPQT2 Pages panel.

Only the page boundary info is written. Proofer names and
bookmarks are not written.

If you edit the book and save it, the metadata changes, and you need to
make a new .bin file.
'''

import logging
my_logger = logging.getLogger()
import sys
import os
import json

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# These items are copied from constants.py to avoid having to import it.

FolioFormatArabic = 0x00
FolioFormatUCRom = 0x01
FolioFormatLCRom = 0x02
FolioFormatSame = 0x03 # the "ditto" format
FolioRuleAdd1 = 0x00
FolioRuleSet = 0x01
FolioRuleSkip = 0x02

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Write a brief help message to stdout

def help():
    print( DOCSTRING )

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Open the book file and read it all by lines. Make a table (actually just
# a list) of the offsets of the lines. This is used to convert a PPQT
# text position (an offset into the entire text) into a Guiguts lll.xx
# position (line-number and offset within line).
#
LINE_TABLE = []

def make_line_table( book_file ):
    global LINE_TABLE

    position = 0
    for line in book_file.readlines():
        LINE_TABLE.append( position )
        position = position + len(line) + 1
    # put a stopper at the end of the list
    LINE_TABLE.append( position + 1000 )

# Given a position within the whole book document, convert it to a line
# number and offset within the line, returned as a tuple (llll, xx).
#
# The job is to find the first item of LINE_TABLE that is greater than or
# equal to position. If greater-than, the llll value is the index of the
# preceding entry, and the xxx is the position minus the preceding entry.
# Because page boundaries are between lines, it should often happen that
# position==LINE_TABLE[x].
#
# We expect to be called with positions that are monotonically increasing,
# so we just do a sequential search from the last position found. If by
# chance we are already past the given position, we start over from the
# top. (Given random data this would be a "pessimal" algorithm.)
#
#

LAST_LINE = 0

def convert_position( position ) :
    global LAST_LINE

    index = LAST_LINE
    if position < LINE_TABLE[ index ] :
        # oops, out of sequence, start scan over
        index = 0
    assert position >= LINE_TABLE[ index ]

    while position > LINE_TABLE[ index ] :
        index += 1
    if position < LINE_TABLE[ index ] :
        index -= 1
    offset = position - LINE_TABLE[ index ]
    LAST_LINE = index

    return ( index, offset )

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# The following code is copied from metadata.py in the PPQT2 app.
#
# JSON does not support saving Python sets or Python bytes. PPQT2 extends
# JSON to save values of these kinds using a custom encoder. To read the
# metadata file we need to use the custom decoder.
#
# To do custom JSON decoding, define an object-hook function. It is called
# during decoding to inspect each decoded JSON object as a dict {"key":value}
# and it may return either the input dict, or a replacement object.
#
# In this case it looks for a set or bytestring as encoded by PPQT. If it
# finds either it returns the actual data; else returns the input.
#

def _json_object_hook(object_dict):
    if 1 == len(object_dict):
        # simple single-key value, get key and value.
        [(key, value)] = object_dict.items()
        if key == '<SET>' :
             # instead of the dict, return the value of the encoded set
            return set(value)
        if key == '<BYTE>' :
            # instead of the dict, return the value of the encoded bytestring
            return bytes.fromhex(value)
    return object_dict

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Decimal integer to Roman-numeral conversion. Adapted from Mark Pilgrim's
# "Dive Into Python". PPQT supports both upper and lowercase roman but
# Guiguts only does lowercase.

_ROMAN_MAP = (('M',  1000),
              ('CM', 900),
              ('D',  500),
              ('CD', 400),
              ('C',  100),
              ('XC', 90),
              ('L',  50),
              ('XL', 40),
              ('X',  10),
              ('IX', 9),
              ('V',  5),
              ('IV', 4),
              ('I',  1))
def to_roman( n, lc=True ):
    if (0 < n < 5000) and int(n) == n :
        result = ""
        for numeral, integer in _ROMAN_MAP:
            while n >= integer:
                result += numeral
                n -= integer
    else : # invalid number, log but don't raise an exception
        my_logger.error(
            'Invalid number for roman numeral {}'.format(n) )
        result = "????"
    if lc : result = result.lower()
    return result

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Write one line of GG page data to a file object.
#
# Input is a Python list containing one row of Page metadata:
#
#  [position, filename, proofers, rule, format, number]
#
# Output is one Perl dict item, a pagename as key and a Perl dict as value:
#
# 'Pg001' => {'offset' => 'ppp.0', 'label' => 'Pg 1', 'style' => 'Arabic', 'action' => 'Start @', 'base' => '001'},
#
# Translation dicts for the style and action codes:

XLATE_STYLE = {
    FolioFormatArabic : 'Arabic',
    FolioFormatLCRom : 'Roman',
    FolioFormatUCRom : 'Roman',
    FolioFormatSame  : '"'
    }

XLATE_ACTION = {
    FolioRuleAdd1 : '+1',
    FolioRuleSkip : 'No Count',
    FolioRuleSet  : 'Start @',
    }

# remember last explicit style in order to translate the ditto format

DITTO_STYLE = FolioFormatArabic

# template for the output line. The parameter names are given
# as **kwargs to TEMPLATE.format()

TEMPLATE = "'{scan}' => {{'offset' => '{line}.{offset}', 'label' => '{folio}', 'style' => '{style}', 'action' => '{action}', 'base' => '{base}'}},\n"

def do_one_line( bin_file, metadata, sequence ) :
    global DITTO_STYLE

    # unpack the metadata
    (position, filename, proofers, rule, fmt, number) = metadata

    # prepare a dict that will be TEMPLATE.format(**kwargs)
    format_kwargs = dict()

    # convert the position
    (format_kwargs['line'] , format_kwargs['offset']) = convert_position( position )

    # convert the style and action codes
    format_kwargs['style'] = XLATE_STYLE[ fmt ]
    format_kwargs['action'] = XLATE_ACTION[ rule ]
    format_kwargs['base'] = str(number) if rule == FolioRuleSet else ''

    if fmt != FolioFormatSame : # note change of style
        DITTO_STYLE = fmt

    # convert the label (folio) value. PPQT doesn't store that in
    # the metadata so we have to generate it.
    format_kwargs['folio'] = '' # assume Skip
    if rule != FolioRuleSkip :
        if DITTO_STYLE == FolioFormatArabic :
            format_kwargs['folio'] = str(number)
        else : # roman or ROMAN
            format_kwargs['folio'] = to_roman( number )

    # generate a sequential key Pgnnn from the sequence number
    # allow for book of 1000 pages.
    format_kwargs['scan'] = 'Pg{:04d}'.format(sequence)

    # build the output string and write it
    out_line = TEMPLATE.format( **format_kwargs )
    bin_file.write( out_line )

def main( argv ):

    # were we given an argument?

    if len(argv) <= 1 :

        # it would appear not.
        help()
        return

    # were we given too many arguments?

    if len(argv) > 2 :

        # it would appear so
        my_logger.error( 'Too many arguments' )
        help()
        return

    # arguments are juuuust right, so...
    book_name = argv[1]

    # is it a file and can we read it?

    if not ( os.path.isfile( book_name ) ) or not ( os.access( book_name, os.R_OK ) ) :

        # seems not
        my_logger.error( 'Cannot access {} to read it'.format( book_name ) )
        help()
        return

    # yes. Figure its encoding based on PPQT's simple rules.

    encoding = 'UTF8'
    if ( '-l.' in book_name ) or ( '-ltn' in book_name ) or (book_name.endswith( '.ltn' ) ) :
        encoding = 'LATIN-1'

    # Make sure that a .ppqt file exists and is readable.

    meta_name = book_name + '.ppqt'
    if not ( os.path.isfile( meta_name ) ) or not ( os.access( meta_name, os.R_OK ) ) :

        # seems it is not
        my_logger.error( 'Cannot access metadata file {} to read it'.format( meta_name ) )
        help()
        return

    # read the book and make a table from it in LINE_TABLE
    book_file = open( book_name, 'r', encoding=encoding )
    make_line_table( book_file )

    # read the meta file, decode it, placing the whole dict of meta stuff in meta_dict

    meta_file = open( meta_name, 'r', encoding='UTF8' )
    json_input_string = meta_file.read()
    meta_dict = dict()
    try:
        meta_dict = json.loads( json_input_string, object_hook=_json_object_hook )
    except ValueError as json_error_object :
        json_error_str = str(json_error_object)
        my_logger.error('JSON error: '+json_error_str)

    # if that failed, meta_dict is empty; in that case, or if the book has no
    # page info, the following exits.
    if not 'PAGETABLE' in meta_dict or 0 == len(meta_dict['PAGETABLE']) :
        my_logger.error( 'Book {} has no page info.'.format( book_name ) )
        return

    page_list = meta_dict['PAGETABLE']

    bin_name = book_name + '.bin'
    bin_file = open( bin_name, 'w', encoding='LATIN1', errors='replace' )
    bin_file.write( "%pagenumbers = (\n" )

    sequence = 0
    for one_page in page_list :
        do_one_line( bin_file, one_page, sequence )
        sequence += 1

    bin_file.write( ");\n" )
    bin_file.close()


if __name__ == '__main__' :
    main( sys.argv )