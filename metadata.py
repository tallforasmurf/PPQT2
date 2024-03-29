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
__copyright__ = "Copyright 2013, 2014, 2015 David Cortesi"
__maintainer__ = "David Cortesi"
__email__ = "tallforasmurf@yahoo.com"


'''

                          METADATA.PY

The class defined here supervises the loading and saving of metadata, and
provides a level of indirection (symbolic binding) between file management
and data management. One object of class MetaMgr is created by each Book to
handle the metadata for that book.

The metadata filename for a book has an required file suffix specified in the
constants module as C.METAFILE_SUFFIX.

We want to encapsulate knowledge of the content and format of each type of
metadata within the class that creates and uses that type of metadata.
So we set up a level of indirection in the form of a dict that relates
section objects to methods that create or consume the data in those sections.
Each of the various objects instantiated by the Book, register their reader
and writer methods here by section name.

The metadata file consists of a single, giant JSON object. Logically, that
object is a dict. Each key in the dict is a metadata section name, for
example "BADWORDS". Each value is a single Python value that contains all the
metadata for that section.

The metadata section names are defined in constants.py, for example C.MD_BW
has the name for the "BADWORDS" section. The value of each section is defined
entirely by the metadata writers and readers provided by each module. For
example the value of the BADWORDS section is a list of strings, because that is
what the module responsible for managing that metadata chooses to write, and
expects to read.

The metadata manager stores its registered users in MetaMgr.section_dict.
Each key is a section name and its value is [reader,writer] where those are
references to functions. MetaMgr.register(section,reader,writer) is called to
register the reader and a writer for a given section.

In MetaMgr.load_meta(), we read the entire metadata file and give it to JSON
to decode. The result is a dict with a key for each section name. We call the
reader that was registered for each section name, passing the decoded value.

In MetaMgr.save_meta() we go through the keys of section_dict, calling each
registered writer in turn. The writer returns a single Python value. We build
a temporary dict with keys of section names and values as returned by the
writers, and dump the JSON encoding of that dict to the output file.

The signature of a reader is:  rdr(section, value, version), where
    * section is the section name string,
    * value is the decoded value for the section
    * version is the value "n" of a {"VERSION":n} object, if one has been
      seen in the metadata input

It is possible to register the same reader function for multiple SECTIONNAME
values, and it can use the section parameter to tell which it is decoding.

The signature of a writer is wtr(section). The writer is expected to return a
single Python value containing the data that the corresponding reader would
expect on load of that section. A given writer function could be registered
for multiple sections, distinguishing what to do from the section parameter.

The standard JSON encoder does not support Python set or byte values. We
extend it with customized encode and decode operations. A set value is
encoded as a dict {"<SET>":[list_of_set_values]}. A byte value is encoded as
a dict {"<BYTE>":"string_of_hex_chars"}.

There is nothing top stop the user from editing a metadata file, modifying
values within JSON object definitions. Reader functions must allow for this
and not assume all values are trustworthy. Reader methods have to permit:
    * arbitrary whitespace within sections (JSON handles this)
    * sections occuring multiple times - Each reader function determines if
      a later section will extend or replace an earlier one
    * arbitrary sequence of items within a section value, because the JSON
      encoder rearranges the order of dict entries, and the user might
      rearrange items of a list.
'''

import logging
metadata_logger = logging.getLogger(name='metadata')

import constants as C
import types # for FunctionType validation in register
import json

'''
The JSON objects don't retain any state between uses, and PPQT is
single-threaded, so we can store them as globals.

The JSON library API for custom encoding/decoding is rather magnificently
random. To do custom DEcoding, we define an object-hook function. It will be
called during decoding to inspect each decoded JSON object as a dict
{"key":value} and it may return either the input dict, or a replacement
object.
'''
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
    ''' else not one of our special types '''
    return object_dict

'''
To create a custom ENcoder, we define a class derived from JSONEncoder, with
an override of its default() method. It gets a look at every Python object
about to be encoded, and can return a substitute Python object that the
default encoder is able to serialize.

To use the custom encoder we pass that class definition(!) to the standard
method json.dumps(), see MetaMgr.write_meta() below.
'''
class _Extended_Encoder(json.JSONEncoder):
    def default(self,obj):
        if isinstance(obj, bytes) :
            # Thanks Frank Zago for this code!
            return { '<BYTE>' : " ".join("{:02x} ".format(c) for c in obj) }
        if isinstance(obj, set) :
            return { '<SET>' : list(obj) }
        return super().default(obj)

'''
Each instance of the MetaMgr class encapsulates what is known about the
metadata of a single book. The book creates one of these and all of the
Book's components register for their sections through it.
'''
class MetaMgr(object):
    ''' class constant for validating reader and writer parameters '''
    _rdr_wtr_types = (types.FunctionType, types.MethodType, types.LambdaType)

    def __init__(self):
        '''
        Initialize version flags: we always write v.2, while
        version_read is set by reading the file.
        '''
        self.version_write = '2'
        self.version_read = '0'
        '''
        Initialize the important section_dict, initialized with our version
        reader and writer pre-registered in it.
        '''
        self.section_dict = {C.MD_V : [self._v_reader, self._v_writer]}
        # End of __init__

    ''' The reader and writer methods for the {"VERSION":n} section. '''
    def _v_reader(self, section, value, version) :
        if (isinstance(value, int) or isinstance(value,float)) \
           and value >= 2 and value <= 9 :
            ''' Reasonable numeric value, convert to string '''
            value = str(value)
        if isinstance(value, str) and value >= '2' and value <= '9' :
            self.version_read = value
        else:
            metadata_logger.warn('{0} with unexpected value {2}, assuming "2"'.format(section,value))
            self.version_read = '2'

    def _v_writer(self, section) :
        return self.version_write

    def version(self):
        return self.version_read

    '''
    Members of the Book's fleet of objects, while initializing themselves,
    call this method to register to read and write a section of metadata.
    '''
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

    '''
    Load the contents of a metadata file stream. Input is an input text
    stream. If there is any error in the decoding, document it and return an
    error to our caller (Book).
    '''

    def load_meta(self, qts) :
        global _json_object_hook
        '''
        Get the whole stream of encodes as a single string value. JSON then
        decodes it all into a single dict whose keys are the section names
        and values the section values (possibly large).
        
        Pass each section value to the registered reader (section_dict[section][0])
        
        Thanks Frank Zago for shortening this code.
        
        Pull the VERSION section and process it first if it is present.
        '''
        json_string = qts.readAll()
        try:
            bookconf = json.loads( json_string, object_hook=_json_object_hook )
        except ValueError as json_error_object :
            json_error_str = str(json_error_object)
            metadata_logger.error('JSON error:'+json_error_str)
            return json_error_str

        received_sections = [ _s for _s in bookconf.keys() ]
        if C.MD_V in received_sections :
            ''' VERSION is there, make sure it comes first in the list '''
            received_sections.remove(C.MD_V)
            received_sections.insert(0,C.MD_V)
        for section in received_sections:
            if section in self.section_dict :
                metadata_logger.debug('loading metadata section '+section)
                self.section_dict[section][0](section, bookconf[section], self.version_read)
            else:
                '''
                Nobody has registered for this section (or it is a user typo)
                so just log the problem.
                '''
                metadata_logger.error(
                    'No reader registered for {}, ignoring it'.format(section))

    '''
    Write the contents of a metadata file by calling the writer for each
    registered section, saving each value returned in a dict keyed by
    section-name. Dump that whole dict via JSON as the metadata file.
    Argument qts is an output file stream.
    '''
    def write_meta(self, qts) :
        global _Extended_Encoder
        bookconf = dict()
        for section in self.section_dict.keys():
            metadata_logger.debug('collecting metadata section {}'.format(section) )
            # make a one-entry dict of section : value
            bookconf[section] = self.section_dict[section][1](section)
        qts << json.dumps(bookconf, indent=2, cls=_Extended_Encoder )

    '''
    Primarily for the use of the translator code, write the contents of a
    a single section by name.
    '''
    def write_section( self, qts, section ) :
        global _Extended_Encoder
        if section in self.section_dict :
            out = { section : self.section_dict[section][1](section) }
            qts << json.dumps(out, indent=2, cls=_Extended_Encoder )
