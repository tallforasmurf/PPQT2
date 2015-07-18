'''
   ASCII Translator

This Translator takes a DP-formatted book and generates one formatted
as an ASCII etext. The user is queried for the optimum and maximum line lengths
(typically 73 and 75), and for the treatment of italic, bold and smallcap markup.

The input book's txt is formatted to DP standards (as extended by PPQT):

No-reflow /X..X/ indented by the First: value (typically 2).

Center /C..C/ indented by the First: value (typically 2).

Right /R..R/ right-aligned to the Right: margin (typically 0).

Poems /P..P/ lines individually reflowed to the First: Left: and Right:
values (typically 2, 12, 2).

Tables /T..T/ formatted with column widths as set by the /T line spec or by
the spacing of stiles in the first line (this is calculated by PPQT). Cell
text is reflowed within its column width and aligned l/r/c per the /T spec.

Chapter paragraphs set off by 4 newlines above and 2 below.

Subhead paragraphs set off by 2 newlines above and 1 below.

Block quotes /Q..Q/ and lists /U..U/ reflowed according to their First:,
Left: and Right: values.

The following markups are discarded and do not appear in the output: <id='x'>
targets, <span>s, 'lang="dict"' and any other syntax within HTML-like markup.
The visible part of a link (#visible:target#) is retained.

Sub_{script} and super^{script} markup is retained as-is. Italic, Bold and
Smallcap markups are converted according to user option. They may be
retained, dropped, or replaced by single-character flags, for example
underscores for italic.

For purposes of reflow, the "word" units are the space-delimited tokens that
are left after processing markups as above. For example a "word" might be
"<i>Gen^{rl}</i>" or "$Bold$", and all such characters are counted in the
length of the "word" token.

All reflowed paragraphs (including table cells) are reflowed using the
Knuth-Pratt optimal reflow algorithm which yields better results than
a typical "greedy" algorithm.

'''
import regex # This should work, as PPQT imports the same module

import xlate_utils as XU

MENU_NAME = 'ASCII' # change to proper translator name in menu

# Dialog items for user input: how to treat the italic, bold and smallcap
# markups, and the max and optimal line lengths. In V1 the "reflow" panel
# also offered choices for the F/L/R values for Centered and Poetry sections.
# We could add those to this dialog but don't see a need. Just in case we DO
# see a need at some future time, we put those values into the OPTIONS dict,
# rather than hard-coding them, just in case.

DI_ITALIC = XU.Dialog_Item(
    "choice",
    "Italics",
    "How to convert &lt;i> markup: underscore, omit, or leave alone",
    choices=[
        ("underscore","Replace markup with underscore character"),
        ("omit","Omit the markup and leave text as-is"),
        ("leave","Leave  &lt;i>markup&lt;/i> in the output")
        ],
    result=0 # preferred: use underscore
)
DI_BOLD = XU.Dialog_Item(
    "choice",
    "Bold",
    "How to convert &lt;b> markup: capitalize, omit, $, or leave alone",
    choices=[
        ("Caps","Capitalize the marked words"),
        ("omit","Omit the markup and leave text as-is"),
        ("$","Replace markup with the dollar-sign character"),
        ("leave","Leave &lt;b>markup&lt;/b> as-is in the output")
        ],
    result=0 # preferred: capitalize
)
DI_SCAPS = XU.Dialog_Item(
    "choice",
    "Small caps",
    "How to convert &lt;sc> markup: capitalize, omit, or leave alone",
    choices=[
        ("omit","Omit the markup and leave text as-is"),
        ("capitalize","Capitalize the marked words"),
        ("leave","Leave markup  &lt;sc>markup&lt;/sc> in the output")
        ],
    result=0 # preferred: omit <sc> and leave normal capitalization
)
DI_MAX_LINE = XU.Dialog_Item(
    "number",
    "Max Line",
    "Absolute limit on line length, usually 75",
    minimum=40,
    maximum=80,
    result=75
)
DI_OPT_LINE = XU.Dialog_Item(
    "number",
    "Optimum Line",
    "Preferred or best line length, usually 72",
    minimum=40,
    maximum=80,
    result=72
)
DI_CENTER = XU.Dialog_Item(
    "choice",
    "Centering",
    "How to format /C..C/ centered sections",
    choices=[
        ("self","The longest line starts at the left indent (narrow page)"),
        ("page","Lines are centered in the Max Line width (wide page)")
        ],
    result=0 # preferred: longest line at the F indent
)
OPTION_DIALOG = [
    DI_ITALIC,
    DI_BOLD,
    DI_SCAPS,
    DI_MAX_LINE,
    DI_OPT_LINE,
    DI_CENTER
]

# Globals for initialize() to stow stuff in for later use

PROLOG = None
BODY = None
EPILOG = None
OPTIONS = { } # set up during initialize()
ERRORS = [] # written during translate(), used in finalize()

def initialize( prolog, body, epilog, facts, pages ) :
    global PROLOG, BODY, EPILOG, OPTIONS, ERRORS
    # save the memory-streams
    PROLOG = prolog
    BODY = body
    EPILOG = epilog
    # FACTS = facts # ASCII conversion ignores the facts dict info.
    # PAGES = pages # ASCII conversion does not support retaining page info
    # Parse the results out of the dialog items and make them
    # more conveniently available in the OPTIONS dict.
    OPTIONS = {}
    OPTIONS['center'] = DI_CENTER.result

    n = DI_ITALIC.result
    OPTIONS['i_on']    = '_' if n==0 else '' if n==1 else '<i>'
    OPTIONS['i_off']   = '_' if n==0 else '' if n==1 else '</i>'

    n = DI_BOLD.result
    OPTIONS['b_on']    = '!' if n==0 else '' if n==1 else '$' if n==2 else '<b>'
    OPTIONS['b_off']   = '!' if n==0 else '' if n==1 else '$' if n==2 else '</b>'

    n = DI_SCAPS.result
    OPTIONS['sc_on']   = '' if n==0 else '!' if n==1 else '<sc>'
    OPTIONS['sc_off']  = '' if n==0 else '!' if n==1 else '</sc>'

    OPTIONS['maxl']   = DI_MAX_LINE.result
    OPTIONS['optl']   = DI_OPT_LINE.result

    # Install defaults that we currently do not offer the user.
    OPTIONS['poem_flr'] = ( 2, 12, 2 )

    # Initialize list of error messages, which consist of tuples,
    # (linenum, message-text). These are output by finalize()
    ERRORS = []

    return True

# Finalize the document by writing any error messages into the PROLOG (not
# the EPILOG) so if there are any problems, they are right there at the top
# of the file.

def finalize( ) :
    global PROLOG, ERRORS

    if len(ERRORS) :
        fmt = '{0:6}: {1}\n'
        PROLOG << '========      ERRORS NOTED     =========\n'
        PROLOG << ' (Line numbers refer to the source book)\n'
        for (linenum, text) in ERRORS :
            PROLOG << fmt.format( linenum, text )
        PROLOG << '========= END OF ERROR MESSAGES ========\n'

    return True

# The following globals are used to communicate between the action
# functions.

# The collected text of the current paragraph or table cell:

PARA = ''

# The stack of First, Left and Right indents. A triple is appended when
# opening a section, and one is popped when exiting the section. Thus
# the current (F,L,R) is FLR[-1].

FLR = [ ( 0, 0, 0 ) ]

# Push a new F/L/R triple based on the 'F'/'L'/'R' keys of a stuff dict.
# The new indents are the sums of the current and new ones.

def push_flr( stuff ) :
    global FLR
    current_flr = FLR[-1]
    new_flr = ( current_flr[0]+stuff['F'],
                current_flr[1]+stuff['L'],
                current_flr[2]+stuff['R'] )
    FLR.append( new_flr )

# The state of how to handle a LINE event, a stack of letters where the
# rightmost letter says p/lain text (open text or in a quote), v/erse
# (in a poem), x/noflow, c/enter, r/ight, t/able.

LINE_CONTEXT = ['p']

# List to collect lines for a centered section. They are then written on the
# CLOSE_CENTER event, at which time we can know the longest line.

CENTERLINE = []

# The following functions are called from the event loop. Each is called with
# the four elements of an event unpacked: code, text, stuff, lnum.

def open_quote( code, text, stuff, lnum ) :
    global LINE_CONTEXT
    # /Q.. Set new indents, go to plain text.
    push_flr( stuff )
    LINE_CONTEXT.append( 'p' )

def open_poem( code, text, stuff, lnum ) :
    global LINE_CONTEXT
    # /P.. Set new indents (translate.py supplies 2,12,2) and
    # begin treating lines as verse. Also emit one blank line.
    push_flr( stuff )
    LINE_CONTEXT.append( 'v' )
    BODY << '\n'

def open_noflow( code, text, stuff, lnum ) :
    global FLR, LINE_CONTEXT
    # /X.. force 2,0,0 indents, treat lines as noflow.
    FLR.append( (stuff['F'], 0, 0 ) )
    LINE_CONTEXT.append( 'x' )

def open_right( code, text, stuff, lnum ) :
    global LINE_CONTEXT
    # /R.. set user's FLR, treat lines as right-align.
    push_flr( stuff )
    LINE_CONTEXT.append( 'r' )

def open_list( code, text, stuff, lnum ) :
    global LINE_CONTEXT
    # /U.. set user's FLR, set plain-text reflow (list items are just paras).
    push_flr( stuff )
    LINE_CONTEXT.append( 'p' )

# Close any of the above sections by popping them off the stack.

def close_section( code, text, stuff, lnum ) :
    global FLR, LINE_CONTEXT
    FLR.pop()
    LINE_CONTEXT.pop()

# To handle centered lines, we collect the (stripped) lines and on
# CLOSE_CENTER, figure out the width and write them. Detection of too-long
# lines happens in add_line(), not here, because in add_line() we have the
# lnum for the diagnostic message.
def open_center( code, text, stuff, lnum ) :
    global LINE_CONTEXT, CENTERLINE, FLR
    push_flr( stuff )
    CENTERLINE = [] # clear residue of earlier section
    LINE_CONTEXT.append( 'c' )# treat lines as centered

def close_center( code, text, stuff, lnum ) :
    global FLR, LINE_CONTEXT, CENTERLINE, BODY
    # Scan the collected lines and get the length of the longest. Note we are
    # allowing too-long lines to go through, so add_space could be negative.
    max_line = 0
    for line in CENTERLINE :
        max_line = max( max_line, len( line ) )
    # Center on longest line plus F, or on page width -- user option.
    center_width = OPTIONS['maxl'] if OPTIONS['center'] else max_line
    # write the collected lines with spaces to indent them.
    for line in CENTERLINE :
        add_space = int( ( center_width - len(line) ) / 2 )
        BODY << FLR[-1][0] * ' '
        if add_space > 0 : BODY << add_space * ' '
        BODY.writeLine( line )
    # and clean up
    FLR.pop()
    LINE_CONTEXT.pop()

# Open an illustration, footnote or sidenote by putting the initial
# boilerplate text in the PARA buffer, so it will be part of the first
# paragraph that goes out. These "bracket" items only appear at the
# outermost level, cannot be nested in anything, so no need to push
# FLR or LINE_CONTEXT nor pop them later.

def open_illo( code, text, stuff, lnum ) :
    global PARA
    PARA = '[Illustration:'

def open_fnote( code, text, stuff, lnum ) :
    global PARA
    PARA = '[Footnote {}:'.format( stuff['key'] )

def open_snote( code, text, stuff, lnum ) :
    global PARA
    PARA = '[Sidenote:'

# Close an illustration, footnote or sidenote by adding a right bracket to
# the output. This would go out after a newline, which we are sure was the
# last thing written to BODY. However we are going to play a little game with
# the BODY MemoryStream object and overwrite that newline with a bracket and
# a newline.

def close_brkt( code, text, stuff, lnum ) :
    global BODY
    p = BODY.pos() # position in bytes
    BODY.seek( p-2 ) # 2 bytes per char
    BODY << ']\n'

# Table stuff. On OPEN_TABLE we save what is known about the column widths
# and alignments, as well as pushing the FLR and context. We save the lnum
# at this point for possible error messages. We emit one blank line.
#
# On OPEN_TROW we clear out a list of cell-contents.
#
# On OPEN_TCELL we clear the PARA global, where add_line will append the
# lines (probably only one line) of text for this cell.
#
# On CLOSE_TCELL we reflow the collected cell contents within the specified
# width of the cell, and save the (probably one) reflowed lines as a list by
# splitting on any newlines that reflow added.
#
# On CLOSE_TROW we run over the collected lists of cell-content-lines and
# print them out row by row (probably only one row) with stiles between.
#
# The CLOSE_TABLE event is like close_section() above but also issues
# warning diagnostics.

TABLE_COLS = []
TABLE_CELLS = []

def open_table( code, text, stuff, lnum ) :
    global LINE_CONTEXT, TABLE_COLS, BODY
    TABLE_COLS = stuff['columns']
    push_flr( stuff )
    LINE_CONTEXT.append( 't' )
    BODY << '\n'

def open_table_row( code, text, stuff, lnum ) :
    global TABLE_CELLS
    TABLE_CELLS = []

def open_table_cell( code, text, stuff, lnum ) :
    global PARA
    PARA = ''

def close_table_cell( code, text, stuff, lnum ) :
    global TABLE_COLS, TABLE_CELLS, ERRORS, PARA
    col = len( TABLE_CELLS ) # number of current column
    if col < len( TABLE_COLS ) :
        (w, h, v) = TABLE_COLS[col]
        reflow = do_reflow( PARA, 0, 0, 0, maxl=w, optl=w, lnum=lnum )
        TABLE_CELLS.append( reflow.split('\n')[:-1] )
    else :
        # there was one more stile (hence column) in this row
        # than was indicated by the /T line or the first line.
        ERRORS.append(
            ( lnum, 'Excess table cell in this row ignored ("{}")'.format(PARA) )
            )

def close_table_row( code, text, stuff, lnum ) :
    global TABLE_CELLS, TABLE_COLS, ERRORS

    # These flags are set during the printout of the possibly multiple
    # lines of the table row, and used to generate errors afterward.
    warn_cell = False
    warn_row = False

    # Run over list of cell row-lists and learn how many physical
    # lines we print for this row. Normally it is 1.
    passes = 0
    for line_list in TABLE_CELLS :
        passes = max( passes, len( line_list ) )

    # If passes>1, there are multiple physical lines to this table row.
    # In that case, look through the column specs and see if any column
    # wants 'B' bottom alignment. And if it does, implement that by moving
    # any blank lines in its cell to the top.

    if passes > 1 :
        for col, (w, h, v) in enumerate( TABLE_COLS ) :
            if v == 'B' :
                while passes > len( TABLE_CELLS[col] ) :
                    TABLE_CELLS[col].insert( 0, '' )

    # Print each line of this row, making each column its proper width.
    # Take note if the output line length exceeds the book max, and also
    # take note if a cell is wider than its column's designated width
    # (this could happen if a cell has a single word token wider than the
    # column width).

    for pass_no in range(passes) : # "pass" is a reserved word!
        row_length = 0
        for (col, line_list) in enumerate( TABLE_CELLS ) :
            (w, h, v) = TABLE_COLS[col]
            if pass_no < len( line_list ) :
                line = line_list[pass_no]
            else :
                line = ''
            add_spaces = w - len(line)
            if add_spaces < 0 :
                warn_cell = True
                add_spaces = 0
            if h == 'c' :
                space_left = int(add_spaces/2) * ' '
                space_right = ( add_spaces - int(add_spaces/2) ) * ' '
            elif h == 'r' :
                space_right = ''
                space_left = add_spaces * ' '
            else : # h=='l' or h is None
                space_right = add_spaces * ' '
                space_left = ''
            col_text = '{}{}{}|'.format( space_left, line, space_right )
            row_length += len( col_text )
            BODY << col_text
        BODY << '\n'
        if row_length > OPTIONS['maxl'] : warn_row = True

    # If we noticed cells or rows too long, put up error message(s).
    if warn_row :
        ERRORS.append(
            ( lnum, 'Data in this table row is too long' )
            )
    if warn_cell :
        ERRORS.append(
            ( lnum, 'One or more cells in this table row are wider than the column width' )
            )

def close_table( code, text, stuff, lnum ) :
    global FLR, LINE_CONTEXT, PARA
    FLR.pop()
    LINE_CONTEXT.pop()
    PARA = '' # clean up our mess - there is no open_para() to do it

# Handle the LINE event. In hindsight, the API design is not the best. It
# would have been better to have unique LINE events for the context (e.g.
# QUOTE_LINE, RIGHT_LINE, etc.). As it is, the Translator needs to be
# "stateful", keeping track of the context and handling LINEs different ways.
# We do that here.

PLINE = regex.compile(r'\n?(.+?)(\s\d+\n)$')

def add_line( code, text, stuff, lnum ) :
    global PARA, LINE_CONTEXT, FLR, CENTERLINE, ERRORS
    ctx = LINE_CONTEXT[-1]
    if ctx == 'p' :
        # the usual case, para or heading, collect paragraph lines
        if PARA : # has some text in it already,
            PARA += ' ' # space-delimit the new line text
        PARA += text

    elif ctx == 'x' :
        # noflow: warn about a long line; and write the line
        add_space = len(text) - len( text.lstrip() ) # how many left spaces
        line = clean_up( text, lnum) # process out i/b/sc
        maxl = OPTIONS['maxl'] - FLR[-1][0]
        if maxl < ( len( line ) + add_space ) :
            ERRORS.append(
                (lnum, 'No-flow line too long at {} for width {}'.format( len(line), maxl ) )
            )
        BODY << ( FLR[-1][0] + add_space) * ' ' # indent by First: plus left-spacing
        BODY.writeLine(line) # and write the line even if it is too long

    elif ctx == 'r' :
        # right-align: warn about a long line; and write the line
        line = clean_up( text.strip(), lnum )
        # available length is maxl - F - R
        maxl = OPTIONS['maxl'] - FLR[-1][0] - FLR[-1][2]
        add_space = maxl - len(line)
        if add_space < 0 :
            ERRORS.append(
                (lnum, 'Right-align too long at {} for width {}'.format( len(line), maxl ) )
            )
            add_space = 0
        BODY << add_space * ' '
        BODY.writeLine(line)

    elif ctx == 'c' :
        # centering: warn of long line; save line for close_center()
        line = clean_up( text.strip(), lnum )
        maxl = OPTIONS['maxl'] - FLR[-1][0]
        if len(line) > maxl :
            ERRORS.append(
                (lnum, 'Centered line too long at {} for width {}'.format( len(line), maxl ) )
            )
        CENTERLINE.append( line )

    elif ctx == 't' : # in a table; just save the text for close_cell
        PARA += text

    elif ctx == 'v' :
        # In a poem, so reflow just the line. Note the line could be empty;
        # in HTML that's a stanza break, here it is just a blank line.

        # do_reflow gets F, L, R values. We account for a user-indent by
        # incrementing the specified F by any leading spaces on the line.
        (F, L, R) = FLR[-1]
        strip_text = text.lstrip()
        F += len(text) - len(strip_text)
        line = do_reflow( strip_text, F, L, R, lnum=lnum )
        # do_reflow treats poem line numbers as tokens. But this actually IS
        # a poem line and if it ends in a number, it's a line number, which
        # we want to exdent to the margin. (We can't use XU.POEM_LNUM_XP for
        # this test; it does not expect the newline at the end of the
        # reflowed text.)
        mob = PLINE.search(line)
        if mob :
            # mob.group(2) is the ' \d+\n' part. Make a new line with spaces inserted
            # to push that bit to the full line length, OPTIONS['maxl']-R
            used_part = len(mob.group(0)) - 1 - mob.group(0).startswith('\n')
            available = OPTIONS['maxl'] - R - used_part
            if available :
                line = line[:-len(mob.group(2))] + (available * ' ') + mob.group(2)
        BODY << line

    else :
        assert False # we never get here

# To close any paragraph, reflow the accumulated text based on the current
# F/L/R value and write that to BODY.
#
# The reflowed text consists of at least one non-empty line ending a newline.
# We PRECEDE the output with one additional newline. This ensures that the
# paragraph is set off with a blank line. After closing the para, clear the
# PARA field.

def close_para( code, text, stuff, lnum ) :
    global BODY, FLR, PARA
    # do_reflow is at the end of the module.
    BODY << '\n'
    BODY << do_reflow( PARA, *FLR[-1], lnum=lnum )
    PARA = ''

def translate( event_generator ) :
    global BODY, FLR

    FLR = [ ( 0, 0, 0 ) ] # clean up from previous run

    # The following dict acts as a computed go-to, distributing each event
    # code to an action that deals with it. An action can be None (not
    # defined yet, or nothing to do), or a string literal to be output to
    # BODY, or a callable, either a function-name or a lambda expression.
    #
    # The callables, and some globals they use, are defined below this function.

    actions = {
        XU.Events.LINE          : add_line,
        XU.Events.OPEN_PARA     : None, # nothing needed here
        XU.Events.CLOSE_PARA    : close_para,
        XU.Events.OPEN_NOFLOW   : open_noflow,
        XU.Events.CLOSE_NOFLOW  : close_section,
        XU.Events.OPEN_CENTER   : open_center,
        XU.Events.CLOSE_CENTER  : close_center,
        XU.Events.OPEN_RIGHT    : open_right,
        XU.Events.CLOSE_RIGHT   : close_section,
        XU.Events.OPEN_HEAD2    : '\n\n\n', # three extra newlines before PARA
        XU.Events.CLOSE_HEAD2   : '\n', # one extra newline after PARA
        XU.Events.OPEN_HEAD3    : '\n', # one extra newline before
        XU.Events.CLOSE_HEAD3   : None, # nothing special after
        XU.Events.OPEN_POEM     : open_poem,
        XU.Events.CLOSE_POEM    : close_section,
        XU.Events.OPEN_QUOTE    : open_quote,
        XU.Events.CLOSE_QUOTE   : close_section,
        XU.Events.OPEN_LIST     : open_list,
        XU.Events.CLOSE_LIST    : close_section,
        XU.Events.OPEN_ILLO     : open_illo,
        XU.Events.CLOSE_ILLO    : close_brkt,
        XU.Events.OPEN_SNOTE    : open_snote,
        XU.Events.CLOSE_SNOTE   : close_brkt,
        XU.Events.OPEN_FNOTE    : open_fnote,
        XU.Events.CLOSE_FNOTE   : close_brkt,
        XU.Events.PAGE_BREAK    : None, # don't care
        XU.Events.T_BREAK       : '\n\n*    *    *    *    *\n',
        XU.Events.OPEN_FNLZ     : None, # nothing to do
        XU.Events.CLOSE_FNLZ    : None, # nothing to do
        XU.Events.OPEN_TABLE    : open_table,
        XU.Events.OPEN_TROW     : open_table_row,
        XU.Events.OPEN_TCELL    : open_table_cell,
        XU.Events.CLOSE_TCELL   : close_table_cell,
        XU.Events.CLOSE_TROW    : close_table_row,
        XU.Events.CLOSE_TABLE   : close_table,

        }

    for event_tuple in event_generator :
        action = actions[ event_tuple[0] ]
        if action : # is not None or a null string,
            if isinstance( action, str ) :
                BODY << action # write string literal
            else :
                action( *event_tuple ) # call the callable
        # else do nothing

    return True

#
# clean_up( text, lnum ) processes text through the XU.tokenize() iterator to
# deal with the ital/bold/smallcap markups and to omit things like
# link-targets, spans etc. Returns a new text string with those markups
# converted as requested. Adds a warning message if markup is not balanced
# (hence need for lnum).
#
# This is applied to individual lines of no-flow, centered, right sections as
# well as to table cells and paragraphs before they are reflowed.

def clean_up( text, lnum ) :

    izer = XU.tokenize( text )
    new_text_parts = []
    next_tok = ''
    force_caps = False
    balances = 0 # markup depth counters
    simple_tokens = [XU.TokenCodes.WORD, XU.TokenCodes.PUNCT, XU.TokenCodes.PLINE, XU.TokenCodes.OTHER]
    for (ttype, token) in izer :

        # for performance it is important to have the most common token types
        # found at the top of this if-stack.

        if ttype in simple_tokens :
            # something innocent and nonblank: add it to the token (treating
            # poem line number as a token)
            next_tok += token

        elif ttype == XU.TokenCodes.SPACE :
            # Space means force out the current token and start a new one.
            # Collecting each token in a list rather than building and rebuilding
            # the output string with "new_text += next_tok".
            if force_caps : next_tok = next_tok.upper()
            new_text_parts.append( next_tok )
            next_tok = ''

        elif ttype == XU.TokenCodes.ITAL_ON :
            balances += 1
            next_tok += OPTIONS['i_on']

        elif ttype == XU.TokenCodes.ITAL_OFF :
            balances -= 1
            next_tok += OPTIONS['i_off']

        elif ttype == XU.TokenCodes.BOLD_ON :
            balances += 100
            if OPTIONS['b_on'] == '!' : # bold==caps
                force_caps = True
            else :
                next_tok += OPTIONS['b_on']

        elif ttype == XU.TokenCodes.BOLD_OFF :
            balances -= 100
            if OPTIONS['b_off'] == '!' :
                next_tok = next_tok.upper()
                force_caps = False
            else :
                next_tok += OPTIONS['b_off']

        elif ttype == XU.TokenCodes.SCAP_ON :
            balances += 10000
            if OPTIONS['sc_on'] == '!' : # sc==caps
                force_caps = True
            else :
                next_tok += OPTIONS['sc_on']

        elif ttype == XU.TokenCodes.SCAP_OFF :
            balances -= 10000
            if OPTIONS['sc_off'] == '!' :
                next_tok = next_tok.upper()
                force_caps = False
            else :
                next_tok += OPTIONS['sc_off']

        elif ttype == XU.TokenCodes.SUP :
            if len(token) == 1 :
                next_tok += '^' + token
            else :
                next_tok += '^{' + token + '}'

        elif ttype == XU.TokenCodes.SUB :
            next_tok += '_{' + token + '}'

        elif ttype == XU.TokenCodes.FNKEY :
            next_tok += '[' + token + ']'

        elif ttype == XU.TokenCodes.LINK :
            next_tok += token.split(':')[0] # just take the visible link

        elif ttype == XU.TokenCodes.BRKTS :
            brkt_parts = token.split(':')
            if ( brkt_parts[0].lower() == 'typo' ) and ( len(brkt_parts) > 2 ) :
                next_tok += brkt_parts[2] # just the "corrected" part
            else : # assume [Greek:blah...]
                next_tok += '[' + brkt_parts[0] + ':' + brkt_parts[1] + ']'

        else :
            #assert ttype in [XU.TokenCodes.SPAN_ON,
                       #XU.TokenCodes.SPAN_OFF,
                       #XU.TokenCodes.DICT_ON,
                       #XU.TokenCodes.DICT_OFF,
                       #XU.TokenCodes.TARGET] # all these are omitted
            pass

    new_text_parts.append(next_tok) # collect the last word
    new_text = ' '.join(new_text_parts) # just build one string

    # if balance is nonzero, the user forgot a </i/b/sc>
    if balances :
        ERRORS.append(
            (lnum, 'Italic, bold or smallcap markup is not properly balanced near here.')
            )

    return new_text

# The do_reflow function takes the following parameters:
#
# text: a possibly-empty string of text to be flowed into a paragraph
#       by the addition of newlines.
#
# F:    left-indent for the first line
# L:    left-indent for second and subsequent lines if any
# R:    right-indent from the maximum line, usually 0
#
# maxl: maximum line length not to be exceeded if possible, although
#       if there is a single word-token whose length is >maxl, it will
#       be on a line by itself.
# optl: the preferred or optimum line length, <= maxl.
#
# lnum: a line number of (typically) the end of paragraph, for use
#       in error messages.
#
# When maxl and optl are omitted (None) these values are taken from
# the global OPTIONS['maxl'] and OPTIONS['optl']
#
# The algorithm is a simplified version of the famous Knuth-Pratt
# algorithm, based on a slavish copy of the fmt_paragraph() function
# in the GNU fmt utility.

def do_reflow( text, F, L, R, maxl=None, optl=None, lnum=0 ):
    global OPTIONS, ERRORS
    if maxl is None :
        maxl = OPTIONS['maxl']
        optl = OPTIONS['optl']

    new_text = clean_up( text, lnum )

    # Now, if the end result is an empty line, we are done.
    if len(new_text) == 0 :
        return '\n'

    # Set up the K-P algorithm stuff.
    # The output is collected here:
    flow_text = ''

    # In Gnu fmt, the paragraph is read into a list of structs, but this can
    # be seen as a table, with each struct a row and its members, columns.
    # Here we make the same table using parallel lists. If you read the C
    # code (http://lingrok.org/xref/coreutils/src/fmt.c) the "struct word"
    # members map as follows:
    #
    # const char *text -- T[j] a word string from text.split()
    # int length       -- W[j] length of T[j]
    # int line_length  -- LL[j] length of line starting from j
    # COST best_cost   -- C[j] cost of line of length L[j]
    # WORD *next_break -- P[j] index of first T[j] of following line
    #
    # Struct members space, paren, period, punct and final from the C source
    # are not maintained. Gnu fmt uses the convention that dot-space-space
    # ends a sentence, so it can distinguish sentence-ending periods from
    # abbreviation periods. PG does not use this convention (too bad!) so we
    # can't detect end of a sentence and accordingly the related cost
    # calculations can't be done.

    T = []
    W = []
    for tok in new_text.split() :
        T.append(tok)
        W.append( len(tok) )

    N = len(T) # valid tokens are 0..N-1

    # The line length is the allowed line size minus the left- and
    # right-indents if any. We will make a series of lines of at most this
    # length. On output we will prefix each line with L (or F) spaces.

    L_optimum = optl - L - R
    L_maximum = maxl - L - R

    # The output is collected here:
    flow_text = ''

    # first_indent_diff is the difference between the F and L. If the first
    # line is INdented (as usual) this is positive. It is added to W[0] to make
    # the first word in effect wider. That forces the first line to be shorter
    # and on output it will be indented by F spaces.
    #
    # If the first line is EXdented (as in poetry) this is negative. We
    # distribute it over the first few tokens (not driving any to zero) in
    # effect fooling the algorithm to make the first line net longer than
    # L_maximum.
    first_indent_diff = F - L

    if (N == 1) or ( L_maximum >= ( sum(W) + (N-1) + F) ) :
        # There is but one token (of any length), or the sum of tokens fits
        # in the first line. No reflow needed, just put it all together now.
        # Likely most poetry lines, headings, and table cells go here.
        flow_text = F * ' ' # leading indent
        flow_text += ' '.join(T)
        flow_text += '\n'
    else:
        # The text will not fit one L_maximum line, so we will be reflowing it.

        # Add first_indent_diff to the first token's width.
        if first_indent_diff > 0 :
            W[0] += first_indent_diff
        else:
            j = 0
            first_indent_diff = abs( first_indent_diff )
            while first_indent_diff > 0 :
                f = min( (W[j]-1), first_indent_diff )
                W[j] -= f
                first_indent_diff -= f
                j += 1

        # Set up the Costs column; C[N] is a sentinel.
        C = (N+1)*[0]

        # Add a sentinel value to the W column as W[N]
        W.append( maxl * 2)

        # Prepare the next-word link column and length-from-here column
        P = (N+1)*[N]
        LL = (N+1)*[0]

        # The reflow calculation loop scans backward over the word list.
        # In C, it is for (start = word_limit - 1; start >= word; start--)

        scan_ptr = N-1
        while True :
            best_cost = int(32767*32767) # "infinity"
            test_ptr = scan_ptr
            current_len = W[test_ptr]
            while True : # do{...} while(len < maxwidth)
                test_ptr += 1 # this goes to N on first iteration
                # "consider breaking before test_ptr" : bringing line_cost() inline
                this_cost = 0
                if test_ptr != N:
                    this_cost = L_optimum - current_len
                    this_cost *= 10
                    this_cost = int(this_cost * this_cost)
                    if P[test_ptr] != N :
                        n = (current_len - LL[test_ptr])/2
                        this_cost += int(n * n)
                this_cost += C[test_ptr]
                if this_cost < best_cost : # possible break point
                    best_cost = this_cost
                    P[scan_ptr] = test_ptr
                    LL[scan_ptr] = current_len
                current_len += 1 + W[test_ptr] # picks up L_maximum when test_ptr==N
                if current_len >= L_maximum : break
            # end inner do-while(len < maxwidth)

            # We don't try to implement base_cost() which penalizes short widows
            # and orphans, encourages breaks after sentences and right parens,
            # and so forth, all because we can't detect ends of sentences.

            C[scan_ptr] = best_cost # + base_cost(scan_ptr)
            if scan_ptr == 0 : break # all done
            scan_ptr -= 1
        # end main for-loop

        # Prepare the output as a string of text with appropriate newlines
        # followed by appropriate indents.
        first_indent = F * ' '
        left_indent = L * ' ' # left-indent space for lines 2-m
        indent = first_indent
        longest_out = 0
        # Each logical line extends from T[a] to T[z-1]
        a = 0
        while True : # do until z == N
            spacer = indent
            z = P[a]
            this_line = ''
            while a < z :
                this_line += spacer
                this_line += T[a]
                a += 1
                spacer = ' '
            longest_out = max(longest_out, len(this_line))
            flow_text += this_line
            flow_text += '\n'
            indent = left_indent
            if z == N : break
            a = z

        # At this point we have one or more lines in flow_text. If any of them
        # went over the limit, file a warning.
        if longest_out > (L_maximum + L) :
            ERRORS.append(
                ( lnum, 'One or more lines exceeded the maximum width for this paragraph' )
                )
    # end else the line is too long and must be reflowed
    # Now we have one or more complete lines in flow_text, return them.
    return flow_text