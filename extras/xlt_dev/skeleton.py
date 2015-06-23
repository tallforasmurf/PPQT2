'''
   TRANSLATOR SKELETON

This file is a skeleton form of a PPQT2 Translator module.

You can use this as a the basis of a new Translator by filling out
the code framework below following the comments given.

'''

import xlate_utils as XU

MENU_NAME = 'Skeletor' # change to proper translator name in menu

CB = XU.Dialog_Item( "checkbox", "Shall We?" "Check this for a tooltip, dude!" )

OPTION_DIALOG = [] # empty list = no options dialog

# Globals for initialize() to stow stuff in for later use

PROLOG = None
BODY = None
EPILOG = None
PAGES = []
FACTS = dict()

def initialize( prolog, body, epilog, facts, pages ) :
    global PROLOG, BODY, EPILOG, PAGES, FACTS
    PROLOG = prolog
    BODY = body
    EPILOG = epilog
    FACTS = facts
    # Instead of saving the whole facts dict, you could analyze the fact items
    # here and save the relevant parts as globals, or deal with them entirely
    # at this point. See html.py for an example.

    PAGES = pages

    # analyze the book facts dict and save relevant items in globals.

    # write some standard boilerplate into PROLOG.

    # if all is well,
    return True

def finalize( ) :
    global PROLOG, BODY, EPILOG, PAGES

    # write some boiler-plate text into EPILOG, perhaps based
    # on items noted and saved by translate()

    # if the PAGES list is not empty, add PROLOG.cpos() to every item

    return True

def translate( event_generator ) :
    global PROLOG, BODY, PAGES

    # def action functions and status variables, e.g.

    def note_page_break( ):
        PAGES[ stuff[ 'page' ] ] = BODY.cpos()
        # possibly BODY << a link target based on stuff['folio'] ?

    # The following dict acts as a computed go-to, distributing each event
    # code to an action that deals with it. An action can be None (not
    # defined yet, or nothing to do), or a string literal to be output to
    # BODY, or a callable, either a function-name or a lambda expression.

    actions = {
        XU.Events.LINE          : None,
        XU.Events.OPEN_PARA     : None,
        XU.Events.CLOSE_PARA    : None,
        XU.Events.OPEN_NOFLOW   : None,
        XU.Events.CLOSE_NOFLOW  : None,
        XU.Events.OPEN_CENTER   : None,
        XU.Events.CLOSE_CENTER  : None,
        XU.Events.OPEN_RIGHT    : None,
        XU.Events.CLOSE_RIGHT   : None,
        XU.Events.OPEN_HEAD2    : None,
        XU.Events.CLOSE_HEAD2   : None,
        XU.Events.OPEN_HEAD3    : None,
        XU.Events.CLOSE_HEAD3   : None,
        XU.Events.OPEN_POEM     : None,
        XU.Events.CLOSE_POEM    : None,
        XU.Events.OPEN_QUOTE    : None,
        XU.Events.CLOSE_QUOTE   : None,
        XU.Events.OPEN_LIST     : None,
        XU.Events.CLOSE_LIST    : None,
        XU.Events.OPEN_ILLO     : None,
        XU.Events.CLOSE_ILLO    : None,
        XU.Events.OPEN_SNOTE    : None,
        XU.Events.CLOSE_SNOTE   : None,
        XU.Events.OPEN_FNOTE    : None,
        XU.Events.CLOSE_FNOTE   : None,
        XU.Events.PAGE_BREAK    : note_page_break ,
        XU.Events.OPEN_FNLZ     : None,
        XU.Events.CLOSE_FNLZ    : None,
        XU.Events.OPEN_TABLE    : None,
        XU.Events.OPEN_TROW     : None,
        XU.Events.OPEN_TCELL    : None,
        XU.Events.CLOSE_TCELL   : None,
        XU.Events.CLOSE_TROW    : None,
        XU.Events.CLOSE_TABLE   : None,

        }

    for (code, text, stuff, lnum) in event_generator :
        action = actions[ code ]
        if action : # is not None or null string,
            if isinstance( action, str ) :
                BODY << action # write string literal
            else :
                action() # call the callable
        # else do nothing

    return True

# =+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+

# Here define any "boilerplate" text that you need to write into PROLOG
# or EPILOG. Use Python triple-quotes so you needn't escape newlines.
# You can of course use {} .format syntax for variable insertion.

BOILER = '''Any amount of
whatever...
'''
