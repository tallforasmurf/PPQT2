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

The main window calls initialize() during startup, when we get the user's
preferred default tag from saved settings.

The set_default_tag() functiion is called from the preferences dialog.

initialize(settings)     Get default tag from settings if available.

shutdown(settings)       Save default tag in settings.

set_default_tag(tag)     Note the tag of the preferred dictionary
                         from preferences

get_default_tag()        Return the preferred main dictionary tag.

get_tag_list(path)       Prepare and return a dict{tag:path} where each
                         tag is an available language tag and path is
                         where the tag.dic/tag.aff files can be found.
                         The list is developed searching first in path
                         (presumably a book path), then in the dict path
                         then the extras path.

make_speller(tag, path)  Make a spellcheck object of class Speller
                         for the language tag using path/tag.dic .aff.
                         The tag and path are expected to be valid and
                         accessible, probably from a tag_list above.

class Speller.check(word, alt_tag=None) Check the spelling of word in the
                         primary or alternate dictionary. Return True for
                         correctly-spelled or when no dictionary is found.

'''
import os
import logging
dictionaries_logger = logging.getLogger(name='dictionaries')
import paths
import hunspell

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Static functions to manage the default language tag.

_PREFERRED_TAG = ''

def set_default_tag(tag):
    global _PREFERRED_TAG
    _PREFERRED_TAG = str(tag)
def get_default_tag():
    return str(_PREFERRED_TAG)


# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Static functions called from mainwindow to fetch and store system
# default values in the settings.

def initialize(settings):
    global _PREFERRED_TAG
    set_default_tag(
        settings.value("dictionaries/default_tag","en_US")
        )
    dictionaries_logger.debug( 'Dictionaries initialized, default is {}'.format(_PREFERRED_TAG) )

def shutdown(settings):
    settings.setValue("dictionaries/default_tag",_PREFERRED_TAG)
    dictionaries_logger.debug( 'Default dict {} saved to settings'.format(_PREFERRED_TAG) )

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Internal function to search one folder path for all matching dictionary
# file-pairs lang.dic/lang.aff.
#
# For each pair, if that lang is not in the tag_dict already (from a prior
# call to a higher-priority path), add it to the dict as lang:path.

def _find_tags(path, tag_dict):
    if not paths.check_path(path) :
        return # path does not exist or is not readable

    # Get a list of all files in this path.
    try:
        file_names = os.listdir(path)
    except OSError as E:
        dictionaries_logger.error("OS error listing files in {0}".format(path))
        file_names = []
    except Exception:
        dictionaries_logger.error("Unexpected error listing files in {0}".format(path))
        file_names = []
    # Collect the set of matching pairs lang.dic/lang.aff
    aff_set = set()
    dic_set = set()
    for one_name in file_names:
        if one_name[-4:] == '.aff':
            aff_set.add(one_name[:-4])
        if one_name[-4:] == '.dic':
            dic_set.add(one_name[:-4])
    pair_set = aff_set & dic_set # names with both .dic and .aff
    # Process the paired files by name
    for lang in pair_set:
        if lang not in tag_dict :
            tag_dict[lang] = path
        else:
            dictionaries_logger.debug("Skipping {0} in {1}".format(lang,path))
    # Log any mismatched dic/aff names
    no_dic = aff_set - pair_set # should be empty set
    for lang in no_dic:
        dictionaries_logger.error(
            "Found {0}.aff but not {0}.dic in {1}".format(lang,path) )
    no_aff = dic_set - pair_set # also should be empty set
    for lang in no_aff:
        dictionaries_logger.error(
        "Found {0}.dic but not {0}.aff in {1}".format(lang,path) )


# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Make a (python) dict with all available language tags with their paths.
# Give priority to the ones on the path argument (which may be the null
# string), then the dict_path, then the extras_path.

def get_tag_list(path = ''):
    tag_dict = {}
    _find_tags(path, tag_dict)
    _find_tags(paths.get_dicts_path(), tag_dict)
    _find_tags(paths.get_extras_path(), tag_dict)
    return tag_dict


# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Make a spell-check object given a language tag and a path. The language tag
# names the primary or default dictionary. The path is used to find its
# .dic/.aff files. However a spell-check object can be called with an alt-tag
# in which case it uses get_tag_list to find the files for the alt-tag.
#
# If the Speller cannot make a primary dictionary it writes a log message and
# sets itself "invalid". Its validity can be checked by calling is_valid().
# Normally an object of this type should not be created except with a
# path and tag that were returned by get_tag_list above. However we put
# in checks to make sure.
#
# If it is used when not valid, all spelling checks return True, meaning
# correct spelling (this avoids marking every word in a book misspelled when
# a dictionary is temporarily missing).
#
# If it cannot make an alt dict, the same: log message and True for any word
# in that alt dict.
#

class Speller(object):
    def __init__(self, primary_tag, dict_path ):
        self.primary_tag = primary_tag
        self.dict_path = dict_path
        self.primary_dictionary = self._make_a_dict(primary_tag,dict_path)
        self.alt_tag = None
        self.alt_dictionary = None

    # Defensive programming, path and tag are probably just fine, but...
    def _make_a_dict(self, tag, path):
        aff_path = os.path.join(path, tag + '.aff')
        dic_path = os.path.join(path, tag + '.dic')
        if paths.check_path(aff_path) and paths.check_path(dic_path) :
            try:
                dic = hunspell.HunSpell(dic_path, aff_path)
            except :
                dictionaries_logger.error(
                "Unexpected error opening dictionary {0} on {1}".format(tag,path)
                )
                dic = None
        else:
            dictionaries_logger.error('bad dictionary path to Speller: '+path)
            dic = None
        return dic

    def is_valid(self):
        return self.primary_dictionary is not None

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
            except UnicodeError as UE :
                dictionaries_logger.error("error encoding spelling word {}".format(word))
                return False
            except Exception as Wha :
                dictionaries_logger.error("Unexpected error spelling {}".format(word))
                return False
        else: # No available dictionary, say it is correct
            return True