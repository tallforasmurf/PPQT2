.. ppqt2help documentation master file, created by
   sphinx-quickstart on Fri Feb  6 21:54:35 2015.


.. toctree::
   :maxdepth: 2

Welcome to PPQT Help
=====================================

PPQT helps you, a volunteer for Distributed Proofreaders,
to post-process a book. See the Table of Contents to jump
to the major sections. To search, key control-f (Mac: command-f).

See `The Big Picture`_ for a first-time orientation.

See `What's New`_ for the latest changes in this release.

**Mac Users**: Whenever you see "control-" or "ctl-", think "command-".
Whenever you see "alt-", think "option-".

Licenses
------------------------------

**The source code of PPQT2 is licensed under the GPL v3**:
see the file COPYING.TXT distributed with the program.
You can read the code, post issue reports, and contribute, at the
`Github page`_.

.. _Github page: https://github.com/tallforasmurf/PPQT2

PPQT is based on the Qt5_ platform.
Qt is licensed for noncommercial use under the LGPL.

.. _Qt5: http://qt.io

PPQT is coded in Python 3 using the PyQt5_ package,
which is licensed for noncommercial use under the GPL v2 and the GPL v3.

.. _PyQt5: http://riverbankcomputing.co.uk/software/pyqt/intro

Distributed with PPQT2 is a copy of the `Liberation Mono font`_ which
is licensed under the `SIL Open Font License`_,
and also a copy of the `Cousine font`_ which is licensed under the
`Apache 2.0 license`_.

.. _Liberation Mono font: https://fedorahosted.org/liberation-fonts/

.. _SIL Open Font License: http://scripts.sil.org/cms/scripts/page.php?site_id=nrsi&id=ofl 

.. _Cousine font: http://www.google.com/fonts/specimen/Cousine

.. _Apache 2.0 license: https://www.apache.org/licenses/LICENSE-2.0.html

Acknowledgements and History
----------------------------

The idea of an integrated editor with special features for
post-processing originated with Steve Shulz (Thundergnat), who created Guiguts,
the program that inspired PPQT and provided most of its ideas.

Version 1 of PPQT (Post-Processing in Qt)
was written in 2011-12 and has been successfully used by a few people.
Mark Summerfield's book
`Rapid GUI Development with PyQt <http://www.qtrac.eu/pyqtbook.html>`_
was an essential learning tool when writing PPQT.

Although PPQT V1 is still functional even now, it has shortcomings and
a clumsy internal design.
This, Version 2, has a cleaner internal structure,
adds the ability to have multiple books open at once,
and stores metadata in JSON format, among many other changes.

Most important, Version 2 makes a clean division between the *editorial*
tasks of post-processing, such as healing page breaks, checking spelling,
moving footnotes and the like,
and the *translation* of the final, clean etext
into other markup formats like fp, or delivery formats such as HTML, EPUB, etc.

It defers those tasks to pluggable translator modules that can be supplied
by  others, making PPQT2 an open-ended application.

.. _The Big Picture:

The Big Picture
================

PPQT is an editor designed for post-processing books that have
been prepared by the volunteers of `Distributed Proofreaders`_.

.. _Distributed Proofreaders: http://www.pgdp.net

On the left side of the main window is an area for editing the text
of book files. You can open several book files.
Each open book file appears as a tab.
Only one book file is visible and active at any time.

On the right side is a set of tabs that open panels with different
functions:

* The `Images panel`_ displays the scan images for the pages of the active book.
  It usually shows the image for the location of the edit cursor.

* The `Notes panel`_ is a simple editor where you can keep notes about your work
  on a book. The notes are saved and loaded with the book.

* The `Find panel`_ lets you do search and replace. It has many special features
  including support for full (PCRE) regular expressions and
  the ability to save complex searches for later use.

* The `Characters panel`_ shows all the characters used in the book.
  You can quickly find non-ASCII characters, or replace special
  characters with HTML entity codes.

* The `Words panel`_ shows all the words used in the book, with their
  counts. You can quickly find all words that fail spell-check here.

* The `Pages panel`_ lists all the page boundaries. Here you can
  adjust the visible page numbers (folios) to match the original book.

* The `Footnote panel`_ organizes all footnotes. Here you can find
  footnote errors, and move footnotes to the end of a chapter or
  end of the book.

* The `Bookloupe panel`_ lets you run the `Bookloupe program`_ and display
  all its diagnostic messages in a table you can sort by message
  or by line number for easy editing.

.. _Bookloupe program: http://www.juiblex.co.uk/pgdp/bookloupe/

Each open book has its own set of these panels.
When you make a book text active on the left side, the panels
for that book appear on the right side.

You use these features to bring a book into
perfect conformity with the DP `Formatting Guidelines`_.
You check all formatting.
You remove page separator lines and fix the words or footnotes
that were broken across pages.
You move footnotes, sidenotes, and illustrations into their
proper locations.
You handle all proofer queries.
You resolve all spellcheck errors.
And so on.

When the book is 100% correct per the Guidelines,
you apply one of the Translators_ to convert the book to a
different form such as HTML.

The translated book text appears in a new edit panel in PPQT.
You may continue to edit it there, or save it and process it with
some other program.

.. _Formatting Guidelines: http://www.pgdp.net/c/faq/document.php

.. _Extras:

Extras
--------

The "Extras" folder is a folder of useful things that is distributed
along with PPQT. Here are the things you can find there:

* This very file, "ppqt2help.html" is there. You can open it in
  any browser.

* "Suggested_workflow.rtf" describes the steps of post-processing in detail
  and shows how to use the features of PPQT at each step.

* en-common-ltn.txt is a file of common "scannos". See `Marking Scannos`_.

* The "dictionaries" folder contains spell-check dictionaries for several languages.

* Several sets of saved Find/Replace operations are here.
  You can load them into the `Find panel`_ to do complex searches.
  For example, "common_errors.utf"
  has regular-expression searches for common text errors such as
  whitespace preceding punctuation or a paragraph that starts with
  a lowercase letter.

* The "Translators" folder contains the Translators_ you can apply.
  You can obtain other Translator modules and put them there.

* The "xlt_dev" folder contains files that enable a Python programmer
  to write a new Translator module.

You can move the Extras folder anywhere you like.
You would do that if you changed or added any files in it, 
because it would be replaced when you downloaded a new version of the program.
If you move it, tell PPQT where it is using the `Preferences`_ dialog.

Settings
---------

PPQT remembers the size and position of the window and other
important preference choices from one run to the next.
It saves these items in a settings file.
The location of the settings depends on your operating system:

* In Mac OS X, it is a file in $HOME/Library/Preferences/com.PGDP.PPQT2.

* In Linux it is a file in $HOME/.config/PGDP/PPQT2.

* In Windows it is in the Registry under HKEY_CURRENT_USER\\Software\\PGDP\\PPQT2.

Files and Folders
=================

When you open a book file, say `bookname`\ ``.utf``,
PPQT expects to find two things in the same folder:

* `bookname`\ ``.utf.ppqt`` is a file of information about the book
  (see `Metadata`_). It is created the first time you save the book.

* ``pngs`` is a folder that contains the scanned page images for this book.
  These are the images that are shown in the `Images panel`_.

It also looks in the same folder for spelling dictionaries;
see Dictionaries_.

Unicode and Fonts
------------------

The book text is held in memory as Unicode, so it may use
virtually any alphabet or special characters.
There are two restrictions.

PPQT can only display characters that are defined in the
font you select (see `Edit font`_).
For example the DPCustomMono2 font familiar to DP proofers
lacks Greek and Cyrillic.
The Liberation Mono and Cousine fonts,
which are embedded in PPQT,
have characters from several languages and many symbols.

Second, although it can display alphabets such as Arabic and Hebrew
if they are in the current font,
PPQT does not understand right to left editing.
The edit cursor only moves left to right during text entry.

File Encodings and File Names
-------------------------------

Characters in a file are encoded somehow.
The preferred encoding for modern text files is UTF-8.
This encoding can store any Unicode character.
**PPQT expects book and other files to be encoded UTF-8**.
PPQT always saves its `Metadata`_ file in UTF-8.

Another common encoding is Latin-1 (also called ISO8859-1).
PPQT **allows** files to be encoded in Latin-1.
Before you open a file encoded Latin-1, you must give it
a file *name* that ends in ``-l`` (for example ``latinbook-l.txt``),
or ends in ``-ltn`` (``latinbook-ltn.txt``).
Or, you may give the file a *suffix* of ``.ltn`` (``latinbook.ltn``).
PPQT uses the Latin-1 encoding when it opens or saves a file named in any of these ways.

If the text in your book is strictly ASCII, PPQT will handle it correctly
no matter how the book is named.
ASCII is a proper subset of both UTF-8 and Latin-1.

There are many other encodings (`here is a list`_),
such as the "Windows CP1252" encoding
often found in older Windows files.
PPQT does not support any encodings except UTF-8 and Latin-1.

**If you open a file and PPQT warns you that it contains Unicode
Replacement Characters, you should close the file immediately without saving it.**
If it is encoded Latin-1, rename it.
Otherwise, use some other utility  to convert it to UTF-8.

.. _here is a list: http://en.wikipedia.org/wiki/Character_encoding#Common_character_encodings

The Main Window
================

The main window is divided into left and right halves.
The left half is for editing.
The right half is for the Image, Find, Notes and other panels.

You can make the window larger by dragging a corner.
You can slide the "splitter" bar left and right.
The position and size of the window and position of the splitter are
remembered from one session to the next.

If you quit PPQT with books open, it remembers their names.
When you start PPQT, it asks if you want to re-open those books.
Otherwise, it starts with one empty book named "Untitled-0".

When you tell PPQT to Quit, it checks to see if any open book has been modified
since it was saved.
For each modified file it asks you if you want to save it.
You can save, not save, or cancel the Quit.

The main window has two important features, the Preferences dialog and the File menu.

.. _Preferences:

Preferences
------------

You find the Preferences dialog in the File menu (Windows and Linux)
or under the Application menu (Mac OS).
The Preferences dialog lets you choose three different file paths,
a default spell-check dictionary,
the font for the editor,
and four kinds of text highlighting used in the editor.
These choices are explained below.

Your choices are saved when the PPQT ends and restored when it next starts up.

At the bottom of the dialog are four buttons:

Set Defaults:
  Sets all the preference choices to default values and Applies them.

Cancel:
  Closes the dialog without applying any further changes.

Apply:
  Applies any changes you have made.

OK:
  Applies all changes you have made and closes the dialog.

.. _Bookloupe path:

Bookloupe path
^^^^^^^^^^^^^^

The `Bookloupe panel`_ displays the messages produced by the 
Bookloupe program.
PPQT needs to know the path to the bookloupe executable.
Otherwise, the Bookloupe panel will remain empty.

If you have not installed Bookloupe, you can find it at the `Bookloupe home page`_.

.. _Bookloupe home page: http://www.juiblex.co.uk/pgdp/bookloupe/

You can click the Browse button to find the bookloupe program,
or you can type or paste the file path into the text field.
You must enter a path to a file that is readable and executable.
If the path is not to a readable, executable file the text field 
remains pink and the choice will not be applied.

Although PPQT ensures that you choose an executable file it does not
verify that the file is in fact, bookloupe.

.. _Extras path:

Extras path
^^^^^^^^^^^^

The Extras_ folder is where PPQT looks for this help file
and other useful things.

You can click the Browse button to find the folder,
or you can type or paste the file path into the text field.
You must enter a path to a folder that is readable.
If the path is not to a readable folder, the text field
remains pink and the choice will not be applied.

.. _Dictionaries path:

Dictionaries path
^^^^^^^^^^^^^^^^^

PPQT looks for spelling dictionaries in three places:
first, in the folder of the current book file;
second in the folder you choose here;
third in the Extras folder.

When PPQT is distributed, there is a folder named ``dictionaries``
inside the Extras folder
that contains dictionaries for several languages.
However, you can move or copy that folder to some other place,
or create a dictionary folder of your own.
Use this preference to set the path to your folder of dictionaries.

You can click the Browse button to find the folder,
or you can type or paste the file path into the text field.
You must enter a path to a folder that is readable.
If the path is not to a readable folder, the text field
remains pink and the choice will not be applied.

.. _Default Dictionary:

Default Dictionary
^^^^^^^^^^^^^^^^^^

When you open a book for the first time, or when you create a new, empty file,
PPQT assigns this spelling dictionary.
Choose the dictionary for the language used by most of the books you work on.

The pop-up list contains all the dictionaries found on the `Dictionaries path`_ 
and on the `Extras path`_.
If you change those paths, the contents of this pop-up list changes.

You can change the spelling dictionary assigned to a book: see Dictionaries_.
The name of the dictionary is saved with the book.

.. _Edit font:

Edit Font
^^^^^^^^^

The `Edit panel`_ displays text using this font.
You can change the size of the font at any time in each Edit panel.
Here you choose the font family for all edit panels.
Choose a monospaced font that clearly distinguishes similar letters
(1/l, O/0, B/8) and has a good repertoire of characters.

The pop-up list contains all monospaced fonts known in your system.
It always includes Liberation Mono and Cousine which are embedded in the program.

.. _Edit highlights:

Edit Highlights
^^^^^^^^^^^^^^^

There are four choices of text highlighting:

* Scanno highlighting sets how "scannos" (words that are often scanned
  incorrectly in the OCR process) are marked.
  The default is a light purple background.

* Spellcheck highlighting sets how words that fail spellcheck are marked.
  The default is a wiggly red underline.

* Find Range highlighting sets how the extent of a limited Find range is marked
  (see `Find range`_).
  The default is a light cyan background.

* Current line highlighting sets how the text line with the edit cursor
  is marked.
  The default is a very pale yellow background.

For each kind of highlighting, you choose whether it uses an underline
or a background color.
If you select "No Underline" from the pop-up list, the highlight is applied
as a background color.
If you select one of the underline styles, the highlight is applied as
an underline in that style.

You select the color of the highlight by clicking the small color swatch.
A color-choice dialog is presented.
The color you choose is set in the swatch.

When you change the color or the underline style, the text sample
changes to show the effect.

File Menu
----------

Use the File menu to open and save books,
to open and save Find button definitions,
and to display this Help window.

File: New
^^^^^^^^^^

This creates a new, empty edit panel.
The name of the panel is "Untitled-*n*".
It has no data and is not modified.
The `Default Dictionary`_ is assigned to it.

If you save this file you will be asked to give it a name.
When you save it, a Metadata_ file will also be created. 

File: Open
^^^^^^^^^^^

This displays a dialog to open an existing file.
Choose the book file to edit.
The contents of the book file are displayed in a new `Edit panel`_.
If there is a ``pngs`` folder in the same location, the images in it
are displayed in the `Images panel`_.

If there is a Metadata_ file in the same folder, PPQT knows
that this book has been saved before.
PPQT reads the metadata file and restores all the information about
the book that is in it.
For example, it restores the default dictionary for the book,
and any Bookmarks_ you had set.

PPQT checks that the metadata file matches the book file.
It is possible, for example, to restore the book file from backup but
not the metadata file.
If the metadata was not saved at the same time as the book, PPQT warns you.

.. _First open:

Opening for the first time
^^^^^^^^^^^^^^^^^^^^^^^^^^^
When there is no metadata file, PPQT assumes this is the first time the
book has been opened.
In this case it does the following things:

* It assigns the `Default Dictionary`_ and initializes other metadata.
  When you save the book, a metadata file will also be created.

* It scans the book text looking for page-separator lines like this:

    ``-----File: 006.png---\proofer\puffer\ruffler\fiddlestix\--------``

  The position of these lines is noted in the `Pages panel`_.
  The names
  of the image files (``006.png`` in the example) are saved for use by
  the `Images panel`_.

* It looks for a file named ``good_words*.*``
  and if one exists, its contents are loaded as the list of words that are
  not spell-checked but are always correctly spelled.
  See `Good words list`_.

* It also looks for ``bad_words*.*``
  and loads its contents as the list of words that are always wrongly spelled.

Just as with the book file,
PPQT *expects* the ``good_words`` and ``bad_words`` files to be encoded UTF-8.
If they are actually encoded Latin-1,
you need to tell PPQT by making their filenames end in ``-ltn`` (``good_words-ltn.txt``)
or by giving them the ``.ltn`` suffix (``good_words.ltn``).

The good- and bad-word files are only read on this occasion, and never again.
Their contents are saved in the metadata file.
You can edit the good-words list in the `Words panel`_.
You can only change the bad-words list by editing the metadata file.

File: Recent Files
^^^^^^^^^^^^^^^^^^^

This sub-menu contains the names of files you have opened during this session
and closed.
Use it to quickly re-open a file.

File: Save and Save-As
^^^^^^^^^^^^^^^^^^^^^^^

These choices write the contents of the active `Edit panel`_ into the book file,
and also write a Metadata_ file, creating it if necessary.

PPQT *always* writes a metadata file when you save a file.
For this reason, PPQT is not a good choice for editing ordinary text files.

File: Close
^^^^^^^^^^^^

This closes the active `Edit panel`_ and all its other panels.
You can also close the active book with a keyboard signal, usually control-w.

If the text in the active editor has been modified,
PPQT asks you if you want to save the book first.

File: Load and Save Find Buttons
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use these choices to save and load sets of customized `Find buttons`_ in the
`Find panel`_.

The Load action shows a dialog to look for an existing file.
The dialog is initialized to start in the folder for the active book.
The file you select is given to the Find panel.
The Find panel reads the text looking for valid definitions of custom buttons,
and installing them.
It silently ignores anything that else.
It does not diagnose errors.

The Save action displays a save dialog.
The dialog is initialized to start in the folder for the active book.
The file you specify is written as a UTF-8 text file containing definitions
of all custom Find buttons that are not empty.

.. _Edit panel:

Edit panel
==========

The edit panel contains a standard, modern plain-text editor.
At the bottom of the panel are the following fields:

Bookname:
  The name of the book is in bold red letters if the text has been modified,
  or if the metadata has changed in any way. When you open a book for the first
  time it is marked as modified immediately, because its metadata is new.

Folio:
  Shows the folio (visible page number) of the page under the cursor.
  Initially this is the index number of the page, from 1 to the end.
  Use the `Pages panel`_ to make folio values match the original book.

Image:
  Shows the filename of the image file for the page under the cursor.
  This is the image file shown in the `Images panel`_.
  Image filenames are usually decimal numbers, but they can be
  alphanumeric.

  You can type the name of a different image file in this field.
  When you press Enter the cursor moves to the top of that page.
  
Line#:
  Shows the number of the line under the cursor.
  Line numbers start at 1.
  To see the how many lines are in the book,
  move the cursor to the last line (ctl-down arrow).
  
  You can type a new line number in this field.
  When you press Enter the cursor moves to that line.

Col:
  Shows the index of the character to the left of the cursor.
  Position 0 is at the left margin.
  To see how many characters are in the line,
  move the cursor to the end of the line (ctl-right arrow).

Editing
---------

In the editor the current line is highlighted.
Usually it is pale yellow, but see `Edit Highlights`_.

You can change the size of the font.
Key ctl-hyphen to display text one point smaller.
Key ctl-plus to display text one point larger.

You can select text in the usual ways:

* dragging
* double-click to select a word
* triple-click to select a line

You can extend the selection by shift-click,
or by holding the shift key and pressing any arrow key.
You can also extend the selection by
selecting one of the Bookmarks_ while holding the shift key.

You can move the selected text by dragging it.
You can copy the selected text to a new location by alt-dragging.

While the focus is in the editor, the Edit menu has
functions for Cut, Copy and Paste; 
for Undo and Redo;
and for changing the selection to Uppercase, Titlecase, and Lowercase.

Editing Keys
-------------------

The arrow keys and the Home, End, PageUp and PageDown keys work together
with the control key to move the edit cursor.
These keys follow the usual conventions for your operating system.

Add the shift key to any cursor move to extend the selection by that amount.
For example, ctl-right arrow goes to the end of the line,
but shift-ctl-right arrow selects text to the end of the line.

Other editing keys are:

* ctl-c/ctl-x/ctl-v for copy/cut/paste
* ctl-z for undo
* ctl-y, also shift-ctl-z for redo
* shift-ctl-u, shift-ctl-l, shift-ctl-i change the selected text
  to uppercase, lowercase, or titlecase (Unicode-aware)

The following keys work in conjunction with the `Find panel`_.

* ctl-f: display the Find panel and put the focus there.
* shift-ctl-f: copy the selected text to the Find panel
  and put the focus there ("find this").
* ctl-g: repeat the last search forward (same as Find Next).
* shift-ctl-g: repeat the last search backward (same as Find Prior).
* ctl-=: replace selection (same as Find panel Replace button #1).
* ctl-t: replace selection and Find Next.
* shift-ctl-t: replace selection and Find Prior.

.. _Bookmarks:

Bookmarks
-----------

You may set 9 bookmarks or saved cursor positions.
The bookmarks are saved in the metadata file.

To set a bookmark, on Windows or Linux
key ctl-alt-1 through ctl-alt-9 to set bookmark 1-9 to the cursor position.

On Mac OS, use control-command-1 to control-command-9.

If text is selected, the length of the selection is saved with the bookmark.

Key ctl-1 through ctl-9 to jump to bookmark 1-9
(Mac: command-1 to command-9).
This clears any text selection, and if the bookmark included a selection,
it is restored.

Key shift-ctl-1 through shift-ctl-9 to extend the current selection to 
the position of bookmark 1-9.
(Mac: shift-command-1 to 9. However under Mac OS X,
shift-command-3 is "capture screen" and shift-command-4 is "capture selection".
You cannot use these keys to extend a selection to bookmark 3 or 4,
unless you use System Preferences to disable these two keys.)

Context Menu
------------

Right-click or control-click in the editor to bring up a context menu with five actions.

.. _Marking Scannos:

Marking Scannos
--------------------

Select Mark Scannos to turn on or off the highlighting of common OCR errors.
The style of highlighting is set by `Edit highlights`_.
The marks only appear if a scannos file has been loaded.

Select "Scanno File..." to choose a file with a list of scanno words
to mark, for example en-common in the Extras folder.

.. _Marking Spelling:

Marking Spelling
-------------------

Select Mark Spelling to turn on or off the highlighting of words that fail spellcheck
with the current dictionary.
The style of highlighting is set by `Edit highlights`_.

.. _Dictionaries:

Dictionaries
^^^^^^^^^^^^^

Most words in the book are checked for spelling against the dictionary you have assigned
to the book.
The `Default Dictionary`_ is assigned when a book is opened for the first time.

Choose the Dictionary... action in the context menu to assign a different dictionary.
It presents a list of dictionaries as found in the following places:

* First, the folder containing the book file.
  If you want to use a certain dictionary for this book only, put a copy of the
  dictionary in the book folder.

* Second, the `Dictionaries path`_ is searched for dictionary files.
  Any dictionaries found there are added to the list.

* Finally, the `Extras path`_ is searched for dictionary files.

Dictionaries are named with two lowercase letters for the language
and two uppercase letters for the nation.
For example, ``en_GB`` is English for Great Britain; ``fr_CA`` is French for Canada.
If there are dictionaries with the same name, for example if there are two
dictionaries with the name ``en_GB``, the one found first in the above sequence is shown.

When you assign a different dictionary, PPQT re-checks the spelling of all words.

You can have specific words checked against an alternate dictionary.
You do this by surrounding those words with any HTML code containing
the ``lang=`` property. For example:

    ``<span lang='fr_FR'>Je t'aime</span> he whispered.``

The words ``je t'aime`` will be spell-checked against dictionary ``fr_FR`` 
provided a dictionary of that name exists somewhere in the dictionary search path
given above.

You may put the ``lang=`` property in any HTML markup, but it is probably
best to only use the ``span`` markup for this purpose.

Translators_ may or may not support the use of ``span`` markup or the ``lang=`` property.

Book Facts
-------------------

Select Book Facts... in the context menu to enter information about the book
such as its title, author, or publication date.
Facts of this kind are often referred to as "metadata". 
However in this document, we use "metadata" to mean all the many kinds of
information stored in a `Metadata file`_.

This action displays a dialog with a multi-line text entry area.
You may enter any number of facts about the book in this form:

    *fact-name* **:** *fact-value*

For example:

| ``Title : A Tendentious Blather``
| ``Published:1842``.
| ``Author   :  Phlebotomous Millrash``

Both the *fact-name* and the *fact-value* may contain spaces or special characters.

This collection of facts is saved in the metadata file.
It is presented to the Translators_ for use in translation.
Not all Translators use the book facts.
Different translators may have different rules about the format of titles and facts.

.. _Images panel:

Images Panel
=================

The Images panel displays the scanned page images of the book.
The image files must be stored as files of type ``.png`` in a folder named ``pngs``
in the same folder as the book.

When the book is opened for the first time, the names of the image files
are copied from the page-separator lines.
Each time the edit cursor enters the text of a different book page,
the Images panel displays the image file for that page.

You can zoom the page image from the keyboard.
Click on the image and then key control-+ to zoom in (larger)
and control-minus to zoom out (smaller).
The zoom changes by about 16% each time.

When the image is too large to fit in the window,
scroll bars appear on the bottom and right side.

At the bottom of the panel there are three zoom controls.
You can use the numeric box to specify a zoom value from 15% up to 200%.
You can click the "to Height" button to zoom the image so that the printed part
fills the window top to bottom.
Click "to Width" to zoom the image so that the printed part
fills the window from side to side.
These buttons take any dark pixels as part of the printing.
If there is a marginal note or some kind of blob or fly-speck on the page,
the buttons may not zoom as much as you expect.

Normally the Images panel follows the edit cursor.
As you move the cursor through the text, the image changes to match.
You can disable this by clicking the little hand icon at the top left of the panel.
When that hand is open, moving the edit cursor has no effect on the image.
When the hand is closed, the edit panel "grips" the image panel,
and the images follow the edit cursor.

You can click in the Images panel and then use the Page Up and Page Down
keys to step through images.
Do this when you want to look at some page before or after the current page.
Normally this has no effect on the edit cursor.
You can change this by clicking the little hand icon at the bottom left of the panel.
When that hand is closed, the Images panel "grips" the edit panel.
If you use Page Up or Page Down in the Images panel, the edit cursor will
follow along.

.. _Notes panel:

Notes Panel
=================

The Notes panel is a simple text editor.
Use it to keep notes about the book as you process it.
For example you might make notes on

* typos you find and correct
* usage of special characters
* a to-do list of things not to forget
* drafts of your Transcriber's Note
* complex tables or other special formatting that needs attention

The contents of the Notes panel are saved in the Metadata_ file
and loaded again when the book is opened.

While the focus is in the Notes panel, the Edit menu has commands
for Undo/Redo, Cut/Copy/Paste, Find and Find-Next, with the usual
keyboard accelerators.
The Find operation is a local search within the note text.

With the focus in the Notes panel, key shift-ctl-m to insert
the line number of the book edit cursor, in curly braces: ``{2217}``.
Use this feature to note a location, for instance the line where
a typo is found.

Place the cursor in or near one of these line numbers and key ctl-m.
The book edit panel jumps to that line number.

Key shift-ctl-p to insert the page number of the book edit cursor
in square brackets: ``[138]``.
Use this to note the location of, for example, a table you need to format.

Place the cursor in or near one of these page numbers and key ctl-p.
The book edit panel will jump to the top of that page.


.. _Find panel:

Find Panel
=================

Use the Find panel to search for text and replace it.
The panel has three groups of controls.
There is a block of controls for searching.
Below it is a block of controls for replacing.
At the bottom is a block of user buttons.

Controls for searching
-----------------------

The top group of controls are for searching.
In the center is a large text-entry field.
Here you enter the text you want to find in the book.

Just left of the search text field is a small clock icon.
This reveals a pop-up list of up to ten recent searches.
To repeat a search, select it in this list.

Below the search text are four buttons:

**First**
  looks for the search text starting at the top of the book
  (or the top of the range).
  It finds the first occurrence of the text.

**Last**
  looks for the search text starting at the `end` of the book
  (or the end of the range) and searching `backward`.
  It finds the last occurrence of the text.

**Next**
  looks for the search text moving forward from the current
  cursor location.
  It stops looking at the end of the book (or the end of the range).

**Prior**
  looks for the search text moving `backward` from the current
  cursor location.
  It stops looking at the top of the book (or top of the range).

Above the search text are four switches:

When **Respect Case** is on (✓), letter case is significant: A≠a.
When it is off, letter case is ignored.

When **Whole Word** is on (✓), normal searches will only match to
complete words.
This switch is disabled during regular-expression searches.
(In a regular expression, use ``\b`` to find a word-boundary.)

When **Regex** is on (✓), the search text is a `regular expression`_.
When it is off, the search text is compared normally

**In Range** is used to confine search and replace to a
limited range of the book text.
  
.. _Find range:

Using a Limited Find Range
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use a limited Find range when you want to use search and replace in one
part of the book.

For example, suppose you are working on the Table of Contents,
and you want to make use find/replace to make changes only in that part of the book.
Select the Table of Contents by clicking at the top of it,
and shift-clicking at the end.
Then on the Find panel, click **In Range**.
The text selection will be highlighted to show it is now
a Find Range.
(The highlight is normally light-blue, but see `Edit highlights`_.)

Now searches and replaces will take place in that range only.
First will find the first match in the range,
Last will find the last match in the range,
Next and Prior will stop at the ends of the range.
Especially useful, a "replace all" will replace only the
matching text in the range.

To remove the limited range, turn off the **In Range** switch.

Controls for Replacing
-----------------------

There are three replace text fields.
You can use any of the fields to replace the last text you found.
For example, suppose you want to search for bold markup
(``<b>`` or ``</b>``).
Some of the time you want to replace the markup with a double asterisk,
and sometimes you want to delete it.
Set the Find text to ``</?b>`` and turn on **Regex**.
Put the double asterisk in the first replace field.
Clear the second replace field.
Click **First**.
Then decide: replace or delete?
Click the first **Replace** button to replace the found text with the asterisks.
Click the second **Replace** button to replace it with nothing, that is, to delete it.
Click **Next** and repeat.

Each replace field has its own **Replace** button.
Each has a clock icon that pops up a list of recent replacement strings.

A **Replace** button only works when the current selection in the Edit panel
was created by a Find.
If you perform a Find and then move the cursor, the **Replace** buttons are disabled.

To the right of the replace fields are three switches.

**+Next**
  means, after any replace operation, do a Find Next.

**+Prior**
  means, after any Replace, do a Find Prior.

**ALL!**
  means do a global replace.

.. _Global replace:

Global Replace
^^^^^^^^^^^^^^^^

When you click any **Replace** with the **ALL!** switch checked,
PPQT finds all matches to the search text in the book,
or within the `Find range`_.
It displays a warning saying

|    OK to replace `n` occurences of
|        `search-text`
|             with
|        `replace text`

The count of matching strings `n` is shown.
If the count agrees with what you expect, click OK.
If it seems too many or too few, click Cancel.

You can Undo a global replace with Edit>Undo or ^z.

.. _regular expression:

Regular Expression Support
----------------------------

Regular expressions are an important tool for post processing.
PPQT supports "Perl-Compatible Regular Expressions" (PCRE).
This help has no details on regular expressions.
Instead, refer to these places.

* The Distributed Proofreaders `Regex Cookbook`_.
* The summary at `Regular-Expressions.info`_. Their `Regex Tutorial`_ may be helpful.
* The official summary of `PCRE syntax`_ (accurate and complete but not friendly).
* Experiment, test and debug your regexes in an interactive test page.
  `Regulex`_ is a good one but doesn't recognize all the PCRE doodads;
  `Rubular`_ and `RegexPlanet`_ work ok.
* When puzzled, ask for help in the Distributed Proofreaders `Regular expression clinic`_.

.. _Regex Cookbook: http://www.pgdp.net/wiki/Regex_Cookbook
.. _Regular-Expressions.info: http://www.regular-expressions.info/refquick.html
.. _Regex Tutorial: http://www.regular-expressions.info/tutorialcnt.html
.. _PCRE syntax: http://www.pcre.org/current/doc/html/pcre2syntax.html
.. _Regulex: http://jex.im/regulex
.. _Rubular: http://rubular.com/
.. _RegexPlanet: http://www.regexplanet.com/advanced/java/index.html
.. _Regular expression clinic: http://www.pgdp.net/phpBB2/viewtopic.php?t=4381

When the Regex switch is on, the Find string must be a valid regular
expression.
When the Find string is not a valid regular expression
the background of the field is pink and none of the Find buttons will work.
To see a diagnostic message, hover the mouse over the Find field.

It is possible for a regular expression Replace string to be invalid.
For example, if the string contains ``\2`` (a reference to the second
parenthesized group in the Find expression) but there is no second group,
this is an error.

Errors in Replace strings cannot be detected in advance of actually using them.
When you click Replace after a regular expression search,
you may be shown an error dialog.
The dialog contains a diagnostic message explaining the error.


.. _Find buttons:

Using the Find buttons
-----------------------

At the bottom of the Find panel is an array of 24 buttons.
You use these to save find/replace operations for use later.
These are especially useful when you have with great effort worked
out a complicated regular expression. 

Programming a button
^^^^^^^^^^^^^^^^^^^^^

To program one button,

* Create and test a complicated find/replace operation.

* When the operation is working correctly, control-click or right-click on any button.
  A dialog opens asking you to "Enter a short label for button `n`".

* Enter a word to remind you of the operation you are saving.

* When you click OK, all the Find and Replace controls are saved
  in this button. The Find text, the Respect Case, Whole Word, and Regex switches,
  all three Replace texts, and the +Next, +Prior and ALL! switches are recorded.

When you want to perform the same operation later, just click that button.
All the controls are set as they were when you programmed the button.

To clear the definition of a button, right-click on it and then click OK
without entering a label.
The button will be shown as (empty).

Saving and loading the buttons
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To save all defined buttons into a file, select File > Save Find Buttons.
Choose the name and location for the small file.
You might save it with the book, or in the Extras folder, or anywhere you like.
The file that is created is a text file encoded UTF-8.
It contains definitions of all the non-empty buttons.
Buttons marked "(empty)" are not saved.

You may edit a file of saved buttons.
(PPQT is not a good editor for this. Use some other simple text editor.)
One reason to edit a file of buttons is to add "tooltip" strings to them.

To load a file of buttons, select File > Load Find Buttons.
Choose a file of saved buttons.

Buttons distributed with PPQT
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Several files of saved buttons are located in the Extras folder.
They define some interested regular-expression search and replace operations.
You can edit these files (in some other text editor).
They contain comments documenting the regular expressions.

``clear_all_buttons.utf``
  This file loads "(empty)" definitions for all 24 buttons.
  Normally when you save the buttons, only the non-empty ones are saved.
  So this file was made by hand.

``find_page_separators.utf``
  This defines button 23 to find any page-separator line.
  The regular expression is quite complex and is documented in the file.

``common_errors.utf``
  This loads buttons 7-23 with expressions that search for common errors.
  Some of the regular expressions are documented in the file.

  7. "Faux hyphens", Unicode characters that look like hyphens 
  8. Whitespace before punctuation or after a hyphen
  9. Stand-alone 0 or 1
  10. Some unbalanced delimiters
  11. Dot followed by space followed by lowercase letter
  12. Comma followed by space and uppercase letter
  13. Single-letter line
  14. Paragraph starting with lowercase
  15. Non-Latin-1 letters
  16. Non-7-bit letters
  17. End of paragraph without punctuation
  18. Line longer than 75 characters
  19. Dash at end of line
  20. Space at end of line
  21. Closing quote without preceding punctuation
  22. Multiple punctuation characters
  23. Any asterisk (e.g. proofer notes)
  
``review_text_markup.utf``

  This loads buttons 18-23 with convenient operations on markup:
  
  18. Find \<tb>, replace with 5-star string
  19. Find open and close block markup lines such as /\*, /Q, P/, etc.
  20. Find "[typo:orig:fixed]" and replace with "fixed"
  21. Find \<sc> markup and replace
  22. Find \<b> markup and replace
  23. Find \<i> markup and replace

``unbalanced_markup.utf``

  This loads buttons 21-23 with searches that find most cases of
  unbalanced italic, bold, and smallcap markup.

See the file "Suggested Workflow" for how to use these buttons.

.. _Characters panel:

Characters Panel
=================

The Characters panel shows you all the characters used in the book.
Click the **Refresh** button to update the counts.

The table shows you

* The symbol of the character
* Its value in hexadecimal
* The count of how many times it appears in the book
* The HTML Entity value for the character
* Its Unicode letter category
* Its Unicode name

Click on any column heading to sort the table on that column.

Double-click on some character in the first column.
That character is placed in the `Find panel`_ as the Find text.
The **Respect Case** switch is on, 
and the Edit panel scrolls to show first occurrence of that character.

If you double-click on the HTML entity column,
the Entity value is also put into the first Replace string field.

In the upper right there is a pop-up menu with three choices.
These are "filters" that make the table display only certain characters.

**All**
  makes the table display all the characters.

**Not 7-bit**
  makes the table display only characters with values greater than 127 (hex 7f).
  These characters are not valid in an ASCII etext.

**Not Latin-1**
  makes the table display only characters with values greater than 255 (hex ff).
  These characters are not valid in a Latin-1 etext.

.. _Words panel:

Words Panel
=================

The Words panel displays all the words in the book.
Use it to find words that are often errors.
In particular the Words panel is your best tool for correcting spelling.
The file "Suggested Workflow" in the Extras folder describes 
the procedure for correcting spelling errors and other ways to use the Words panel.

Click the **Refresh** button to update the words and their counts after editing.
When a book has more than a few thousand unique words, the Refresh
operation may take a few seconds.

Click on any column heading to sort the table on that column.
The sort is "locale-aware" and Unicode aware.
As a result, all forms of a letter sort near each other.

When the **Respect Case** switch is on, words that have initial capital letters
sort together.
This makes it easy to view proper nouns and acronyms.
Turn **Respect Case** off to make all forms of a letter sort together.

The table shows three items about each word:

* The word itself.

  Be aware that PPQT defines "word" rather loosely.
  A "word" may include digits, hyphens and apostrophes.
  "Mother-in-law's" is a word, as is "1925ʼs" (note the curly apostrophe).

* The count of times the word appears in the book.

* The "features" of the word. Features include:

  * 'A' if the word contains an uppercase letter.
  * 'a' if the word contains a lowercase letter
  * '9' if the word contains a digit
  * 'h' if the word contains a hyphen
  * 'p' if the word contains an apostrophe
  * 'X' if the word fails spellcheck

The uppercase, lowercase and digit tests are Unicode-aware.

A word has the hyphen feature if it contains the Latin-1 hyphen (\\u002d)
or the Unicode hyphen (\\u2010).
(For other types of hyphen, see the "Similar words" feature below.)

The check for apostrophe recognizes the Latin-1 quote (\\u0027),
the Unicode modifier letter apostrophe (\\u02bc)
and the right single quote (\\u2019). 

With the focus in the Word panel, key any letter.
The table scrolls to put the first word starting with that letter in the middle of the window.

You can search for words within the table using the Edit>Find menu command or by 
keying control-f (command-f).
Enter some letters and press Return.
The table scrolls to the first word that starts with those letters.
Key control-g (command-g) to search for the next match.

Searching for a word in the text of the book
---------------------------------------------

Double-click any word in the table.
The `Find panel`_ is displayed.
The text of that word is in the Find text field.
**Respect Case** and **Whole Word** are checked.
The Edit panel scrolls to show the first occurrence of the word.

Filtering the words
------------------------

At the upper right of the panel is a pop-up menu of "filters".
You can filter the table to show only:

* All-uppercase words
* All-lowercase words
* Mixed-case words (words with both an uppercase and a lowercase letter)
* All-numeric words
* Alpha-numeric words (words with at least one letter and one digit)
* Hyphenated words
* Words containing an apostrophe
* Words that fail spellcheck

To return to the full list, select the **All** choice from the pop-up menu.

Context Menu
------------------------

Right-click on a row to open a context menu with three actions.

Words Similar to This
  Filters the table to show only words that are like the clicked word
  if letter case, apostrophes, and all types of hyphens are ignored.
  If the word is "to-day", similar words include "To-Day" and "today".
  
  Use this to find inconsistent usage of hyphens and apostrophes.
  This filter ignores all Unicode characters that
  are hyphen-like, including non-breaking hyphen (\\u2011),
  figure dash (\\u2012), en-dash, (\\u2013), small figure dash (\\ufe58),
  small hyphen-minus (\\ufe63), and fullwidth hyphen-minus (\\uff0d).
  So if a word is similar to a hyphenated word, but does not show an
  "h" in the features column, it may contain one of these "faux hyphens". 

First Harmonic
  Filters the table to show words that are the same as that word
  except for one edit change: one insertion, or one deletion, 
  or one change.
  
  If the word is "dog" other words might include
  "doe" (one change), "do" (one deletion) and "dogs"
  (one insertion), but not "Do" because that needs
  two changes (d to D and delete the g).

Second Harmonic
  Filters the table to show words that are the same as that word
  except for exactly two edit changes.
  
  If the word is "dog" other
  words might include "Dow" or "foe" (two changes), "doggy" (two
  insertions) or "dang" (one insertion, one change).

First and Second Harmonics are good tools for finding keywords that
proofers might misspell, such as Footnote or Illustration.
For example, the First Harmonic of the word `Footnote` would include
`Footnotes` and `footnote`; and the Second harmonic would include
`footnotes` and `Footntoe`.

.. _Good words list:

Good Words list
------------------------

Beside the table of words is a one-column list headed "Good Words".
This contains the list of words that are always correctly spelled.
It is initialized from the good_words file that is loaded
when the book is opened for the first time (see `First open`_).
The words in this list are saved in the `Metadata`_.

Words in this list are never shown as spelling errors.
You can add words to the list in two ways.
You can select words in the Word table and then drag them and drop them on the
Good Words list.
You can copy a word or words from the book text and paste them into the Good Words list.

You can remove words from the Good Words list.
Click in the list to select a word or words.
Then key Delete or Backspace.

.. _Pages panel:

Pages Panel
=================

The Pages panel displays a table with one row for each page boundary in the book.
It is initialized from the page separator lines the first time you open a book
(see `First open`_).

The first column of the table shows the name of the scanned image file for that page.
For example if the scanned image file is ``0078.png`` in the ``pngs`` folder,
this column shows 0078.

The fifth column of the table shows a list of the names of the proofers who worked on
that page.

The second, third and fourth columns are used to control the Folio, or visible page number
value for this page.
You use these columns to make the folio numbers agree with the folios printed in the book.
For example, a book might begin with four pages that have no number.
Then might come several pages that are numbered in lowercase Roman numerals,
i, ii, ... xvi.
After this, the main part of the book begins with Arabic page number 1 and
continues to the end, perhaps numbered 278.

Column 1 of the table shows the format of the folio for this page.
This column may have any of four values:

Arabic
   The folio is an Arabic numeral like 399.

roman
   The folio is a lowercase Roman numeral like xiv.
   
ROMAN
   The folio is an uppercase Roman numeral like XIV.

(same)
   The folio has the same format as the page above it.

Column 2 of the table has a rule saying how the folio value for this page is computed:

Omit
    There is no folio on this page.
Add 1
    The folio is made by adding 1 to the folio of the nearest preceding page
    that is not set to "Omit".
Set to:
    The folio is set to a specific number to start a new sequence.

Column 3 of the table shows the result of applying these rules.

When the book is first opened,
the first page is set to format:Arabic, rule:Set to 1. 
All other pages are set to format:(same), rule:Add 1.
The result is that the Folio numbers are just the sequence numbers of the scan images.
These numbers will usually match the image names, that is,
image 0027 will have Folio 27.

To change the format, double-click in column 2.
A small pop-up menu appears.
Select Arabic, roman, ROMAN or (same) for that page.

To change the folio rule, double-click in column 3.
A small pop-up menu appears.
Select Omit, Add 1, or Set to:.

If you choose the rule Set to, you can double-click in column 4.
A small numeric entry field appears.
Use it to set the folio value for this page.

In each of these menus, you can cancel the action by keying Escape.
Key Enter to accept the value.

Click the Refresh button to update the table with changes.
For example, double-click the first row, column 4.
Set the starting folio to 5.
Click refresh and see how all the other rows are now
numbered from 5 instead of from 1.

Using this table you can make the folio values agree exactly with the
folios printed in the book.

At the top of the table is a text field.
You can put a string of text here and click Insert.
A warning dialog asks if it is OK to insert text on every page.
If you click OK, the text in the field is inserted at the start of every page.

The inserted text may include the string ``%f``. 
This will be replaced with the folio value on each page.
The text may include %i; it will be replaced with the image filename.

Translators_ may or may not preserve, or use, the Folio values.

.. _Footnote panel:

Footnote Panel
=================

The Footnote panel displays footnotes that are coded according to
the DP formatting guidelines.
Click **Refresh**.
The panel scans the book and displays one row for each footnote.
The Footnote panel works with these definitions:

Anchor
  An `Anchor` is text in square brackets
  that shows where a footnote is used, for example ``[A]``.

Note
  The note begins with ``[Footnote A:`` and a space.
  A note may contain many lines of text and other markup
  including quotes and tables. It ends with a line in which
  ``]`` is the last character on the line.

Key
  The `Key` of a footnote is the letter, number or symbol that
  appears in both the Anchor and the Note and connects them.

The table displays the notes in these six columns:

Key
  The letter, number or symbol that appears in this Anchor and Note.
Class
  There are six possible classes of Keys: Arabic (123), ROMAN (IVX),
  roman (ivx), lowercase (abc), uppercase (ABC) or symbol (\*¤§).
Anchor line
  The line number of the book where the Anchor of this footnote is found.
Note line
  The line number of the book where the Note of this footnote begins.
Note length
  The number of lines of text in this footnote.
Note text
  The first 40 characters or so of the Note.

Click on an Anchor line cell.
The edit cursor jumps to the Anchor line.
Click on a Note line cell.
The edit cursor jumps to the first line of the Note.

Click repeatedly on a Key cell.
The edit cursor jumps between the Anchor line and the Note line.
In this way you can "bounce" the cursor back and forth between the
Anchor and the Note.

Footnote errors and warnings
--------------------------------

If PPQT finds what appears to be an Anchor, but cannot find a Note
with the same Key, it displays that row of the table in pink.
The Note line column is blank.

If PPQT finds what looks like a Note but did not find an Anchor
with the same Key, it displays that row of the table in pink.
The Anchor line column is blank.

If any rows of the table are pink, the **Renumber** and **Move to Zones**
buttons do not work.

If the Note line is 50 or more lines beyond the Anchor line,
the table row is shown in green.
Also if the Note length is greater than 10, the table row is shown in green.
These represent possible errors that should be examined.

Renumbering
------------

When you click **Renumber**, if there are no pink rows in the table,
PPQT renumbers all the notes.

There are five "number streams", one for each Class of Anchor.
Each stream is initialized to 1, and incremented each time it is used.
For example, the abc stream produces a series of lowercase letters,
from a to zzz. The 123 stream produces a series of Arabic numbers,
from 1 to 999.

At the bottom of the Footnote panel are six pop-up menus, one for each
class of Key.
Use these to say which stream will provide the numbers to that class of Key.
For example, you can set class ABC to receive numbers from the 123 stream.
Then all uppercase Keys will be replaced with Arabic numbers.

PPQT looks at each footnote in turn from the top of the book to the end.
It gives that footnote the next sequential number from the stream
you have assigned to its class of Key.

Renumbering footnotes is a single-undo operation.
Click in the Edit panel and key ctl-z to undo it.

Be aware that some Roman numerals are also letters.
If there is a footnote with a Key value of ``i`` or ``X``,
it will be classed as Roman ivx or IVX.
If you renumber all footnotes with uppercase alphabetic Keys,
a few will be classed as Roman.
The ninth footnote will have Key ``I`` and the 22nd key will
have Key ``V``.
To make sure there are no mistakes, when you renumber
with alphabetic Keys,
set the Roman classes to use the same number stream as the alphabetic classes.

Moving Footnotes
--------------------

When you click **Move to Zones**, if there are no pink rows in the table,
PPQT moves footnotes to marked footnote zones.

You create a footnote zone by inserting two lines:

|  ``/F``
|  ``F/``

PPQT examines each Note from the top of the book down.
If the Note is not already inside a zone, PPQT looks for a zone
below the Note.
If there is a zone below the Note, the lines of the Note are
moved to the bottom of that zone.

To put all Notes at the ends of the chapters, insert a footnote zone
after the last paragraph of every chapter.
To put all Notes at the end of the book, put a single zone at the
end of the final chapter.

You can insert a heading into a zone: 

|  ``/F``
|
|
|  ``FOOTNOTES``
|
|  ``F/``

The moved notes go to the end of the zone, above the ``F/`` line.
Anything other than headings and footnotes in a footnote zone will
cause a "document structure error".

Moving footnotes is a single-undo operation.

.. _Bookloupe panel:

Bookloupe Panel
=================

The `Bookloupe`_ program is a utility that reads a DP book file
and looks for many different types of common errors.

.. _Bookloupe: http://www.juiblex.co.uk/pgdp/bookloupe/

Using the Bookloupe panel you run Bookloupe against the book being edited.
The many diagnostic messages are displayed in a convenient table.

Before you can use the Bookloupe panel you must install `Bookloupe`_.
Then you must tell PPQT where the executable program is.
Do that with the `Bookloupe path`_ part of the Preferences panel.

Click Refresh to run Bookloupe.
The current book text is copied to a temporary file.
Bookloupe is started and reads the temporary file.
The messages it prints are captured and displayed in a table
with three columns:

Line#
  The line number mentioned in the error message.
Col#
  The column number mentioned in the error message
Diagnostic message
  The text of Bookloupe's message.

You can sort the table by clicking in the column headings.
Sort on Line# if you want to deal with the messages line by line.
Sort on Message text if you want to deal with (or ignore)
each group of similar messages.

Click on any line of the table.
The edit cursor jumps to the line and column for that message.
The current line is highlighted.
The focus remains in the table.
You can move up and down the table using the up- and down-arrow keys.
When you find an error you want to fix, click on the current line in the Edit panel.

At the top of the panel are five checkboxes.
Use these to control five of the Bookloupe command-line options
as described in the Bookloupe documentation file.

**Quotes**
  Pass the ``-p`` option that requires any open-quote
  to be closed in the same paragraph, even if the next paragraph
  begins with an open-quote.

**SQuotes**
  Pass the ``-s`` option that causes single-quote
  (apostrophe) characters to be treated the same as double-quote
  characters.

**Verbose**
  Pass the ``-v`` option so that all errors are 
  reported. When this is off, common errors that occur a large
  number of times are not reported.

**Relaxed**
  Pass the ``-x`` option which turns off some
  less-important diagnostics.

**No-CR**
  Do not pass the ``-l`` option. As a result, any line
  that terminates in LF only will be get a "No CR?" diagnostic.
  Useful for Windows text files; do not use with Linux or Mac.

.. _Translators:

Translators
=================

A Translator is a sub-program that knows how to convert
text in *guidelines format* to some other markup format.

First you use PPQT to bring a book to complete agreement
with the DP formatting guidelines.
Then you apply a Translator to change the book to another format,
for example, `PPGEN format`_ or `FPGEN format`_ or HTML, to name a
few possibilities.

The translated document appears as a new document with its own edit panel.
Its name is Untitled-n.
It has some of the metadata from the source document, for example
it has a copy of your notes from the Notes panel and the same
good-words and bad-words lists.

You inspect the translated book.
If you do not approve the translation, you can simply close it without saving it.
If the translation is satisfactory, you save it under its own name.
You can continue to edit it using PPQT, or work on it using a different editor.

.. _PPGEN format: http://www.pgdp.net/wiki/PPTools/Ppgen/Manual

.. _FPGEN format: http://www.pgdpcanada.net/wiki/index.php/Fpgen

Using and Installing Translators
----------------------------------

The available Translators are named in the File>Translators... menu.
PPQT builds this menu when it first starts up,
by inspecting the files in the Translators folder
in the `Extras`_ folder.

A Translator is a module of Python code in a file with the suffix ``.py``.
To install a Translator, just put its file in the Translators folder
in Extras, and re-start PPQT.

PPQT recommends that each Translator have a matching documentation file,
with the same filename and a different suffix.
For example a translator ``html.py`` might come with a file ``html.txt``
in which the author of the translator explains what the Translator 
can and cannot do, and how it handles PPQT extensions to DP markup.
These documentation files can be stored in the Translators folder along
with the Translators themselves.

Translation of Extended DP Format
-----------------------------------

The DP Formatting Guidelines only support two types of block markup,
``/#..#/`` for block quotes, and ``/*..*/`` for everything else.
PPQT supports additional block markers:

* ``/Q..Q/`` for block quotes,
* ``/X..X/`` for general no-reflow text,
* ``/C..C/`` for text to be centered
* ``/R..R/`` for text to be right-aligned
* ``/P..P/`` for poetry
* ``/T..T/`` for tables

The use of these codes is described in the *Suggested Workflow*
document in the Extras folder.

It is up to the writer of each Translator to support these extra
types of formatting.
If the Translator does not support a format, the Translator may
simply ignore the feature (for example, it can treat all these
forms of markup as if they were ``/*..*/``),
or it may put an error message in the translated book.

Checking Document Format
--------------------------

Before calling a Translator, PPQT checks the document format to make sure
that every markup section is properly closed, and that
sections are only nested in the permitted ways; for example
a Footnote can contain a Quote but not another Footnote.
These checks are needed in order to give the Translator a
predictable document format.

The first time you try to run a Translator, this check is likely to stop
with an error message "Document Structure Error around line `number`".
Below this it displays the name of the document element it was 
processing, and the names of the document elements that it would
accept at this point, but has not found.

Some of these errors will have an obvious cause, for example that you
have omitted the closing ``Q/`` on a Quote section.
Others will not be so obvious.
One common issue is that the algorithm that analyzes the document expects
any paragraph to end with a blank line.
This will cause an error:

|    ``...last line of a paragraph in a quote.``
|    ``Q/``

The error will say "Processing PARA, Trying to find one of EMPTY, END, LINE".
Just add a blank line after the paragraph:

|    ``...last line of a paragraph in a quote.``
|
|    ``Q/``


Writing or Editing a Translator
---------------------------------

A Translator can be written by anyone with some Python programming experience
and a good understanding of the DP markup format and the target markup format.

Anyone with even minimal Python programming skills can edit an existing Translator
to make it work differently.
Make a copy of the translator module; edit it to have a different MENU_NAME
value; and restart PPQT.
The edited Translator will show up in the File>Translators menu.

The following files are in the ``xlt_dev`` folder of the Extras folder:

* ``TranslatorAPI.html`` documents the interface between PPQT and a Translator.

* ``skeleton.py`` is the minimal skeleton of a Translator. Copy it and
  use it as the basis of a new Translator.

* ``testing.py`` is a simple Translator that makes a document
  showing all the "events" that PPQT passed to it. When in doubt about how
  PPQT handles some particular feature, make a small test document and
  translate it using the ``Testing`` translator.

* ``testing.utf`` is a document that exercises all the DP formatting features
  and all the PPQT extensions.

.. _Metadata:

Metadata File
==============

The PPQT metadata file is a text file in UTF-8 encoding.
The file has the same name as the book, with the addition of ``.ppqt``.
For example, a book file named ``terrif_book.utf`` has a metadata file
named ``terrif_book.utf.ppqt``.

The metadata file contains all kinds of information about the book.
The information is encoded in `JSON format`_.

.. _JSON format: https://www.json.com/

Here is a partial list of the things in the metadata file:

* Bookmark positions
* Contents of the Notes panel
* Facts about the book
* The Good words list and the Bad words list
* The Scannos list from the last scanno file opened
* The Footnote table information
* The last 10 Find strings, and the last 10 Replace strings for each Replace field
* The Page table information
* The Character table information
* The Word table information

You are welcome to browse the metadata file.
(Use some other plain text editor, not PPQT.)
In some rare circumstances you may have a reason to modify it.
For example you could add or remove words in the Bad words list,
as there is no other way to do that.

When PPQT reads the metadata file, it takes some care to avoid
any errors you might make in editing the metadata file.
If it finds errors, it writes log messages about them,
and skips the bad section.

.. _What's New:

What's New
===========

21 July 2015
-------------

This updated release has a few minor usability fixes in the app itself.
For example, previously when you did a Find, the yellow current-line
highlight did not appear and it was hard to see where the "found" thing
was in the Edit panel. Now the current-line highlight shows up to draw
your eye to the found text.

The main change is in the supplied Translators.
There is an HTML Translator as before (one fix there).
There is a short document, extras/Translators/html.utf,
that documents what the HTML Translator does.

And now there is an ASCII Translator also.
It supports all the PPQT markup conventions for /Q, /C, /R
and also properly supports /T table markup as described in the
"suggested workflow" document. It even reflows text inside table cells.
The short document extras/Translators/ascii.utf describes it.

The ASCII Translator uses a more sophisticated algorithm for paragraph
reflow than usual, and should do a nice job of reflowing longer paragraphs.

Also in the extras/xlt_dev folder the TranslatorAPI.html document is
revised for clarity.
If you are a Python programmer, please read it:
you could write a Translator for your favorite markup style!

1 July 2015
-------------
It's all new! This is the first release of version 2!
Version 2 is not compatible with Version 1 because the metadata file
format is different.
If you are working on a book using PPQT version 1, complete that book.
Use Version 2 to start your next new project.

Here are the main points of difference (aside from all the shiny
new more efficient Python code underneath):

* You can open as many books as you like. Each book has its own
  set of panels which are switched in as needed.

* The editor shows the current line with a highlight.

* There is a fancy Preferences dialog.

* The Bookloupe panel integrates Bookloupe into the process.

* Help is in a separate window, not a panel, so you can position
  it where you can read it while looking at another panel.

* The Find panel now supports full PCRE regular expressions.
  The old "Greedy" switch is gone; use the ``?`` qualifier to
  make any expression non-greedy.

* It is easier to set a limited Find range, and the range 
  is colored so you can see where it is.

* The HTML and ASCII conversion panels are gone.
  In this version, all types of conversions are handled by
  plug-ins called Translators.

* The HTML preview panel is gone. There are too many different
  etext formats, we can't provide preview panels for all of them.
  Open an HTML file in a browser.
  Then just save (ctl-s) in PPQT and click the refresh button on the browser.



