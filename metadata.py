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
metadata for that book. Also included: a method to import a Guiguts .bin file,
convert it to a metadata stream, and then load that.

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
indirection in the form of a dict that relates SECTIONNAMEs to the functions
that read and write the data in those sections.

Because we expect some users will sometimes edit .meta files, first,
the file must be editable UTF-8 (no binary data, or binary data must
be converted to hex characters) and second, we do not restrict:
    * blank lines within sections,
    * blank lines between sections,
    * leading and trailing spaces on section header/footer lines or data lines
    * undefined nonblank data between sections
    * order of data lines (the user might stick in lines anywhere)
    * sections occuring multiple times (usually just additive)

The key to self.section_dict is a SECTIONNAME. The value is [reader, writer]
where those are functions. The Register(section,reader,writer) method is
called to register the reader and a writer for a given section.

During load_meta(), the code scans a file for "{{SECTIONNAME...}}", looks up
that section in self.section_dict, and calls the reader. During save_meta(), we go
through the keys of self.section_dict, calling each writer in turn.

The signature of a reader is rdr(qts, section, vers, parm), where
    * qts is a QTextStream positioned at the line after the {{SECTIONNAME line,
    * vers is the value of a {{VERSION n}} line if one has been seen,
    * section is the SECTIONNAME as a Python string,
    * parm is whatever text was found between SECTIONNAME and }}.

The reader is expected to consume the stream through the {{/SECTIONNAME}} line
if any. A single-line section of course needs no input; the value is in parm
and the stream is already positioned after it.

The signature of a writer is wtr(qts, section). The writer is expected to write
the entire section including {{SECTIONNAME}} and {{/SECTIONNAME}}, or the single
line of a one-line section.

'''

from PyQt4.QtCore import QString, QTextStream
import types
import re
# set up an RE to recognize a sentinel and capture its parameter
# if any. This can be global because the result of using it
# is a match object that is local to the caller.
re_sentinel = re.compile("^\\{\\{([A-Z]+)([^}]*)\\}\\}")

import pagedata # for the format constants

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
# 3. Provide a generator that reads a stream to a sentinel or end of file.
# This makes for simple coding of a loop to process the lines of a section or
# a whole file.
#
def read_to(qts, sentinel):
    stopper = close_string(sentinel)
    while True:
        if qts.atEnd() :
            line = stopper # end of file before sentinel seen
        else:
            line = unicode(qts.readLine()).encode('UTF-8').strip()
        if line == stopper :
            break # end the loop for one reason or the other
        yield line

class MetaMgr(object):
    def __init__(self):
        # Initialize version flags: we always write v.2, but
        # version_read is set by reading a file.
        self.version_write = '2'
        self.version_read = '0'
        # Initialize the important section_dict with our version
        # reader and writer pre-registered.
        self.section_dict = {'VERSION':[v_reader, v_writer]}
        # This string remains "in scope" forever so it can be the basis of a
        # QTextStream that is handed around.
        self.stream_string = QString()
        # End of __init__

    # The reader and writer methods for the {{VERSION n}} section.
    def v_reader(qts, section, vers, parm) :
        global Version_read
        Version_read = parm
    def v_writer(qts, section) :
        global Version_write
        qts << open_line(section, Version_write)

    # Other members of the Book's fleet of objects call this method
    # to register to read and write a section of metadata.

    def register(sentinel, rdr, wtr):
        if type(rdr) == types.FunctionType \
        and type(wtr) == types.FunctionType \
        and type(sentinel) == types.UnicodeType :
            if sentinel not in self.section_dict :
                # TODO: log info
                self.section_dict[sentinel] = [rdr, wtr]
            else :
                pass # TODO: log an error
        else:
            pass # TODO: log an error or raise Type Error?

    # This reader/writer pair is entered into the self.section_dict when a
    # section with no registered handler is found.

    def unknown_reader(qts, section, vers, parm) :
        # TODO: log reading unknown section
        line = unicode(qts.readLine()).strip()
        while not qts.atEnd() :
            if line == close_string(section) :
                break
            line = unicode(qts.readLine()).strip()
    def unknown_writer(qts, section) :
        pass

    # Load the contents of a metadata file by directing each section
    # to its registered reader. If there is no registered reader,
    # set that sentinel to the unknowns above.

    def load_meta(qts) :
        global re_sentinel
        while not qts.atEnd() :
            line = unicode(qts.readLine()).strip()
            m = re_sentinel.match(line)
            if m :
                section = m.group(1)
                parm = m.group(2).strip()
                if section not in self.section_dict :
                    # Nobody has registered for this section (or it is
                    # {{USER-TYPO}}) so register it to the garbage reader/writer.
                    self.section_dict[section] = [unknown_reader,unknown_writer]
                # Call the reader.
                self.section_dict[section][0](qts, section, self.version_read, parm)

    # Write the contents of a metadata file by calling the writer for
    # each registered section. Call VERSION first, others in whatever order
    # the dictionary hash gives them.

    def write_meta(qts) :
        self.section_dict['VERSION'][1](qts,'VERSION')
        for section, [r, w] in self.section_dict.items() :
            if section != 'VERSION' :
                w(qts, section)

    # Load the contents of a Guiguts .bin file by converting it to our .meta
    # format as a QTextStream and passing that to load_meta(). The code needs
    # access to the book file in order to convert char offsets into line numbers.

    def load_gg_bin(book_stream, bin_stream) :
        self.stream_string = QString() # gcoll any residual stuff
        meta_stream = QTextStream(self.stream_string)

        # Regex to recognize the page info string, a perl dict like:
        # 'Pg001' => {'offset' => 'ppp.0', 'label' => 'Pg 1', 'style' => 'Arabic', 'action' => 'Start @', 'base' => '001'},
        rePage = QRegExp(u"\s+'Pg([^']+)'\s+=>\s+(\{.*\}),")

        # Regex to recognize the proofer info string, something like this:
        # $::proofers{'002'}[2] = 'susanskinner';
        #     png # ---^^^   ^ index - we assume these come in sequence 1-n!
        reProof = QRegExp(u"\$::proofers\{'(.*)'\}\[\d\] = '(.*)'")

        # Regex to recognize the bookmark info string, like this:
        # $::bookmarks[0] = 'ppp.lll';
        reMark = QRegExp(u"\$::bookmarks\[(\d)\]\s*=\s*'(\d+)\.(\d+)'")

        # Read the book_stream and note the offset of each line.
        line_offsets = [] # an integer for every line in book_stream
        offset = 0
        while not book_stream.atEnd() :
            line_offsets.append(offset)
            line = book_stream.readLine()
            offset += len(line) + 1
        # Reposition book_stream to the start
        book_stream.seek(0)

        in_pgnum = False # True while in the page-info section of the .bin
        proofers = defaultdict(str) # accumulates proofer string per page
        # This list gets for each page, a dict of info with keys of
        # offset, label, style, action and base, from the perl dict.
        page_list = []
        mark_list = [] # list of ( key, offset ) bookmark values

        # Scan the .bin text collecting page and proofer data.
        while not bin_stream.atEnd() :
            # n.b. blank lines and things we don't recognize are just ignored
            line = bin_stream.readLine()
            if line.startsWith(u"%::pagenumbers") :
                in_pgnum = True
                continue
            if in_pgnum and line.startsWith(u");") :
                in_pgnum = False
                continue
            if in_pgnum and (0 <= rePage.indexIn(line) ) :
                # We have a page-info line. Convert the perl dict syntax to
                # python dict syntax.
                perl_dict_line = rePage.cap(2)
                perl_dict_line.replace(u"=>", u":")
                # Note that eval() is a security hole that could be used for
                # code injection. See pqFind for a safer method. Using eval here
                # because who would want to inject code into this obscure app?
                page = eval(unicode(perl_dict_line))
                # convert "offset:ppp.ccc" into a document offset integer
                (ppp, ccc) = page['offset'].split('.')
                page['offset'] = int( line_offsets[int(ppp)-1] + int(ccc) )
                # add png number string to the dict
                page['png'] = unicode(rePage.cap(1))
                # save for later
                page_list.append(page)
                continue
            if 0 <= reProof.indexIn(line) :
                # append this proofer name to the (possibly zero) others for
                # the given line. They can contain spaces! Replace with numspace.
                # Going from QString to Python string to use defaultdict.
                one_proofer = unicode(reProof.cap(2).replace(QChar(" "), QChar(0x2002)))
                proofers[ unicode(reProof.cap(1)) ] += ("\\" + one_proofer)
                continue
            if 0 <= reMark.indexIn(line) :
                offset = int( line_offsets[ int(unicode(reMark.cap(2)))-1 ] \
                                        + int( unicode(reMark.cap(3)) ) )
                key = int( reMark.cap(1) )
                mark_list.append( (key, offset) )
            # blank line, whatever, ignored
        # For convenience add the accumulated proofer strings to the info dict
        # for each page.
        for page in page_list :
            page['proofers'] = proofers[page['png']]
        #Write the accumulated data into the meta_stream.
        meta_stream << u"{{VERSION 0}}\n"
        meta_stream << u"{{STALECENSUS TRUE}}\n"
        meta_stream << u"{{NEEDSPELLCHECK TRUE}}\n"
        meta_stream << u"{{PAGETABLE}}\n"
        # TODO: pagetable.py
        prior_format = pagedata.FolioFormatArabic # Default starting folio format
        for page in page_list :
            # See pagedata.py for the PAGETABLE metadata format.
            # Translate the GG folio actions
            folio_rule = pagedata.FolioRuleSkip # Skip anything not recognized
            if page['action'] == '+1' :
                folio_rule = pagedata.FolioRuleAdd1
            elif page['action'] == 'Start @':
                folio_rule = pagedata.FolioRuleSet
            # Translate the GG folio styles
            folio_format = pagedata.FolioFormatArabic # in case nothing matches
            if page['style'] == '"' :
                folio_format = prior_format
            elif page['style'] == 'Roman':
                folio_format = pagedata.FolioFormatLCRom
            elif page['style'] == 'Arabic' :
                folio_format = pagedata.FolioFormatArabic
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
        meta_stream << u"{{/PAGETABLE}}\n"
        meta_stream << u"{{BOOKMARKS}}\n"
        for (key, offset) in marks :
            meta_stream << '{0} {1}\n'.format(key, offset)
        meta_stream << u"{{/BOOKMARKS}}\n"
        meta_stream.seek(0) # that's all, folks

        self.load_meta(meta_stream)
