from PyQt5.QtWidgets import *
from PyQt5 import QtCore
from PyQt5 import QtGui
from .QChrootFileDirDialog import *
from .regexManager import *
from .edgeDialog import *
from .pasteDialog import *
from .setTagDialog import *

class Menubar(QtCore.QObject):
    progress_signal = QtCore.pyqtSignal(int, int)

    def __init__(self, ui, menubar):
        QtCore.QObject.__init__(self)
        self.ui = ui
        self.menubar = menubar

        menuBatch = menubar.addMenu('&Batch')

        batchTrim = QAction('Trim', self.menubar)
        batchTrim.triggered.connect(self.onBatchTrim)
        menuBatch.addAction(batchTrim)

        batchShrink = QAction('Shrink', self.menubar)
        batchShrink.triggered.connect(self.onBatchShrink)
        menuBatch.addAction(batchShrink)

        batchColsToChildren = QAction('Columns to children', self.menubar)
        batchColsToChildren.triggered.connect(self.onBatchColsToChildren)
        menuBatch.addAction(batchColsToChildren)

        batchRowsToChildren = QAction('Rows to children', self.menubar)
        batchRowsToChildren.triggered.connect(self.onBatchRowsToChildren)
        menuBatch.addAction(batchRowsToChildren)

        batchAutoPaste = QAction('Auto Paste', self.menubar)
        batchAutoPaste.triggered.connect(self.onBatchAutoPaste)
        menuBatch.addAction(batchAutoPaste)

        batchSettag = QAction('Set Tag', self.menubar)
        batchSettag.triggered.connect(self.onBatchSetTag)
        menuBatch.addAction(batchSettag)

        menuThis = menubar.addMenu('&This')

        thisTrim = QAction('Trim', self.menubar)
        thisTrim.triggered.connect(self.onThisTrim)
        menuThis.addAction(thisTrim)

        thisShrink = QAction('Shrink', self.menubar)
        thisShrink.triggered.connect(self.onThisShrink)
        menuThis.addAction(thisShrink)

        thisColsToChildren = QAction('Columns to children', self.menubar)
        thisColsToChildren.triggered.connect(self.onThisColsToChildren)
        menuThis.addAction(thisColsToChildren)

        thisRowsToChildren = QAction('Rows to children', self.menubar)
        thisRowsToChildren.triggered.connect(self.onThisRowsToChildren)
        menuThis.addAction(thisRowsToChildren)

        menuOCR = menubar.addMenu('&OCR')
        ocrRegex = QAction('Regular Expression', self.menubar)
        ocrRegex.triggered.connect(self.onOcrRegex)
        menuOCR.addAction(ocrRegex)

        self.progress_dialog = None
        self.progress_signal.connect(self._onProgress)

    def onBatchTrim(self):
        EdgeDialog(self.ui, "Batch Trim", "Margin", 5, self.doBatchTrim)

    def doBatchTrim(self, left, top, right, bottom, margin):
        self.ui.core.batchTrim(left, top, right, bottom, margin, self.onProgress)

    def onBatchColsToChildren(self):
        self.ui.core.batchColsToChildren(self.onProgress)

    def onBatchRowsToChildren(self):
        self.ui.core.batchRowsToChildren(self.onProgress)

    def onBatchShrink(self):
        EdgeDialog(self.ui, "Batch Shrink", "Amount", 1, self.doBatchShrink)

    def doBatchShrink(self, left, top, right, bottom, amount):
        self.ui.core.batchShrink(left, top, right, bottom, amount, self.onProgress)

    def onBatchAutoPaste(self):
        PasteDialog(self.ui)

    def onBatchSetTag(self):
        SetTagDialog(self.ui, self.doBatchSetTag)

    def doBatchSetTag(self, key, value, isFormula):
        self.ui.core.batchSetTag(key, value, isFormula, self.onProgress)

    def onProgress(self, done, total):
        self.progress_signal.emit(done, total)

    def _onProgress(self, done, total):
        if done==total:
            if self.progress_dialog and not self.progress_dialog.wasCanceled():
                self.progress_dialog.setValue(done)
                self.progress_dialog.hide()
            self.progress_dialog = None
        else:
            if self.progress_dialog is None:
                self.progress_dialog = QProgressDialog("Running batch task...", None, done, total, self.ui.ui)
                self.progress_dialog.setAutoReset(False)
                self.progress_dialog.setAutoClose(False)
                self.progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
                self.progress_dialog.show()
            self.progress_dialog.setValue(done)

    def onOcrRegex(self):
        RegexManager(self.ui)

    def onThisTrim(self):
        EdgeDialog(self.ui, "Trim", "Margin", 5, self.doThisTrim)

    def doThisTrim(self, left, top, right, bottom, margin):
        item = self.ui.core.getCurrentItem()
        if item:
            item.trim(left, top, right, bottom, margin)

    def onThisShrink(self):
        EdgeDialog(self.ui, "Shrink", "Amount", 1, self.doThisShrink)

    def doThisShrink(self, left, top, right, bottom, amount):
        item = self.ui.core.getCurrentItem()
        if item:
            item.shrink(left, top, right, bottom, amount)

    def onThisColsToChildren(self):
        item = self.ui.core.getCurrentItem()
        if item:
            item.colsToChildren()
            self.ui.onContentChanged()

    def onThisRowsToChildren(self):
        item = self.ui.core.getCurrentItem()
        if item:
            item.rowsToChildren()
            self.ui.onContentChanged()
