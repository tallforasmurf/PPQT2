'''
                          SPELLCHECK.PY

Implements spellcheck via hunspell.

One of these is created for each open Book because the
default dict is different per book.

TBS: How do we generate the list of available dicts? Where
do we store the list? When this object gets an alt-dict tag
where does it go to validate it and find the files?

'''