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
provides a level of indirection (symbolic binding) between file management
and data management. One object of class MetaMgr is created by each Book to
handle the metadata for that book.

The metadata file for a book has the suffix .ppqt. It consists of a series of
JSON objects. Each JSON object has a single named value. The name of the
value is the section name as defined in constants.py: MD_BW and following.
Each encoded section object begins with "\n{" and runs through the matching
"}". (Note this means the file should *start*with* a newline!)

    \n{ "SECTIONNAME" : one Python value, usually a dict, occupying
         an arbitrary number of lines... }
    \n{ "NEXT SECTION NAME" : ...

The user may edit the file, modifying values within JSON object definitions;
of course any such modifications will be lost when the file is rewritten on a
Save operation. Because we expect users will (rarely) edit the metadata file
we have to permit:

    * arbitrary whitespace within sections (JSON handles this)
    * arbitrary text of any length between sections,
    * arbitrary sequence of sections
    * sections occuring multiple times - Each reader function determines if
      a later section will extend or replace an earlier one
    * arbitrary sequence of items within a section because the JSON encoder
      rearranges the order of dict entries, and the user might rearrange
      items of a list.

We want to encapsulate knowledge of the content and format of of each type of
metadata in the classes that create and use that type of metadata. We do not
want that knowledge to leak into the load/save logic as it did in version 1.
So we set up a level of indirection in the form of a dict that relates
section objects to methods that create or consume the data in those sections.
Objects instantiated by the Book register their reader and writer methods
here by section name.

The key to MetaMgr.section_dict is a SECTIONNAME and its value is [reader,
writer] where those are methods. MetaMgr.register(section,reader,writer) is
called to register the reader and a writer for a given section.

In MetaMgr.load_meta(), we scan a stream for top-level objects, and decode
them in turn. Each decoded object should be a Python dict with just one key,
the section name, whose value is a single Python object. We look up that
section in section_dict, and call the reader passing the decoded value.

In MetaMgr.save_meta() we go through the keys of section_dict, calling each
registered writer in turn. The writer returns a single Python value. We write
to the output stream the JSON encoding of {'SECTION':value}, with newlines on
each side. Also available is MetaMgr.save_section() to write the metadata of
a single section by name (used when duplicating a Book).

The signature of a reader is:  rdr(section, value, version), where
    * section is the SECTIONNAME string,
    * value is the decoded value for SECTIONNAME
    * version is the value "n" of a {"VERSION":n} object if one has been seen

It is possible to register the same reader function for multiple SECTIONNAME
values, and it can use the section parameter to tell which it is decoding.

The signature of a writer is wtr(section). The writer is expected to return a
single Python value, typically a dict, containing the data that the
corresponding reader would expect on load of that section. That value is
JSON-encoded with the key of section. A given writer function could be
registered for multiple sections, distinguishing which to do from the section
parameter.

The standard JSON encoder does not support Python set or byte values. We
extend it with customized encode and decode operations. A set value is
encoded as a dict {"<SET>":[list_of_set_values]}. A byte value is encoded as
a dict {"<BYTE>":"string_of_hex_chars"}.

'''

import constants as C
import logging
import types # for FunctionType validation in register

metadata_logger = logging.getLogger(name='metadata')

# =-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# The json objects don't retain any state between uses, and PPQT is
# single-threaded, so we can store them as globals. The JSON library API for
# custom encoding/decoding is rather magnificently random. To do custom
# DEcoding, we define an object-hook function. It will be called during
# decoding to inspect each decoded JSON object as a dict {"key":value} and it
# may return either the input dict, or a replacement object.

import json

def _json_object_hook(object_dict):
    if 1 == len(object_dict):
        # simple single-key value, get key and value.
        [(key, value)] = object_dict.items()
        if key == '<SET>' :
             # instead of the dict, return the value of the encoded set
            object_dict = set(value)
        if key == '<BYTE>' :
            # instead of the dict, return the value of the encoded bytestring
            object_dict = bytes.fromhex(value)
    return object_dict

# Now we create a custom decoder object passing the name of our hook.

_metadata_decoder = json.JSONDecoder(object_hook=_json_object_hook)

# Then we can use that decoder object's .raw_decode() method for decoding,
# see MetaMger.load_meta.

# To create a custom ENcoder, we define a class derived from JSONEncoder,
# with an override of its default() method. It gets a look at every Python
# object about to be encoded, and can return a substitute Python object that
# the default encoder is able to serialize.

class _Extended_Encoder(json.JSONEncoder):
    def default(self,obj):
        if isinstance(obj, bytes) :
            # Thanks Frank Zago for this code!
            return { '<BYTE>' : "".join("{:02x} ".format(c) for c in obj) }
        if isinstance(obj, set) :
            return { '<SET>' : list(obj) }
        return super().default(obj)

# To use the custom encoder we pass that class definition(!) to the standard
# method json.dumps(), see MetaMgr.write_meta() below.

# =-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Each instance of the MetaMgr class encapsulates what is known about the
# metadata of a single book. The book creates one of these and all of its
# components register for their sections through it.

class MetaMgr(object):
    # class constant for validating reader and writer parameters
    _rdr_wtr_types = (types.FunctionType, types.MethodType, types.LambdaType)

    def __init__(self):
        # Initialize version flags: we always write v.2, but
        # version_read is set by reading a file.
        self.version_write = '2'
        self.version_read = '0'
        # Initialize the important section_dict with our version
        # reader and writer pre-registered in it.
        self.section_dict = {C.MD_V : [self._v_reader, self._v_writer]}
        # End of __init__

    # =-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # The reader and writer methods for the {"VERSION":n} section.
    def _v_reader(self, section, value, version) :
        if (isinstance(value, int) or isinstance(value,float)) \
           and value >= 1 and value <= 9 :
            # convert reasonable numeric value to string
            value = str(value)
        if isinstance(value, str) and value >= '1' and value <= '9' :
            self.version_read = value
        else:
            metadata_logger.warn('{0} with unexpected value {2}, assuming "1"'.format(section,value))
            self.version_read = '1'

    def _v_writer(self, section) :
        return self.version_write

    def version(self):
        return self.version_read

    # =-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # Members of the Book's fleet of objects call this method to register to
    # read and write a section of metadata.
    def register(self, section, rdr, wtr):
        if isinstance(rdr, self._rdr_wtr_types) \
        and isinstance(wtr, self._rdr_wtr_types) :
            if isinstance(section,str) :
                if section not in self.section_dict :
                    self.section_dict[section] = [rdr, wtr]
                    metadata_logger.debug('Registered reader/writer for '+section)
                else :
                    metadata_logger.warn('Duplicate metadata registration ignored for '+section)
            else:
                metadata_logger.error('Registered section name not a string value')
        else:
            metadata_logger.error('Registered rdr/wtr not function types section '+section)

    # =-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # Load the contents of a metadata file stream by decoding each section in
    # turn, and passing the decoded section value to its registered reader.
    # If there is no registered reader, log it.

    def load_meta(self, qts) :
        global _metadata_decoder
        # Get the whole stream of encodes as a single string value. (Remember
        # the good old days when we didn't have gigs of RAM and this kind of
        # thing would be unthinkable?)
        json_string = qts.readAll()
        # In the following, object_start is the index of where we see the
        # next "\n{" and object_end is the index returned by raw_encode().
        object_start = 0
        object_end = 0
        while True:
            # get the index of the next encoded {item and quit if no more.
            object_start = json_string.find('\n{',object_end) + 1
            if 0 >= object_start : break # no more objects
            try:
                (decoded_value, object_end) = _metadata_decoder.raw_decode(
                    json_string, idx=object_start)
                if isinstance(decoded_value,dict) and \
                   1 == len(decoded_value) :
                    [(section, value)] = decoded_value.items()
                    if section in self.section_dict :
                        metadata_logger.debug('loading section '+section)
                        self.section_dict[section][0](section,value,self.version_read)
                    else:
                        # Nobody has registered for this section (or it is a user typo)
                        # so log the problem.
                        metadata_logger.error(
                            'No reader registered for {}, ignoring it'.format(section))
                else :
                    # Decoded JSON object is not a simple {"key":value}. Don't know
                    # what to do, just log it and go on.
                    metadata_logger.error(
                        'Unexpected JSON object type in metadata file between {} and {}, ignoring it'.format(object_start,object_end))
            except ValueError as error_object :
                # Log the error. A typical msg would be "Expecting property
                # name enclosed in double quotes: line n column n (char n)"
                error_msg = str(error_object)
                text_end = min(object_start+100, len(json_string))
                metadata_logger.error("Error decoding metadata: "+error_msg)
                metadata_logger.error("Text reads: "+json_string[object_start:text_end])
                # Advance the pointers so we don't loop on the same error.
                object_end = object_start
                # and continue the loop on the next section.
            # end of while True
        # end of load_meta

    # =-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # Write the contents of a single metadata section. This is a subroutine
    # for write_meta(), and also called from unit-test code and from the
    # code that clones a book.

    def write_section(self, qts, section) :
        if section in self.section_dict :
            metadata_logger.debug('writing metadata section {}'.format(section) )
            # make a one-entry dict of section : value
            _d = { section : self.section_dict[section][1](section) }
            qts << '\n' # start every section-object on a new line
            qts << json.dumps(_d, indent=2, cls=_Extended_Encoder )
        else :
            metadata_logger.error('No writer registered for section {}'.format(section))

    # =-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # Write the contents of a metadata file by calling the writer for each
    # registered section, and encoding the value it returns. Start the file
    # with a newline. Write the VERSION section first, others in whatever
    # order the dictionary hash gives them.

    def write_meta(self, qts) :
        global _Extended_Encoder
        sections = [_s for _s in self.section_dict.keys() ]
        sections.remove(C.MD_V)
        sections.insert(0,C.MD_V)
        for section in sections:
            self.write_section(qts, section)
