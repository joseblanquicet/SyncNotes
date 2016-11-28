# coding=utf-8
__author__ = 'Jose Blanquicet'

from PyQt5.QtWidgets import QMainWindow, QAction, QTextEdit, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QTimer


class MainWindow(QMainWindow):

    newNoteAdded = pyqtSignal(int)
    noteDeleted = pyqtSignal(int)
    noteSaved = pyqtSignal(int, str)
    synced = pyqtSignal()
    showed = pyqtSignal()
    logFile = pyqtSignal(str)

    def __init__(self, _id, _index):
        super().__init__()

        self.noteID = _id
        self.mpos = QPoint()  # Mouse position
        self.myIndex = _index
        self.showedFlag = False

        # INITIALIZE TOOLBAR
        # 1 . New
        new_action = QAction(QIcon('img/add.png'), 'New', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.newNote)
        self.toolbar_add = self.addToolBar('New')
        self.toolbar_add.addAction(new_action)

        # 2. Delete
        delete_action = QAction(QIcon('img/delete.png'), 'Delete', self)
        delete_action.setShortcut('Ctrl+D')
        delete_action.triggered.connect(self.deleteNote)
        self.toolbar_delete = self.addToolBar('Delete')
        self.toolbar_delete.addAction(delete_action)

        # 3. Save
        # save_action = QAction(QIcon('img/save.png'), 'Save', self)
        # save_action.setShortcut('Ctrl+S')
        # save_action.triggered.connect(self.Save)
        # self.toolbar_save = self.addToolBar('Save')
        # self.toolbar_save.addAction(save_action)

        # INSERTING TEXT FIELD
        self.noteItself = QTextEdit()
        self.setCentralWidget(self.noteItself)
        self.noteItself.setFocus()
        self.noteItself.textChanged.connect(self.timerToSave)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.Save)

    def initUI(self):
        # INITIALIZE USER INTERFACE

        # Initialize Status Bar
        self.updateStatusBar('Disconnected from Dropbox')
        # self.statusBar().hide()
        # self.statusBar().setVisible(False)

        # Set General Styles of window
        if self.myIndex < 2:
            x = 1024
            y = 50 + 250 * self.myIndex
        elif self.myIndex < 4:
            x = 1024 - 250
            y = 50 + 250 * (self.myIndex - 2)
        else:
            x = 1024 - 500
            y = 50

        self.setGeometry(x, y, 200, 200)
        # Do not show tittle bar and do not create icon in taskbar
        flagsOnTop = Qt.CustomizeWindowHint | Qt.Tool
        self.setWindowFlags(flagsOnTop)
        self.show()
        self.showed.emit()

    def showEvent(self, *args, **kwargs):
        # self.logFile.emit("MW: ShowEvent flag = {} index = {}".format(self.showedFlag, self.myIndex))
        #if self.showedFlag is False and self.myIndex == 0:
        #    # self.logFile.emit("MW: Emit show")
        #    self.updateStatusBar('Connecting to Dropbox ...')
        #    self.showed.emit()
        #    self.showedFlag = True

        flags = Qt.CustomizeWindowHint | Qt.Tool
        self.setWindowFlags(flags)
        self.show()

    def mousePressEvent(self, qmouseEvent):
        self.mpos = qmouseEvent.pos()

    def mouseMoveEvent(self, qmouseEvent):
        if qmouseEvent.buttons() & Qt.LeftButton:
            diff = qmouseEvent.pos() - self.mpos
            newpos = self.pos() + diff
            self.move(newpos)

    def newNote(self):
        # ADDING NEW NOTE
        # self.logFile.emit("MW: New note will be added")
        self.newNoteAdded.emit(-1)

    def deleteNote(self):
        # DELETING NEW NOTE
        self.logFile.emit("MW: Note {} will be deleted".format(self.noteID))

        reply = QMessageBox.question(self, 'Note Deletion', "Are you sure to delete this note?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.noteDeleted.emit(int(self.noteID))
            self.close()
        else:
            self.logFile.emit("MW: Deletion cancelled")

    def Save(self):
        # STORE NOTE IN DROPBOX
        self.timer.stop()
        self.logFile.emit("MW: Save note {} with timer".format(self.noteID))
        self.noteSaved.emit(self.noteID, self.noteItself.toPlainText())

    def timerToSave(self):
        # Start timer to save the new note
        self.timer.start(5000)

    def Sync(self):
        # SYNCHRONIZE WITH DROPBOX
        self.logFile.emit("MW: Let's try to sync")
        self.synced.emit()

    def updateStatusBar(self, text):
        self.statusBar().showMessage(text)

    def updateNote(self, _noteText):

        self.logFile.emit("MW: Updating notes from Dropbox")
        # Read saved notes in Dropbox and update them
        self.noteText = _noteText
        # Update note text
        self.noteItself.setText(self.noteText)

        if self.myIndex == 0:
            self.setFocus()
            self.noteItself.setFocus()

    def setNoteID(self, _newID):
        self.noteID = _newID
