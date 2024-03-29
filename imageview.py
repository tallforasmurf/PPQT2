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
                     IMAGEVIEW.PY

Display one scanned page image, usually the one associated with the page the
edit cursor is on. Support paging, zooming and scrolling the image.

The Book creates an ImageView object as part of its own initialization
before it is called to load a book. So on creation we set up for the
"no-image" condition, displaying a gray image and disabling all controls.
We register reader/writer functions for two metadata sections.

The Book is also responsible for linking the editor's cursorMoved signal
to our cursor_move() method.

When (if) the Book loads an existing file, it processes that file's metadata
which may enter our metadata reader functions. Then the Book calls the
set_path() method. There we find out if a folder of scanned image .pngs
exists. If so we enable all our controls and set up to display images.

Rather than using the Qt Designer this widget is "hand-made", however the
lengthy code to set it up, including translation of labels, is taken out of
line to the _uic() method below. See comments there on layout.

If the cursor_to_image button is checked (default true), whenever the edit
cursor moves we check to see if the cursor location falls on a different
page, and if so, we change the display.

If the image_to_cursor button is checked (default false), when we perform a
page up or down, we force the edit cursor to move to the top of text
corresponding to the new page.

We intercept keystrokes and process them as follows:
  ctrl-plus:  zoom up by 1.25
  ctrl-minus: zoom down by 0.8
  page up:    go to the next-lower page index
  page down:  go to the next-higher page index

'''
import constants as C
import metadata
import pagedata
import resources # for hand icons
import math # for isnan() only

from PyQt6.QtCore import (
    Qt,
    QDir,
    QCoreApplication,
    QSize
)
_TR = QCoreApplication.translate

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QAbstractScrollArea, QScrollArea,
    QSizePolicy,
    QPushButton,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget
)
from PyQt6.QtGui import (
    QColor,
    QFontMetrics,
    QIcon,
    QImage,
    QPixmap,
    QPalette
)
import logging
imageview_logger = logging.getLogger(name='imageview')

'''
Establish min/max zoom settings as module constants (they affect
only this module, so not placed in constants.py).
'''
ZOOM_FACTOR_MIN = 0.15
ZOOM_FACTOR_MAX = 2.0

class ImageDisplay(QWidget):
    def __init__(self, my_book, parent=None):
        super().__init__(parent)
        self.my_book = my_book
        ''' register metadata readers and writers '''
        md = my_book.get_meta_manager()
        md.register(C.MD_IZ,self._zoom_read,self._zoom_write)
        md.register(C.MD_IX,self._link_read,self._link_write)
        '''
        Create all our widgets including cursor_to_image and image_to_cursor
        pushbuttons
        '''
        self._uic()
        ''' set defaults in case no metadata is read '''
        self.cursor_to_image.toggled.connect( self.toggle_cursor_to_image )
        self.cursor_to_image.setChecked(True)
        self.image_to_cursor.toggled.connect( self.toggle_image_to_cursor )
        self.image_to_cursor.setChecked(False)
        self.zoom_factor = 0.25
        self.png_path = None
        ''' disable all widgetry until we get some metadata '''
        self._disable()
        # end of __init__()

    ''' Disable our widgets because we have no image to show. '''
    def _disable(self):
        self.no_image = True
        self.last_index = None # compares unequal to anything
        self.pix_map = QPixmap()
        self.image = QImage()
        self.cursor_to_image.setEnabled(False)
        self.image_to_cursor.setEnabled(False)
        self.zoom_pct.setEnabled(False)
        self.zoom_to_width.setEnabled(False)
        self.zoom_to_height.setEnabled(False)
        self.image_display.setPixmap(self.gray_image)
        self.image_display.setToolTip(
            _TR('Image view tooltip',
                'Display of one scanned page (no images available)')
            )

    '''
    Enable our widgets, we have images to show. At this time the Book
    has definitely created an edit view and a page model.
    '''
    def _enable(self):
        self.edit_view = self.my_book.get_edit_view()
        self.editor = self.edit_view.Editor # access to actual QTextEdit
        self.page_data = self.my_book.get_page_model()
        self.cursor_to_image.setEnabled(True)
        self.image_to_cursor.setEnabled(True)
        self.zoom_to_width.setEnabled(True)
        self.zoom_to_height.setEnabled(True)
        self.image_display.setToolTip('')
        #self.image_display.setToolTip(
            #_TR('Image view tooltip',
                #'Display of one scanned page from the book')
            #)
        self.no_image = False
        self.zoom_pct.setEnabled(True)
        '''
        The following, in changing the value of the zoom factor,
        raises the signal that is caught by _new_zoom_pct() below
        '''
        self.zoom_pct.setValue(int(100*self.zoom_factor))

    '''
    Metadata: read/write the value of the current image zoom factor as a
    decimal between 0.15 and 2.0. On input defend against user mistakes.
    TODO: explain why _zoom_read doesn't call _set_zoom_real?
    '''
    def _zoom_read(self, section, value, version):
        try:
            z = float(value) # throws exception on non-numeric value
            if math.isnan(z) or (z < 0.15) or (z > 2.0) :
                raise ValueError
            self.zoom_factor = z
        except:
            imageview_logger.error('Invalid IMAGEZOOM "{}" ignored'.format(value))

    def _zoom_write(self, section):
        return self.zoom_factor

    '''
    Metadata: read or write the values of the image_to_cursor and
    cursor_to_image switches as a list [cursor_to_image, image_to_cursor].
    On input defend against user meddling. Actually bool(x) is pretty lax,
    any scalar not zero and any iterable not empty is True. Zero and
    iterables of length 0 are False.
    '''
    def _link_read(self, section, value, version):
        try:
            (c2i, i2c) = value # exception if not iterable of 2 items
            self.cursor_to_image.setChecked( bool(c2i) )
            self.image_to_cursor.setChecked( bool(i2c) )
        except :
            imageview_logger.error('Invalid IMAGELINKING "{}" ignored'.format(value))

    def _link_write(self, section):
        return [self.cursor_to_image.isChecked(), self.image_to_cursor.isChecked()]

    '''
    The Book calls here after it has loaded a book which it is sure has
    defined page data, passing the path to the folder containing the book. If
    we can find a folder named 'pngs' or one named 'images' we record that
    path as self.png_dir. Having what looks like a folder of page images,
    enable our widgets, and fake a cursorMoved signal to display the current
    edit page.
    
    There is no guarantee that this folder contains all, or indeed any, of
    the page images. But when it is time to display, see _show_page(), that
    is where we look for the image file named in the page-boundary line.
    '''
    def set_path(self,book_folder_path):
        book_dir = QDir(book_folder_path)
        folder_name = None
        if book_dir.exists('pngs') : folder_name = 'pngs'
        elif book_dir.exists('images') : folder_name = 'images'
        if folder_name :
            self.png_dir = QDir(book_dir.absoluteFilePath(folder_name))
            self._enable()
            self.cursor_move()

    '''
    
    Come here to display or re-display an image. The last-displayed page
    image index (if any) is in self.last_index. The desired page index is
    passed as the argument, which among other things could be:
    
    * the same as last_index, for example on a change of zoom%. Just
      redisplay the current page.
      
    * negative or None if the cursor is "above" the first available page on
      a Page-Up keystroke. Display the gray image.
      
    * greater than page_data.page_count() on a Page-Down keystroke.
      Display the last available page.
    
    If different from last_index, try to load the .png file for that
    page. If that fails, use the gray image. Otherwise display that
    page and save it as last_index.
    '''
    def _show_page(self, page_index):
        if page_index != self.last_index :
            ''' Change of page. Note new page. '''
            self.last_index = page_index
            ''' Ask the page data model for its filename '''
            self.pix_map = self.gray_image # assume failure...
            im_name = self.page_data.filename(page_index)
            if im_name :
                '''
                pagedata has a filename; of course there is no guarantee
                such a file exists now or ever did. Use the QDir to look for
                the file as .png or .jpg.
                '''
                f_name = im_name + '.png'
                if not self.png_dir.exists( f_name ) :
                    f_name = im_name + '.jpg'
                if self.png_dir.exists(f_name) :
                    ''' file exists, try to load it as a QImage '''
                    self.image = QImage(self.png_dir.absoluteFilePath(f_name))
                    if not self.image.isNull():
                        ''' we loaded it; make a full-scale pixmap for display '''
                        self.pix_map = QPixmap.fromImage(self.image,Qt.ImageConversionFlag.ColorOnly)
        '''
        Whether or not the page changed, rescale the pixmap to the current
        zoom. The .resize method takes a QSize; pix_map.size() returns one,
        and QSize supports being multiplied by a real.
        '''
        self.image_display.setPixmap(self.pix_map)
        self.image_display.resize( self.zoom_factor * self.pix_map.size() )

    '''
    Slot to receive the cursorMoved signal from the editview widget. This is
    entered every frickin' time the cursor moves!
    
    If we are in no_image state, do nothing. If the cursor_to_image switch is
    not checked, do nothing.
    
    Else get the character position of the high-end of the current edit
    selection, and use that to get the current page index from pagedata, and
    pass that to _show_page.
    '''
    def cursor_move(self):
        if self.no_image : return
        if self.cursor_to_image.isChecked() :
            pos = self.editor.textCursor().selectionEnd()
            self._show_page( self.page_data.page_index(pos) )

    '''
    Slots to receive the signals from our zoom percent and zoom-to buttons.
    The controls are disabled while we are in no_image state, so if a signal
    arrives, we are not in that state.
    
    These are strictly internal hence _names.

    Handle any change in the value of the zoom % spin-box including calling
    setValue(). Convert the integer widget value to a real, and force the
    page to be displayed again.
    '''
    def _new_zoom_pct(self,new_value):
        self.zoom_factor = self.zoom_pct.value() / 100
        self._show_page(self.last_index)

    '''
    Set a new zoom factor (a real) and update the zoom pct spinbox. Setting
    zoom_pct triggers a signal to _new_zoom_pct above, and thence to
    _show_page which repaints the page at the new scale value.
    '''
    def _set_zoom_real(self,new_value):
        zoom = max(new_value, ZOOM_FACTOR_MIN)
        zoom = min(zoom, ZOOM_FACTOR_MAX)
        self.zoom_factor = zoom
        self.zoom_pct.setValue(int(100*zoom))

    '''
    
    Re-implement QWidget.keyPressEvent in order to provide zoom and page up/down.
    The page display widget ignores all keystrokes except for:
    
    * ctrl-plus increases the image size by a factor of 1.25
    * ctrl-minus decreases the image size by a factor of 0.8
    * page-up displays the next-higher page
    * page-down displays the next-lower page
    '''
    def keyPressEvent(self, event):
        ''' assume we will not handle this key and clear its accepted flag '''
        event.ignore()
        ''' ignore all keys until we are showing some image '''
        if self.no_image or (self.last_index is None) : return 
        ''' We have images to show, check the key value. '''
        modkey = int( int(event.key() | (int(event.modifiers().value) & C.KBD_MOD_PAD_CLEAR)) )
        if modkey in C.KEYS_ZOOM :
            ''' ctrl-+/- keys, modify the zoom value '''
            event.accept()
            fac = (0.8) if (modkey == C.CTL_MINUS) else (1.25)
            self._set_zoom_real( fac * self.zoom_factor)
        elif (event.key() == Qt.Key.Key_PageUp) or (event.key() == Qt.Key.Key_PageDown) :
            ''' page up/down, show the current page +/- 1 if it exists '''
            event.accept()
            pgix = self.last_index + (1 if (event.key() == Qt.Key.Key_PageDown) else -1)
            if pgix >= 0 and pgix < self.page_data.page_count() :
                self._show_page(pgix)
                if self.image_to_cursor.isChecked():
                    self.edit_view.show_position(self.page_data.position(pgix))

    '''
    Zoom to width and zoom to height are basically the same thing:
    
    1. Using the QImage of the current page in self.image,
       scan its pixels to find the width (height) of the nonwhite area.
    2. Get the ratio of that to our image label's viewport width (height).
    3. Set that ratio as the zoom factor and redraw the image.
    5. Set the scroll position(s) of our scroll area to left-justify the text.
    
    We get access to the pixel data using QImage.bits() which gives us a
    "sip.voidptr" object that we can index to get byte values.
    
    TODO: finish editing comments on this section after verifying it works
    and understanding WTF it is really doing.
    '''
    def _zoom_to_width(self):
        '''
        Generic loop to scan from the left or right edge of one column,
        inward until a dark pixel is seen, and return that margin.
        
        White pixels are 255 or nearly, black pixels are 0 or nearly. What we
        actually do is move a 3-px window along looking for 3 adjacent pixels
        that sum to less than 24. This skips tiny noise freckles that
        are common in scanned page images.        
        '''
        def inner_loop(row_range, col_start, margin, col_step):
            pa, pb = 255, 255 # virtual white outside column
            for row in row_range:
                for col in range(col_start, margin, col_step):
                    pc = color_table[ bytes_ptr[row+col] ]
                    if (pa + pb + pc) < 24 : # black or dark gray trio
                        margin = col # new, narrower, margin
                        break # no need to look further on this row
                    pa, pb = pb, pc # else shift 3-pixel window
            return margin - (2*col_step) # allow for 3-px window

        if self.no_image or self.image.isNull() :
            return # nothing to do
        scale_factor = 4
        orig_rows = self.image.height() # number of pixels high
        orig_cols = self.image.width() # number of logical pixels across
        # Scale the image to 1/4 size (1/16 the pixel count) and then force
        # it to indexed-8 format, one byte per pixel.
        work_image = self.image.scaled(
            QSize(int(orig_cols/scale_factor),int(orig_rows/scale_factor)),
            Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
        work_image = work_image.convertToFormat(QImage.Format.Format_Indexed8,Qt.ImageConversionFlag.ColorOnly)
        # Get a reduced version of the color table by extracting just the GG
        # values of each entry, as a dict keyed by the pixel byte value. For
        # PNG-2, this gives [0,255] but it could have 8, 16, even 256 elements.
        color_table = { bytes([c]): int((work_image.color(c) >> 8) & 255)
                         for c in range(work_image.colorCount()) }
        # Establish limits for the inner loop
        rows = work_image.height() # number of pixels high
        cols = work_image.width() # number of logical pixels across
        stride = (cols + 3) & (-4) # scan-line width in bytes
        bytes_ptr = work_image.bits() # uchar * a_bunch_o_pixels
        bytes_ptr.setsize(stride * rows) # make the pointer indexable

        # Scan in from left and from right to find the outermost dark spots.
        # Pages tend to start with many lines of white pixels so in hopes of
        # establishing a narrow margin quickly, scan from the middle to the
        # end, then do the top half.
        left_margin = inner_loop(
                        range(int(rows/2)*stride, (rows-1)*stride, stride*2),
                        0, int(cols/2), 1
        )
        left_margin = inner_loop(
                        range(0, int(rows/2)*stride, stride*2),
                        0, left_margin, 1
                        )
        # Now do exactly the same but for the right margin.
        right_margin = inner_loop(
                        range(int(rows/2)*stride, (rows-1)*stride, stride*2),
                        cols-1, int(cols/2), -1
                        )
        right_margin = inner_loop(
                        range(0, int(rows/2)*stride, stride*2),
                        cols-1, right_margin, -1
                        )
        # Adjust the margins by the scale factor to fit the full size image.
        #left_margin = max(0,left_margin*scale_factor-scale_factor)
        #right_margin = min(orig_cols,right_margin*scale_factor+scale_factor)
        left_margin = left_margin*scale_factor
        right_margin = right_margin*scale_factor
        text_size = right_margin - left_margin + 2
        port_width = self.scroll_area.viewport().width()
        # Set the new zoom factor, after limiting by min/max values
        self._set_zoom_real(port_width/text_size)
        # Set the scrollbar to show the page from its left margin.
        self.scroll_area.horizontalScrollBar().setValue(
                             int( left_margin * self.zoom_factor)
                         )
        # and that completes zoom-to-width

    def _zoom_to_height(self):
        def dark_row(row_start, cols):
            '''
            Scan one row of pixels and return True if it contains
            at least one 3-pixel blob of darkness, or False if not.
            '''
            pa, pb = 255, 255
            for c in range(row_start,row_start+cols):
                pc = color_table[ bytes_ptr[c] ]
                if (pa + pb + pc) < 24 : # black or dark gray trio
                    return True
                pa, pb = pb, pc
            return False # row was all-white-ish

        if self.no_image or self.image.isNull() :
            return # nothing to do
        scale_factor = 4
        orig_rows = self.image.height() # number of pixels high
        orig_cols = self.image.width() # number of logical pixels across
        # Scale the image to 1/4 size (1/16 the pixel count) and then force
        # it to indexed-8 format, one byte per pixel.
        work_image = self.image.scaled(
            QSize(int(orig_cols/scale_factor),int(orig_rows/scale_factor)),
            Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
        work_image = work_image.convertToFormat(QImage.Format.Format_Indexed8,Qt.ImageConversionFlag.ColorOnly)
        # Get a reduced version of the color table by extracting just the GG
        # values of each entry, as a dict keyed by the pixel byte value. For
        # PNG-2, this gives [0,255] but it could have 8, 16, even 256 elements.
        color_table = { bytes([c]): int((work_image.color(c) >> 8) & 255)
                         for c in range(work_image.colorCount()) }
        rows = work_image.height() # number of pixels high
        cols = work_image.width() # number of logical pixels across
        stride = (cols + 3) & (-4) # scan-line width in bytes
        bytes_ptr = work_image.bits() # uchar * a_bunch_o_pixels
        bytes_ptr.setsize(stride * rows) # make the pointer indexable
        # Scan the image rows from the top down looking for one with darkness
        for top_row in range(rows):
            if dark_row(top_row*stride, cols): break
        if top_row > (rows/2) : # too much white, skip it
            return
        for bottom_row in range(rows-1, top_row, -1):
            if dark_row(bottom_row*stride, cols) : break
        # bottom_row has to be >= top_row. if they are too close together
        # set_zoom_real will limit the zoom to 200%.
        top_row = top_row*scale_factor
        bottom_row = bottom_row*scale_factor
        text_height = bottom_row - top_row + 1
        port_height = self.scroll_area.viewport().height()
        self._set_zoom_real(port_height/text_height)
        self.scroll_area.verticalScrollBar().setValue(
                         int( top_row * self.zoom_factor ) )
        # and that completes zoom-to-height

    # Two tiny slots to receive the "toggled(bool)" signal of the grippy
    # hands icons. All we do is swap out the tooltip text to reflect
    # what they are set to do. Note that during __init__ there is a
    # setChecked() call on both, which causing a call to these.

    def toggle_cursor_to_image(self, bool):
        if bool :
            self.cursor_to_image.setToolTip(
                _TR( 'imageview edit-to-image button tooltip',
                     'Images change when the edit cursor moves.' )
                )
        else:
            self.cursor_to_image.setToolTip(
                _TR( 'imageview edit-to-image button tooltip',
                     'Images do NOT change when the edit cursor moves.' )
                )
    def toggle_image_to_cursor(self, bool):
        if bool :
            self.image_to_cursor.setToolTip(
                _TR( 'imageview image-to-cursor button tooltip',
                     'The edit cursor moves when you use Page Up/Down to change images.' )
                )
        else:
            self.image_to_cursor.setToolTip(
                _TR( 'imageview image-to-cursor button tooltip',
                     'The edit cursor does NOT move when you use Page Up/Down to change images.' )
                )

    '''
    Build the widgetary contents. The widget consists mostly of a vertical
    layout with two items: A scrollArea containing a QLabel used to display
    an image, and a horizontal layout containing the zoom controls.
        '''
    def _uic(self):

        '''
        Function to return the actual width of the label text
        of a widget. Get the fontMetrics and ask it for the width
        of the widget's text contents.
        '''
        def _label_width(widget:QWidget):
            fm = widget.fontMetrics()
            return fm.horizontalAdvance(widget.text())

        ''' Create a gray field to use when no image is available. '''
        self.gray_image = QPixmap(700,900)
        self.gray_image.fill(QColor("gray"))

        '''
        Build the QLabel that displays the image pixmap. It gets all
        available space and scales its contents to fit that space.
        '''
        self.image_display = QLabel()
        self.image_display.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.image_display.setScaledContents(True)
        '''
        Create a scroll area within which to display the image. It will
        create a horizontal and/or vertical scroll bar when
        the image_display size exceeds the size of the scroll area.
        '''
        self.scroll_area = QScrollArea()
        self.scroll_area.setBackgroundRole(QPalette.ColorRole.Dark)
        self.scroll_area.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.scroll_area.setWidget(self.image_display)
        ''' Make sure the scroll area does not swallow user keystrokes '''
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus) # focus into whole widget
        self.scroll_area.setFocusProxy(self) # you, pass it on.
        '''
        Create the image-linking toolbuttons using images from resources.py.
        Cursor-to-image uses left-hands.
        '''
        c2i_on = QPixmap(':/hand-left-closed.png')
        c2i_off = QPixmap(':/hand-left-open.png')
        c2i_con = QIcon()
        c2i_con.addPixmap(c2i_on,QIcon.Mode.Normal,QIcon.State.On)
        c2i_con.addPixmap(c2i_off,QIcon.Mode.Normal,QIcon.State.Off)
        self.cursor_to_image = QToolButton()
        self.cursor_to_image.setCheckable(True)
        self.cursor_to_image.setContentsMargins(0,0,0,0)
        self.cursor_to_image.setIconSize(QSize(30,24))
        self.cursor_to_image.setMaximumSize(QSize(32,26))
        self.cursor_to_image.setIcon(c2i_con)
        ''' Image-to-cursor uses right-hands. '''
        i2c_on = QPixmap(':/hand-right-closed.png')
        i2c_off = QPixmap(':/hand-right-open.png')
        i2c_con = QIcon()
        i2c_con.addPixmap(i2c_on,QIcon.Mode.Normal,QIcon.State.On)
        i2c_con.addPixmap(i2c_off,QIcon.Mode.Normal,QIcon.State.Off)
        self.image_to_cursor = QToolButton()
        self.image_to_cursor.setCheckable(True)
        self.image_to_cursor.setContentsMargins(0,0,0,0)
        self.image_to_cursor.setIconSize(QSize(30,24))
        self.image_to_cursor.setMaximumSize(QSize(32,26))
        self.image_to_cursor.setIcon(i2c_con)
        '''
        Create a spinbox to set the zoom from 15 to 200 and connect its
        signal to our slot.
        '''
        self.zoom_pct = QSpinBox()
        self.zoom_pct.setRange(
            int(100*ZOOM_FACTOR_MIN),int(100*ZOOM_FACTOR_MAX))
        self.zoom_pct.setToolTip(
            _TR('Imageview zoom control tooltip',
                'Set the magnification of the page image')
            )
        '''
        Connect the valueChanged(int) signal as opposed to the
        valueChanged(str) signal.
        '''
        self.zoom_pct.valueChanged['int'].connect(self._new_zoom_pct)
        '''
        Create a label for the zoom spinbox. (the label is not saved as a
        class member, its layout will keep it in focus) Not translating
        the word "Zoom".
        '''
        pct_label = QLabel(
            '&Zoom {0}-{1}%'.format(
                str(self.zoom_pct.minimum() ),
                str(self.zoom_pct.maximum() )
                )
            )
        pct_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        pct_label.setBuddy(self.zoom_pct)
        '''
        Create the to-width and to-height zoom buttons. Make
        sure their widths are equal after translation.
        '''
        self.zoom_to_width = QPushButton(
            _TR('Imageview zoom control button name','to Width')
            )
        self.zoom_to_width.setToolTip(
            _TR('Imageview zoom control tooltip',
                'Adjust the image to fill the window side to side.')
            )
        self.zoom_to_width.clicked.connect(self._zoom_to_width)
        self.zoom_to_height = QPushButton(
            _TR('Imageview zoom control button name','to Height')
            )
        self.zoom_to_height.setToolTip(
            _TR('Imageview zoom control tooltip',
                'Adjust the image to fill the window top to bottom.')
            )
        self.zoom_to_height.clicked.connect(self._zoom_to_height)

        w = 20 + max(_label_width(self.zoom_to_height),_label_width(self.zoom_to_width))
        self.zoom_to_height.setMinimumWidth(w)
        self.zoom_to_width.setMinimumWidth(w)
        '''
        Create an HBox for the top of the panel which contains only
        the cursor-to-image link button.
        '''
        tophbox = QHBoxLayout()
        tophbox.setContentsMargins(0,0,0,0)
        tophbox.addWidget(self.cursor_to_image,0)
        tophbox.addStretch() # left-align the button
        '''
        Create an HBox layout to contain the above controls, using
        spacers left and right to center them and a spacers between
        to control the spacing.
        '''
        zhbox = QHBoxLayout()
        zhbox.setContentsMargins(0,0,0,0)
        zhbox.addWidget(self.image_to_cursor,0)
        zhbox.addStretch(2) # left and right spacers have stretch 2
        zhbox.addWidget(pct_label,0)
        zhbox.addWidget(self.zoom_pct,0)
        zhbox.addStretch(1) # spacers between widgets are stretch 1
        zhbox.addWidget(self.zoom_to_height,0)
        zhbox.addSpacing(10) # juuuust a little space between buttons
        zhbox.addWidget(self.zoom_to_width,0)
        zhbox.addStretch(2) # right side spacer
        '''
        With all the pieces in hand, create our layout with a stack of image
        over row of controls. The image gets a high stretch and default
        alignment.
        '''
        vbox = QVBoxLayout()
        vbox.setContentsMargins(0,0,0,0)
        vbox.addLayout(tophbox,0)
        vbox.addWidget(self.scroll_area,2)
        vbox.addLayout(zhbox,0)
        self.setLayout(vbox)
        # And that completes the UI setup.