'''
   TRANSLATOR SKELETON

This file is a skeleton form of a PPQT2 Translator module.

You can use this as a the basis of a new Translator by filling out
the code framework below following the comments given.

'''

import xlate_utils as XU

MENU_NAME = 'Ppgen' # Translator's name in the menu

OPTION_DIALOG = [] # empty list = no options dialog

# Globals where initialize() stows stuff for later use

PROLOG = None
BODY = None
EPILOG = None
PAGES = []
FACTS = dict()

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# The initialize() function is called after the document has been parsed
# to save important information structures. It writes any opening stuff
# to the PROLOG file stream -- here, .dt and .h1 lines.
#

def initialize( prolog, body, epilog, facts, pages ) :
    global PROLOG, BODY, EPILOG, PAGES, FACTS, IN_TABLE, TABLE_ROW_DATA, IN_LL_USAGE
    PROLOG = prolog
    BODY = body
    EPILOG = epilog
    FACTS = facts # in case we think of any other use for them
    PAGES = pages
    IN_TABLE = False # clear residue of any prior translate call
    TABLE_ROW_DATA = []
    IN_LL_USAGE = []

    # Start the file with a display title command, based on the title and
    # author items in the facts dict. Follow it with the .h1 line.
    title = 'No Title Given?'
    author = 'Author Unknown?'
    for (key, value) in facts.items() :
        if key.lower().strip() == 'title' :
            title = value
        if key.lower().strip() == 'author' :
            author = value
    PROLOG.writeLine( '.dt The Project Gutenberg eBook of {}, by {}'.format(title, author) )
    PROLOG.writeLine( '.h1 title=' + title )
    PROLOG.writeLine( title )

    return True

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# The finalize() function is called when the translate() function returns
# success. It writes any needed boilerplate to PROLOG or EPILOG (in this
# case, neither) and updates the PAGES offset list to account for any
# data in PROLOG.
#

def finalize( ) :
    global PROLOG, BODY, EPILOG, PAGES

    # No boilerplate or stored messages to write

    # if the PAGES list is not empty, add PROLOG.cpos() to every item

    if PAGES :
        offset = PROLOG.cpos()
        for j in range( len( PAGES ) ) :
            PAGES[j] += offset

    return True

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
# The following are the action functions called from the translate() loop,
# in the order they are named in the actions dict.
#

# Status flag: the action code before the current one, for open_para
LAST_CODE = None
# Status flag: are we working in a table?
IN_TABLE = False
# When in a table, cell values for one row are collected here
TABLE_ROW_DATA = []
# Pushdown stack of .in/.ll status flags, see open_noflow, close_noflow
IN_LL_USAGE = []

# Process a LINE event. text is a line from a paragraph, a no-flow, a poem,
# or a table cell. Convert any in-line markup to Ppgen format. Not by
# coincidence, PPQT in-line markup is almost identical to Ppgen's. The only
# real difference is <id='target'> versus <target id='target'>. Use a regex
# replace to fix that. Pass everything else unchanged.
#
# If we are not in a table, just write the line to BODY with a newline after.
# In a table, this is a cell's content. We save it in TABLE_ROW_DATA for
# close_trow to write.
#

import regex # PPQT imports regex, so we know it is available.

rex_target = regex.compile( r'\<\s*id=' ) # matches <id=

def do_line( code, text, stuff ) :
    global BODY, IN_TABLE, TABLE_ROW_DATA

    # convert <id=whatever> to <target id=whatever>
    line_text = rex_target.sub( r'<target id=', text )

    # dispose of the converted line text
    if IN_TABLE :
        TABLE_ROW_DATA.append( line_text )
    else :
        BODY.writeLine( line_text )

# Open a paragraph. If the preceding action was CLOSE_PARA or closing any
# head, then emit a blank line. Otherwise, the preceding action was
# close of a noflow, quote, footnote or table and there's no need for
# another space.

def open_para( code, text, stuff ) :
    global BODY, LAST_CODE
    if LAST_CODE in ( XU.Events.CLOSE_PARA, XU.Events.CLOSE_HEAD2, XU.Events.CLOSE_HEAD3, XU.Events.T_BREAK ) :
        BODY << '\n'

# Open a /X.. or /C.. or /R.. or /P.. noflow section. In all four cases set
# left and right indents based on First and Right values. Use the code
# parameter to decide what kind of .nf line to write.
#
# Write a .in +F line when the First indent is nonzero. Write a .ll -R line
# when the Right indent is nonzero. Save a status tuple showing which lines
# we wrote. See close_noflow for its use.

def open_noflow( code, text, stuff ):
    global BODY, IN_LL_USAGE

    nf_line = '.nf c' if code == XU.Events.OPEN_CENTER else \
              '.nf r' if code == XU.Events.OPEN_RIGHT else \
              '.nf' # code is either OPEN_NOFLOW or OPEN_POEM

    left = stuff['F'] # for noflow, left margin is First indent
    right = stuff['R']
    do_left = left != 0
    do_right = right != 0

    if do_left  : BODY.writeLine( '.in +{}'.format(left) )
    if do_right : BODY.writeLine( '.ll -{}'.format(right) )
    IN_LL_USAGE.append( (do_left, do_right ) )
    BODY.writeLine( nf_line )

# Close a /X.., /C.., /R.. or /P.. section. All lines have been written.
# Just put out .in and .ll lines, if any were written, then the .nf- line.

def close_noflow( code, text, stuff ) :
    global BODY, IN_LL_USAGE

    (did_left, did_right) = IN_LL_USAGE.pop()
    BODY.writeLine( '.nf-' )
    if did_right : BODY.writeLine( '.ll' )
    if did_left  : BODY.writeLine( '.in' )

# Open a /Q..Q/ or /U..U/ section by indenting by the value of the L and R values.
# Sorry, no support for First: line indents. See Ppgen doc.
#
# Some code could be refactored out of open_/close_quote/noflow. If I cared.

def open_quote( code, text, stuff ):
    global BODY, IN_LL_USAGE
    left = stuff['L']
    right = stuff['R']
    do_left = left != 0
    do_right = right != 0
    if do_left  : BODY.writeLine( '.in +{}'.format(left) )
    if do_right : BODY.writeLine( '.ll -{}'.format(right) )
    IN_LL_USAGE.append( (do_left, do_right ) )

def close_quote( code, text, stuff ) :
    global BODY, IN_LL_USAGE

    (did_left, did_right) = IN_LL_USAGE.pop()
    if did_right : BODY.writeLine( '.ll' )
    if did_left  : BODY.writeLine( '.in' )

# Open the [Illustration: markup with or without filenames. Write one of:
#  .il (if no files)
#  .il file=xxx.png (if one file)
#  .il file=xxx.png link=yyy.jpg (if both files)
# In all cases follow with .ca on a new line.

def open_illo( code, text, stuff ):
    global BODY
    image = stuff['image']
    hires = stuff['hires']
    BODY << '.il'
    if image :
        BODY << ' fn=' + image
        if hires :
            BODY << ' link=' + hires
    BODY <<' w=77%\n.ca\n'

# Open a [Footnote X: markup, emitting .fn X. This will be followed by
# paragraph events, possibly quotes and noflows, who knows? Eventually we get
# the CLOSE_FNOTE event and write a .fn- line.

def open_fnote( code, text, stuff ):
    global BODY, PARA_NLS
    BODY.writeLine( '.fn {}'.format( stuff['key'] ) )

# Note a page boundary event in the PAGES list so PPQT can show the scan
# images while editing the translated file. Also enter the folio value in the
# document with .pn.

def note_page_break( code, text, stuff ):
    global PAGES, BODY
    # note position for PPQT page display in translated file
    PAGES[ stuff[ 'page' ] ] = BODY.cpos()
    # put a visible page-number directive in the output, if a visible folio
    folio = stuff['folio'] # null string means folio-action:omit
    if folio:
        BODY.writeLine( '.pn {}'.format(folio) )

# Handle the OPEN_TABLE event. Translate the PPQT column specs into the ppgen
# ones. The former is a list of lists, [ [width,h-letter,v-letter]...] and it
# is possible the h-letter is None. However the .ta column syntax does not
# allow a column with no h-letter, so translate None into "l" for
# left-aligned. .ta wants vertical align letters lowercase t/m/b, translate
# from PPQT's T/C/B.

def open_table( code, text, stuff ) :
    global BODY, IN_TABLE
    cell_spec = ''
    for [w, h, v] in stuff['columns'] :
        if h is None: h = 'l' # default to left-align if not given
        if v == 'T' : v = 't' # translate PPQT vertical aligns
        elif v == 'C' : v = 'm'
        elif v == 'B' : v = 'b'
        else: v = '' # v was None
        cell_spec += ' {}{}:{}'.format( h, v, w ) # e.g. " lC:25"
    BODY << '.ta'
    BODY.writeLine( cell_spec )
    IN_TABLE = True

# Upon the CLOSE_TROW event, concatenate the cell values (delivered as LINE
# events between OPEN_TCELL and CLOSE_TCELL events) into a single line with
# stile separators.

def close_trow( code, text, stuff ):
    global BODY, TABLE_ROW_DATA
    BODY.writeLine( '|'.join( TABLE_ROW_DATA ) )
    TABLE_ROW_DATA = []

# On CLOSE_TABLE, just write .ta-. This wouldn't need to be a function
# except we need to turn off IN_TABLE.

def close_table( code, text, stuff ):
    global BODY, IN_TABLE
    BODY.writeLine( '.ta-' )
    IN_TABLE = False

def translate( event_generator ) :
    global PROLOG, BODY, PAGES, LAST_CODE

    # The following dict acts as a computed go-to, distributing each event
    # code to an action that deals with it. An action can be None (not
    # defined yet, or nothing to do), or a string literal to be output to
    # BODY, or a callable to be called with the code, line-text, and stuff
    # values from the event.

    actions = {
        XU.Events.LINE          : ( do_line ) ,
        XU.Events.OPEN_PARA     : ( open_para ) , # maybe a newline, maybe not
        XU.Events.CLOSE_PARA    : ( None ) , # nothing after a para
        XU.Events.OPEN_NOFLOW   : ( open_noflow ) , # open no-fill .nf
        XU.Events.CLOSE_NOFLOW  : ( close_noflow ) , #close no-fill
        XU.Events.OPEN_CENTER   : ( open_noflow ) , # open no-fill .nf c
        XU.Events.CLOSE_CENTER  : ( close_noflow ) , #close no-fill
        XU.Events.OPEN_RIGHT    : ( open_noflow ) , # open no-fill .nf r
        XU.Events.CLOSE_RIGHT   : ( close_noflow ) , #close no-fill
        XU.Events.OPEN_HEAD2    : ( '.sp 4\n.h2\n') , # open chapter head
        XU.Events.CLOSE_HEAD2   : ( '\n' ) , # add second blank line after close-para
        XU.Events.OPEN_HEAD3    : ( '.sp 2\n.h3\n' ) , # open section head
        XU.Events.CLOSE_HEAD3   : ( None ) , # do nothing at end of H2 para
        XU.Events.OPEN_POEM     : ( open_noflow ) , # poem is just a .nf block
        XU.Events.CLOSE_POEM    : ( close_noflow ) , # close no-fill poem
        XU.Events.OPEN_QUOTE    : ( open_quote ) , # set .ll and .in
        XU.Events.CLOSE_QUOTE   : ( close_quote ) , # clear quote indenting
        XU.Events.OPEN_LIST     : ( open_quote ) , # treat as block quote
        XU.Events.CLOSE_LIST    : ( close_quote ) , # clear quote indenting
        XU.Events.OPEN_ILLO     : ( open_illo ) , # start illustration markup
        XU.Events.CLOSE_ILLO    : ( '.ca-\n' ) , # close caption after illo
        XU.Events.OPEN_SNOTE    : ( '.sn ' ) , # no newline - LINE text on same line
        XU.Events.CLOSE_SNOTE   : ( '\n' ) , # blank line before next para
        XU.Events.OPEN_FNOTE    : ( open_fnote ) , # start footnote
        XU.Events.CLOSE_FNOTE   : ( '.fn-\n' ) , # close footnote
        XU.Events.PAGE_BREAK    : ( note_page_break ) ,
        XU.Events.T_BREAK       : ( '.tb\n' ) , # thought break with blank line after
        XU.Events.OPEN_FNLZ     : ( '.fm\n' ) , # simple .fm for a rule above..
        XU.Events.CLOSE_FNLZ    : ( '.fm\n' ) , # ..and below block of footnotes
        XU.Events.OPEN_TABLE    : ( open_table ) , # start .ta
        XU.Events.OPEN_TROW     : ( None ) , # nothing at start of row
        XU.Events.OPEN_TCELL    : ( None ) , # nothing at start of cell
        XU.Events.CLOSE_TCELL   : ( None ) , # nothing at end of cell
        XU.Events.CLOSE_TROW    : ( close_trow ) , # write row of cells with stiles
        XU.Events.CLOSE_TABLE   : ( close_table ) # write .ta-
        }

    for (code, text, stuff, lnum) in event_generator :
        action = actions[ code ]
        if action is not None :
            if isinstance( action, str ) :
                BODY << action # write string literal
            else :
                action( code, text, stuff ) # call the callable
        LAST_CODE = code

    return True
