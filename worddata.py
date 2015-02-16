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

                          WORDDATA.PY

Defines a class for an object to build and store the census of
word-tokens of a document, with their properties, and also
the good-words, bad-words, and scannos lists, and apply spell-check.

One of these objects is created by each Book object. It:
  * is called by the Book while loading metadata for a known book
  * or is initialized by the user clicking Refresh in the Words panel
  * is called by the Book during save, to write metadata.
  * acts as Data Model to the the Word view panel
  * also is data model to the Edit syntax highlighter for scannos and misspelled words
  * is called from the Words panel to add to the good-words list
  * is called to recheck spelling when the default spelling dictionary is changed.

The WordData object is given a reference to its parent Book object when
instantiated. From the Book it can retrieve references to the metadata manager,
a spell check object, and the document.

    Relation to Spell Checker

A reference to the spell checker is obtained from the Book. The only
requirement on the speller is that it supports a method check(word,dict_tag)
returning True when word checks correct against dict_tag or the default dict.
This is called as words are found in the census and added to the database.

If the user chooses a new spelling dictionary the Book calls
recheck_spelling() to reapply check() to all words in the database.

    Save Process

On creation this object registers with the metamanager to read and write the
metadata sections for word-census, good-words, bad-words, and scannos.

During a Save, the metadata manager calls the methods good_save(),
bad_save(), scanno_save() and word_save() in some order. Each returns a
single object that encodes its data items. For good, bad, and scanno words,
that is a list of string tokens. For word_save() it is a more complex list,
see comments near that method.

    Load Process

Good-words, bad-words, and scannos sections are handled by good_read(),
bad_read() and scanno_read() respectively, which save words in separate sets
-- in sets not dicts, because these words basically have no properties aside
from being good or bad or scanno-ish. These three sections are expected to
each be a list of tokens. They are not required to be sorted, as the user can
edit the metadata file. scanno_read() is also called by the Book when the
user selects a new scannos file.

word_read() is registered to read the WORDCENSUS section and initializes the
vocabulary dict from the object saved by word_save(), with validity checks in
case of user editing.

We do not know (nor should care) in which order the metadata readers are
called. However, each of good_, bad_ and word_read can affect the display of
the word table, so after each one we emit a signal, WordsUpdated, which is
received by the wordview module for which we are the model.

    Census Process

When the user requests a "refresh" of the Words panel the refresh() method is
called. This method gets the edit model from the Book and from it gets an
iterator to fetch the lines of the document.

The first time this is done in a new book, the dictionary is empty. But on
all following times, the dictionary already has all or most of the tokens in
the book and the only changes will be due to user editing, possibly removing
or adding a few tokens. So the refresh process is geared to this use-case.

We zero out the counts on all previously-known tokens. We also empty our
dictionary of words that use alt-dict tags, as the user might have added or
removed some lang= properties. Then we parse each line into tokens using a
regex, adding new tokens to the dictionary only as necessary, and
incrementing the counts.

After scanning all lines we scan the dict and any token whose count is now
zero. That could happen if the token was once in the document, but has since
been edited out.

    Storing Word-tokens

It is not unusual to have 10k-30k unique word tokens, hence performance is an
issue. We use a SortedDict to record the tokens, with the token as key
and its value a list of [count, property_set].

The tokens are Python strings. We flatten them by applying NFKC composition
before storing or comparing them.

The properties of a token are coded as a set comprising these values:

    UC   token is all upper-case
    LC   token is all lower-case
    MC   token is mixed-case, having at least one lower and one upper
    ND   token contains one or more unicode numeric characters
    HY   token contains one or more hyphens
    AP   token contains one or more apostrophe (straight or curly)
    BW   token appears also in the bad_words set
    GW   token appears also in the good_words set
    XX   token fails spellcheck
    AD   token is spell-checked against an alternate dictionary

(Properly speaking the above names should be defined as an Enum type, but the
official Enum type doesn't arrive until 3.4, and the pypi enum lib yields not
ints, but enum value objects. So we just do it C-style, defining these as
module globals with int values. See also prop_encode and prop_decode dicts.)

Spelling is checked only when a word is first added to the vocabulary or when
recheck_spelling() is called. Later queries just return "XX in" the token's
property set.

If a word or hyphenated member is in the good-words set it gets GW. If it is
all-numeric it is also assumed correctly spelled. If it is in the bad-words
set it gets BW and XX. Otherwise it is spell-checked and given XX or not. If
it is added with an alternate dictionary tag, it is checked against that
dictionary, else the current default dictionary.

If a token contains hyphens, it is split at the hyphens and the members are
entered individually. Then the complete hyphenated token is entered with
properties that are the set-union of the member tokens, less XX. Thus
"Mother-in-law's" will have MC from "Mother", AP from "law's", and HY for
itself. ("law's" might have XX, but that is not propogated to the parent
phrase.) "1985-89" will have ND from its parts and HY for itself.

    Interrogation Methods

The Words panel calls word_count() to get the count of words for table
sizing. It calls word_at(n) to get the text of the n'th word (by way of a
sorteddict KeysView) and word_props_at(n) to get a list [count, propset] for
the n'th word (by way of a sorteddict ValuesView). Use KeysView and
ValuesView of the sorteddict supposedly get us O(1) retrieval time.

The Edit syntax highlighter, when misspelled highlights are requested, calls
spelling_test(token_string) and gets back "XX in" that token's properties
(that is, False means correctly spelled). If the token is not in the table,
for example the user typed in a new word since the last refresh, we return
False. So newly entered words are not highlighted as misspellings until after
a refresh.

When scanno highlighting is on, the syntax highlighter calls scanno_test() to
see if a token is in the scanno set. The return is True when the given token
is in the scanno list. Thus when no scannos have been loaded, none will be
found.

'''
import constants as C
import metadata
from sortedcontainers import SortedDict
import regex
import unicodedata # for NFKC
import ast # for literal_eval
import logging
worddata_logger = logging.getLogger(name='worddata')
from PyQt5.QtCore import QObject, pyqtSignal

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Global function to strip all types of apostrophe and dash from a word.
# Global static set of all types of unicode apostrophe and dash forms.

APO_DASH_SET = {"'","\u02bc","\u2019","-","\u00ad","\u2010",
                "\u2011","\u2012","\u2013","\u2014","\u2015",
                "\ufe58","\ufe63","\uff0d" }

def clean_word(word):
    return ''.join([c for c in word if not c in APO_DASH_SET])

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Define the properties of a vocabulary token and provide dicts to
# convert between properties and their name-strings.

UC = 1 # token is all upper-case
LC = 2 # token is all lower-case
MC = 3 # token is mixed-case, having at least one lower and one upper
HY = 4 # token contains one or more hyphens
AP = 5 # token contains one or more apostrophe (straight or curly)
ND = 6 # token contains one or more unicode numerics
BW = 7 # token appears also in the bad_words set
GW = 8 # token appears also in the good_words set
XX = 9 # token fails spellcheck
AD = 10 # token is spell-checked against an alternate dictionary

prop_encode = {
    UC:'UC', LC:'LC', MC:'MC', HY:'HY', AP:'AP',
    ND:'ND', BW:'BW', GW:'GW', XX:'XX', AD:'AD'
    }

prop_decode = {
    'UC':UC, 'LC':LC, 'MC':MC, 'HY':HY, 'AP':AP,
    'ND':ND, 'BW':BW, 'GW':GW, 'XX':XX, 'AD':AD
    }
# set of all properties for checking metadata
prop_all = set([UC,LC,MC,HY,AP,ND,BW,GW,XX,AD])
# set to test lack of spell-check-ability
prop_bgh = set([BW,GW,HY])
# set used to clear XX from a set of properties -- set.remove(XX) raises an
# exception if no XX but set & prop_nox ensures it is gone.
prop_nox = set([UC,LC,MC,HY,AP,ND,BW,GW,AD])

# Convert a property set from set values to a feature string
def prop_string(props):
    ps = ['-','-','-','-','-','-']
    if UC in props or MC in props: ps[0] = 'A'
    if LC in props or MC in props: ps[1] = 'a'
    if ND in props: ps[2] = '9'
    if HY in props: ps[3] = 'h'
    if AP in props: ps[4] = 'p'
    if XX in props: ps[5] = 'X'
    return ''.join(ps)

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# A suite of regexes to parse out important tokens from a text line.
#
# First, a word composed of digits and/or letters, where
# the letters may include PGDP ligature notation: [OE]dipus, ma[~n]ana

xp_word = "(\\w*(\\[..\\])?\\w+)+"

# Note that although xp_word recognizes words with multiple ligatures, it
# does not recognize adjacent ligatures (problem?). It does not recognize
# terminal ligatures on the grounds that a word-terminal [..] is likely a
# two-digit footnote anchor.

# Next: the above with embedded hyphens or apostrophes (incl. u2019's):
# She's my mother-in-law's 100-year-old ph[oe]nix by [OE]dipus. This
# will not recognize a singleton ligature preceding or following an apostrophe.
# It also will not recognize several forms of dash (\u2011-\u2015) as hyphens.

xp_hyap = "(" + xp_word + "[\\'\\-\u2019])*" + xp_word

# re_word is used to select word-like tokens only.
re_word = regex.compile(xp_hyap, regex.IGNORECASE)

# Detect an HTML starting tag with possible attributes:
# <div lang=en_GB>, <hr class='major'>, or <br />

xp_start = '''(<(\w+)([^>]*)>)'''

# Detect an HTML end tag, not allowing for any attributes (or spaces)

xp_end = '''(</(\w+)>)'''

# Put it all together: a token is any of those three things:
xp_any = '|'.join([xp_hyap,xp_start,xp_end])

re_token = regex.compile(xp_any, regex.IGNORECASE)

# When re_token.search returns a match object its groups are:
#   a word-like token,
#       0 is the token string
#       6 and 9 are None
#   an HTML start tag,
#       6 is the tag, e.g. "div" or "i"
#   an HTML end tag,
#       9 is the tag, e.g. "div" or "i"
#
# Note I am fully aware of stackoverflow.com/questions/1732348, the
# great rant on not using REs to parse HTML. We are not parsing HTML.
# We are selecting and recognizing isolated HTML productions which
# *are* regular and hence, parseable by regular expressions.
#
# For a start tag (group(6) is not None), group(7) is its attribute string,
# e.g. "class='x' lang='en_GB'"
#
# According to W3C (www.w3.org/TR/html401/struct/dirlang.html) you can put
# lang= into any tag, esp. span, para, div, td, and so forth. We scan an
# attribute string for lang='value' allowing for single, double, or no quotes
# on the value.

xp_lang = '''lang=[\\'\\"]*([\\w\\-]+)[\\'\\"]*'''
re_lang_attr = regex.compile(xp_lang, regex.IGNORECASE)

# The value string matched by re_lang_attr.group(0) is a language designation
# but we require it to be a dictionary tag such as 'en_US' or 'fr_FR'. It is
# not clear from the W3C docs whether all (or any) of our dic tags really
# qualify as language designations. Nevertheless, during the refresh() we
# save the dict tag as an alternate dictionary for all words until the
# matching close tag is seen.

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Class to implement saving all the census data related to one book. Created
# by a Book object, which passes itself as my_book so that this object can
# call back to the Book to get the meta manager, the current spellcheck
# object, and the edit data model.

class WordData(QObject):
    # Define the signal we emit when we have loaded new data
    WordsUpdated = pyqtSignal()

    def __init__(self, my_book):
        super().__init__(None)
        # Save reference to the book
        self.my_book = my_book
        # Save reference to the metamanager
        self.metamgr = my_book.get_meta_manager()
        # Save reference to the edited document
        self.document = my_book.get_edit_model()
        # Save reference to a speller, which will be the default
        # at this point.
        self.speller = my_book.get_speller()
        # The vocabulary list as a sorted dict.
        self.vocab = SortedDict()
        # Key and Values views on the vocab list for indexing by table row.
        self.vocab_kview = self.vocab.keys()
        self.vocab_vview = self.vocab.values()
        # The good- and bad-words sets and the scannos set.
        self.good_words = set()
        self.bad_words = set()
        self.scannos = set()
        # A dict of words that use an alt-dict tag. The key is a word and the
        # value is the alt-dict tag string.
        self.alt_tags = SortedDict()
        # Register metadata readers and writers.
        self.metamgr.register(C.MD_GW, self.good_read, self.good_save)
        self.metamgr.register(C.MD_BW, self.bad_read, self.bad_save)
        self.metamgr.register(C.MD_SC, self.scanno_read, self.scanno_save)
        self.metamgr.register(C.MD_VL, self.word_read, self.word_save)
    # End of __init__


    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # Methods used when saving metadata. The items in the good_words,
    # bad_words, and scanno sets are simply returned as a list of strings.
    #
    def good_save(self, section) :
        return [ token for token in self.good_words ]

    def bad_save(self, section) :
        return [ token for token in self.bad_words ]

    def scanno_save(self, section) :
        return [ token for token in self.scannos ]
    #
    # To save the vocabulary, write a list for each word:
    #   [ "token", "tag", count, [prop-code...] ]
    # where "token" is the word as a string, "tag" is its alt-dict tag
    # or a null string, count is an integer and [prop-code...] is the
    # integer values from the word's property set as a list. Note that
    # alt_tag needs to be a string because json doesn't handle None.
    #
    def word_save(self, section) :
        vlist = []
        for word in self.vocab:
            [count, prop_set] = self.vocab[word]
            tag = "" if AD not in prop_set else self.alt_tags[word]
            plist = list(prop_set)
            vlist.append( [ word, count, tag, plist ] )
        return vlist

    #
    # Methods used to load metadata. Called by the metadata manager with
    # a single Python object, presumably the object that was prepared by
    # the matching _save method above. Because the user might edit the metadata
    # file, do a little quality control.
    #

    def good_read(self, section, value, version):
        if isinstance(value, list) :
            for token in value :
                if isinstance(token, str) :
                    if token in self.bad_words :
                        worddata_logger.warn(
                            '"{}" is in both good and bad words - use in good ignored'.format(token)
                            )
                    else :
                        self.good_words.add(token)
                        if token in self.vocab : # vocab already loaded, it seems
                            props = self.vocab[token][1]
                            props.add(GW)
                            props &= prop_nox
                else :
                    worddata_logger.error(
                        '{} in GOODWORDS list ignored'.format(token)
                        )
            if len(self.good_words) :
                # We loaded some, the display might need to change
                self.WordsUpdated.emit()
        else :
            worddata_logger.error(
                'GOODWORDS metadata is not a list of strings, ignoring it'
                )

    def bad_read(self, section, value, version):
        if isinstance(value, list) :
            for token in value :
                if isinstance(token, str) :
                    if token in self.good_words :
                        worddata_logger.warn(
                            '"{}" is in both good and bad words - use in bad ignored'.format(token)
                            )
                    else :
                        self.bad_words.add(token)
                        if token in self.vocab : # vocab already loaded, it seems
                            props = self.vocab[token][1]
                            props.add(BW)
                            props.add(XX)
                else :
                    worddata_logger.error(
                        '{} in BADWORDS list ignored'.format(token)
                        )
            if len(self.bad_words) :
                # We loaded some, the display might need to change
                self.WordsUpdated.emit()
        else :
            worddata_logger.error(
                'BADWORDS metadata is not a list of strings, ignoring it'
                )

    def scanno_read(self, section, value, version):
        if isinstance(value, list) :
            for token in value :
                if isinstance(token, str) :
                    self.scannos.add(token)
                else :
                    worddata_logger.error(
                        '{} in SCANNOLIST ignored'.format(token)
                        )
        else :
            worddata_logger.error(
                'SCANNOLIST metadata is not a list of strings, ignoring it'
                )

    # Load the vocabulary section of a metadata file, allowing for
    # user-edited malformed items. Be very generous about user errors in a
    # modified meta file. The expected value for each word is as written by
    # word_save() above, ["token", count, tag, [props]] but allow a single
    # item ["token"] or just "token" so the user can put in a single word
    # with no count or properties. Convert null-string alt-tag to None.
    #
    # Before adding a word make sure to unicode-flatten it.
    #
    def word_read(self, section, value, version) :
        global prop_all, prop_nox
        # get a new speller in case the Book read a different dict already
        self.speller = self.my_book.get_speller()
        # if value isn't a list, bail out now
        if not isinstance(value,list):
            worddata_logger.error(
                'WORDCENSUS metadata is not a list, ignoring it'
                )
            return
        # inspect each item of the list.
        for wlist in value:
            try :
                if isinstance(wlist,str) :
                    # expand "token" to ["token"]
                    wlist = [wlist]
                if not isinstance(wlist, list) : raise ValueError
                if len(wlist) != 4 :
                    if len(wlist) > 4 :raise ValueError
                    if len(wlist) == 1 : wlist.append(0) # add default count of 0
                    if len(wlist) == 2 : wlist.append('') # add default alt-tag
                    if len(wlist) == 3 : wlist.append([]) # add default props
                word = wlist[0]
                if not isinstance(word,str) : raise ValueError
                word = unicodedata.normalize('NFKC',word)
                count = int(wlist[1]) # exception if not numeric
                alt_tag = wlist[2]
                if not isinstance(alt_tag,str) : raise ValueError
                if alt_tag == '' : alt_tag = None
                prop_set = set(wlist[3]) # exception if not iterable
                if len( prop_set - prop_all ) : raise ValueError #bogus props
            except :
                worddata_logger.error(
                    'WORDCENSUS item {} is invalid, ignoring it'.format(wlist)
                    )
                continue
            # checking done, store the word.
            if (0 == len(prop_set)) or (0 == count) :
                # word with no properties or count is a user addition, enter
                # it as if we found it in the file, including deducing the
                # properties, spell-check, hyphenation split.
                self._add_token(word, alt_tag)
                continue # that's that, on to next line
            # Assume we have a word saved by word_save(), but possibly the
            # good_words and bad_words have been edited and read-in first.
            # Note we are not checking for duplicates
            if word in self.bad_words :
                prop_set.add(BW)
                prop_set.add(XX)
            if word in self.good_words :
                prop_set.add(GW)
                prop_set &= prop_nox
            if alt_tag :
                prop_set.add(AD)
                self.alt_tags[word] = alt_tag
            self.vocab[word] = [count, prop_set]
        # end of "for wlist in value"
        # Tell wordview that the display might need to change
        self.WordsUpdated.emit()
    # end of word_read()

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # Methods used when opening a new file, one with no metadata.
    #
    # The Book will call these methods passing a text stream when it finds a
    # good-words file or bad-words file. Each of these is expected to have
    # one token per line. We don't presume to know in what order the files
    # are presented, but we DO assume that the vocabulary census has not yet
    # been taken. That requires the user clicking Refresh and that cannot
    # have happened while first opening the file.

    def good_file(self, stream) :
        while not stream.atEnd() :
            token = stream.readLine().strip()
            if token in self.bad_words :
                worddata_logger.warn(
                    '"{}" is in both good and bad words - use in good ignored'.format(token)
                    )
            else :
                self.good_words.add(token)

    def bad_file(self, stream) :
        while not stream.atEnd() :
            token = stream.readLine().strip()
            if token in self.good_words :
                worddata_logger.warn(
                    '"{}" is in both good and bad words - use in bad ignored'.format(token)
                    )
            else :
                self.bad_words.add(token)
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    #
    # The user can choose a new scannos file any time while editing. So there
    # might be existing data, so we clear the set before reading.
    #
    def scanno_file(self, stream) :
        self.scannos = set() # clear any prior values
        while not stream.atEnd() :
            token = stream.readLine().strip()
            self.scannos.add(token)

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # The following is called by the Book when the user chooses a different
    # spelling dictionary. Store a new spellcheck object. Recheck the
    # spelling of all words except those with properties HY, GW, or BW.
    #
    # NOTE IF THIS IS A PERFORMANCE BURDEN, KILL IT AND REQUIRE REFRESH
    #
    def recheck_spelling(self, speller):
        global prop_bgh, prop_nox
        self.speller = speller
        for i in range(len(self.vocab)) :
            (c, p) = self.vocab_vview[i]
            if not( prop_bgh & p ) : # then p lacks BW, GW and HY
                p = p & prop_nox # and now it also lacks XX
                w = self.vocab_kview[i]
                t = self.alt_tags.get(w,None)
                if not self.speller.check(w,t):
                    p.add(XX)
                self.vocab_vview[i][1] = p

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # Method to perform a census. This is called from wordview when the
    # user clicks the Refresh button asking for a new scan over all words in
    # the book. Formerly this took a progress bar, but the actual operation
    # is so fast no progress need be shown.
    #
    def refresh(self):
        global re_lang_attr, re_token

        count = 0
        end_count = self.document.blockCount()

        # get a reference to the dictionary to use
        self.speller = self.my_book.get_speller()
        # clear the alt-dict list.
        self.alt_tags = SortedDict()
        # Zero out all counts and property sets that we have so far. We will
        # develop new properties when each word is first seen. Properties
        # such as HY will not have changed, but both AD and XX might have
        # changed while the word text remains the same.
        for j in range(len(self.vocab)) :
            self.vocab_vview[j][0] = 0
            self.vocab_vview[j][1] = set()

        # iterate over all lines extracting tokens and processing them.
        alt_dict = None
        alt_tag = None
        for line in self.document.all_lines():
            count += 1
            j = 0
            m = re_token.search(line,0)
            while m : # while match is not None
                if m.group(6) : # start-tag; has it lang= ?
                    d = re_lang_attr.search(m.group(8))
                    if d :
                        alt_dict = d.group(1)
                        alt_tag = m.group(7)
                elif m.group(9) :
                    if m.group(10) == alt_tag :
                        # end tag of a lang= start tag
                        alt_dict = None
                        alt_tag = None
                else :
                    self._add_token(m.group(0),alt_dict)
                j = m.end()
                m = re_token.search(line,j)
        # look for zero counts and delete those items. In order not to
        # confuse the value and keys views, make a list of the actual word
        # tokens to be deleted, then use del.
        togo = []
        for j in range(len(self.vocab)) :
            if self.vocab_vview[j][0] == 0 :
                togo.append(self.vocab_kview[j])
        for key in togo:
            del self.vocab[key]

    # Internal method for adding a possibly-hyphenated token to the vocabulary,
    # incrementing its count. This is used during the census/refresh scan, and
    # can be called from word_read to process a user-added word.
    # Arguments:
    #    tok_str: a normalized word-like token; may be hyphenated a/o apostrophized
    #    dic_tag: an alternate dictionary tag or None
    #
    # If the token has no hyphens, this is just a cover on _count. When the
    # token is hyphenated, we enter each part of it alone, then add the
    # phrase with the union of the prop_sets of its parts, plus HY. Thus
    # "mother-in-law's" will be added as "mother", "in" and "law's", and as
    # itself with HY, LC, AP. If a part of a phrase fails spellcheck, it
    # will have XX but we do not propogate that to the phrase itself.
    # "1989-1995" puts 1989 and 1995 in the list and will have HY and ND.
    # Yes, this means that a hyphenation could have all of UC, MC and LC.
    #
    # Note: en-dash \u2013 is not supported here, only the ascii hyphen.
    # Support for it could be added if required.
    #
    # Defensive programming: '-'.split('-') --> ['','']; '-9'.split('-') --> ['','9']

    def _add_token(self, tok_str, dic_tag ) :
        global prop_nox
        # Count the entire token regardless of hyphens
        self._count(tok_str, dic_tag) # this definitely puts it in the dict
        [count, prop_set] = self.vocab[tok_str]
        if (count == 1) and (HY in prop_set) :
            # We just added a hyphenated token: add its parts also.
            parts = tok_str.split('-')
            prop_set = {HY}
            for member in parts :
                if len(member) : # if not null split from leading -
                    self._count(member, dic_tag)
                    [x, part_props] = self.vocab[member]
                    prop_set |= part_props
            self.vocab[tok_str] = [count, prop_set & prop_nox]

    # Internal method to count a token, adding it to the list if necessary.
    # An /alt-tag must already be removed. The word must be already
    # normalized. Because of the way we tokenize, we know the token contains
    # only letter forms, numeric forms, and possibly hyphens and/or
    # apostrophes.
    #
    # If it is in the list, increment its count. Otherwise, compute its
    # properties, including spellcheck for non-hyphenated tokens, and
    # add it to the vocabulary with a count of 1. Returns nothing.

    def _count(self, word, dic_tag ) :
        [count, prop_set] = self.vocab.get( word, [0,set()] )
        if count : # it was in the list: a new word would have count=0
            self.vocab[word][0] += 1 # increment its count
            return # and done.
        # Word was not in the list (but is now): count is 0, prop_set is empty.
        # The following is only done once per unique word.
        self.my_book.metadata_modified(True, C.MD_MOD_FLAG)
        work = word[:] # copy the word, we may modify it next.
        # If word has apostrophes, note that and delete for following tests.
        if -1 < work.find("'") : # look for ascii apostrophe
            prop_set.add(AP)
            work = work.replace("'","")
        if -1 < work.find('\u02bc') : # look for MODIFIER LETTER APOSTROPHE
            prop_set.add(AP)
            work = work.replace('\u02bc','')
        # If word has hyphens, note that and remove them.
        if -1 < work.find('-') :
            prop_set.add(HY)
            work = work.replace('-','')
        # With the hyphens and apostrophes out, check letter case
        if not work.isalpha() :
            # word has at least some numerics
            prop_set.add(ND)
        if not work.isnumeric() :
            # word is not all-numeric, determine case of letters
            if work.lower() == work :
                prop_set.add(LC) # most common case
            elif work.upper() != work :
                prop_set.add(MC) # next most common case
            else : # work.upper() == work
                prop_set.add(UC)
        if HY not in prop_set : # word is not hyphenated, so check its spelling.
            if word not in self.good_words :
                if word not in self.bad_words :
                    # Word in neither good- nor bad-words
                    if dic_tag : # uses an alt dictionary
                        self.alt_tags[word] = dic_tag
                        prop_set.add(AD)
                    if not self.speller.check(word, dic_tag) :
                        prop_set.add(XX)
                else : # in bad-words
                    prop_set.add(XX)
            # else in good-words
        # else hyphenated, spellcheck only its parts
        self.vocab[word] = [1, prop_set]

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    #
    # The following methods are used by the Words panel.
    #
    #  Get the count of words in the vocabulary.
    #
    def word_count(self):
        return len(self.vocab)
    #
    # Get the word at position n in the vocabulary, using the SortedDict
    # KeysView for O(1) lookup time. Guard against invalid indices.
    #
    def word_at(self, n):
        try:
            return self.vocab_kview[n]
        except Exception as whatever:
            worddata_logger.error('bad call to word_at({0})'.format(n))
            return ('?')
    #
    # Get the count and/or property-set of the word at position n in the
    # vocabulary, using the SortedDict ValuesView for O(1) lookup time.
    #
    def word_info_at(self, n):
        try:
            return self.vocab_vview[n]
        except Exception as whatever:
            worddata_logger.error('bad call to word_count_at({0})'.format(n))
            return [0, set()]
    def word_count_at(self, n):
        try:
            return self.vocab_vview[n][0]
        except Exception as whatever:
            worddata_logger.error('bad call to word_count_at({0})'.format(n))
            return 0
    def word_props_at(self, n):
        try:
            return self.vocab_vview[n][1]
        except Exception as whatever:
            worddata_logger.error('bad call to word_props_at({0})'.format(n))
            return (set())

    # Return a reference to the good-words set
    def get_good_set(self):
        return self.good_words

    # Note the addition of a word to the good-words set. The word probably
    # (but does not have to) exist in the database; add GW and remove XX from
    # its properties.
    def add_to_good_set(self, word):
        self.good_words.add(word)
        if word in self.vocab_kview :
            [count, pset] = self.vocab[word]
            pset.add(GW)
            pset -= set([XX]) # conditional .remove()
            self.vocab[word] = [count,pset]

    # Note the removal of a word from the good-words set. The word exists in
    # the good-words set, because the wordview panel good-words list only
    # calls this for words it is displaying. The word may or may not exist in
    # the database. If it does, remove GW and set XX based on a spellcheck
    # test.
    def del_from_good_set(self, word):
        self.good_words.remove(word)
        if word in self.vocab_kview :
            [count, pset] = self.vocab[word]
            pset -= set([GW,XX])
            dic_tag = self.alt_tags.get(word)
            if not self.speller.check(word, dic_tag) :
                pset.add(XX)
            self.vocab[word] = [count, pset]

    # mostly used by unit test, get the index of a word by its key
    def word_index(self, w):
        try:
            return self.vocab_kview.index(w)
        except Exception as whatever:
            worddata_logger.error('bad call to word_index({0})'.format(w))
            return -1

    # The following methods are used by the edit syntax highlighter to set flags.
    #
    # 1. Check a token for spelling. We expect the vast majority of words
    # will be in the list. And for performance, we want to respond in as little
    # code as possible! So if we know the word, reply at once.
    #
    # If the word in the document is not normalized it might seem not to be.
    # Try again, normalized.
    #
    # If the token is not in the list, return False, meaning it is not
    # misspelled. This because otherwise, if the user turns on spellcheck
    # hilites in a new book before a census is done, adding all the words
    # would lock the program up for a long time. We will document that you
    # have to do a Refresh from the Words panel before spellcheck hilites
    # work.
    #
    def spelling_test(self, tok_str) :
        count, prop_set = self.vocab.get(tok_str,[0,set()])
        if count : # it was in the list
            return XX in prop_set
        tok_nlz = unicodedata.normalize('NFKC',tok_str)
        [count, prop_set] = self.vocab.get(tok_nlz,[0,set()])
        return XX in prop_set
    #
    # 2. Check a token for being in the scannos list. If no scannos
    # have been loaded, none will be hilited.
    #
    def scanno_test(self, tok_str) :
        return tok_str in self.scannos
