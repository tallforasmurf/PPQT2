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

                          METADATA.PY

The class defined here supervises the loading and saving of metadata, and
provides a level of indirection (symbolic binding) between file management and
data management. One object of this class is created by a Book to handle the
metadata for that book. Also included: a method to translate a Guiguts .bin file
into our metadata format.

The .meta data file comprises a number of sections that are marked
off by boundary lines similar to:

    {{SECTIONNAME}}
    ...data lines...
    {{/SECTIONNAME}}

It also contains one-line items of the form:

    {{SECTIONNAME single-value}}

We want to encapsulate knowledge of the content and format of metadata in the
classes that create and use it. We do not want that knowledge to leak into
the load/save logic as it did in version 1. So we set up a level of
indirection in the form of a dict that relates SECTIONNAME strings to the
functions that read and write the data in those sections.

Because we expect some users will sometimes edit .meta files we assume,
first, the file must be editable UTF-8 (no binary data, or binary data must
be converted to hex characters) and second, we cannot restrict:
    * blank lines within sections,
    * blank lines between sections,
    * leading and trailing spaces on section header/footer lines or data lines
    * undefined nonblank data between sections e.g. commentary
    * order of data lines (the user might stick in vocabulary words out of order)
    * sections occuring multiple times (the reader function determines if later
      sections should add or replace earlier ones)

The key to self.section_dict is a SECTIONNAME and its value is [reader, writer]
where those are functions. The Register(section,reader,writer) method is
called to register the reader and a writer for a given section.

During load_meta(), the code scans a file for "{{SECTIONNAME...}}", looks up
that section in self.section_dict, and calls the reader. During save_meta(), we go
through the keys of self.section_dict, calling each writer in turn.

The signature of a reader is rdr(qts, section, vers, parm), where
    * qts is a QTextStream positioned at the line after the {{SECTIONNAME line,
    * vers is the value "n" of a {{VERSION n}} line if one has been seen,
    * section is the SECTIONNAME string,
    * parm is whatever text was found between SECTIONNAME and }}.

The reader is expected to consume the stream through the {{/SECTIONNAME}}
line if any. The utility read_to() is provided as a generator that returns
lines up to a section boundary or end of file. A single-line section of
course needs no input; the value is in parm and the stream is already
positioned after it. It is possible to register the same reader function for
multiple SECTIONNAME values, and it can use the section parameter to tell
which it is decoding.

The signature of a writer is wtr(qts, section). The writer is expected to write
the entire section including {{SECTIONNAME}} and {{/SECTIONNAME}}, or the single
line of a one-line section. The utilities open_line() and close_line() return
strings ready to be output. A given writer function could be registered for
multiple sections, distinguishing which to do from the section parameter.

The class MemoryStream implements a QTextStream with an in-memory buffer.
This is used by unit tests and when calling translate_bin() below.
'''

import constants as C
import utilities # for MemoryStream
import regex
import logging
import types # for FunctionType validation in register

metadata_logger = logging.getLogger(name='metadata')

# Set up an RE to recognize a sentinel and capture its parameter if any. This
# can be global because the result of using it is a match object, which is
# local to the caller. Correct use is m=re_sentinel.match(string), after
# which m.group(1) is the section name and m.group(2) is all that followed it
# before the closing braces, including spaces, so apply strip() to that
# before using it. Don't use re_sentinel.search as this would allow
# non-spaces to precede a sentinel. Whitespace ok, others not.

re_sentinel = regex.compile("^\\s*\\{\\{([A-Z]+)([^}]*)\\}\\}")

# Helpful utilities for our reader/writer clients:
#
# 1. Format an open string given a sentinel.
#
def open_string( section, parm = None ):
    if parm :
        section = section + ' ' + str(parm)
    return '{{' + section + '}}'
def open_line( section, parm = None ):
    return open_string(section, parm) + '\n'
#
# 2. Format a close string given a sentinel
#
def close_string(section) :
    return '{{/' + section + '}}'
def close_line(section) :
    return close_string(section) + '\n'
#
# 3. Provide a generator that reads a stream to a given end-sentinel,
# or to any end-sentinel (preventing runaway if the opening sentinel
# is mis-typed) or to end of file, whichever comes first.
# This makes for simple coding of a loop to process the lines of a section or
# a whole file.
#
def read_to(qts, sentinel):
    stopper = close_string(sentinel)
    while True:
        if qts.atEnd() :
            line = stopper # end of file before sentinel seen
        else:
            line = qts.readLine().strip()
        if line.startswith('{{/') : # looks like a /sentinel
            break # end the loop for one reason or the other
        yield line

# Each instance of MetaMgr encapsulates what is known about the
# metadata of a single book. The book creates one of these and
# all of its components register for their sections through it.

class MetaMgr(object):
    # class constant for validating readers and writers
    _rdr_wtr_types = (types.FunctionType, types.MethodType, types.LambdaType)

    def __init__(self):
        # Initialize version flags: we always write v.2, but
        # version_read is set by reading a file.
        self.version_write = '2'
        self.version_read = '0'
        # Initialize the important section_dict with our version
        # reader and writer pre-registered.
        self.section_dict = {C.MD_V : [self._v_reader, self._v_writer]}
        # End of __init__

    # The reader and writer methods for the {{VERSION n}} section.
    def _v_reader(self, qts, section, vers, parm) :
        if len(parm) :
            # some nonempty parameter followed VERSION
            self.version_read = parm
            metadata_logger.debug('metadata {0} {1}'.format(section,parm) )
        else:
            metadata_logger.warn('{0} with no parameter: assuming 1'.format(section))
            self.version_read = '1'

    def _v_writer(self, qts, section) :
        qts << open_line(section, self.version_write)

    def version(self):
        return self.version_read

    # Other members of the Book's fleet of objects call this method
    # to register to read and write a section of metadata.
    # TODO a way to prioritize single-line items like VERSION, DEFAULTDICT
    def register(self, sentinel, rdr, wtr):
        if isinstance(rdr, self._rdr_wtr_types) \
        and isinstance(wtr, self._rdr_wtr_types) :
            if isinstance(sentinel,str) :
                if sentinel not in self.section_dict :
                    self.section_dict[sentinel] = [rdr, wtr]
                    metadata_logger.debug('registered metadata for '+sentinel)
                else :
                    metadata_logger.warn('duplicate metadata registration ignored for '+sentinel)
            else:
                metadata_logger.error('metadata reg. sentinel not a string value')
        else:
            metadata_logger.error('metadata reg. rdr/wtr not function types')

    # Load the contents of a metadata file stream by directing each section
    # to its registered reader. If there is no registered reader,
    # set that sentinel to the unknowns above.

    def load_meta(self, qts) :
        global re_sentinel
        while not qts.atEnd() :
            line = qts.readLine().strip()
            m = re_sentinel.match(line)
            if m :
                section = m.group(1)
                parm = m.group(2).strip()
                if section in self.section_dict :
                    metadata_logger.debug('reading '+section+' metadata')
                    self.section_dict[section][0](qts, section, self.version_read, parm)
                else:
                    # Nobody has registered for this section (or it is
                    # {{USER-TYPO}}) so skip all its lines.
                    metadata_logger.error('No reader registered for '+section+' - skipping')
                    for line in read_to(qts, section):
                        pass

    # Write the contents of a metadata file by calling the writer for
    # each registered section. Call VERSION first, others in whatever order
    # the dictionary hash gives them.

    def write_meta(self, qts) :
        self.section_dict[C.MD_V][1](qts,C.MD_V)
        for section, [rdr, wtr] in self.section_dict.items() :
            if section != C.MD_V :
                metadata_logger.debug('writing {0} metadata'.format(section) )
                wtr(qts, section)

# Utility to translate the contents of a Guiguts .bin file to our .meta
# format and return it in a QTextStream. Arguments are:
# bin_stream, an open QTextStream representing a GG .bin file
# book_stream, the book file described by bin_stream (we need to read
#    through it to get the character offset to each line, in order to
#    translate GG line numbers into PPQT char offsets

import ast # for literal_eval
import collections # for defaultdict

def translate_bin(bin_stream, book_stream) :

    meta_stream = utilities.MemoryStream()
    # Regex to recognize the GG page info string, which is a perl dict:
    #    'Pg001' => {'offset' => 'ppp.0', 'label' => 'Pg 1', 'style' => 'Arabic', 'action' => 'Start @', 'base' => '001'},
    #cap(1) ^^^     ^ ------ cap(2) ------->
    re_page = regex.compile("\s+'Pg([^']+)'\s+=>\s+(\{.*\}),")

    # Regex to recognize the proofer info string, something like this:
    # $::proofers{'002'}[2] = 'susanskinner';
    #     png # ---^^^   ^ index - we assume these come in sequence 1-n!
    re_proof = regex.compile("\$::proofers\{'(.*)'\}\[\d\] = '(.*)'")

    # Regex to recognize the bookmark info string, like this:
    # $::bookmarks[0] = 'ppp.lll';
    #   cap(1)-----^  (2)^^^ ^^^--cap(3)
    re_mark = regex.compile("\$::bookmarks\[(\d)\]\s*=\s*'(\d+)\.(\d+)'")

    # Read the book_stream and note the offset of each line.
    # When the book is in the QPlainTextDocument each line has its length
    # in characters plus 1 for the \u2029 line-separator.
    line_offsets = [] # an integer for every line in book_stream
    offset = 0
    while not book_stream.atEnd() :
        line_offsets.append(offset)
        line = book_stream.readLine()
        offset += len(line) + 1
    line_offsets.append(offset) # offset to EOF just in case

    # Reposition book_stream to the start as a courtesy to our caller
    book_stream.seek(0)

    # A dict in which the keys are page #s and the values, proofer strings
    proofers = collections.defaultdict(str)

    # A list that gets for each page, a dict of info with keys of
    # offset, label, style, action and base, all from the perl dict.
    page_list = []

    # list of that gets ( key, offset ) tuples for bookmark values.
    mark_list = []

    # Scan the .bin text collecting page and proofer data.
    # Blank lines and things we don't recognize are just ignored.

    in_pgnum = False # True while in the page-info section of the .bin

    while not bin_stream.atEnd() :
        line = bin_stream.readLine()
        if line.startswith('%::pagenumbers') :
            in_pgnum = True
            continue
        if in_pgnum and line.startswith(');') :
            in_pgnum = False
            continue
        match = re_page.search(line)
        if in_pgnum and ( match ) :
            # We have a page-info line. Convert the perl dict syntax to
            # python syntax, so 'key'=>'val' becomes 'key':'val'
            perl_dict_line = match.cap(2)
            perl_dict_line.replace('=>', ':')
            try: # some things with a small chance of failing
                page = ast.literal_eval(perl_dict_line)
                # convert "offset:ppp.ccc" into a document offset integer
                (ppp, ccc) = page['offset'].split('.')
                page['offset'] = int( line_offsets[ int(ppp) - 1 ] + int(ccc) )
            except Exception:
                msg = line
                if len(line) > 30 : msg = line[:30] + '...'
                metadata_logger.warn('error on .bin line '+msg)
                continue
            # add png number string to the dict
            page['png'] = match.cap(1)
            # save for later
            page_list.append(page)
            continue # finished with page info...
        # not page info, is it a proofer line?
        match = re_proof.indexIn(line)
        if match :
            # append this proofer name to the (possibly zero) others for
            # the given line. They can contain spaces! Replace with numspace.
            one_proofer = match.cap(2).replace(' ', '\u2002')
            proofers[ match.cap(1) ] += ('\\' + one_proofer)
            continue
        # neither of those, is it a bookmark?
        match = re_mark.match(line)
        if match :
            offset = int( line_offsets[ int(match.cap(2))-1 ] + int(match.cap(3)) )
            key = int( match.cap(1) )
            mark_list.append( (key, offset) )
        # blank line, whatever, ignored

    # For convenience add the accumulated proofer strings to the info dict
    # for each page.
    for page in page_list :
        page['proofers'] = proofers[page['png']]
    #Write the accumulated data into the meta_stream.
    meta_stream << u"{{" + C.MD_V + "2}}\n"
    meta_stream << u"{{" + C.MD_PT + "}}\n"
    prior_format = C.FolioFormatArabic # Default starting folio format
    for page in page_list :
        # See pagedata.py for the PAGETABLE metadata format.
        # Translate the GG folio actions to our pagetable form.
        folio_rule = C.FolioRuleSkip # Skip anything not recognized
        if page['action'] == '+1' :
            folio_rule = C.FolioRuleAdd1
        elif page['action'] == 'Start @':
            folio_rule = C.FolioRuleSet
        # Translate the GG folio styles
        folio_format = C.FolioFormatArabic # in case nothing matches
        if page['style'] == '"' :
            folio_format = prior_format
        elif page['style'] == 'Roman':
            folio_format = C.FolioFormatLCRom
        elif page['style'] == 'Arabic' :
            folio_format = C.FolioFormatArabic
        prior_format = folio_format
        # Note: we are not collecting the GG "label" data, as it
        # is the formatted value "Pg xiv" or "Pg 25". Instead we
        # keep the "base" data which is the integer for "Start @"
        # entries, or null. In the Page panel folio numbers will be
        # mostly 0 until you click Update, then all will be correct.
        meta_stream << '{0} {1} {2} {3} {4} {5}\n'.format(
            page['offset'], page['png'], page['proofers'],
            folio_rule, folio_format, int(page['base'] or 1)
            )
    meta_stream << u"{{/" + C.MD_PT + "}}\n"
    meta_stream << u"{{" + C.MD_BM + "}}\n"
    for (key, offset) in mark_list :
        meta_stream << '{0} {1}\n'.format(key, offset)
    meta_stream << u"{{/" + C.MD_BM + "}}\n"
    meta_stream.seek(0) # that's all, folks
# that's it. output data written into the stream.