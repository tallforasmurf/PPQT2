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
                         constants.py

Define global values that are used in multiple modules. These values are
read-only. Stylistically they should be ALL-CAP.

'''
# Make available values for our platform levels:
from PyQt5.QtCore import PYQT_VERSION_STR
from PyQt5.QtCore import QT_VERSION_STR
import os
PLATFORM_NAME_STR = os.uname().sysname # e.g 'Darwin', 'Windows'
PLATFORM_IS_MAC = PLATFORM_NAME_STR.startswith('Darw')

# default values for the rare startup where the settings are empty
from PyQt5.QtCore import QSize
STARTUP_DEFAULT_SPLITTER = b'\x00\x00\x00\xff\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x02"\x00\x00\x01\xec\x00\x00\x00\x00\x07\x01\x00\x00\x00\x01\x00'
STARTUP_DEFAULT_SIZE = QSize(1024,600)

# constant values for file encodings, just cause I was trained
# not to go writing literal string constants everywhere
ENCODING_UTF = 'UTF-8'
ENCODING_LATIN = 'ISO-8859-1'

# constant value for the line-delimiter used by QPlainTextEdit
UNICODE_LINE_DELIM = '\u2029'
# constant for the en-space used instead of spaces when
# writing a proofer string to metadata
UNICODE_EN_SPACE = '\u2002'
# constant value for the zero-width-non-joiner used as a marker in reflow
UNICODE_ZWNJ = '\u200C'
# constant value for the Unicode Replacement character that is
# stuck into Notes metadata that looks like a metadata section mark.
UNICODE_REPL = '\uFFFD'
# default size for fonts, used only in totally clean installation
DEFAULT_FONT_SIZE = 13

'''
Names for sections of the metadata file.
'''
MD_BW = 'BADWORDS'
MD_BM = 'BOOKMARKS'
MD_CC = 'CHARCENSUS'
MD_CU = 'CURSOR'
MD_DH = 'DOCHASH'
MD_ES = 'EDITSIZE'
MD_GW = 'GOODWORDS'
MD_IZ = 'IMAGEZOOM'
MD_IX = 'IMAGELINKING'
MD_MD = 'MAINDICT'
MD_NO = 'NOTES'
MD_PT = 'PAGETABLE'
MD_SC = 'SCANNOLIST'
MD_V  = 'VERSION'
MD_VL = 'WORDCENSUS'

'''
These values are used to encode folio controls for the
Page/folio table.
'''

FolioFormatArabic = 0x00
FolioFormatUCRom = 0x01
FolioFormatLCRom = 0x02
FolioFormatSame = 0x03 # the "ditto" format
FolioRuleAdd1 = 0x00
FolioRuleSet = 0x01
FolioRuleSkip = 0x02

'''
Keystrokes checked by editor and other panels that monitor KeyEvent signals.

^f start search,
^F start search with selection
^g and ^G, search again forward/backward,
^= replace (using rep#1)
^t and ^T replace (rep#1) then search forward/backward,

^1-9 go to bookmarks
^-alt-1-9 set bookmarks
^-shift-1-9 go to bookmark with selection from cursor

^+ and ^- for zoom in/out
    note ctl-plus can be received as ctl-shft-equal and ctl-sht-plus!

^m and ^-alt-m, ^p and ^-alt-p used by the Notes panel

^b, ^[, ^left : "Back" in html windows

The following definitions combine the key value with the modifier) value,
so a keyEvent method begins with
    key = int(event.key()) | int(event.modifiers())
    if key in <list of relevant keys>...
'''

from PyQt5.QtCore import Qt # Qt namespace including keys

KEYPAD_MOD_CLEAR = int(0xffffffff ^ Qt.KeypadModifier)
# File menu keys
CTL_N = int(Qt.ControlModifier) | Qt.Key_N
CTL_S = int(Qt.ControlModifier) | Qt.Key_S
CTL_SHFT_S = int(Qt.ShiftModifier) | CTL_S
CTL_O = int(Qt.ControlModifier) | Qt.Key_O
CTL_W = int(Qt.ControlModifier) | Qt.Key_W
# Editor key actions
CTL_F = int(Qt.ControlModifier) | Qt.Key_F
CTL_SHFT_F = int(Qt.ShiftModifier) | CTL_F
CTL_G = int(Qt.ControlModifier) | Qt.Key_G
CTL_SHFT_G = int(Qt.ShiftModifier) | CTL_G
CTL_EQUAL = int(Qt.ControlModifier) | Qt.Key_Equal
CTL_T = int(Qt.ControlModifier) | Qt.Key_T
CTL_SHFT_T = int(Qt.ShiftModifier) | CTL_T
CTL_1 = int(Qt.ControlModifier) | Qt.Key_1
CTL_2 = int(Qt.ControlModifier) | Qt.Key_2
CTL_3 = int(Qt.ControlModifier) | Qt.Key_3
CTL_4 = int(Qt.ControlModifier) | Qt.Key_4
CTL_5 = int(Qt.ControlModifier) | Qt.Key_5
CTL_6 = int(Qt.ControlModifier) | Qt.Key_6
CTL_7 = int(Qt.ControlModifier) | Qt.Key_7
CTL_8 = int(Qt.ControlModifier) | Qt.Key_8
CTL_9 = int(Qt.ControlModifier) | Qt.Key_9
CTL_SHFT_1 = int(Qt.ShiftModifier) | CTL_1
CTL_SHFT_2 = int(Qt.ShiftModifier) | CTL_2
CTL_SHFT_3 = int(Qt.ShiftModifier) | CTL_3
CTL_SHFT_4 = int(Qt.ShiftModifier) | CTL_4
CTL_SHFT_5 = int(Qt.ShiftModifier) | CTL_5
CTL_SHFT_6 = int(Qt.ShiftModifier) | CTL_6
CTL_SHFT_7 = int(Qt.ShiftModifier) | CTL_7
CTL_SHFT_8 = int(Qt.ShiftModifier) | CTL_8
CTL_SHFT_9 = int(Qt.ShiftModifier) | CTL_9
CTL_ALT_1 = int(Qt.AltModifier) | CTL_1
CTL_ALT_2 = int(Qt.AltModifier) | CTL_2
CTL_ALT_3 = int(Qt.AltModifier) | CTL_3
CTL_ALT_4 = int(Qt.AltModifier) | CTL_4
CTL_ALT_5 = int(Qt.AltModifier) | CTL_5
CTL_ALT_6 = int(Qt.AltModifier) | CTL_6
CTL_ALT_7 = int(Qt.AltModifier) | CTL_7
CTL_ALT_8 = int(Qt.AltModifier) | CTL_8
CTL_ALT_9 = int(Qt.AltModifier) | CTL_9
CTL_MINUS = int(Qt.ControlModifier) | Qt.Key_Minus
CTL_PLUS = int(Qt.ControlModifier) | Qt.Key_Plus
CTL_SHFT_EQUAL = int(Qt.ShiftModifier) | CTL_EQUAL
CTL_SHFT_PLUS = int(Qt.ShiftModifier) | CTL_PLUS
CTL_M = int(Qt.ControlModifier) | Qt.Key_M
CTL_ALT_M = int(Qt.AltModifier) | CTL_M
CTL_P = int(Qt.ControlModifier) | Qt.Key_P
CTL_ALT_P = int(Qt.AltModifier) | CTL_P
CTL_LEFT = int(Qt.ControlModifier) | Qt.Key_Left
CTL_LEFT_PAD = CTL_LEFT | int(Qt.KeypadModifier)
CTL_LEFT_BRACKET = int(Qt.ControlModifier) | Qt.Key_BracketLeft
CTL_B = int(Qt.ControlModifier) | Qt.Key_B
# Groups of keys by function
KEYS_BACK = {CTL_B, CTL_LEFT, CTL_LEFT_BRACKET, CTL_LEFT_PAD}
KEYS_FIND = {CTL_G, CTL_SHFT_G, CTL_F, CTL_SHFT_F, CTL_T, CTL_EQUAL, CTL_SHFT_T}
KEYS_MARK = {CTL_1, CTL_2, CTL_3, CTL_4, CTL_5, CTL_6, CTL_7, CTL_8, CTL_9 }
KEYS_MARK_SET = {CTL_ALT_1, CTL_ALT_2, CTL_ALT_3, CTL_ALT_4,
                 CTL_ALT_5, CTL_ALT_6, CTL_ALT_7, CTL_ALT_8, CTL_ALT_9 }
KEYS_MARK_SHIFT = {CTL_SHFT_1, CTL_SHFT_2, CTL_SHFT_3,
                   CTL_SHFT_4, CTL_SHFT_5, CTL_SHFT_6,
                   CTL_SHFT_7, CTL_SHFT_8, CTL_SHFT_9 }
KEYS_BOOKMARKS = KEYS_MARK | KEYS_MARK_SET | KEYS_MARK_SHIFT
KEYS_ZOOM = {CTL_MINUS, CTL_PLUS, CTL_SHFT_EQUAL, CTL_SHFT_PLUS}
# Keys acted on by the edit view
KEYS_EDITOR = KEYS_FIND | KEYS_BOOKMARKS | KEYS_ZOOM
# Keys acted on by the Notes panel
KEYS_NOTES = {CTL_M, CTL_ALT_M, CTL_P, CTL_ALT_P} | KEYS_ZOOM
# TODO keys acted on by html panel, others?

'''
A dictionary of the 252 Named Entities of HTML 4. The names are indexed by
the unicode characters they translate. To complete an entity prepend & and
append ;, thus quot -> &quot; This list was lifted from
en.wikipedia.org/wiki/List_of_XML_and_HTML_character_entity_references and
processed into this form using regex changes in BBEdit.
'''
NAMED_ENTITIES = {
u'\u0022' : u'quot', # quotation mark (= APL quote)
u'\u0026' : u'amp', # ampersand
u'\u0027' : u'apos', # apostrophe (= apostrophe-quote); see below
u'\u003C' : u'lt', # less-than sign
u'\u003E' : u'gt', # greater-than sign
u'\u00A0' : u'nbsp', # no-break space (= non-breaking space)[d]
u'\u00A1' : u'iexcl', # inverted exclamation mark
u'\u00A2' : u'cent', # cent sign
u'\u00A3' : u'pound', # pound sign
u'\u00A4' : u'curren', # currency sign
u'\u00A5' : u'yen', # yen sign (= yuan sign)
u'\u00A6' : u'brvbar', # broken bar (= broken vertical bar)
u'\u00A7' : u'sect', # section sign
u'\u00A8' : u'uml', # diaeresis (= spacing diaeresis); see Germanic umlaut
u'\u00A9' : u'copy', # copyright symbol
u'\u00AA' : u'ordf', # feminine ordinal indicator
u'\u00AB' : u'laquo', # left-pointing double angle quotation mark (= left pointing guillemet)
u'\u00AC' : u'not', # not sign
u'\u00AD' : u'shy', # soft hyphen (= discretionary hyphen)
u'\u00AE' : u'reg', # registered sign ( = registered trademark symbol)
u'\u00AF' : u'macr', # macron (= spacing macron = overline = APL overbar)
u'\u00B0' : u'deg', # degree symbol
u'\u00B1' : u'plusmn', # plus-minus sign (= plus-or-minus sign)
u'\u00B2' : u'sup2', # superscript two (= superscript digit two = squared)
u'\u00B3' : u'sup3', # superscript three (= superscript digit three = cubed)
u'\u00B4' : u'acute', # acute accent (= spacing acute)
u'\u00B5' : u'micro', # micro sign
u'\u00B6' : u'para', # pilcrow sign ( = paragraph sign)
u'\u00B7' : u'middot', # middle dot (= Georgian comma = Greek middle dot)
u'\u00B8' : u'cedil', # cedilla (= spacing cedilla)
u'\u00B9' : u'sup1', # superscript one (= superscript digit one)
u'\u00BA' : u'ordm', # masculine ordinal indicator
u'\u00BB' : u'raquo', # right-pointing double angle quotation mark (= right pointing guillemet)
u'\u00BC' : u'frac14', # vulgar fraction one quarter (= fraction one quarter)
u'\u00BD' : u'frac12', # vulgar fraction one half (= fraction one half)
u'\u00BE' : u'frac34', # vulgar fraction three quarters (= fraction three quarters)
u'\u00BF' : u'iquest', # inverted question mark (= turned question mark)
u'\u00C0' : u'Agrave', # Latin capital letter A with grave accent (= Latin capital letter A grave)
u'\u00C1' : u'Aacute', # Latin capital letter A with acute accent
u'\u00C2' : u'Acirc', # Latin capital letter A with circumflex
u'\u00C3' : u'Atilde', # Latin capital letter A with tilde
u'\u00C4' : u'Auml', # Latin capital letter A with diaeresis
u'\u00C5' : u'Aring', # Latin capital letter A with ring above (= Latin capital letter A ring)
u'\u00C6' : u'AElig', # Latin capital letter AE (= Latin capital ligature AE)
u'\u00C7' : u'Ccedil', # Latin capital letter C with cedilla
u'\u00C8' : u'Egrave', # Latin capital letter E with grave accent
u'\u00C9' : u'Eacute', # Latin capital letter E with acute accent
u'\u00CA' : u'Ecirc', # Latin capital letter E with circumflex
u'\u00CB' : u'Euml', # Latin capital letter E with diaeresis
u'\u00CC' : u'Igrave', # Latin capital letter I with grave accent
u'\u00CD' : u'Iacute', # Latin capital letter I with acute accent
u'\u00CE' : u'Icirc', # Latin capital letter I with circumflex
u'\u00CF' : u'Iuml', # Latin capital letter I with diaeresis
u'\u00D0' : u'ETH', # Latin capital letter Eth
u'\u00D1' : u'Ntilde', # Latin capital letter N with tilde
u'\u00D2' : u'Ograve', # Latin capital letter O with grave accent
u'\u00D3' : u'Oacute', # Latin capital letter O with acute accent
u'\u00D4' : u'Ocirc', # Latin capital letter O with circumflex
u'\u00D5' : u'Otilde', # Latin capital letter O with tilde
u'\u00D6' : u'Ouml', # Latin capital letter O with diaeresis
u'\u00D7' : u'times', # multiplication sign
u'\u00D8' : u'Oslash', # Latin capital letter O with stroke (= Latin capital letter O slash)
u'\u00D9' : u'Ugrave', # Latin capital letter U with grave accent
u'\u00DA' : u'Uacute', # Latin capital letter U with acute accent
u'\u00DB' : u'Ucirc', # Latin capital letter U with circumflex
u'\u00DC' : u'Uuml', # Latin capital letter U with diaeresis
u'\u00DD' : u'Yacute', # Latin capital letter Y with acute accent
u'\u00DE' : u'THORN', # Latin capital letter THORN
u'\u00DF' : u'szlig', # Latin small letter sharp s (= ess-zed); see German Eszett
u'\u00E0' : u'agrave', # Latin small letter a with grave accent
u'\u00E1' : u'aacute', # Latin small letter a with acute accent
u'\u00E2' : u'acirc', # Latin small letter a with circumflex
u'\u00E3' : u'atilde', # Latin small letter a with tilde
u'\u00E4' : u'auml', # Latin small letter a with diaeresis
u'\u00E5' : u'aring', # Latin small letter a with ring above
u'\u00E6' : u'aelig', # Latin small letter ae (= Latin small ligature ae)
u'\u00E7' : u'ccedil', # Latin small letter c with cedilla
u'\u00E8' : u'egrave', # Latin small letter e with grave accent
u'\u00E9' : u'eacute', # Latin small letter e with acute accent
u'\u00EA' : u'ecirc', # Latin small letter e with circumflex
u'\u00EB' : u'euml', # Latin small letter e with diaeresis
u'\u00EC' : u'igrave', # Latin small letter i with grave accent
u'\u00ED' : u'iacute', # Latin small letter i with acute accent
u'\u00EE' : u'icirc', # Latin small letter i with circumflex
u'\u00EF' : u'iuml', # Latin small letter i with diaeresis
u'\u00F0' : u'eth', # Latin small letter eth
u'\u00F1' : u'ntilde', # Latin small letter n with tilde
u'\u00F2' : u'ograve', # Latin small letter o with grave accent
u'\u00F3' : u'oacute', # Latin small letter o with acute accent
u'\u00F4' : u'ocirc', # Latin small letter o with circumflex
u'\u00F5' : u'otilde', # Latin small letter o with tilde
u'\u00F6' : u'ouml', # Latin small letter o with diaeresis
u'\u00F7' : u'divide', # division sign (= obelus)
u'\u00F8' : u'oslash', # Latin small letter o with stroke (= Latin small letter o slash)
u'\u00F9' : u'ugrave', # Latin small letter u with grave accent
u'\u00FA' : u'uacute', # Latin small letter u with acute accent
u'\u00FB' : u'ucirc', # Latin small letter u with circumflex
u'\u00FC' : u'uuml', # Latin small letter u with diaeresis
u'\u00FD' : u'yacute', # Latin small letter y with acute accent
u'\u00FE' : u'thorn', # Latin small letter thorn
u'\u00FF' : u'yuml', # Latin small letter y with diaeresis
u'\u0152' : u'OElig', # Latin capital ligature oe[e]
u'\u0153' : u'oelig', # Latin small ligature oe[e]
u'\u0160' : u'Scaron', # Latin capital letter s with caron
u'\u0161' : u'scaron', # Latin small letter s with caron
u'\u0178' : u'Yuml', # Latin capital letter y with diaeresis
u'\u0192' : u'fnof', # Latin small letter f with hook (= function = florin)
u'\u02C6' : u'circ', # modifier) letter circumflex accent
u'\u02DC' : u'tilde', # small tilde
u'\u0391' : u'Alpha', # Greek capital letter Alpha
u'\u0392' : u'Beta', # Greek capital letter Beta
u'\u0393' : u'Gamma', # Greek capital letter Gamma
u'\u0394' : u'Delta', # Greek capital letter Delta
u'\u0395' : u'Epsilon', # Greek capital letter Epsilon
u'\u0396' : u'Zeta', # Greek capital letter Zeta
u'\u0397' : u'Eta', # Greek capital letter Eta
u'\u0398' : u'Theta', # Greek capital letter Theta
u'\u0399' : u'Iota', # Greek capital letter Iota
u'\u039A' : u'Kappa', # Greek capital letter Kappa
u'\u039B' : u'Lambda', # Greek capital letter Lambda
u'\u039C' : u'Mu', # Greek capital letter Mu
u'\u039D' : u'Nu', # Greek capital letter Nu
u'\u039E' : u'Xi', # Greek capital letter Xi
u'\u039F' : u'Omicron', # Greek capital letter Omicron
u'\u03A0' : u'Pi', # Greek capital letter Pi
u'\u03A1' : u'Rho', # Greek capital letter Rho
u'\u03A3' : u'Sigma', # Greek capital letter Sigma
u'\u03A4' : u'Tau', # Greek capital letter Tau
u'\u03A5' : u'Upsilon', # Greek capital letter Upsilon
u'\u03A6' : u'Phi', # Greek capital letter Phi
u'\u03A7' : u'Chi', # Greek capital letter Chi
u'\u03A8' : u'Psi', # Greek capital letter Psi
u'\u03A9' : u'Omega', # Greek capital letter Omega
u'\u03B1' : u'alpha', # Greek small letter alpha
u'\u03B2' : u'beta', # Greek small letter beta
u'\u03B3' : u'gamma', # Greek small letter gamma
u'\u03B4' : u'delta', # Greek small letter delta
u'\u03B5' : u'epsilon', # Greek small letter epsilon
u'\u03B6' : u'zeta', # Greek small letter zeta
u'\u03B7' : u'eta', # Greek small letter eta
u'\u03B8' : u'theta', # Greek small letter theta
u'\u03B9' : u'iota', # Greek small letter iota
u'\u03BA' : u'kappa', # Greek small letter kappa
u'\u03BB' : u'lambda', # Greek small letter lambda
u'\u03BC' : u'mu', # Greek small letter mu
u'\u03BD' : u'nu', # Greek small letter nu
u'\u03BE' : u'xi', # Greek small letter xi
u'\u03BF' : u'omicron', # Greek small letter omicron
u'\u03C0' : u'pi', # Greek small letter pi
u'\u03C1' : u'rho', # Greek small letter rho
u'\u03C2' : u'sigmaf', # Greek small letter final sigma
u'\u03C3' : u'sigma', # Greek small letter sigma
u'\u03C4' : u'tau', # Greek small letter tau
u'\u03C5' : u'upsilon', # Greek small letter upsilon
u'\u03C6' : u'phi', # Greek small letter phi
u'\u03C7' : u'chi', # Greek small letter chi
u'\u03C8' : u'psi', # Greek small letter psi
u'\u03C9' : u'omega', # Greek small letter omega
u'\u03D1' : u'thetasym', #  Greek theta symbol
u'\u03D2' : u'upsih', #  Greek Upsilon with hook symbol
u'\u03D6' : u'piv', # Greek pi symbol
u'\u2002' : u'ensp', # en space[d]
u'\u2003' : u'emsp', # em space[d]
u'\u2009' : u'thinsp', # thin space[d]
u'\u200C' : u'zwnj', # zero-width non-joiner
u'\u200D' : u'zwj', # zero-width joiner
u'\u200E' : u'lrm', #  RFC 2070 left-to-right mark
u'\u200F' : u'rlm', #  RFC 2070 right-to-left mark
u'\u2013' : u'ndash', # en dash
u'\u2014' : u'mdash', # em dash
u'\u2018' : u'lsquo', # left single quotation mark
u'\u2019' : u'rsquo', # right single quotation mark
u'\u201A' : u'sbquo', # HTML  single low-9 quotation mark
u'\u201C' : u'ldquo', # left double quotation mark
u'\u201D' : u'rdquo', # right double quotation mark
u'\u201E' : u'bdquo', # HTML  double low-9 quotation mark
u'\u2020' : u'dagger', # dagger, obelisk
u'\u2021' : u'Dagger', # double dagger, double obelisk
u'\u2022' : u'bull', # bullet (= black small circle)[f]
u'\u2026' : u'hellip', # horizontal ellipsis (= three dot leader)
u'\u2030' : u'permil', # per mille sign
u'\u2032' : u'prime', # prime (= minutes = feet)
u'\u2033' : u'Prime', # double prime (= seconds = inches)
u'\u2039' : u'lsaquo', # proposed single left-pointing angle quotation mark[g]
u'\u203A' : u'rsaquo', # proposed single right-pointing angle quotation mark[g]
u'\u203E' : u'oline', #  overline (= spacing overscore)
u'\u2044' : u'frasl', #  fraction slash (= solidus)
u'\u20AC' : u'euro', # HTML  euro sign
u'\u2111' : u'image', # black-letter capital I (= imaginary part)
u'\u2118' : u'weierp', # script capital P (= power set = Weierstrass p)
u'\u211C' : u'real', # black-letter capital R (= real part symbol)
u'\u2122' : u'trade', # trademark symbol
u'\u2135' : u'alefsym', #  alef symbol (= first transfinite cardinal)[h]
u'\u2190' : u'larr', # leftwards arrow
u'\u2191' : u'uarr', # upwards arrow
u'\u2192' : u'rarr', # rightwards arrow
u'\u2193' : u'darr', # downwards arrow
u'\u2194' : u'harr', # left right arrow
u'\u21B5' : u'crarr', #  downwards arrow with corner leftwards (= carriage return)
u'\u21D0' : u'lArr', # leftwards double arrow[i]
u'\u21D1' : u'uArr', # upwards double arrow
u'\u21D2' : u'rArr', # rightwards double arrow[j]
u'\u21D3' : u'dArr', # downwards double arrow
u'\u21D4' : u'hArr', # left right double arrow
u'\u2200' : u'forall', # for all
u'\u2202' : u'part', # partial differential
u'\u2203' : u'exist', # there exists
u'\u2205' : u'empty', # empty set (= null set = diameter)
u'\u2207' : u'nabla', # nabla (= backward difference)
u'\u2208' : u'isin', # element of
u'\u2209' : u'notin', # not an element of
u'\u220B' : u'ni', # contains as member
u'\u220F' : u'prod', # n-ary product (= product sign)[k]
u'\u2211' : u'sum', # n-ary summation[l]
u'\u2212' : u'minus', # minus sign
u'\u2217' : u'lowast', # asterisk operator
u'\u221A' : u'radic', # square root (= radical sign)
u'\u221D' : u'prop', # proportional to
u'\u221E' : u'infin', # infinity
u'\u2220' : u'ang', # angle
u'\u2227' : u'and', # logical and (= wedge)
u'\u2228' : u'or', # logical or (= vee)
u'\u2229' : u'cap', # intersection (= cap)
u'\u222A' : u'cup', # union (= cup)
u'\u222B' : u'int', # integral
u'\u2234' : u'there4', # therefore sign
u'\u223C' : u'sim', # tilde operator (= varies with = similar to)[m]
u'\u2245' : u'cong', # congruent to
u'\u2248' : u'asymp', # almost equal to (= asymptotic to)
u'\u2260' : u'ne', # not equal to
u'\u2261' : u'equiv', # identical to; sometimes used for 'equivalent to'
u'\u2264' : u'le', # less-than or equal to
u'\u2265' : u'ge', # greater-than or equal to
u'\u2282' : u'sub', # subset of
u'\u2283' : u'sup', # superset of[n]
u'\u2284' : u'nsub', # not a subset of
u'\u2286' : u'sube', # subset of or equal to
u'\u2287' : u'supe', # superset of or equal to
u'\u2295' : u'oplus', # circled plus (= direct sum)
u'\u2297' : u'otimes', # circled times (= vector product)
u'\u22A5' : u'perp', # up tack (= orthogonal to = perpendicular)[o]
u'\u22C5' : u'sdot', # dot operator[p]
u'\u2308' : u'lceil', # left ceiling (= APL upstile)
u'\u2309' : u'rceil', # right ceiling
u'\u230A' : u'lfloor', # left floor (= APL downstile)
u'\u230B' : u'rfloor', # right floor
u'\u2329' : u'lang', # left-pointing angle bracket (= bra)[q]
u'\u232A' : u'rang', # right-pointing angle bracket (= ket)[r]
u'\u25CA' : u'loz', # lozenge
u'\u2660' : u'spades', # black spade suit[f]
u'\u2663' : u'clubs', # black club suit (= shamrock)[f]
u'\u2665' : u'hearts', # black heart suit (= valentine)[f]
u'\u2666' : u'diams' # black diamond suit[f]
}