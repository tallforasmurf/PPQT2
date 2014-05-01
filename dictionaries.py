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
                          dictionary.py

Global spelling dictionary resource for PPQT2.

This module allows spell-check objects to be created for languages given only
the "tag" or dictionary filename, for example "en_US".

The main window calls initialize() during startup, when we get the last-set
dictionary path and preferred default tag from saved settings.

The set_dict_path() and set_default_tag() methods are called from the
preferences dialog.

initialize(settings)     Get dictionary defaults from settings if available.

shutdown(settings)       Save dictionary defaults in settings.

set_default_tag(tag)     Note the tag of the preferred dictionary
                         from preferences

get_default_tag()        Return the preferred main dictionary tag.

set_dict_path(path)      Note the path to the user's choice of
                         a folder of dictionaries.

get_tag_list(path)       Prepare and return a dict{tag:path} where each
                         tag is an available language tag and path is
                         where the tag.dic/.aff files can be found.
                         The list is developed searching first in path
                         (presumably a book path), then in the dict_path
                         then the extras_path.

make_speller(tag, path)  Make a spellcheck object of class Speller
                         for the language tag using path/tag.dic .aff.

class Speller.check(word, alt_tag=None) Check the spelling of word in the
                         primary or alternate dictionary. Return True for
                         correctly-spelled or when no dictionary is found.

'''
import os
import logging
dictionaries_logger = logging.getLogger(name='dictionaries')
import mainwindow
import hunspell

_DICTS = ''
_PREFERRED_TAG = ''

def initialize(settings):
    global _DICTS, _PREFERRED_TAG
    dictionaries_logger.debug('Dictionaries initializing')
    # TODO get stuff from settings
    _PREFERRED_TAG = 'en_US'
    _DICTS = mainwindow.get_extras_path()

def shutdown(settings):
    global _DICTS, _PREFERRED_TAG
    dictionaries_logger.debug('Dictionaries saving to settings')
    # TODO save stuff
    pass

def set_default_tag(tag):
    global _PREFERRED_TAG
    _PREFERRED_TAG = tag
def get_default_tag():
    return str(_PREFERRED_TAG)
def set_dict_path(path):
    global _DICTS
    _DICTS = path
def get_dict_path():
    global _DICTS
    return str(_DICTS)

# Search one path for all matching pairs of files lang.dic, lang.aff. For
# each, add it to the dict as lang:path, unless it is already known.

def _find_tags(path, tag_dict):
    # Get a list of all files in this path.
    try:
        if 0 == len(path) :
            path = os.getcwd()
        file_names = os.listdir(path)
    except OSError as E:
        dictionaries_logger.error("OS error on path",path)
        file_names = []
    except Exception:
        dictionaries_logger.error("Unexpected error")
        file_names = []
    for one_name in file_names:
        if one_name[-4:] == '.aff' :
            # this is a lang.aff file, look for a matching lang.dic
            lang = one_name[:-4]
            if (lang + '.dic') not in file_names:
                dictionaries_logger.error("Found {0}.aff but not {0}.dic".format(lang))
                continue
            if lang not in tag_dict :
                tag_dict[lang] = path
            else:
                dictionaries_logger.info("Skipping {0} in {1}".format(lang,path))

# Make a dict with all available language tags, giving priority to the
# ones on the path argument, then the dict_path, then extras_path.

def get_tag_list(path):
    tag_dict = {}
    _find_tags(path, tag_dict)
    _find_tags(_DICTS, tag_dict)
    _find_tags(mainwindow.get_extras_path(), tag_dict)
    return tag_dict

# Make a spell-check object given a language tag and a path. The language tag
# names the primary or default dictionary. The path is used to find its
# .dic/.aff files. However a spell-check object can be called with an alt-tag
# in which case it uses get_tag_list to find the files for the alt-tag.
#
# If the Speller cannot make a primary dictionary it fails with only a log
# message. All checks will return True, correct spelling. If it cannot make
# an alt dict, the same: log message and True for any word on that alt dict.
#

class Speller(object):
    def __init__(self, primary_tag, dict_path ):
        self.primary_tag = primary_tag
        self.dict_path = dict_path
        self.primary_dictionary = self._make_a_dict(primary_tag,dict_path)
        self.alt_tag = None
        self.alt_dictionary = None

    # We are assured that tag.dic and tag.aff exist on path.
    def _make_a_dict(self, tag, path):
        try:
            aff_path = os.path.join(path, tag + '.aff')
            dic_path = os.path.join(path, tag + '.dic')
            dic = hunspell.HunSpell(dic_path, aff_path)
        except :
            dictionaries_logger.error("Unexpected error making a dictionary")
            dic = None
        return dic

    def check(self, word, alt_tag = None):
        if alt_tag is None:
            dict_to_use = self.primary_dictionary
        else : # alt_tag given,
            if alt_tag == self.alt_tag : # same alt_tag as last time
                dict_to_use = self.alt_dictionary
            else :
                # first use of this alt_tag, make the dict for it.
                dict_list = get_tag_list(self.dict_path)
                if alt_tag in dict_list :
                    dic = self._make_a_dict(alt_tag, dict_list[alt_tag])
                    self.alt_dictionary = dic
                    self.alt_tag = alt_tag
                    dict_to_use = dic
                else :
                    dictionaries_logger.error("Cannot find dictionary for "+alt_tag)
                    dict_to_use = None
        if dict_to_use : # we have a valid primary or alt dictionary
            try :
                return dict_to_use.spell(word)
            except Exception : # ? error: whatever, misspelled
                dictionaries_logger.error("Unexpected error spelling {0}:{1}".format(alt_tag,encword))
                return False
        else: # No available dictionary, say it is correct
            return True