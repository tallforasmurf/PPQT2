# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'editview.ui'
#
# Created: Mon Mar 31 15:14:11 2014
#      by: PyQt5 UI code generator 5.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_EditViewWidget(object):
    def setupUi(self, EditViewWidget):
        EditViewWidget.setObjectName("EditViewWidget")
        EditViewWidget.resize(757, 481)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(EditViewWidget.sizePolicy().hasHeightForWidth())
        EditViewWidget.setSizePolicy(sizePolicy)
        EditViewWidget.setMinimumSize(QtCore.QSize(250, 250))
        EditViewWidget.setWindowTitle("Form")
        EditViewWidget.setToolTip("")
        EditViewWidget.setStatusTip("")
        EditViewWidget.setWhatsThis("")
        self.gridLayout = QtWidgets.QGridLayout(EditViewWidget)
        self.gridLayout.setContentsMargins(8, 8, 8, 8)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setSizeConstraint(QtWidgets.QLayout.SetMaximumSize)
        self.verticalLayout.setObjectName("verticalLayout")
        self.Editor = QtWidgets.QPlainTextEdit(EditViewWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Editor.sizePolicy().hasHeightForWidth())
        self.Editor.setSizePolicy(sizePolicy)
        self.Editor.setMinimumSize(QtCore.QSize(0, 0))
        font = QtGui.QFont()
        font.setKerning(False)
        self.Editor.setFont(font)
        self.Editor.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.Editor.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        self.Editor.setAcceptDrops(False)
        self.Editor.setStatusTip("")
        self.Editor.setLineWidth(2)
        self.Editor.setDocumentTitle("")
        self.Editor.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        self.Editor.setPlainText("")
        self.Editor.setObjectName("Editor")
        self.verticalLayout.addWidget(self.Editor)
        self.frame = QtWidgets.QFrame(EditViewWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setMinimumSize(QtCore.QSize(0, 24))
        self.frame.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        self.frame.setToolTip("")
        self.frame.setStatusTip("")
        self.frame.setWhatsThis("")
        self.frame.setFrameShape(QtWidgets.QFrame.Panel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.frame.setLineWidth(3)
        self.frame.setObjectName("frame")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.frame)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.DocName = QtWidgets.QLabel(self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(2)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.DocName.sizePolicy().hasHeightForWidth())
        self.DocName.setSizePolicy(sizePolicy)
        self.DocName.setMinimumSize(QtCore.QSize(60, 12))
        self.DocName.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        self.DocName.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.DocName.setObjectName("DocName")
        self.horizontalLayout.addWidget(self.DocName)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.FolioLabel = QtWidgets.QLabel(self.frame)
        self.FolioLabel.setToolTip("")
        self.FolioLabel.setStatusTip("")
        self.FolioLabel.setWhatsThis("")
        self.FolioLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.FolioLabel.setObjectName("FolioLabel")
        self.horizontalLayout.addWidget(self.FolioLabel)
        self.Folio = QtWidgets.QLabel(self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Folio.sizePolicy().hasHeightForWidth())
        self.Folio.setSizePolicy(sizePolicy)
        self.Folio.setMinimumSize(QtCore.QSize(30, 12))
        self.Folio.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        self.Folio.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.Folio.setText("")
        self.Folio.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.Folio.setObjectName("Folio")
        self.horizontalLayout.addWidget(self.Folio)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.ImageFilenameLabel = QtWidgets.QLabel(self.frame)
        self.ImageFilenameLabel.setToolTip("")
        self.ImageFilenameLabel.setStatusTip("")
        self.ImageFilenameLabel.setWhatsThis("")
        self.ImageFilenameLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.ImageFilenameLabel.setObjectName("ImageFilenameLabel")
        self.horizontalLayout.addWidget(self.ImageFilenameLabel)
        self.ImageFilename = QtWidgets.QLineEdit(self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ImageFilename.sizePolicy().hasHeightForWidth())
        self.ImageFilename.setSizePolicy(sizePolicy)
        self.ImageFilename.setMinimumSize(QtCore.QSize(30, 12))
        self.ImageFilename.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.ImageFilename.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        self.ImageFilename.setAcceptDrops(False)
        self.ImageFilename.setInputMask("")
        self.ImageFilename.setText("")
        self.ImageFilename.setMaxLength(8)
        self.ImageFilename.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.ImageFilename.setPlaceholderText("")
        self.ImageFilename.setObjectName("ImageFilename")
        self.horizontalLayout.addWidget(self.ImageFilename)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.LineNumberLabel = QtWidgets.QLabel(self.frame)
        self.LineNumberLabel.setToolTip("")
        self.LineNumberLabel.setStatusTip("")
        self.LineNumberLabel.setWhatsThis("")
        self.LineNumberLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.LineNumberLabel.setObjectName("LineNumberLabel")
        self.horizontalLayout.addWidget(self.LineNumberLabel)
        self.LineNumber = QtWidgets.QLineEdit(self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.LineNumber.sizePolicy().hasHeightForWidth())
        self.LineNumber.setSizePolicy(sizePolicy)
        self.LineNumber.setMinimumSize(QtCore.QSize(0, 12))
        self.LineNumber.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.LineNumber.setAcceptDrops(False)
        self.LineNumber.setLayoutDirection(QtCore.Qt.LeftToRight)
        #self.LineNumber.setInputMask("00000D")
        self.LineNumber.setText("")
        #self.LineNumber.setCursorPosition(0)
        self.LineNumber.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.LineNumber.setPlaceholderText("")
        self.LineNumber.setCursorMoveStyle(QtCore.Qt.LogicalMoveStyle)
        self.LineNumber.setObjectName("LineNumber")
        self.horizontalLayout.addWidget(self.LineNumber)
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem3)
        self.ColNumberLabel = QtWidgets.QLabel(self.frame)
        self.ColNumberLabel.setToolTip("")
        self.ColNumberLabel.setStatusTip("")
        self.ColNumberLabel.setWhatsThis("")
        self.ColNumberLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.ColNumberLabel.setObjectName("ColNumberLabel")
        self.horizontalLayout.addWidget(self.ColNumberLabel)
        self.ColNumber = QtWidgets.QLabel(self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ColNumber.sizePolicy().hasHeightForWidth())
        self.ColNumber.setSizePolicy(sizePolicy)
        self.ColNumber.setMinimumSize(QtCore.QSize(24, 12))
        self.ColNumber.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        self.ColNumber.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.ColNumber.setFrameShadow(QtWidgets.QFrame.Plain)
        self.ColNumber.setLineWidth(1)
        self.ColNumber.setText("")
        self.ColNumber.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.ColNumber.setObjectName("ColNumber")
        self.horizontalLayout.addWidget(self.ColNumber)
        self.horizontalLayout_2.addLayout(self.horizontalLayout)
        self.verticalLayout.addWidget(self.frame)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)
        self.ImageFilenameLabel.setBuddy(self.ImageFilename)
        self.LineNumberLabel.setBuddy(self.LineNumber)

        self.retranslateUi(EditViewWidget)
        QtCore.QMetaObject.connectSlotsByName(EditViewWidget)

    def retranslateUi(self, EditViewWidget):
        _translate = QtCore.QCoreApplication.translate
        self.Editor.setToolTip(_translate("EditViewWidget", "Document editor"))
        self.Editor.setWhatsThis(_translate("EditViewWidget", "The document being edited. Click in the window and use standard editing methods."))
        self.DocName.setToolTip(_translate("EditViewWidget", "Document filename"))
        self.DocName.setWhatsThis(_translate("EditViewWidget", "The filename of the document being edited. It changes color when the document has been modified."))
        self.DocName.setText(_translate("EditViewWidget", "docname"))
        self.FolioLabel.setText(_translate("EditViewWidget", "Folio"))
        self.Folio.setToolTip(_translate("EditViewWidget", "Folio value"))
        self.Folio.setStatusTip(_translate("EditViewWidget", "Folio value for the page under the edit cursor"))
        self.Folio.setWhatsThis(_translate("EditViewWidget", "The Folio (page number) value for the page under the edit cursor. Use the Pages panel to adjust folios to agree with the printed book."))
        self.ImageFilenameLabel.setText(_translate("EditViewWidget", "Image"))
        self.ImageFilename.setToolTip(_translate("EditViewWidget", "Scan image filename"))
        self.ImageFilename.setStatusTip(_translate("EditViewWidget", "Index of the scan image under the edit cursor"))
        self.ImageFilename.setWhatsThis(_translate("EditViewWidget", "This is the number of the scanned image that produced the text under the edit cursor. This image is displayed in the Image panel."))
        self.LineNumberLabel.setText(_translate("EditViewWidget", "Line#"))
        self.LineNumber.setToolTip(_translate("EditViewWidget", "Line number at cursor"))
        self.LineNumber.setStatusTip(_translate("EditViewWidget", "Line number under cursor or top of selection"))
        self.LineNumber.setWhatsThis(_translate("EditViewWidget", "The line number in the document where the edit cursor is, or the top line of the selection. Enter a new number to jump to that line."))
        self.ColNumberLabel.setText(_translate("EditViewWidget", "Col#"))
        self.ColNumber.setToolTip(_translate("EditViewWidget", "Cursor column number"))
        self.ColNumber.setStatusTip(_translate("EditViewWidget", "Cursor column number"))
        self.ColNumber.setWhatsThis(_translate("EditViewWidget", "The column number position of the cursor in the current line."))

