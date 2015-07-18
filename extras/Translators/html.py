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
                HTML Translator

This file exists as extras/Translators/html.py. It implements a DP-format to
HTML translation using the Translator API.

The boilerplate text for the HTML header and CSS style sheet is at the end of
the module as triple-quoted literals named DTD and CSS.

TODO:
  fix kludge in tokenize
  sc->smcap
  markup tokens?
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
    global PROLOG, BODY, EPILOG, PAGES, FNKEYS, POEM_EMS

    # clear lists that may have junk from a prior translation
    POEM_EMS = set()
    FNKEYS = set()

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
    XU.TokenCodes.PLINE     : ('z', None) , # cannot occur, do_poem_line eats it
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

# In a no-flow section? Affects how text lines are terminated.
IN_NO_REFLOW = False

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
    global IN_POEM, STARTING_FNOTE, IN_NO_REFLOW, PARA_CLASS, IN_STANZA_DIV

    # Converts a character length on a 75-char line to a percent margin.
    def pct( n ) :
        return int( 100 * (n / 75) )

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
    # based on the F and R margin values. The style argument, if not omitted,
    # must be a CSS property complete with semicolon, e.g. 'text-align:left;'

    def open_noflow( style='' ) :
        global IN_NO_REFLOW

        marge = ''
        if stuff['F'] : # is not 0
            marge = 'margin-left:{}%;'.format( pct( stuff['F'] ) )
        if stuff['R'] :
            marge += 'margin-right:{}%;'.format( pct( stuff['R'] ) )
        css = ''
        if style or marge :
            css = 'style="{}{}"'.format( marge, style )
        BODY << '<div {}>\n'.format( css )
        IN_NO_REFLOW = True

    def close_noflow( ) :
        global IN_NO_REFLOW

        BODY << '</div>\n' # close the div
        IN_NO_REFLOW = False

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

        L = pct( stuff['L'] )
        F = L - pct( stuff['F'] )
        css = 'margin-left:{}%;text-indent:{}%;'.format( L, F )
        if stuff['R'] :
            css += 'margin-right:{}%;'.format( pct( stuff['R'] ) )
        BODY << '\n<div class="poetry" style="{}">\n'.format( css )
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
    # If it has a line number, extract and format that, so the span
    # for the line number precedes the line text.
    #
    # Determine its indent in ems and generate the paragraph start.
    # Note the indent value for final CSS.
    #
    # Process the line through trans_line.
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
            plnum = XU.poem_line_number( text )
            if plnum :
                BODY << '<span class="linenum">{}</span>'.format( plnum )
                text = XU.poem_line_strip( text )
            ems = round( (len( text ) - len( text.lstrip() )) / 2 )
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
        css = ''
        F = stuff['F']
        L = stuff['L']
        R = stuff['R']
        if F :
            css += 'text-indent:{}%;'.format( pct( F-L ) )
        if L :
            css += 'margin-left:{}%;'.format( pct( L ) )
        if R :
            css += 'margin-right:{}%;'.format( pct( R ) )
        if css :
            BODY.writeLine( '<blockquote style="{}">'.format( css ) )
        else :
            BODY.writeLine( '<blockquote>' )

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
            WIDTHS.append( 'width:{}%;'.format( pct( chars ) ) )
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
        XU.Events.LINE          : lambda : do_poem_line( text, lnum ) if IN_POEM \
                                           else trans_line( text, lnum, linebreak='<br />\n' ) if IN_NO_REFLOW \
                                           else trans_line( text, lnum ) ,
        XU.Events.OPEN_PARA     : open_para ,
        XU.Events.CLOSE_PARA    : close_para ,
        XU.Events.OPEN_NOFLOW   : open_noflow ,
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
# finalize(): Add any poem indents to the CSS and append it to the prolog.
#
# Update the page breaks if any.
#
# Put </body></html> in epilog

def finalize() :
    global POEM_EMS, PAGES

    if len( POEM_EMS ) :
        # Some poetry indents were noted. Generate matching CSS.
        for em in sorted( POEM_EMS ) :
            PROLOG.writeLine( '.stanza .i{0} {{margin-left:{0}em;}}'.format( em ) )
    PROLOG << CSS_CLOSE # finish the prolog

    if PAGES :
        for j in range( len( PAGES ) ) :
            PAGES[j] += PROLOG.cpos()

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
DTD = '''
<!DOCTYPE html
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
 * Different bROWsers have different defaults when loading a new page. The
 * following CSS Reset makes all bROWsers start out with the same properties.
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
 * set the body margins to allow whitespace along sides of window - use
 * width rather than margin-right to get IE5 to behave itself.
 * ********************************************************************** */
body { margin-left:5%; width:90%; /* == margin-right:5% */ }
/* ************************************************************************
 * set the indention, spacing, and leading for ALL paragraphs
 * ********************************************************************** */
p {
        margin-top: 1em; 	/* inter-paragraph space */
	margin-bottom: 0;	/* use only top-margin for spacing */
	line-height: 1.4em;	/* generous interline spacing */
}
/* ************************************************************************
 * Style all paragraphs of open text (not quotes, table CELLs etc)
 * ********************************************************************** */
body > p {
	text-align: justify; /* or left?? */
	text-indent: 2em;	/* first-line indent, could be 0em */
}
/* ************************************************************************
 * suppress first-line-indent on paragraphs that following heads and
 * on paragraphs in table data CELLs
 * ********************************************************************** */
h2+p, h3+p, h4+p, td, td > p { text-indent: 0; }
/* ************************************************************************
 * Set tighter spacing for list item paragraphs
 * ********************************************************************** */
dd, li, li > p {
	margin-top: 0.25em;
	margin-bottom:0;
	line-height: 1.2em; /* leading a bit tighter than p's */
}
/* ************************************************************************
 * Small-cap font class, for use in spans.
 * ********************************************************************** */
.smcap {font-variant: small-caps;}
/* ************************************************************************
 * Head 2 is for chapter heads.
 * ********************************************************************** */
h2 {
	margin-top:3em;			/* extra space above.. */
	margin-bottom: 2em;		/* ..and below */
	clear: both;			/* don't let sidebars overlap */
	font-size: 133%;		/* larger font than body */
	/* font-weight: bold;      change these to match book */
	/* letter-spacing: 3px;    older books often have loose headers */
	/* text-align:center;	   left-aligned by default. */
}
/* ************************************************************************
 * Head 3 is for section heads, if any, or perhaps poem titles
 * ********************************************************************** */
h3 {
	margin-top: 2em;	/* extra space above but not below */
	clear: both;		/* don't let sidebars overlap */
	/* text-align:center;  left-aligned by default. */
	/* font-weight: bold;  match the original */
}
/* ************************************************************************
 * Styles for images and captions
 * ********************************************************************** */
img { /* style the default inline image here, e.g. */
	/* border: 1px solid black; a thin black line border.. */
	/* padding: 6px; ..spaced a bit out from the graphic */
}
p.caption {
	margin-top: 0; /* snuggled up to its image */
	font-size: smaller;
	/* font-style: italic; 		match style to orginal */
	/* font-variant: small-caps; ditto */
}
}
/* ************************************************************************
 * Styling tables and their contents:
 *   automatic center/bold for header and footer CELLs.
 *   use class="shade" to put gray background in a <tr> or a <td>.
 * ********************************************************************** */
table { /* these affect all <table> elements */
	margin-top: 1em;	/* space above the table */
	caption-side:		/* top; or */ bottom ;
	empty-CELLs: show;	/* remove need for nbsp's in empty CELLs */
}
td, td > p { /* style all text inside body CELLs */
	margin-top: 0.25em;	/* compact vertical.. */
	line-height: 1.1em;	/* ..spacing */
	font-size: 90%;		/* smaller than book body text */
	text-align: left;	/* left-align even if table in "center" div */
}
thead td, tfoot td {	/* header/footer CELLs: center & bold */
	text-align: center;
	font-weight: bold;
	/* background-color: #ddd;  optional: gray background */
}
td.c { text-align:center; } /* align text in table CELLs */
td.r { text-align:right; }  /* generated by PPQT table->html */

table .shade { /* class="shade" apply to <tr> or <td> */
	background-color: #ddd;
}
/* ************************************************************************
 * Style the blockquote tag and related elements:
 *  - inset left and right
 *	- one-point smaller font (questionable?)
 * ********************************************************************** */
blockquote {
	margin-left: 5%;
	margin-right: 5%;
	/*font-size: 90%;  optional: smaller font */
}
/* ************************************************************************
 * [Sidenote:stuff] becomes <div class="sidenote"><p>stuff</p></div>.
 * ********************************************************************** */
.sidenote {
/* the following style the look of the sidenote box: */
	width: 5em;			/* ..fixed width, */
	float: right;		/* ..float to the right, */
	margin-right: -4%;	/* ..exdented into body margin of 5% */
	margin-top: 0;		/* top even with following <p>'s top */
	margin-left: 6px;	/* ..ensure space away from body text */
	border: 1px dotted black; /* ..thin dotted border */
	padding: 0 0 0 4px; /* ..ease content out from left border */
	background-color: #ddd; /* ..optional pale tint */
}
/* the following style the look of the text inside the box: */
.sidenote p {
	font-size: smaller;	/* ..small text; could be font-size:x-small */
	/*color: #333;		 ..optional dark-gray text */
	text-indent: 0;		/* ..no para indent */
	text-align: right;	/* ..right align text in box */
	line-height: 1.1em;	/* tight vert. spacing */
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
 /* Style the look of the [nn] Anchor in the body text */
.fnanchor {
	font-size: 75%;		/* small - 2pts less than adjacent text */
	text-decoration: none;	/* no underscore, blue color is enough */
	vertical-align: 0.33em;	/* raise up from baseline a bit */
	/*background-color: #eee;  optional pale gray background */
}
/* Style the /F..F/ block with a border or a background color */
.footnotes {
	margin: 2em 1em 1em 1em;	/* set off from body */
	/*border: dashed 1px gray;	optional border */
	/*background-color: #EEE;	optional light background tint */
	/*padding: 0 1em 1em 1em; 	optional indent note text from border */
}
/* Style an optional header, e.g. "FOOTNOTES" within a footnote block */
.footnotes h3 {
	text-align:center;
	margin-top: 0.5em;
	font-weight:normal;
	font-size:90%;
}
/* Style the label and all text within one footnote */
.footnote {
	/*font-size: 90%;	optional make font 1-pt smaller than body */
}
/* Style the [nn] label separately from the footnote itself */
.fnlabel {
	/*float:left;	optional: float left of footnote text */
	text-align:left;	/* aligned left in span */
	width:2.5em;		/* uniform width of [1] and [99] */
}
/* Style any link within a footnote, in particular the [nn] which is a
   link back to the anchor. */
.footnote a {
	text-decoration:none; /* take the underline off it */
}
/* ************************************************************************
 * Mark corrected typo with:
 *  <ins class="correction" title="Original: typu">typo</ins>
 * ********************************************************************** */
ins.correction {
	text-decoration:none; /* replace default underline.. */
	border-bottom: thin dotted gray; /* ..with delicate gray line */
}
/* ************************************************************************
 * Style visible page numbers in right margin. Pagenum is inserted as
 * <span class='pagenum'> <a id="Page_FOLIO">[FOLIO]</a> </span>
 * where FOLIO is what you set with the Pages panel!
 * ********************************************************************** */
.pagenum { /* right-margin page numbers */
	/*visibility:hidden	uncomment to hide the page numbers */
	font-size:75%;		/* tiny type.. */
	color: #222;		/* ..dark gray.. */
	text-align: right;	/* ..right-justified.. */
	position: absolute;	/* out of normal flow.. */
	right: 0;		/* ..in the right margin.. */
	padding: 0 0 0 0 ;	/* ..very compact */
	margin: auto 0 auto 0;
	}
.pagenum a {/* when pagenum is a self-reference link (see text)... */
	text-decoration:none;	/* no underline.. */
	color:#444;		/* same color as non-link */
	}
.pagenum a:hover { color:#F00; }/* turn red when hovered */
/* ************************************************************************
 * Styling poetry, Guiguts-compatible class names
 * <div class="poem"> around entire poem -- title goes outside as <h2 or 3>
 * <div class="stanza"> around each stanza even if only one
 * <p class="i?">..</p> around each line
 * the span class i<n> is omitted for unindented lines; else <n> is 1/2
 *   the count of ascii spaces preceding the indented line.
 * ********************************************************************** */
div.poem { /* Style the entire poem */
	text-align:left; 	/* make sure no justification attempted */
	margin-left:5%;		/* inset a bit from the left */
	width:90%;		/* inset from the right, & fix IE6 abs.pos. bug */
	position: relative;	/* div is a container for .linenum positions */
}
.poem .stanza {		/* set vertical space between stanzas */
	margin-top: 1em;
}
.stanza p { /* style any one line */
	line-height: 1.2em;	/* set spacing between lines within stanza */
	margin-top: 0;		/* stanza provides vertical break */
}
/* Style poem line numbers, positioned far right or far left */
.stanza .linenum {
/* the following locate poem line numbers horizontally */
	position: absolute;	/* positioned out of text flow */
	top:auto;
	/*left: -2.5em; 		   ..in the LEFT margin, or.. */
	right: -2em;		/* ..in the RIGHT margin */
/* the following determine the look of poem line numbers */
	margin: 0;
	text-indent:0;
	font-size: 90%;		/* they are smaller */
	text-align: center;	/* centered in a space... */
	width: 2.5em;		/* ...about 3+ digits wide */
	color: #555; background-color: #eee; /* dark gray on light gray or */
	/* color: #fff; background-color: #777;  ..white on medium gray */
}
/* Here follows generated lines of the form:
 *     .stanza .i9 {margin-left:9em;}
 * one for each unique poem line indent used, i1 to i?.
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

