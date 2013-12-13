'''
                          NOTESDATA.PY

Created by a Book object to hold the content of the user notes.

Has a notes_read method to receive the metadata section
Has a notes_write method to write the metadata section
Gets the modified signal from the notes panel
Gets the going-out-of-scope signal for the notes panel, and
at that time -- and only if modified -- captures the notes
editor's plaintext content.

TBS: relationship to notes panel, how the panel knows to get
its initial content from here. Well, presumably a reference
to this is handed to the panel widget for initialization.


'''