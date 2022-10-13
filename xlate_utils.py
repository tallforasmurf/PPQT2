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

            Xlate_utils.py

This contains definitions used by Translator modules.

Recommended use is:
    import xlate_utils as XU

Definitions provided:

Events
    an enum of the possible event codes a Translator
    must deal with, such as LINE, START_NOFILL etc.

LineParts
    an enum of the possible line-item codes that
    can be returned by the tokenize() function.

tokenize(text)
    a generator that breaks up a string of text
    into logical bits and yields them as tuples (code,'string').
    The codes are defined in TokenCodes below.
    Usage: tokens = XU.tokenize(string_of_text)
           for ( tcode, tvalue ) in tokens: ...

poem_line_number(text)
    returns either None or an int, a line number set off by at
    least two spaces at the end of text

poem_line_strip(text)
    returns a text with any poem line number stripped.

flatten_line(text)
    returns text stripped of all markup, only words and spaces:
    in:  <id='Africa'><sc>Fig</sc>. 18. The African <i>veldt</i>...
    out: Fig 18 The African veldt...

underscore_line(text, truncate=50)
    returns text stripped of all markup, with words joined by underscores:
    in:  <sc>Fig</sc>. 18. The African <i>veldt</i> drowses in the glowing sun.
    out: Fig_18_The_African_veldt_drowses_in_the_glowing_su (trunc at 50)

Dialog_Item
    a class used to build an Options dialog. Usage:
        Dialog_Item( kind=, label=, tooltip='', result=None,
                     minimum=None, maximum=None, choices=[] )

Create a user query dialog item as follows:

A simple checkbox for yes/no questions:

    XU.Dialog_Item( kind='checkbox', label='Skip tables',
                    tooltip='Check this to skip over /T..T/ tables' )

A string of text:

    XU.Dialog_Item( kind='string', label='CSS URL',
                    tooltip='Enter the URL of a remote CSS script' )

A number:

    XU.Dialog_Item( kind='number', label='Max Line',
                    tooltip='Maximum line width, default is 72',
                    minimum=50, maximum=90, result=72 )

A radio-set of mutually-exclusive choices. The choices= argument is a list of
tuples, ('label','tooltip'), one for each button in the set. Result is the
index of the default choice starting from 0.

    XU.Dialog_Item( kind='choice', label='Italics',
                    tooltip='What to do with <i>: omit it, convert it, pass it on',
                    choices= [
                        ("Omit","Just omit <i> and </i> from the output"),
                        ("Use _","Replace <i> and </i> with a single underscore_"),
                        ("Keep","Retain <i> and </i> in the output")
                    ],
                    result=1 )

'''

import regex

'''
The "events" we can throw at a Translator. Most of them are, by a
remarkable coincidence, the same as the token codes used when parsing.
'''
class Events( object ) :
    LINE          = 'L'
    OPEN_PARA     = 'E'
    CLOSE_PARA    = 'e'
    OPEN_NOFLOW   = 'X'
    CLOSE_NOFLOW  = 'x'
    OPEN_CENTER   = 'C'
    CLOSE_CENTER  = 'c'
    OPEN_RIGHT    = 'R'
    CLOSE_RIGHT   = 'r'
    OPEN_HEAD2    = '2'
    CLOSE_HEAD2   = '4'
    OPEN_HEAD3    = '3'
    CLOSE_HEAD3   = '5'
    OPEN_POEM     = 'P'
    CLOSE_POEM    = 'p'
    OPEN_QUOTE    = 'Q'
    CLOSE_QUOTE   = 'q'
    OPEN_LIST     = 'U'
    CLOSE_LIST    = 'u'
    OPEN_ILLO     = 'I'
    CLOSE_ILLO    = 'i'
    OPEN_SNOTE    = 'S'
    CLOSE_SNOTE   = 's'
    OPEN_FNOTE    = 'F'
    CLOSE_FNOTE   = 'f'
    PAGE_BREAK    = '!'
    T_BREAK       = '%'
    OPEN_FNLZ     = 'N'
    CLOSE_FNLZ    = 'n'
    OPEN_TABLE    = 'T'
    OPEN_TROW     = '<'
    OPEN_TCELL    = '('
    CLOSE_TCELL   = ')'
    CLOSE_TROW    = '>'
    CLOSE_TABLE   = 't'

''' The parts of a LINE as yielded by line_parts(). '''

class TokenCodes ( object ) :
    ITAL_ON   = 'ITAL_ON'  # ( 'ITAL_ON, "i" ) or ('ITAL_ON', "i lang='fr_FR')
    ITAL_OFF  = 'ITAL_OFF' # ( 'ITAL_OFF', "i" )
    BOLD_ON   = 'BOLD_ON'  # ( 'BOLD_ON, "b" )
    BOLD_OFF  = 'BOLD_OFF' # ( 'BOLD_OFF', "b" )
    SCAP_ON   = 'SCAP_ON'  # ( 'SCAP_ON, "sc" )
    SCAP_OFF  = 'SCAP_OFF' # ( 'SCAP_OFF', "sc" )
    SPAN_ON   = 'SPAN_ON'  # ( 'SPAN_ON, "span" ) or ('SPAN_ON', "span lang='en_GB')
    SPAN_OFF  = 'SPAN_OFF' # ( 'SCAP_OFF', "sc" )
    DICT_ON   = 'DICT_ON'  # ( DICT_ON, 'fr_FR' ) redundant but useful
    DICT_OFF  = 'DICT_OFF' # ( DICT_OFF, "" ) always follows ITAL_OFF or SPAN_OFF
    SUP       = 'SUP'      # ( SUP, "r" or "bt" ) Y^r, O^{bt}, 2^2, 10^{23}
    SUB       = 'SUB'      # ( SUB, "2" or "maj" ) H_{2}O, key of A_{maj}
    FNKEY     = 'FNKEY'    # ( FNKEY, 'A' or '17' ) from [A] or [17] BUT NOT [*] or [:u]
    BRKTS     = 'BRKTS'    # ( BRKTS, "Greek:book:βιβλίο" or "typo:original:correct" )
    LINK      = 'LINK'     # ( LINK, "visible:target" eg "255:Page_255")
    TARGET    = 'TARGET'   # ( TARGET, "target" ) <id='target'>
    PLINE     = 'PLINE'    # ( PLINE, '25' ) poem line number
    SPACE     = 'SPACE'    # ( SPACE, " ")
    WORD      = 'WORD'     # ( WORD, "M[:o]ther-in-law" )
    PUNCT     = 'PUNCT'    # ( PUNCT, '!', ';', '.' etc )
    OTHER     = 'OTHER'    # ( OTHER, '$' maybe? '*'? )

'''
Globals needed to perform "tokenization" of a text line
(c.f. https://docs.python.org/dev/library/re.html#writing-a-tokenizer)
The following tuples are ( match-group-name, match-expression ).

Order matters here, the regexes are applied in sequence. For example
the SUB text \w_(\w+)_ must come before the fallback SUB1.

regex to select a word including hyphenated and possessives.

One wee problem: In the DP format, the only valid use for underscore is to
show a subscript as in H_2_O. However, to a PCRE regular expression, the
"word character" (\w) set includes the underscore. However, the most
excellent regex module allows character class arithmetic! So we look for \w
minus underscore, which is written [\w--_].
'''
WORD_EXPR = r"([\w--_]*(\[..\])?[\w--_]+)+"
WORDHY_EXPR = "(" + WORD_EXPR + r"[\'\-\u2019])*" + WORD_EXPR
'''
regex to parse an html opener to pick up both the verb and
the value of a lang= property. Underscores ok here: fr_FR
'''
LANG_EXPR = r'\<(\w+).+lang=[\'\"]([\w]+)[\'\"]'
LANG_XP = regex.compile( LANG_EXPR )

''' regex to pick off poem line number '''
POEM_LNUM_EXPR = r'\ {2,}(\d+)$'
POEM_LNUM_XP = regex.compile( POEM_LNUM_EXPR )

TOKEN_RXS = [
( TokenCodes.WORD,     WORDHY_EXPR ),
( TokenCodes.TARGET,   r'''\<id=['"](\w+)['"]>''' ),
( TokenCodes.ITAL_ON,  r'\<i\s*([^>]*)>' ),
( TokenCodes.ITAL_OFF, r'\</(i)\s*>' ),
( TokenCodes.BOLD_ON,  r'\<b\s*([^>]*)>' ),
( TokenCodes.BOLD_OFF, r'\</(b)\s*>' ),
( TokenCodes.SCAP_ON,  r'\<sc\s*([^>]*)>' ),
( TokenCodes.SCAP_OFF, r'\</(sc)\s*>' ),
( TokenCodes.SPAN_ON,  r'\<span\s*([^>]*)>' ),
( TokenCodes.SPAN_OFF, r'\</(span)\s*>' ),
( TokenCodes.SUB,      r'_\{(\w+)\}' ),
( TokenCodes.SUP,      r'\^\{(\w+)\}' ),
( TokenCodes.SUP,      r'\^(\w)' ),
( TokenCodes.BRKTS,    r'\[(\w\w+\:[^\[\]\n]+)\]' ),
( TokenCodes.FNKEY,    r'\[(\w+)\]' ),
( TokenCodes.LINK,     r'\#(\d+)\#' ),
( TokenCodes.LINK,     r'\#([^:]+?\:[^#]+?)\#' ),
( TokenCodes.PLINE,    POEM_LNUM_EXPR ),
( TokenCodes.PUNCT,    r'\p{P}' ),
( TokenCodes.SPACE,    r' +' ),
( TokenCodes.OTHER,    r'.' ) # so we always match something.
]

'''
Combine the above as alternatives in a single regex. The combined
expression will always produce a match, to the EMPTY or LINE expressions if
nothing else. The group name of the matching expression is in the lastgroup
member of the match object.
'''
TOKEN_EXPR = '|'.join(
    '(?P<{0}>{1})'.format(*pair) for pair in TOKEN_RXS
)
TOKEN_XP = regex.compile( TOKEN_EXPR, flags=regex.V1 )

def tokenize( string ) :
    global TOKEN_XP, LANG_XP
    html_opens = set([ TokenCodes.BOLD_ON, TokenCodes.ITAL_ON,
                       TokenCodes.SCAP_ON, TokenCodes.SPAN_ON ] )
    html_closes = set([ TokenCodes.BOLD_OFF, TokenCodes.ITAL_OFF,
                       TokenCodes.SCAP_OFF, TokenCodes.SPAN_OFF ] )

    condense = lambda glist : [gp for gp in glist if gp is not None]
    dict_start = None
    j = 0
    while j < len( string ) :
        mob = TOKEN_XP.search( string, j )
        assert mob is not None
        text = mob.group(0)
        code = mob.lastgroup
        j = mob.end()
        if code in html_opens :
            mob2 = LANG_XP.search( mob.group(0) )
            if mob2 : # is not none..
                # ..this html verb has a lang= property. yield the current
                # event and set up to yield the DICT_ON event next.
                yield ( code, text )
                code = TokenCodes.DICT_ON
                text = mob2.group(2)
                dict_start = mob2.group(1) # the verb, e.g. 'span'
        elif code in html_closes and dict_start :
            # See if this is the close of the html verb that started the dict.
            # Condense out all the Nones in the group list -- the verb is
            # the second non-None one.
            mg = [ m for m in mob.groups() if m is not None ]
            if mg[1] == dict_start :
                yield ( code, text )
                code = TokenCodes.DICT_OFF
                text = ''
                dict_start = None
        elif code in ( 'LINK', 'TARGET', 'FNKEY', 'SUP', 'SUB', 'BRKTS', 'PLINE' ) :
            # for these we want to pass only the items of group(1) if the regex
            # had been recognized on its own, but it was part of a huge list of
            # regexes so mob.groups() is a long list, mostly of Nones.
            groups = condense( mob.groups() )
            text = groups[1] # just the target/key/sup/sub/bracketed string
            if code == 'LINK' and (not ':' in text) :
                    # One-part link e.g. #255#, expand to 2 parts, 255:Page_255
                    text = text + ':' + 'Page_' + text
        yield ( code, text )

def poem_line_number( string ) :
    mob = POEM_LNUM_XP.search( string )
    if mob : # is not None,
        return mob.group(1)
    return None

def poem_line_strip( string ) :
    mob = POEM_LNUM_XP.search( string )
    if mob : # is not None,
        return string[:mob.start()]
    return string

def flatten_line( string ) :
    izer = tokenize( string )
    out = ''
    for (code, text) in izer :
        if code == TokenCodes.WORD : out += text
        elif code == TokenCodes.SPACE : out += ' '
    return out

def underscore_line(text, truncate=50):
    words = flatten_line( text ).split()
    out = '_'.join( words )
    return out[:maxlen]

EV_NAMES = {
    Events.LINE          : 'Line',
    Events.OPEN_PARA     : 'Open paragraph',
    Events.CLOSE_PARA    : 'Close paragraph',
    Events.OPEN_NOFLOW   : 'Open /X',
    Events.CLOSE_NOFLOW  : 'Close /X',
    Events.OPEN_CENTER   : 'Open /C',
    Events.CLOSE_CENTER  : 'Close /C',
    Events.OPEN_RIGHT    : 'Open /R',
    Events.CLOSE_RIGHT   : 'Close /R',
    Events.OPEN_HEAD2    : 'Open Chapter Head',
    Events.CLOSE_HEAD2   : 'Close Chapter Head',
    Events.OPEN_HEAD3    : 'Open Subhead',
    Events.CLOSE_HEAD3   : 'Close Subhead',
    Events.OPEN_POEM     : 'Open Poem',
    Events.CLOSE_POEM    : 'Close Poem',
    Events.OPEN_QUOTE    : 'Open Block Quote',
    Events.CLOSE_QUOTE   : 'Close Block Quote',
    Events.OPEN_LIST     : 'Open List',
    Events.CLOSE_LIST    : 'Close List',
    Events.OPEN_ILLO     : 'Open Illustration',
    Events.CLOSE_ILLO    : 'Close Illustration',
    Events.OPEN_SNOTE    : 'Open Sidenote',
    Events.CLOSE_SNOTE   : 'Close Sidenote',
    Events.OPEN_FNOTE    : 'Open Footnote',
    Events.CLOSE_FNOTE   : 'Close Footnote',
    Events.PAGE_BREAK    : 'Page break',
    Events.T_BREAK       : 'Thought break',
    Events.OPEN_FNLZ     : 'Open Footnote Zone',
    Events.CLOSE_FNLZ    : 'Close Footnote Zone',
    Events.OPEN_TABLE    : 'Open Table',
    Events.OPEN_TROW     : 'Open Table Row',
    Events.OPEN_TCELL    : 'Open Table Cell',
    Events.CLOSE_TCELL   : 'Close Table Cell',
    Events.CLOSE_TROW    : 'Close Table Row',
    Events.CLOSE_TABLE   : 'Close Table'
    }


import logging
xlt_logger = logging.getLogger(name='Translator Support')

class Dialog_Item(object) :
    def __init__( self, kind, label, tooltip='',
                result=None, minimum=None, maximum=None, choices=None ):
        self.kind = 'error'
        if not isinstance(kind, str):
            xlt_logger.error('Dialog_Item(kind) must be a string')
            return
        if kind.lower() not in ['checkbox','number','string','choice'] :
            xlt_logger.error('Unknown dialog item kind: {}'.format(kind))
            return
        if not isinstance(label,str) :
            xlt_logger.error('Dialog_Item label must be a string')
            return
        self.kind = kind.lower()
        self.label = label
        self.tooltip = tooltip
        self.result = result
        if tooltip is not None and not isinstance( tooltip, str ) :
                xlt_logger.error('Dialog_Item tooltip should be string, using null')
                self.tooltip = ''

        if kind == 'checkbox' :
            if result is not None and not isinstance( result, int ) :
                xlt_logger.error('Dialog_Item checkbox result should be int, using False')
                self.result = False

        elif kind == 'string' :
            if result is not None and not isinstance( result, str ) :
                xlt_logger.error('Dialog_Item string result should be string, using null')
                self.result = ''

        elif kind == 'number' :
            self.minimum = minimum
            self.maximum = maximum
            if minimum is not None and not isinstance( minimum, int ) :
                xlt_logger.error('Dialog_Item minimum should be int, using None')
                self.minimum = None
            if maximum is not None and not isinstance( maximum, int ) :
                xlt_logger.error('Dialog_Item maximum should be int, using None')
                self.maximum = None
            if result is not None and not isinstance( result, int ) :
                xlt_logger.error('Dialog_Item number result should be int, using None')
                self.result = None

        else : # kind == 'choice'
            # the try catches the error that choices is not a list, or that
            # it has elements that are not tuples, and the loop checks for
            # proper types.
            self.choices = []
            try :
                if 0 == len( choices ) :
                    raise IndexError
                for ( lbl, tip ) in choices :
                    if not isinstance( lbl, str ) or not isinstance( tip, str ) :
                        raise TypeError
                    self.choices.append( ( lbl, tip ) )
            except :
                xlt_logger.error('Dialog_Item choices must be a list of tuples')
                self.kind = 'error'
            if result is not None :
                if not isinstance( result, int ) :
                    xlt_logger.error('Dialog_Item choices result should be int, using 0')
                    self.result = 0
                elif (result < 0) or (result >= len(self.choices) ) :
                    xlt_logger.error('Dialog_Item choices result must index a choice, using 0')
                    self.result = 0
            else : self.result = 0 # need one choice checked
        # and that completes validity checking. See translators.py for the
        # implementation of the dialog based on this info.

if __name__ == '__main__':
    s = 'Gen^{rl} L^d'
    izer = tokenize( s )
    for (tok, en ) in izer :
        print( tok, en )
