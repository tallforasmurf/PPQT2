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
                          testing py

This is a Translator module which allows testing and exploration of
the Translators API. Place it in the Translators folder of the extras
folder and its name Testing will appear in the File>Translators...
submenu when PPQT is started.

It implements the top-level API elements as commented below.
Feel free to modify this in any way to explore the Translator system.

'''


# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Import the PPQT translator support module. Make it "as XU" for brevity.
# You could just import it and prefix all names from it with "xlate_utils."
# or you could write from xlate_utils import * if you prefer to bring all
# the names it defines into this namespace without qualification.
#
import xlate_utils as XU

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Establish the menu name of this Translator. This is one 5 names that
# PPQT looks for. If this name is not defined as a string with at least
# 3, but no more than 16 characters, the Translator module will be ignored.
MENU_NAME = 'Testing'

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Demonstrate the options dialog API. Implement
# * a string input
# * a number input
# * a checkbox
# * a radio set
# The following objects can have any names. These are in CAPS because it is
# a Python convention to capitalize globals. The names are used in the
# OPTIONS_DIALOG list and also in the initialize() method.
#
# For convenient reference the init args to Dialog_Items are
# kind, label, tooltip='', result=None, minimum=None, maximum=None, choices=None

OD_STRING = XU.Dialog_Item( 'string',
                            label = 'Stringaling',
                            tooltip = 'Enter a string of some kind',
                            result = 'Default'
                            )

OD_NUMBER = XU.Dialog_Item( 'number',
                            label = 'Numerology',
                            tooltip = 'Think of a number from 1 to 99',
                            result = 1,
                            minimum = 1,
                            maximum = 99
                            )

OD_CHECKBOX = XU.Dialog_Item( 'checkbox',
                              label = 'Tokenize?',
                              tooltip = 'Shall I show the tokenization of each LINE event?',
                              result = False
                              )

OD_CHOICE = XU.Dialog_Item( 'choice',
                            label = 'Failure?',
                            tooltip = 'Shall I return False on some API call?',
                            result = 0,
                            choices = (
                                ('No!','Run normally all three calls'),
                                ('Initialize','Fail on the initialize() call'),
                                ('Translate','Fail on the translate() call'),
                                ('Finalize','Fail on the finalize() call')
                                )
                            )

# To disable the options dialog, just comment out the following name.
# OPTION_DIALOG is the second name PPQT looks for. If it is not defined
# no dialog is displayed.

OPTION_DIALOG = [ OD_CHECKBOX, OD_CHOICE, OD_STRING, OD_NUMBER ]

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# The following three functions must be defined as functions or the
# Translator will not appear in the menu. They are called in sequence.
#
# initialize() stores the important output devices for use from
# translate() and finalize(). This example also begins the output
# by writing values of the user options and the facts into the prolog.
#

PROLOG = None
BODY = None
EPILOG = None
FACTS = None
PAGES = None

def initialize( prolog, body, epilog, facts, pages ) :
    global PROLOG, BODY, EPILOG, FACTS, PAGES

    PROLOG = prolog
    BODY = body
    EPILOG = epilog
    FACTS = facts
    PAGES = pages

    prolog.writeLine( 'Initializing test translator' )
    prolog.writeLine( 'The pages list has {} entries'.format( len(pages) ) )
    prolog.writeLine( 'Given book facts are:' )
    for tag, value in facts.items() :
        prolog.writeLine( '    {} : {}'.format( tag, value ) )
    prolog.writeLine( 'User Option values are:' )
    # OPTION_DIALOG might be commented out
    for item in [OD_CHECKBOX, OD_CHOICE, OD_NUMBER, OD_STRING ] :
        prolog.writeLine(
            'Option {}: {}'.format( item.label, item.result ) )

    if OD_CHOICE.result == 1 :
        return None
    return True

#
# translate() does the real work.
#

EVENT_COUNT = 0
def translate( event_giver ) :
    global BODY, EVENT_COUNT, OD_CHOICE, OD_CHECKBOX, PAGES
    if OD_CHOICE.result == 2 :
        BODY.writeLine( 'Failing as requested' )
        return False

    BODY.writeLine( 'Starting translation' )
    EVENT_COUNT = 0
    for ( code, text, stuff, lnum ) in event_giver :
        BODY << '{} at line {}'.format( XU.EV_NAMES[ code ], lnum )
        BODY << ' stuff'
        for key, value in stuff.items() :
            BODY << ' {}:{}'.format(key,value)
        BODY << '\n'
        if code == XU.Events.LINE :
            if OD_CHECKBOX.result :
                izer = XU.tokenize( text )
                for (tok, en) in izer :
                    BODY << ' {}({})'.format( tok, en )
                BODY << '\n'
            else :
                BODY.writeLine( 'text: ' + text )
        if code == XU.Events.PAGE_BREAK :
            PAGES[ stuff['page'] ] = BODY.cpos()
        EVENT_COUNT += 1
    BODY.writeLine( 'End of event iterator' )
    return True

#
# finalize() cleans up
#

def finalize() :
    global PROLOG, EPILOG, OD_CHOICE, PAGES
    EPILOG.writeLine( 'Translation being finalized' )
    if OD_CHOICE.result == 3 :
        EPILOG.writeLine( 'Failing as requested' )
        return False

    psize = PROLOG.cpos()
    EPILOG.writeLine( 'adding prolog length {} to page list'.format(psize) )
    for j in range( len( PAGES ) ):
        PAGES[j] += psize
    EPILOG.writeLine( '{} events received'.format(EVENT_COUNT) )
    return True


