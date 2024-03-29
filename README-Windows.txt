                      This is PPQT Version 2
			
                    Distribution of 22 August 2015

This 22 August bundle includes two minor fixes for the Translator support
module, a revised HTML Translator, and now, a Ppgen Translator!

You can now take your book through Step 24 (at least) of the Suggested
Workflow and then Translate it to Ppgen markup syntax. Ppgen will process
the translated book correctly, but you will surely want to edit it much
more to make it look its best. You can edit the Ppgen book in PPQT2: the
Image panel will show the scan images at their (approximate) location; your
Notes from the original book are there; the Find panel works; and you can
still use the Words, Characters, and Bookloupe panels. (The Footnotes and
Pages panels are not useful in a Ppgen book.)


Contents of this folder
=======================

Besides this file, this folder contains the following:

* COPYING.TXT -- a copy of the GNU Public License V3 under
  which PPQT2 is released.

* PPQT2.exe -- the PPQT2 application; double-click it to launch.

* extras -- a folder of useful things listed below.

You can put this folder anywhere you wish. You do not need to keep it open
all the time if you make a shortcut to PPQT2. Right-click on PPQT2 and
select Create Shortcut. Drag the shortcut icon to the desktop. You can
double-click it to launch the program.

Documentation
=============

The documentation of PPQT is in two parts:

* Within the program, select File>Help to open the Help file
  in a separate window. The help file is also available in
  extras/ppq2help.html, which you can open in any browser.

* extras/suggested-workflow.rtf describes how to use PPQT in
  every phase of post-processing, with hints and tips.

If you have used PPQT2 before, take a quick look at the Help topic
"What's New" to see what's been changed or added.

If this is your first time with PPQT2, **PLEASE** read these
topics in the Help file now, before you start editing:

  "The Big Picture" 

  "Files and Folders"

  "File: Open"

Especially note that PPQT2 *assumes* files are UTF-8 unless you
tell it otherwise by changing their filenames to end in -ltn.

The extras folder
=================

The extras folder contains these things:

* suggested-workflow.rtf documents how to use PPQT2 in post-processing.

* en_common-ltn.txt is a file of common "scannos"; see the Help topic
  Edit Panel: Marking Scannos. (Note the file is encoded Latin-1, not
  UTF-8, which is indicated by its filename).

* dictionaries is a folder of spell-check dictionaries for several
  languages. PPQT looks for spelling dictionaries in several places; see 
  the Help topic Edit Panel: Marking Spelling : Dictionaries.

* Files of Find buttons to load into a Find panel for special searches;
  see the Help topic Using Find Buttons.

  - clear_all_buttons.utf clears all Find buttons to empty.
  - common_errors.utf has searches for many common format errors.
  - find_page_separators.utf has a regular expression to find and replace
    page-separator lines.
  - heading-format-check.utf has searches for wrongly-formatted headings.
  - review_text_markup.utf has regular expressions to find and replace
    italic, smallcap and bold markup.
  - text_fixups.utf has more searches for common errors.
  - unbalanced_markup.utf has searches to find some unbalanced markup.
  - syntax_of_find_buttons.utf explains the format of these files.

* Translators is a folder of translator modules. See the Help topic
  of that name for an explanation of Translators.

* xlt_dev is a folder of items that help the programmer who wants to
  write a Translator module.

You may move the extras folder anywhere you like, as long as you use the
Preferences dialog to tell PPQT2 where to find it.

The log file
============

PPQT writes a log file. Its location depends on the operating system.

* In Mac OS it is Library/Logs/PPQT2.log in your home folder.
* In Linux it is /var/tmp/PPQT2.log
* In Windows it is \Windows\Temp\PPQT2.log

The log file is not of much interest in normal use but may be helpful
when debugging a software problem.


