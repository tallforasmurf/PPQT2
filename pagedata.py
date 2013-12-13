
'''

                          PAGEDATA.PY

The class defined here implements an object to store all info
related to page boundaries. A Book object creates one and initializes
it either from metadata or during an initial census.

'''

# These values are used to encode folio controls for the
# Page/folio table.
FolioFormatArabic = 0x00
FolioFormatUCRom = 0x01
FolioFormatLCRom = 0x02
FolioFormatSame = 0x03 # the "ditto" format
FolioRuleAdd1 = 0x00
FolioRuleSet = 0x01
FolioRuleSkip = 0x02

# Each .meta page info is a list of 6 items, specifically
# 0: page start offset, 1: png# string, 2: prooferstring,
# 3: folio rule, 4: folio format, 5: folio number
