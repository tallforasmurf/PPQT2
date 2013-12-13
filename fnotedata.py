'''
                          FNOTEDATA.PY

Stores footnote info.

Called at fnote_save() to write footnote metadata.

Can be initialized from a metadata file, at fnote_read.

However version 1 metadata (and new files) don't have
that metadata. So an also be (re-)initialized from the
Refresh button of the fnote panel. At which time it scans
the book -- using a textblock generator provided by the book --
and loads itself with footnote data.

TBS: relationship between this and the fnote panel object,
presumably the panel gets a ref to this at __init__.

TBS: What services this affords to the fnote panel.
Basically it acts as the Data Model for the panel's View.

TBS: Where we put the functions that modify the book text,
renumbering and moving footnotes. Which object owns the
renumber streams?

'''