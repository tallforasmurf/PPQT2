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
word-tokens and characters of a document, with their properties, and also
the good-words, bad-words, and scannos lists, and implement spell-check.

One of these objects is created by each Book object. It is:
  * initialized by the Book while loading or creating metadata.
  * called by the Book during save, to write metadata.
  * acts as Data Model to the Chars and Words view panels
  * interrogated by the Edit syntax highlighter checking scannos and misspelled words
  * called from the Word panel to add to the good-words list
  * called to recheck spelling when the default spelling dictionary is changed.

    Relation to Spell Checker

The WordData object is given a reference to a spellcheck object when
instantiated. The only requirement on the speller is that it supports a
check(word,dict_tag) method returning True when word checks correct against
dict_tag or the default dict. If the user chooses a new spelling dictionary,
recheck_spelling is passed a new speller object.

    Load Process

On creation this object registers with the metamanager to read and write the
scanno sections for word-census, char-census, good-words, bad-words, and
scannos Good-words, bad-words, and scannos sections are handled by
good_read(), bad_read() and scanno_read() respectively, and saved in separate
sets. (Sets, because these words basically have no properties aside from
being good or bad or scanno-ish.)

When loading an existing book, the metadata section for vocabulary is passed
to vocab_read() which uses it to initialize the vocabulary dict. The info on
these lines can differ between version-1 and -2 metadata or if a word has
been edited into the metadata by the user.

When loading a new book (no .meta file) the Book initializes the vocabulary
by way of a census:

    Census Process

The Book performs a census when it first loads a new file or when the user
clicks the "Refresh" button on the Char or Word panel. It commences a census
by calling census_start(), where we zero out the counts on all known tokens
and characters. It then iterates over the document passing whole text lines
(no page separators) to census_line(). Here we parse each line into tokens
using a regex, adding tokens and characters to the sorteddicts only as
necessary, and updating the counts. At end, the Book calls census_end(),
where we delete from the lists any token or character whose count is zero.
That would happen if the token was once in the document, but has been
edited out.

    Storing Characters

Characters are stored in a sorteddict. Their only property is their
count of occurences, tallied during the census of each line.

    Save Process

During a Save, the metamanager calls the methods good_save(), bad_save(),
scanno_save(), vocab_save() and char_save() in some order, passing each a
text stream to write.

    Storing Word-tokens

It is not unusual to have 10k-20k unique word tokens, hence performance is an
issue. We use a blist.sorteddict to record the tokens, with the token as key
and its value a list of [count, property_set].

The tokens are Python unicode strings. We flatten them by applying NFKC
composition before storing or comparing them.

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

(Properly speaking the above should be defined as an Enum type, but the
official Enum type doesn't arrive until 3.4, and the pypi enum lib yields not
ints, but enum value objects. So we just do it C-style, defining these as
module globals with int values. See also prop_encode and prop_decode dicts.)

Spelling is checked only when a word is first added to the vocabulary or when
recheck_spelling() is called on change of spelling dictionary. Later queries just
return "XX not in" the token's property set.

If a word or hyphenated member is in the good-words set it gets GW. If it
is all-numeric it is assumed correctly spelled. If it is in the bad-words set
it gets BW and XX. Otherwise it is spell-checked and given XX or not. If it
is added with an alternate dictionary tag, it is checked against that
dictionary, else the current default dictionary.

If a token contains hyphens, it is split at the hyphens and the members are
entered individually. Then the complete hyphenated token is entered with
properties that are the set-union of the member tokens. Thus
"Mother-in-law's" will have HY, MC from "Mother", AP from "law's" and
probably XX from "law's". "1985-89" will have HY and ND.

    Interrogation Methods

The Word panel calls word_count() to get the count of words (for table
sizing). It calls word_at(n) to get a tuple of (word, [count, propset])
for the nth word in the list.

The Chars panel calls char_count() for the count and char_at(n) for a tuple of
(uchar, count) for the nth char.

The Edit syntax highlighter, when misspelled highlights are requested, calls
spelling_test(tokstr) and gets back "XX not in" that token's properties.
Because the user is editing all the time, it is possible the tested token is
new to the list; if so it is processed and entered at this time. The vast
majority of the time, word_test() finds the word in the table and returns an
answer in O(log2(N)) time.

When scanno highlighting is on, the syntax highlighter also calls scanno_test()
to see if a token is in the scanno set.

'''
import metadata
from blist import sorteddict
from collections import defaultdict
import unicodedata

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

class WordData(object):

    def __init__(self, speller, metamgr ):
        # Save reference to the spell-check object
        self.speller = speller
        # Save reference to the metamanager
        self.metamgr = metamgr
        # The vocabulary list, as a sorted dict with a default so that new
        # keys have zero count and empty prop-set
        self.vocab = sorteddict()
        self.vocab.setdefault([0,set()])
        # A view on the vocab list for indexing from word_at()
        self.vocab_view = self.vocab.viewitems()
        # The character list. New items go in with a value (count) of 0.
        self.chars = sorteddict()
        self.char.setdefault(0)
        # A view on the chars dict for indexed access in char_at()
        self.chars_view = self.chars.viewitems()
        # The good- and bad-words sets and the scannos set.
        self.good_words = set()
        self.bad_words = set()
        self.scannos = set()
        # A dict of words that use an alt-dict tag. Word is the key, alt-dict
        # tag the value.
        self.alt_tags = blist.sorteddict()
        # The modified flag, set whenever a word is added. Cleared on save.
        self.modified = False
        # Register metadata readers and writers.
        self.metamgr.register('CHARCENSUS', self.char_read, self.char_save)
        self.metamgr.register('WORDCENSUS', self.vocab_read, self.vocab_save)
        self.metamgr.register('GOODWORDS', self.good_read, self.good_save)
        self.metamgr.register('BADWORDS', self.bad_read, self.bad_save)
        self.metamgr.register('SCANNOLIST', self.scanno_read, self.scanno_save)
    # End of __init__

    #
    # Methods used when loading a new or existing file:
    #
    # 1. Load a good_words metadata section. Called with a stream positioned
    # just after {{GOODWORDS}}. For each reader, the sentinel is the section
    # name that marks the end of the metadata, e.g. "{{/GOODWORDS}}". The
    # metamanager utility read_to facilitates reading lines to the end.
    #
    # We do not know whether good- and bad-words will be loaded first or after.
    # So we allow for either sequence.
    #
    def good_read(self, stream, v, sentinel) :
        for line in self.metamgr.read_to(stream, sentinel):
            self.good_words.add(line)
            if line in self.vocab :
                self.vocab[line][1].add(GW)
    #
    # 2. Load a bad_words file or metadata segment.
    #
    def bad_read(self, stream, v, sentinel) :
        for line in self.metamgr.read_to(stream, sentinel):
            self.bad_words.add(line)
            if line in self.vocab :
                self.vocab[line][1].add(BW)
                self.vocab[line][1].add(XX)
    #
    # 3. Load the vocabulary segment of a metadata file. If this is an old
    # file, the properies are encoded as a bit-set. If new, as a list of names.
    #
    def word_read(self, stream, v, sentinel) :
        for line in self.metamgr.read_to(stream, sentinel):
            prop_set = set()
            if v < '2' :
                word, count, bits = line.split(' ')
                bitcase = 0x03 & bits
                if 0x03 == bitcase : prop_set.add(MC)
                if 0x01 == bitcase : prop_set.add(UC)
                if 0x02 == bitcase : prop_set.add(LC)
                if 0x04 & bits : prop_set.add(ND)
                if 0x08 & bits : prop_set.add(HY)
                if 0x10 & bits : prop_set.add(AP)
                if 0x80 & bits : prop_set.add(XX)
                if word in self.bad_words : prop_set.add(BW)
                if word in self.good_words : prop_set.add(GW)
            else :
                pass # TODO FINISH
    #
    # 4. Load the scannos segment of a metadata file. This might be called
    # after the file is loaded, if the user chooses a new scannos list, so
    # clear the set before reading.
    #
    def scanno_read(self, stream, v, sentinel) :
        self.scannos = set()
        pass  # TODO FINISH
    #
    # 5. Load a character census from a metadata file.
    #
    def char_read(self, stream, v, sentinel) :
        pass # TODO FINISH
    #
    # Methods used when saving a metadata file. The stream argument is
    # the file to write. The sentinel is written at the start '{{'+sentinel
    # and at the end as sentinel+'}}'. Yes, this could be one method with
    # a list-selecting parameter. But so what.
    #
    # 1. Save the vocabulary
    #
    def word_save(self, stream, sentinel) :
        pass # TODO FINISH
    #
    # 2. Save the character table with counts
    #
    def char_save(self, stream, sentinel) :
        pass # TODO FINISH
    #
    # 3, 4, 5. Save the good-words, bad-words and scanno sets.
    #
    def good_save(self, stream, sentinel) :
        pass # TODO FINISH
    def bad_save(self, stream, sentinel) :
        pass # TODO FINISH
    def scanno_save(self, stream, sentinel) :
        pass # TODO FINISH
    #
    # Methods to perform a census:
    #
    # 1. census_start() clears the counts of words and characters.
    # Also clear any hanging alt-dict tag.
    #
    def census_start(self) :
        pass # TODO FINISH
    #
    # 2. census_end() finishes a census by clearing any 0-count tokens.
    #
    def census_end(self) :
        pass # TODO FINISH
    #
    # 3. census_line() processes one line of text into tokens, parses any
    # HTML sufficiently to note lang= attributes for alternate spell dicts,
    # and stores the non-HTML tokens in the vocabulary list. It also counts
    # the characters of the line.
    def census_line(self, line) :
        pass # TODO FINISH

    # Internal method for adding a possibly-hyphenated token to the vocabulary,
    # incrementing its count. This is used during the census/refresh scan only.
    # Arguments:
    #    tok_str: a normalized word-like token; may be hyphenated a/o apostrophized
    #    dic_tag: an alternate dictionary tag
    #
    # If the token has no hyphens, this is just a cover on _count. When the
    # token is hyphenated, we enter each part of it alone, then add the
    # phrase with the union of the prop_sets of its parts, plus HY. Thus
    # "mother-in-law's" will census "mother", "in" and "law's", and as a
    # phrase will have HY, LC, AP and probably ~XX (provided "law's" gets by
    # the spellchecker). "1989-1995" puts 1989 and 1995 in the list and will
    # have HY and ND.
    #
    # Note: en-dash \u2013 is not supported here, only the ascii hyphen.
    # Support for it could be added if required.
    #
    # Defensive programming: '-'.split('-') --> ['','']; '-9'.split('-') --> ['','9']

    def _add_token(self, tok_str, dic_tag = None ) : #TODO: does dic_tag need default?
        if '-' in tok_str :
            parts = tok_str.split('-')
            prop_set = {}
            for member in parts :
                if len(member) :
                    prop_set += self._count(member, dic_tag)
            prop_set.add(Vocab.HY)
            [count, old_props] = self.vocab[tok_str]
            self.vocab[tok_str] = [count+1, prop_set]
        else :
            self._count(tok_str, dic_tag)

    # Internal method to count a token, adding it to the list if necessary.
    # The word must be already normalized. Because of the way we tokenize, we
    # know the token contains only letter forms, numeric forms, and possibly
    # hyphens and/or apostrophes.
    #
    # If it is in the list, increment its count. Otherwise, compute its
    # properties, including spellcheck, and add it to the list with a count
    # of 1. Return the property set of the word.

    def _count(self, word, dic_tag = None ) :
        [count, prop_set] = self.vocab[word]
        if count : # it was in the list:  new words have count == 0
            self.vocab[word][0] += 1 # increment its count
            return prop_set
        # word was not in the list (but is now): count is 0 and prop_set is {}
        self.modified = True
        work = word.copy() # copy the key, we may modify it next.
        # If word has apostrophes, note that and delete for following tests.
        if -1 < work.find("'") :
            prop_set.add(Vocab.AP)
            work.replace("'","")
        if -1 < work.find('\u02bc') :
            prop_set.add(Vocab.AP)
            work.replace('\u02bc','')
        # If word has hyphens, note and remove them.
        if -1 < work.find('-') :
            prop_set.add(Vocab.HY)
            work.replace('-','')
        # With the hyphens and apostrophes out, check letter case
        if not work.isalpha() :
            # word has at least some numerics
            prop_set.add(Vocab.ND)
        if not work.isnumeric() :
            # word is not all-numeric, but case not determined yet
            if work.lower() == work :
                prop_set.add(Vocab.LC) # most common case
            elif work.upper() != work :
                prop_set.add(Vocab.MC) # next most common case
            else : # work.upper() == work
                prop_set.add(Vocab.UC)
            # Now determine spelling failure
            if word not in self.good_words :
                if word not in self.bad_words :
                    # Word in neither good- nor bad-words
                    if dic_tag : # uses an alt dictionary
                        self.alt_tags[word] = dic_tag
                        prop_set.add(Vocab.AD)
                    if not self.speller(word, dic_tag) :
                        prop_set.add(Vocab.XX)
                else : # in bad-words
                    prop_set.add(Vocab.XX)
            # else in good-words
        # else all numeric - assume good spelling
        self.vocab[word] = [1, prop_set]
        return prop_set

    #
    # The following is called by the document when the user chooses a
    # different spelling dictionary. Store a new spellcheck object. Recheck
    # the spelling of all words except those with properties HY, GW, or BW.
    #
    def recheck_spelling(self, speller):
        pass # TODO complete
    #
    # The following methods are used by the Words panel.
    #
    #  Get the count of words in the vocabulary.
    #
    def word_count(self):
        return len(self.vocab)
    #
    #  Get the nth word in the vocabulary. Guard against invalid indices.
    #
    def word_at(self, n):
        try:
            return self.vocab_view[n]
        except whatever:
            return ('?', [0,{}])
    #
    # The following methods are used by the Chars panel.
    #
    #  Get the count of chars in the census.
    #
    def char_count(self):
        return len(self.chars)
    #
    #  Get the nth char. Guard against bad indices.
    #
    def char_at(self,n):
        try:
            return self.chars_view[n]
        except its_always_something:
            return ('?', 0)

    # The following methods are used by the edit syntax highlighter to set flags.
    #
    # 1. Check a token for spelling. The token might be new since the last
    # census. If so, add to the vocabulary with a count of 1. The count will
    # stay at 1 until the next census but if the file is saved in the
    # meantime, the word will be in the metadata.
    #
    def spelling_test(self, tok_str) :
        tok_nlz = unicodedata.normalize('NFKC',tok_str)
        [count, prop_set] = self.vocab[tok_nlz]
        if 0 == count : # oops, it isn't in the list yet
            prop_set = self._count(tok_nlz) # spellcheck it, set count=1
        return Vocab.XX not in prop_set
    #
    # 2. Check a token for being in the scannos list.
    #
    def scanno_test(self, tok_str) :
        return tok_str in self.scannos
