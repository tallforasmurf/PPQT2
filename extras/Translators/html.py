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
__version__ = "2.1.0"
__author__  = "David Cortesi"
__copyright__ = "Copyright 2013, 2014, 2015 David Cortesi"
__maintainer__ = "David Cortesi"
__email__ = "tallforasmurf@yahoo.com"
'''
                HTML Translator

This file exists as extras/Translators/html.py. It implements a DP-format to
HTML translation using the Translator API.

The boilerplate text for the HTML header and CSS style sheet is at the end of
the module as triple-quoted literals named DTD and CSS.

This version is based on actual experience preparing an HTML book
anticipating conversion to EPUB, and reviewing the various EPUB-related
documents in the DP Wiki. The CSS provided (see CSS_START at the end of the
file) is severely pruned back from the previous version (which was based on
old Guiguts practice).

'''

import xlate_utils as XU
import types

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Tell PPQT what to call us in the File>Translators... submenu.
#
MENU_NAME = 'HTML'

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# No OPTIONS_DIALOG needed

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Globals in which to pass initialization items to translate()
#
PROLOG = None
BODY = None
EPILOG = None
PAGES = []
#
# set of poetry indents used, each an integer number of ems.
# Assigned in translate(), used in finalize().
#
POEM_EMS = set()
#
# Set of footnote keys to test for uniqueness and previous definition
#
FNKEYS = set()
#
# Dict of CSS classes that establish left/right margins and text-indent values
# that correspond to F/L/R values passed by the user.
#
FLR_CLASSES = dict()
#
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# Initialize:
#
# Save files and pages list in globals.
#
# Extract title and author from the facts (if given, else use embarrassing
# default strings).
#
# Initialize the prolog with the DTD, basic metadata, and CSS except for
# poetry classes.
#
def initialize( prolog, body, epilog, facts, pages ) :
    global PROLOG, BODY, EPILOG, PAGES, FNKEYS, POEM_EMS, FLR_CLASSES

    # clear lists that may have junk from a prior translation
    POEM_EMS = set()
    FNKEYS = set()
    FLR_CLASSES = dict()

    # save the MemoryStream thingies
    PROLOG = prolog
    BODY = body
    EPILOG = epilog

    # do we have page break info? If not, leave at null list
    if len(pages) : PAGES = pages

    # the only facts we need are Title and Author which go in the <Title>
    title = '!!BOOK TITLE MISSING!!'
    author = '!!NO AUTHOR GIVEN!!'
    for (key, value) in facts.items() :
        if key.lower() == 'title' :
            title = value
        if key.lower() == 'author' :
            author = value

    PROLOG << DTD
    PROLOG << HTML_START.format( title, author )
    PROLOG << CSS_START

    return True

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# The following is a sub-translator for individual line texts. We repeat the
# action-dict trick here, as being more performant than an if/elif stack with
# 8 sequential tests.
#
# The actions are of four kinds. For the most common token codes, the needed
# action is to write the token text to BODY. However we cannot just write "ttext"
# as an action because it would be evaluated when the actions dict is declared,
# not when the tokens are being parsed. So we use '' as a flag meaning, just
# copy the current ttext to BODY.
#
# In some cases it is necessary to write some modification of ttext. These
# are written as lambdas that yield the needed expression. The lambda is
# evaluated when called, so it gets the current value of ttext.
#
# In three cases it is necessary to do something more than a simple format;
# these are moved to functions, and the write to BODY is in the functions.
#
# ...and then I learned: types.LambdaType == types.FunctionType! WTF?
# which means I can't tell the difference between an action that is a lambda
# and one that is a reference to a function.
#
# At this point, the actions became tuples.
#
# In a compiled language with proper scoping, we'd declare the actions dict
# inside trans_line(). However this is an interpreted language, and every
# time trans_line is called (most lines of the document) its contents are
# evaluated -- which would include evaluating the the actions dict. That's
# tolerable in the translate() function below because it is only called once
# per document. But for this one, we move the dict outside the function.
#

def do_fnkey( ttext, lnum ) :
    global FNKEYS, BODY

    # Footnote anchor-point[x] markup per Guiguts, except we require keys to
    # be unique (that's what the Footnotes panel is *for*).

    fnanchor = '''<a id="FNanchor_{0}"></a><a href="#Footnote_{0}" class="fnanchor"><sup>{0}</sup></a>'''

    if ttext in FNKEYS :
        BODY << '\n<b>!!Duplicate footnote key at line {}!!</b>\n'.format(lnum)
    FNKEYS.add( ttext )
    BODY << fnanchor.format( ttext )

def do_brkts( ttext, lnum ) :
    global BODY

    # brkts is anything inside [brackets] with a colon, this includes all
    # transliterations and the ad-hoc PPQT [typo:original:corrected] markup.
    # We are assured at least one colon, often there are two.

    [code, *rest] = ttext.split(':') # rest is one or two things
    if code.strip().lower() == 'typo' :
        # do not assume the user did it right
        orig = rest[0] if len(rest) else '?'
        corr = rest[1] if len(rest)>1 else '?'
        msg = '<ins class="correction" title="Original: {}">{}</ins>'.format( orig, corr )
    else :
        # if not [typo: assume a translieration e.g. [Greek:biblio:βιβλίο] or
        # perhaps [Cyrillic:kinga:книга] -- or just [Greek:biblio], no UTF.
        xlit = rest[0] if len(rest) else '?'
        if len(rest)>1 :
            unicode = rest[1]
            msg = '<span title="{}:{}">{}</span>'.format( code, xlit, unicode )
        else:
            msg = '<span title="{}">{}</span>'.format( code, xlit )
    BODY.writeLine(msg)

def do_link( ttext, lnum ) :
    global BODY
    [ visible, target ] = ttext.split(':')
    BODY << '<a href="#{}">{}</a>'.format( target, visible )

ACTIONS = {
    XU.TokenCodes.ITAL_ON   : ('t', None) ,
    XU.TokenCodes.ITAL_OFF  : ('t', None) ,
    XU.TokenCodes.BOLD_ON   : ('t', None) ,
    XU.TokenCodes.BOLD_OFF  : ('t', None) ,
    XU.TokenCodes.SCAP_ON   : ('c', '<span class="smcap">') ,
    XU.TokenCodes.SCAP_OFF  : ('c', '</span>') ,
    XU.TokenCodes.SPAN_ON   : ('t', None) ,
    XU.TokenCodes.SPAN_OFF  : ('t', None) ,
    XU.TokenCodes.DICT_ON   : ('z', None),
    XU.TokenCodes.DICT_OFF  : ('z', None),
    XU.TokenCodes.SUP       : ('l', lambda ttext : '<sup>' + ttext + '</sup>' ) ,
    XU.TokenCodes.SUB       : ('l', lambda ttext : '<sub>' + ttext + '</sub>' ) ,
    XU.TokenCodes.FNKEY     : ('f', do_fnkey ) ,
    XU.TokenCodes.BRKTS     : ('f', do_brkts ) ,
    XU.TokenCodes.LINK      : ('f', do_link ) ,
    XU.TokenCodes.TARGET    : ('l', lambda ttext : '<a id="{}"></a>'.format( ttext ) ) ,
    XU.TokenCodes.PLINE     : ('l', lambda ttext : '  ({})'.format(ttext) ) ,
    XU.TokenCodes.SPACE     : ('t', None) ,
    XU.TokenCodes.WORD      : ('t', None) ,
    XU.TokenCodes.PUNCT     : ('t', None) ,
    XU.TokenCodes.OTHER     : ('t', None)
    }

def trans_line( text, lnum, linebreak='\n' ):
    global BODY, FNKEYS

    izer = XU.tokenize( text )
    for (tcode, ttext) in izer :
        (x, action) = ACTIONS[ tcode ]
        if x == 't' : # most common case
            BODY << ttext
        elif x == 'c' : # copy a literal
            BODY << action
        elif x == 'l' : # expression on ttext
            BODY << action(ttext)
        elif x == 'f' : # call a function
            action( ttext, lnum )
        # else: pass # do nothing for this one
     # finish the line
    BODY << linebreak

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# This function takes the given First/Left/Right values and composes the
# CSS to implement them. The actual CSS is saved in FLR_CLASSES, keyed to
# a class-name of the form "fnlnrn". The class-name is returned so the
# caller can use it in a class= attribute. If the F/L/R are all zero,
# return a null string.
def indent_by_ems(n):
    #return int( round( 100 * ( n/75 ) ) )
    return int(round(n/2))

def make_flr( F, L, R ) :
    global FLR_CLASSES
    if 0 == F+L+R : return ''
    class_name = 'f{}_l{}_r{}'.format(F,L,R)
    if not class_name in FLR_CLASSES :
        FLR_CLASSES[ class_name ] = ( indent_by_ems(F-L), indent_by_ems(L), indent_by_ems(R) )
    return class_name

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# The translate() function. Just like the skeleton, at the heart is a dict
# of actions which are either string expressions or callable references.
#
# Because of the peculiarities of Python scope rules -- there is no such
# thing as a "relative global", a variable is either local to its innermost
# scope or fully global -- the following status switches have to be global
# to the whole function body.
#
# Usually a paragraph is just a paragraph (S. Freud). However, in a /U list
# section it is <li>, and in a heading, <h2> or <h3>. The different sections
# diddle with this global to change what open_para() and close_para() write.

PARA_TEXT = 'p'

# Are we in a poem? This affects processing of lines.
IN_POEM = False

# Starting footnote? Skip the first OPEN_PARA of the note, it is written
# by the open_fnote() code.
STARTING_FNOTE = False

# Class to give the next OPEN_PARA. Most paras get no class= but this is set
# for sidenotes and illustrations.
PARA_CLASS = None

# In a poem, have we started a stanza <div>? Should we?
IN_STANZA_DIV = False

# Values collected in OPEN_TABLE, used in table lines
WIDTHS = [] # width style string for each cell in ROW 1
ALIGNS = [] # align style string for each cell
ROW = 0 # current row
CELL = 0 # current cell

def translate( eventizer ) :
    global BODY, PAGES
    global IN_POEM, STARTING_FNOTE, PARA_CLASS, IN_STANZA_DIV

    # do_page notes the cpos in the PAGES list, and generates an anchor. If
    # this gets called at all, there must be info in the list.
    def do_page( ) :
        global PAGES

        PAGES[ stuff[ 'page' ] ] = BODY.cpos()
        folio = stuff['folio'] # null string if action is OMIT
        if folio : # is not omitted
            BODY << '\n<span class="pagenum"><a id="Page_{0}">[{0}]</a></span>\n'.format( folio )

    def open_para( ):
        global STARTING_FNOTE, PARA_TEXT, PARA_CLASS

        if STARTING_FNOTE :
            # the opening <p> is in the output of OPEN_FNOTE
            STARTING_FNOTE = False
            return
        if PARA_CLASS :
            # paragraph needs a class
            markup = '<{} class="{}">'.format(PARA_TEXT, PARA_CLASS)
        else :
            markup = '<{}>'.format( PARA_TEXT )
        BODY << markup

    def close_para( ):
        global PARA_TEXT
        markup = '</{}>'.format( PARA_TEXT )
        BODY.writeLine( markup )

    # To open a head, just set PARA_TEXT to h2 or h3. All paragraphs in the
    # head (there is normally only the one) will be <h2-3>..</h2-3>
    # In the unusual case of a Chapter head with multiple paragraphs, each
    # will be an H2, which is easy for the user to spot and change.
    def open_head( head ) :
        global PARA_TEXT
        PARA_TEXT = head

    def close_head( head ) :
        global PARA_TEXT
        PARA_TEXT = 'p'

    # Enclose sidenote in div class sidenote. A normal <p> goes inside it.

    def open_snote() :
        BODY.writeLine( '<div class="sidenote">' )

    def close_snote() :
        BODY.writeLine( '</div>' )

    # open_noflow sets up a noflow, center or right section. It sets margins
    # based on the F and R margin values (Left: is not significant in a
    # no-reflow section). The style argument, if not omitted, must be a CSS
    # property complete with semicolon, e.g. 'text-align:left;'

    def open_noflow( style='' ) :
        global BODY

        BODY << '<div'
        flr_class = make_flr( stuff['F'], stuff['F'], stuff['R'] )
        css = 'white-space:pre;' + style
        BODY << ' style="{}"'.format(css)
        if flr_class :
            BODY << ' class="{}"'.format(flr_class)
        BODY << '>\n'

    def close_noflow( ) :
        global IN_NO_REFLOW

        BODY << '</div>\n' # close the div

    # open_list starts a /U list section. Paras will be list items. The F/L/R
    # values given by the user are ignored; they are only appropriate for
    # ASCII display.

    def open_list( ) :
        global PARA_TEXT
        PARA_TEXT = 'li'
        BODY.writeLine( '<ul>' )

    def close_list( ) :
        global PARA_TEXT
        PARA_TEXT = 'p'
        BODY.writeLine( '</ul>' )

    # open_poem starts a poem with appropriate margins. We are discarding the
    # old Guiguts LYNX-compatible span-per-line markup and just making each
    # line a paragraph:
    #  <div class='poetry' style='
    #              margin-left:based on L;
    #              text-indent:negative based on F-L ;
    #              margin-right:based on R;'>
    #  <div class='stanza'> at the start and after any blank line
    #  <p class='iN'>line with 2N leading spaces</p>

    def open_poem( ):
        global IN_STANZA_DIV, IN_POEM

        flr_class = make_flr(  stuff['F'], stuff['L'], stuff['R']  )

        BODY << '\n<div class="poem'
        if flr_class :
            BODY << ' '+flr_class
        BODY << '">\n'

        IN_STANZA_DIV = False
        IN_POEM = True
    #
    # Process one poetry line:
    #
    # If the line is empty and we are in a stanza, end the stanza div.
    #    n.b. assume that there will never be a line number on a blank line?
    #
    # Else it is not empty. If we are not in a stanza, start the div.
    #
    # Determine its indent in ems and generate the paragraph start.
    # Note the indent value for final CSS.
    #
    # Process the line through trans_line, which handles any line number
    # by putting it in parens at line-end.
    #
    # Generate the paragraph end.
    #
    def do_poem_line( text, lnum ) :
        global POEM_EMS, IN_STANZA_DIV

        if 0 == len( text.strip() ) : # empty line
            if IN_STANZA_DIV :
                BODY << '</div>\n'
                IN_STANZA_DIV = False
        else : # not an empty line
            if not IN_STANZA_DIV :
                BODY << '<div class="stanza">\n'
                IN_STANZA_DIV = True
            ems = round( ( len( text )-len( text.lstrip() ) ) / 2 )
            if ems > 0 :
                POEM_EMS.add( ems )
                BODY << '<p class="i{}">'.format(ems)
            else :
                BODY << '<p>'
            trans_line( text.strip(), lnum, linebreak='</p>\n' )
    #
    # close_poem: close stanza if any, close poem div, set IN_POEM.
    def close_poem( ) :
        global IN_STANZA_DIV, IN_POEM

        if IN_STANZA_DIV :
            BODY << '</div>'
        BODY.writeLine( '</div>' )
        IN_POEM = False

    # Open a block quote, respecting the user's F/L/R indents. Note that
    # the CSS def for blockquote sets some default margins, but if there
    # is an F/L/R it overrides that.
    #
    # There is no close_quote function, it's just a string.

    def open_quote( ) :
        global BODY

        flr_class = make_flr(  stuff['F'], stuff['L'], stuff['R']  )
        BODY << '<blockquote'
        if flr_class :
            BODY << ' class="{}"'.format(flr_class)
        BODY.writeLine( '>' )

    # open_image builds an <img> statement from the filenames if they were
    # provided. The image markup used differs from the old GG. Set up the
    # paragraphs in it to be marked with a class='caption' although this
    # (from the css cookbook) is really not needed because they are inside
    # <div class='image'> and can be styled with a ".image p {}" selector.
    #
    # Unfortunately cannot build an alt="" string in the img because
    # the text for that would come from the first line, and that
    # doesn't appear until the next LINE after the next OPEN_PARA.

    def open_image( ) :
        global PARA_CLASS

        PARA_CLASS = 'caption'
        BODY << '<div class="image">\n'
        preview = XU.flatten_line(text)
        if stuff['image'] :
            if stuff['hires'] :
                BODY << '  <a href="images/{}">\n  '.format( stuff['hires'] )
            BODY << '  <img src="images/{0}"\n    alt="{1}" title="{1}"\n'.format(
                stuff['image'], preview )
            if stuff['hires'] :
                BODY << '    />\n</a>\n'
            else :
                BODY << '  />\n'

    def close_image( ) :
        global PARA_CLASS

        PARA_CLASS = None
        BODY.writeLine( '</div>' )

    # open_fnote generates the GG code:
    #
    # <div class="footnote">
    # <p>
    #   <a id="Footnote_X"></a>
    #   <a href="#FNanchor_X"><span class="label">[X]</span></a>
    #
    # The problem here is that we need to generate the <p> here, not on the
    # upcoming OPEN_PARA event. So we have a kludgy status switch.
    # Also, check for an undefined key.

    def open_fnote( ):
        global STARTING_FNOTE, FNKEYS

        STARTING_FNOTE = True
        BODY << '<div class="footnote">\n'
        key = stuff['key']
        if not key in FNKEYS :
            BODY << '\n<b>!!Undefined Footnote key {} at line {}!!</b>\n'.format( key, lnum )
        BODY << '<p><a id="Footnote_{}"></a>'.format( key )
        BODY << '<a href="#FNanchor_{0}"><span class="label">[{0}]</span></a>\n'.format( key )

    # open_table starts a table including figuring out column WIDTHS and
    # alignments. stuff['columns'] has some info for us. We save CSS width
    # properties in WIDTHS. They are applied on the first ROW only. H/V
    # alignments, if any, are saved in ALIGNS and applied on every cell.

    def open_table( ) :
        global ROW, CELL, WIDTHS, ALIGNS

        WIDTHS = []
        ALIGNS = []
        ROW = 0
        CELL = 0
        for (chars, h, v) in stuff['columns'] :
            WIDTHS.append( 'width:{}%;'.format( indent_by_ems( chars ) ) )
            style = ''
            if h : # is not None,
                if h[0] == 'r' :
                    style = 'text-align:right;'
                elif h[0] == 'c' :
                    style = 'text-align:center;'
                else:
                    style = 'text-align:left;'
            if v : # is not None,
                if v[0] == 'T' :
                    style += 'vertical-align:top;'
                elif v[0] == 'B' :
                    style += 'vertical-align:bottom;'
                else:
                    style += 'vertical-align:center;'
            ALIGNS.append( style )
        BODY << '\n<table>\n' # put a blank line above table

    # At the start of a ROW, increment the ROW # and reset the column #.
    def open_ROW( ) :
        global ROW, CELL

        ROW += 1
        CELL = 0
        BODY << '\n  <tr>\n'

    # At the start of a CELL, generate the style info from WIDTHS & ALIGNS
    def open_CELL( ) :
        global ROW, WIDTHS, ALIGNS, CELL

        style = ''
        if ROW == 1 :
            style += WIDTHS[ CELL ]
        style += ALIGNS[ CELL ]
        if style : # has anything in it,
            style = ' style="{}"'.format(style)
        BODY << '    <td{}>'.format(style)
        CELL += 1

    # The following dict acts as a computed go-to, distributing
    # each event code to an action that deals with it.

    actions = {
        XU.Events.LINE          : lambda : do_poem_line( text, lnum ) if IN_POEM else trans_line( text, lnum ) ,
        XU.Events.OPEN_PARA     : open_para ,
        XU.Events.CLOSE_PARA    : close_para ,
        XU.Events.OPEN_NOFLOW   : lambda : open_noflow( ) ,
        XU.Events.CLOSE_NOFLOW  : close_noflow ,
        XU.Events.OPEN_CENTER   : lambda : open_noflow( 'text-align:center;' ) ,
        XU.Events.CLOSE_CENTER  : close_noflow ,
        XU.Events.OPEN_RIGHT    : lambda : open_noflow( 'text-align:right;', ) ,
        XU.Events.CLOSE_RIGHT   : close_noflow ,
        XU.Events.OPEN_HEAD2    : lambda : open_head( 'h2' ) ,
        XU.Events.CLOSE_HEAD2   : lambda : close_head( 'h2' ) ,
        XU.Events.OPEN_HEAD3    : lambda : open_head( 'h3' ) ,
        XU.Events.CLOSE_HEAD3   : lambda : close_head( 'h3' ) ,
        XU.Events.OPEN_POEM     : open_poem ,
        XU.Events.CLOSE_POEM    : close_poem ,
        XU.Events.OPEN_QUOTE    : open_quote ,
        XU.Events.CLOSE_QUOTE   : '</blockquote>\n',
        XU.Events.OPEN_LIST     : open_list ,
        XU.Events.CLOSE_LIST    : close_list ,
        XU.Events.OPEN_ILLO     : open_image ,
        XU.Events.CLOSE_ILLO    : close_image ,
        XU.Events.OPEN_SNOTE    : open_snote ,
        XU.Events.CLOSE_SNOTE   : close_snote ,
        XU.Events.OPEN_FNOTE    : open_fnote ,
        XU.Events.CLOSE_FNOTE   : '</div>\n' ,
        XU.Events.PAGE_BREAK    : do_page ,
        XU.Events.T_BREAK       : '<hr style="width:30%;margin:0.5em,auto,0.5em,auto;" />',
        XU.Events.OPEN_FNLZ     : '<div class="footnotes">\n',
        XU.Events.CLOSE_FNLZ    : '</div>\n',
        XU.Events.OPEN_TABLE    : open_table ,
        XU.Events.OPEN_TROW     : open_ROW ,
        XU.Events.OPEN_TCELL    : open_CELL ,
        XU.Events.CLOSE_TCELL   : '    </td>\n',
        XU.Events.CLOSE_TROW    : '  </tr>\n',
        XU.Events.CLOSE_TABLE   : '</table>\n\n',

        }

    for (code, text, stuff, lnum) in eventizer :
        action = actions[ code ]
        if isinstance( action, str ) :
            BODY << action
        else :
            action()

    return True


# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# finalize(): Add any poem indents and F/L/R classes to the CSS and append
# them to the prolog.
#
# Update the page breaks if any.
#
# Put </body></html> in epilog

def finalize() :
    global PROLOG, POEM_EMS, FLR_CLASSES, PAGES, EPILOG

    if len( POEM_EMS ) :
        # Some poetry indents were noted. Generate matching CSS. The statement
        # for each value of indent is
        #   .stanza .iN { margin-left:Nem;} for the count of ems N
        for em in sorted( POEM_EMS ) :
            PROLOG.writeLine(
                '.stanza .i{0} {{ margin-left:{0}em; }}'.format( em )
            )

    if len( FLR_CLASSES ) :
        # Some F/L/R classes were encountered; write their CSS. make_flr()
        # has saved a triple (T,L,R) (text-, left-, and right-indent) as
        # counts of ems, keyed by the classname. Convert those to two lines,
        #    .classname { padding-left:L; right-margin:M }
        #    .classname p { text-indent:T; }
        #
        for ( class_name, (T, L, R) ) in FLR_CLASSES.items() :
            PROLOG.writeLine(
                '.{} {{ padding-left:{}em; margin-right:{}em; }}'.format(class_name, L, R)
                )
            PROLOG.writeLine(
                '.{} p {{ text-indent:{}em; }}'.format(class_name, T)
                )

    PROLOG << CSS_CLOSE # finish the prolog

    if PAGES :
        offset = PROLOG.cpos()
        for j in range( len( PAGES ) ) :
            PAGES[j] += offset

    EPILOG << '\n\n</body>\n</html>\n'

    return True

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# HTML and CSS boilerplate. This is based on the html header file that was
# distributed with PPQT V1 -- which in turn was based on the CSS Cookbook
# in the DP Wiki -- which in turn was based on the old GuiGuts practice.
#
# DTD for XHTML Strict
#
DTD = '''<!DOCTYPE html
PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
'''
#
# HTML_START has charset UTF-8 and places to insert title and author.
#
HTML_START = '''
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
  <head>
    <meta http-equiv="Content-Type" content="text/html;charset=UTF-8" />
    <meta http-equiv="Content-Style-Type" content="text/css" />
    <title>
      The Project Gutenberg eBook of {} by {}.
    </title>
'''
#
# CSS defines only the classes that are actually used in the translation.
# Many other useful classes can be found in the CSS Cookbook in the Wiki.
# Also, many of these definitions have optional items that you enable
# by commenting or un-commenting parts.
#

CSS_START = '''
    <style type="text/css">
/*<![CDATA[  XML blockout */
<!--
/* ************************************************************************
 * Different browsers have different defaults when loading a new page. The
 * following CSS Reset makes all browsers start out with the same properties.
 * See meyerweb.com/eric/tools/css/reset/ License: none (public domain)
 * ********************************************************************** */
html, body, div, span, applet, object, iframe,h1, h2, h3, h4, h5, h6, p,
blockquote, a, abbr, acronym, address, big, cite, code, del, dfn, em,
img, ins, kbd, q, s, samp, small, strong, var, u,
dl, dt, dd, ol, ul, li, fieldset, form, label, legend, table,
caption, tbody, tfoot, thead, tr, th, td, article, aside, canvas, details,
embed, figure, figcaption, footer, header, hgroup,  menu, nav, output,
ruby, section, summary, time, mark, audio, video {
	margin: 0;
	padding: 0;
	border: 0;
	font-size: 100%;
	font-weight: normal;
	font: inherit;
	vertical-align: baseline;
}
article, aside, details, figcaption, figure, footer, header, hgroup, menu,
nav, section {	display: block;  }/* HTML5 display-role for older bROWsers */
body {	line-height: 1; }
blockquote, q { quotes: none; }
blockquote:before, blockquote:after, q:before, q:after {
	content: ''; content: none; }
table { border-collapse: collapse; border-spacing: 0; }
/* End of CSS Reset */
/* ************************************************************************
 * set the indention, spacing, and leading for ALL paragraphs
 * ********************************************************************** */
p {
	margin-top: 1em;	/* inter-paragraph space */
	margin-bottom: 0;	/* use only top-margin for spacing */
	text-align: left;	/* some e-readers don't justify well */
	text-indent: 0;		/* first-line indent, could be 0em */
}
/* ************************************************************************
 * Head 2 is for chapter heads, h3 for sub-heads.
 * ********************************************************************** */
h2 { text-align:center; font-size: 150%; }
h3 { text-align:center; font-size: 125%; }
/* ************************************************************************
 * Small-cap font class, for use in spans.
 * ********************************************************************** */
.smcap {font-variant: small-caps;}
/* ************************************************************************
 * Styles for images and captions. All paras directly within an image div
 * get class='caption'.
 * ********************************************************************** */
div.image { /* style the div that contains both image and caption */
	border: 1px solid black;
	text-align: center; /* centers the image */
}
img {   /* style the default inline image here, e.g. */
	/* border: 1px solid black; a thin black line border.. */
	/* padding: 6px; ..spaced a bit out from the graphic */
}
p.caption { /* style the paragraphs of caption text */
	margin-top: 0;		/* snuggled up to its image */
	text-align: left; /* optional, override :center from the div */
}
/* ************************************************************************
 * Styling tables and their contents:
 *   automatic center for header and footer cells.
 * ********************************************************************** */
table { /* these affect all <table> elements */
	margin-top: 1em;	/* space above the table */
	empty-cells: show;	/* remove need for nbsp's in empty cells */
}
td, td > p { /* style all text inside body CELLs */
	text-align: left;	/* in case table in "center" div */
}
thead td, tfoot td {	/* header/footer CELLs: center & bold */
	text-align: center;
	font-weight: bold;
}
td.c { text-align:center; } /* align text in table cells */
td.r { text-align:right; }
/* ************************************************************************
 * Style the blockquote tag inset left and right. Note: many block quotes
 * get a class based on the First/Left/Right values that overrides these.
 * This default is based on F:2 L:2 R:2, 2/75 --> 2.66% rounding to 3%
 * ********************************************************************** */
blockquote {
	margin-left: 3%;
	margin-right: 3%;
}
/* ************************************************************************
 * Style the rule used for a thought-break. Centered, 30% width, space
 * above and below. Note that <p> has 1em top margin. Note that the only
 * way to center a rule, margin-left/right:auto, is stripped out by EPUB
 * conversion, so in an e-reader this rule is left-aligned.
 * ********************************************************************** */
hr.tb {
	width:30%;
	margin-top:1em;
	margin-bottom: 0em;
	margin-left: auto;
	margin-right: auto;
}
/* ************************************************************************
 * [Sidenote:stuff] becomes <div class="sidenote"><p>stuff</p></div>.
 * For HTML you could consider "floating" a sidenote to the right. The code
 * to do so is commented out because floats aren't allowed in EPUB.
 * ********************************************************************** */
.sidenote {
/* the following style the look of the sidenote box: */
	width: 10em;		/* ..fixed width, */
	border: 1px dotted black; /* ..thin dotted border */
	/* Un-comment the following for XML/HTML only (no floats in EPUB) */
	/* float: right;		float style: uncomment for HTML */
	/* margin-top: 0;		top even with following <p>'s top */
	/* margin-left: 6px;	..ensure space away from body text */
}
/* the following style the look of the text inside the box: */
.sidenote p {
	margin-top: 0.1em;	/* snuggle up to top of box */
	font-size: smaller;	/* could be font-size:x-small */
	text-indent: 0;		/* no para indent */
	text-align: center;	/* center text in 10em box */
	line-height: 1.1em;	/* tight leading if it folds */
}
/* ************************************************************************
 * Footnotes and footnote anchors
 * <div class="footnotes"> around a block of footnotes
 * <div class="footnote"> around any one footnote's label and text
 * <span class="fnlabel"> around [nn] in front of footnote text
 *     - used here to float entire label out into left margin
 *     - style ".footnote a" to change look of label link
 * <a ...class="fnanchor"> around [nn] in the body text
 * ********************************************************************** */
div.footnotes {
	/* nothing special, could have a border */
}
/* Style the label and all text within one footnote */
.footnote {
	/*font-size: smaller;  optional smaller font than body */
}
/* Style the [nn] label within the footnote separately */
.fnlabel {
	/* nothing special beyond normal link decoration */
}

/* Style the look of the [nn] Anchor in the body text */
.fnanchor {
	font-size: small;	/* whatever the e-reader thinks is small */
	text-decoration: none;	/* no underscore, blue color is enough */
	vertical-align: 0.33em;	/* raise up from baseline a bit */
}
/* ************************************************************************
 * The translator (see do_brkts()) replaces a corrected typo with:
 *  <ins class="correction" title="Original: typu">typo</ins>
 * NOTE e-readers do not do pop-up titles. So the "Original: XXX" title
 * will never be seen by the e-reader user. For that reason the
 * border-bottom style should only be used in HTML, where it alerts the
 * reader that there is something going on with this word. It should be
 * commented out for EPUB conversion and the correction looks normal.
 * ********************************************************************** */
ins.correction {
	text-decoration:none; /* replace default underline.. */
	/* border-bottom: thin dotted gray; ..with delicate gray line */
}
/* ************************************************************************
 * Style visible page numbers, as described in
 *   www.pgdp.net/wiki/User:Laurawisewell/Content_Method_for_HTML_pagenums
 * (this replaces the old Guiguts code for pagenums).
 *
 * Pagenum is inserted in text at pagebreaks using:
 * <span class="pagenum" title="FOLIO">&nbsp;</span><a id="Page_FOLIO"></a>
 * where FOLIO is what you set with the Pages panel!
 * ********************************************************************** */
.pagenum  {
        position: absolute;
        right: 0;
        font-size: 12px;
        font-weight: normal;
        font-variant:normal;
        font-style:normal;
        text-indent: 0em; text-align:right;
        color: silver;
        background-color: #FFF;
    }
span[title].pagenum:after { content: "[" attr(title) "] "; }
a[name] { position:absolute; }      /* Fix Opera bug  */
/* ************************************************************************
 * Styling poetry, Guiguts-compatible class names
 * <div class="poem"> around entire poem or canto -- any stanza number or
 *    canto title goes outside the poem div as <h3>.
 * <div class="stanza"> around each stanza, even if only one.
 * <p>..</p> around every non-indented line.
 * <p class="i?">..</p> around each indented line. These classes are
 * generated at the end of the styles.
 *
 * Note the translator puts a poem line number at the end of its line
 * in parentheses. No attempt to float it or put it in the margin nor to
 * style it with smaller font or anything.
 * ********************************************************************** */
/* Style the entire poem or canto. */
div.poem {
	text-align:left; 	/* make sure no justification attempted */
	margin-left:3%;		/* inset a bit from the left */
}
.poem .stanza {		/* set vertical space between stanzas */
	margin-top: 1em;
}
/* Style any single poem line which is in <p>...</p> */
.stanza p {
	margin-top: 0.25em;	/* spacing between lines in a stanza */
	line-height: 1.2em;	/* only used if a long line "folds" */
        /* following is needed to get text-indent from div.poem */
	text-indent: inherit;
}
/* Here follows generated lines of the form:
 *     .stanza .iX {margin-left:Xem;}
 * with one class for each unique poem line indent used, i1 to i?.
 *
 * Also generated lines of the form:
 * .fnlnrn { margin-left:L%; text-indent:F%; margin-right:R%; }
 * where the L, F and R percentages are based on the F/L/R values
 * of a /Q block, for example given /Q F:4 Left:2 Right:2,
 * .f4l2r2 { margin-left:3%; text-indent:3%; margin-right:3%; }
 */
'''

#
# The generated poem indent classes are followed by this:

CSS_CLOSE = '''
-->
/* XML end  ]]>*/
    </style>
  </head>
<body>
'''

