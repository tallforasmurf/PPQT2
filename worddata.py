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

                          WORDDATA.PY

Defines a class for an object to build and store the census of
word-tokens of a document, with their properties, and also
the good-words, bad-words, and scannos lists, and apply spell-check.

One of these objects is created by each Book object. It:
  * is initialized by the Book while loading or creating metadata.
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

    Load Process

On creation this object registers with the metamanager to read and write the
metadata sections for word-census, char-census, good-words, bad-words, and
scannos.

Good-words, bad-words, and scannos sections are handled by good_read(),
bad_read() and scanno_read() respectively, which save words in separate sets.
(sets not dicts, because these words basically have no properties aside from
being good or bad or scanno-ish.) All these lines are expected to have a
single token each. They are not required to be sorted, as the user can edit
the metadata file. scanno_read() is also called by the Book when the user
selects a new scannos file.

word_read() is registered to read the WORDCENSUS section and initializes the
vocabulary dict. The info on these lines can differ between version-1 and -2
metadata (see word_read() for format notes) and care is taken to allow for
user mistakes.

    Save Process

During a Save, the metamanager calls the methods good_save(), bad_save(),
scanno_save() and word_save() in some order, passing each a text stream to
write into.

    Census Process

When the user requests a "refresh" of the Words panel the refresh() method is
called. This method gets the Document (see editdata.py) from the Book and
from it gets an iterator to fetch the lines of the document.

We zero out the counts on all known tokens. Then we parse each line into
tokens using a regex, adding tokens to the dictionary only as necessary, and
incrementing the counts of all.

After scanning all lines we delete from the dict any token whose count is zero.
That could happen if the token was once in the document, but has since been
edited out.

    Storing Word-tokens

It is not unusual to have 10k-30k unique word tokens, hence performance is an
issue. We use a blist.sorteddict to record the tokens, with the token as key
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
properties that are the set-union of the member tokens. Thus
"Mother-in-law's" will have MC from "Mother", AP from "law's", probably XX
from "law's", and HY for itself. "1985-89" will have ND from its parts and HY
for itself.

    Interrogation Methods

The Words panel calls word_count() to get the count of words for table
sizing. It calls word_at(n) to get the text of the n'th word (by way of a
sorteddict KeysView) and word_props_at(n) to get a list [count, propset] for
the n'th word (by way of a sorteddict ValuesView). Use of the special "views"
methods of the sorteddict supposedly get us O(1) retrieval time.

The Edit syntax highlighter, when misspelled highlights are requested, calls
spelling_test(token_string) and gets back "XX in" that token's properties. If
the token is not in the table, for example the user typed in a new word since
the last refresh, we return False. So newly entered words are not highlighted
as misspellings until after a refresh.

When scanno highlighting is on, the syntax highlighter also calls
scanno_test() to see if a token is in the scanno set. The return is True when
the given token is in the scanno list. Thus when no scannos have been loaded,
none will be found.

'''
import metadata
from blist import sorteddict
import unicodedata # for NFKC
import ast # for literal_eval
import logging
worddata_logger = logging.getLogger(name='worddata')

# ====================================================================
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

# ====================================================================
# Class to implement saving all the census data related to one book.
# speller is a spellcheck object. metamgr is the MetaMgr object for
# the controlling book.

class WordData(object):

    def __init__(self, my_book):
        # Save reference to the spell-check object
        self.speller = my_book.get_speller()
        # Save reference to the metamanager
        self.metamgr = my_book.get_meta_manager()
        # The vocabulary list, as a sorted dict with a default so that new
        # keys have zero count and empty property set
        self.vocab = sorteddict()
        self.vocab.setdefault([0,set()])
        # Key and Values views on the vocab list for indexing by table row.
        self.vocab_kview = self.vocab.KeysView()
        self.vocab_vview = self.vocab.ValuesView()
        # The good- and bad-words sets and the scannos set.
        self.good_words = set()
        self.bad_words = set()
        self.scannos = set()
        # A dict of words that use an alt-dict tag. Word is the key, alt-dict
        # tag the value. Any word that needs an alt dict is entered here as
        # a key with the alt-tag as its value.
        self.alt_tags = blist.sorteddict()
        # The modified flag, set whenever a word is added. Cleared on metadata
        # load and metadata save.
        self.modified = False
        # Register metadata readers and writers.
        self.metamgr.register('GOODWORDS', self.good_read, self.good_save)
        self.metamgr.register('BADWORDS', self.bad_read, self.bad_save)
        self.metamgr.register('SCANNOLIST', self.scanno_read, self.scanno_save)
        self.metamgr.register('WORDCENSUS', self.vocab_read, self.vocab_save)
    # End of __init__

    #
    # Methods used when loading an existing file:
    #
    # 1. Load a good_words metadata section. Called with a stream positioned
    # just after {{GOODWORDS}}. For each reader, the sentinel is the section
    # name that marks the end of the metadata, e.g. "{{/GOODWORDS}}". The
    # metamanager utility read_to() facilitates reading lines to the end.
    #
    # We do not know whether good- and bad-words will be loaded before
    # or after the vocabulary. So we allow for either sequence. If there are
    # multiples of these sections, they are additive.
    #
    def good_read(self, stream, v, sentinel) :
        for line in self.metamgr.read_to(stream, sentinel):
            # note depending on read_to to strip whitespace
            if line in self.bad_words :
                worddata_logger.warn(
                    '"{0}" is in both good and bad words - ignored'.format(line)
                    )
            else :
                self.good_words.add(line)
                if line in self.vocab : # vocab already loaded, it seems
                    props = self.vocab[line][1]
                    props += GW
                    props -= XX
    #
    # 2. Load a bad_words file or metadata segment.
    #
    def bad_read(self, stream, v, sentinel) :
        for line in self.metamgr.read_to(stream, sentinel):
            if line in self.good_words :
                worddata_logger.warn(
                    '"{0}" is in both good and bad words - ignored'.format(line)
                    )
            else :
                self.bad_words.add(line)
                if line in self.vocab :
                    props = self.vocab[line][1]
                    props += BW
                    props += XX
    #
    # 3. Load the scannos segment of a metadata file or, if the user chooses
    # a new scannos list, load the contents of the designated file. In the
    # latter case we want to replace the list, so here we clear the set
    # before reading. Hence if a metadata file has multiple scanno segments,
    # only the last one is effective. Note: we can use metamgr.read_to() with
    # a scannos file because read_to() stops on either a sentinel or end of
    # file.
    #
    def scanno_read(self, stream, v, sentinel) :
        self.scannos = set() # clear any prior values
        for line in self.metamgr.read_to(stream, sentinel):
            self.scannos.add(line)
    #
    # 4. Load the vocabulary segment of a metadata file, allowing for old and
    # new encodings of the properties, and for user-edited malformed
    # vocabulary lines. Be very generous about user errors in a modified meta
    # file, if the user wants to just put in a single word with no count or
    # properties, fine.
    #
    # Before adding a word make sure to unicode-flatten it. (It should be
    # flat in the file, but we didn't do that in V1, and anyway the user can
    # add words to the file.)
    #
    def word_read(self, stream, v, sentinel) :
        line_num = 0
        for line in self.metamgr.read_to(stream, sentinel):
            line_num += 1
            word = None
            count = 0
            prop_set = set()
            alt_tag = None
            parts = line.split()
            try:
                word = parts[0] # throws an exception if line is empty.
                if word.find('/') : # word/alt-tag
                    (word, alt_tag) = word.split('/')
                word = unicodedata.normalize('NFKC',word)
                if 2 > len(parts) : # just the word, so user addition
                    count = 1
                else:
                    count = int(parts[1]) # exception if not an int str
                    count = max(1,count) # convert 0, negative to 1
                if 3 > len(parts) : # just the word (and count?) but no props
                    # have to allow for user-inserted hyphenated phrase
                    prop_set = self._add_token(word, alt_tag)
                    continue
                elif v < '2' :
                    # In V.1 the third item is an integer representing a set of bits
                    # decoded as follows.
                    bits = int(parts[2]) # throws exception if not an int
                    bitcase = 0x03 & bits
                    if 0x03 == bitcase : prop_set.add(MC)
                    if 0x01 == bitcase : prop_set.add(UC)
                    if 0x02 == bitcase : prop_set.add(LC)
                    if 0x04 & bits : prop_set.add(ND)
                    if 0x08 & bits : prop_set.add(HY)
                    if 0x10 & bits : prop_set.add(AP)
                    if 0x80 & bits : prop_set.add(XX)
                else :
                    # in V.2 the third item is e.g "{1,4}" -- the string form
                    # of a set of ints with spaces compressed out so it
                    # splits as one token. Convert back to a set and
                    # cautiously add its members to prop_set. literal_eval
                    # will throw an exception on bad syntax.
                    input_set = ast.literal_eval(parts[2])
                    if type(input_set) == type(prop_set) :
                        for i in input_set :
                            if i in prop_encode :
                                prop_set.add(i)
                    else: # it was a valid literal but not a set
                        raise ValueError('bad property set')
            except Exception as msg :
                worddata_logger.warn('line {0} of word census list invalid'.format(line_num))
                worddata_logger.warn('  "'+line+'"')
                worddata_logger.warn(' -- '+msg)
                word = None
            if word : # line format was ok, count & prop_set ready
                # note we are not checking for duplicates
                if word in self.bad_words : prop_set.add(BW)
                if word in self.good_words : prop_set.add(GW)
                if alt_tag :
                    prop_set.add(AD)
                    self.alt_tags[word] = alt_tag
                self.vocab[word] = [count, prop_set]
        # end of "for line in vocabulary section"
    #
    # Methods used when saving a metadata file. The stream argument is
    # the file to write. The sentinel is written at the start and end.
    #
    # 1, 2, 3. Save the good-words, bad-words and scanno sets.
    #
    def good_save(self, stream, sentinel) :
        stream << metadata.open_string(sentinel)
        for word in self.good_words:
            stream << word + '\n'
        stream << metadata.close_string(sentinel)
    def bad_save(self, stream, sentinel) :
        stream << metadata.open_string(sentinel)
        for word in self.bad_words:
            stream << word + '\n'
        stream << metadata.close_string(sentinel)
    def scanno_save(self, stream, sentinel) :
        stream << metadata.open_string(sentinel)
        for word in self.scannos:
            stream << word + '\n'
        stream << metadata.close_string(sentinel)
    #
    # 4. Save the vocabulary, each as WORD count {set}
    #
    def word_save(self, stream, sentinel) :
        stream << metadata.open_string(sentinel)
        for word in self.vocab:
            [count, prop_set] = self.vocab[word]
            stream << word
            if AD in prop_set:
                stream << '/' + self.alt_tags[word]
            stream << ' ' + str(count) + ' '
            stream << str(prop_set).replace(' ','')
            stream << '\n'
        stream << metadata.close_string(sentinel)
    #
    # The following is called by the document when the user chooses a
    # different spelling dictionary. Store a new spellcheck object. Recheck
    # the spelling of all words except those with properties HY, GW, or BW.
    #
    def recheck_spelling(self, speller):
        pass # TODO complete
    #
    # Methods to perform a census:
    #
    def refresh(self):
        pass # TODO

    # Internal method for adding a possibly-hyphenated token to the vocabulary,
    # incrementing its count. This is used during the census/refresh scan only.
    # Arguments:
    #    tok_str: a normalized word-like token; may be hyphenated a/o apostrophized
    #    dic_tag: an alternate dictionary tag
    #
    # If the token has no hyphens, this is just a cover on _count. When the
    # token is hyphenated, we enter each part of it alone, then add the
    # phrase with the union of the prop_sets of its parts, plus HY. Thus
    # "mother-in-law's" will be added as "mother", "in" and "law's", and as
    # itself with HY, LC, AP, and with XX if "law's" fails the spellchecker.
    # "1989-1995" puts 1989 and 1995 in the list and will have HY and ND.
    #
    # Note: en-dash \u2013 is not supported here, only the ascii hyphen.
    # Support for it could be added if required.
    #
    # Defensive programming: '-'.split('-') --> ['','']; '-9'.split('-') --> ['','9']

    def _add_token(self, tok_str, dic_tag ) :
        # Count the entire token regardless of hyphens
        self._count(tok_str, dic_tag)
        [count, prop_set] = self.vocab[tok_str]
        if (count == 1) and (HY in prop_set) :
            # We just added a hyphenated token: add its parts also.
            parts = tok_str.split('-')
            prop_set = set()
            for member in parts :
                if len(member) : # if not null split from leading -
                    self._count(member, dic_tag)
                    [x, part_props] = self.vocab(member)
                    prop_set += part_props
            self.vocab[tok_str] = [count, prop_set]

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
        [count, prop_set] = self.vocab[word]
        if count : # it was in the list: new words have count == 0
            self.vocab[word][0] += 1 # increment its count
        else:
            # word was not in the list (but is now): count is 0 and prop_set is {}
            self.modified = True
            work = word.copy() # copy the key, we may modify it next.
            # If word has apostrophes, note that and delete for following tests.
            if -1 < work.find("'") : # look for ascii apostrophe
                prop_set.add(AP)
                work.replace("'","")
            if -1 < work.find('\u02bc') : # look for MODIFIER LETTER APOSTROPHE
                prop_set.add(AP)
                work.replace('\u02bc','')
            # If word has hyphens, note that and remove them.
            if -1 < work.find('-') :
                prop_set.add(HY)
                work.replace('-','')
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
                if HY not in prop_set :
                    # word has some alphas and is not hyphenated,
                    # so check its spelling.
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
            # else all numeric - assume good spelling
            self.vocab[word] = [1, prop_set]
    #
    # The following methods are used by the Words panel.
    #
    #  Get the count of words in the vocabulary.
    #
    def word_count(self):
        return len(self.vocab)
    #
    # Get the word at position n in the vocabulary, using the blist
    # KeysView for O(1) lookup time. Guard against invalid indices.
    #
    def word_at(self, n):
        try:
            return self.vocab_kview[n]
        except whatever:
            worddata_logger.error('bad call to word_at({0})'.format(n))
            return ('?')
    #
    # Get the count or property-set of the word at position n in the
    # vocabulary, using the blist ValuesView for O(1) lookup time.
    #
    def word_count_at(self, n):
        try:
            return self.vocab_vview[n][0]
        except whatever:
            worddata_logger.error('bad call to word_count_at({0})'.format(n))
            return (set())
    def word_props_at(self, n):
        try:
            return self.vocab_vview[n][1]
        except whatever:
            worddata_logger.error('bad call to word_props_at({0})'.format(n))
            return (set())

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
        [count, prop_set] = self.vocab[tok_str]
        if count : # it was in the list
            return XX in prop_set
        tok_nlz = unicodedata.normalize('NFKC',tok_str)
        [count, prop_set] = self.vocab[tok_nlz]
        # If normalized token is not in the list, prop_set is {}
        return XX in prop_set
    #
    # 2. Check a token for being in the scannos list. If no scannos
    # have been loaded, none will be hilited.
    #
    def scanno_test(self, tok_str) :
        return tok_str in self.scannos
