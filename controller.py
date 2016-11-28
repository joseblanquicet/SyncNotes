#  coding=utf-8
__author__ = 'Jose Blanquicet'

from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QLabel, QInputDialog, QMessageBox, QWidget, QSystemTrayIcon

import time
import os
import main
import controller_dropbox
import mainwindow
import systray

DROPBOX_CONNECTION = 1
DROPBOX_DISCONNECTION = 2
FIRST_TIME = 1


class Controller(QObject):

    def __init__(self, _a):
        super().__init__()

        try:
            self.logFileDescriptor = open(main.getLogFilePath(), 'a+')
        except IOError as e:
            self.trayIcon.showMessage("LogFile Error", e.strerror, icon=QSystemTrayIcon.Critical, msecs=3000)
            exit(1)

        self.app = _a
        self.notes = []
        self.counter_noteID = 1
        self.pcPath = main.getAccessTokenPath()

        self.w = QWidget()
        self.trayIcon = systray.SystemTrayIcon(self.w)

        self.dropbox = controller_dropbox.Dropbox(self)
        mw = mainwindow.MainWindow(self.counter_noteID, 0)
        self.notes.append(mw)

        # CONNECTING SIGNALS
        # Main Window
        mw.showed.connect(self.authentication)
        mw.newNoteAdded.connect(self.addNote)
        mw.noteDeleted.connect(self.deleteNote)
        mw.noteSaved.connect(self.saveNote)
        mw.synced.connect(self.Sync)
        mw.logFile.connect(self.LogFile)

        # Dropbox
        self.dropbox.bd.uploaded.connect(self.update)
        self.dropbox.logFile.connect(self.LogFile)
        self.dropbox.bd.logFile.connect(self.LogFile)

        # System Tray
        self.trayIcon.newNote.connect(self.addNote)
        self.trayIcon.synchronized.connect(self.Sync)
        self.trayIcon.quited.connect(self.appQuit)
        self.trayIcon.showAll.connect(self.showAll)
        self.trayIcon.hideAll.connect(self.hideAll)
        self.trayIcon.stop.connect(self.stopSync)
        self.trayIcon.status.connect(self.showStatus)

        mw.initUI()

    def authentication(self):

        self.LogFile("CONTROLLER: Authentication Function")

        access_token = ""

        try:
            f = open(self.pcPath, 'r')
            access_token = f.read()
            self.LogFile("CONTROLLER: Access Token: {}".format(access_token))
            f.close()
        except IOError as e:
            self.LogFile("CONTROLLER: Reading access_token. I/O error({0}): {1}".format(e.errno, e.strerror))

        if not access_token:
            self.Sync()
        else:
            c = self.dropbox.connect(not FIRST_TIME, access_token)
            if c == 1:
                self.notes[0].updateStatusBar('Failed connection to Dropbox')
                self.trayIcon.showMessage("Authenticating ...", "Failed connection to Dropbox", msecs=3000)
            else:
                self.dropbox.startBG_Dropbox_Thread()
                self.trayIcon.showMessage("Authenticating ...", "Connected to Dropbox", msecs=3000)

    def addNote(self, _id=-1):
        if _id == -1:
            # It's a real new note
            self.counter_noteID += 1
            _id = self.counter_noteID

        self.LogFile("CONTROLLER: Adding note {}".format(_id))
        newIndex = len(self.notes)

        mw = mainwindow.MainWindow(_id, newIndex)
        self.notes.append(mw)

        # CONNECTING SIGNALS
        mw.newNoteAdded.connect(self.addNote)
        mw.noteDeleted.connect(self.deleteNote)
        mw.noteSaved.connect(self.saveNote)
        mw.synced.connect(self.Sync)
        mw.logFile.connect(self.LogFile)
        mw.initUI()

        self.LogFile("CONTROLLER: addNote. Setting index {} to note ID {}".format(mw.myIndex, mw.noteID))

        if self.dropbox.client is not None:
            self.notes[mw.myIndex].updateStatusBar('Connected to Dropbox')

    def deleteNote(self, _id):

        index = self.getIndex(_id)
        if index == -1:
            self.LogFile("CONTROLLER: Error deleting note")
        else:
            if self.dropbox.client is not None:
                self.dropbox.deleteFile(_id)

            self.notes.remove(self.notes[index])

            # Update the biggest ID
            if self.counter_noteID == _id:
                self.counter_noteID = self.lookForTheBiggest()

    def saveNote(self, _id, _text):
        # First, check if we are already login in Dropbox
        if self.dropbox.client is not None:
            self.LogFile("CONTROLLER: Note {} will be saved".format(_id))
            self.dropbox.put_file(_id, _text)
        else:
            ok = self.Sync()
            if ok is True:
                self.Save()
            else:
                self.LogFile("CONTROLLER: Current note could not be saved because you are not connected to Dropbox")

    def appQuit(self):
        self.LogFile("CONTROLLER: Exiting")
        self.trayIcon.hide()
        self.app.quit()

    def showAll(self):
        self.LogFile("CONTROLLER: Show on Top")
        flagsOnTop = Qt.CustomizeWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint
        for m in self.notes:
            m.setWindowFlags(flagsOnTop)
            m.show()

    def hideAll(self):
        self.LogFile("CONTROLLER: Hide all notes")
        flagsOnBottom = Qt.CustomizeWindowHint | Qt.Tool | Qt.WindowShadeButtonHint
        for m in self.notes:
            m.setWindowFlags(flagsOnBottom)

    def showStatus(self):

        if self.dropbox.client is None:
            status = "Your notes are not associated to any Dropbox account"
        else:
            user = self.dropbox.client.account_info()
            status = "Hi {}\n\nThe notes are associated to your {} Dropbox account".format(user['display_name'], user['email'])

        dlg = QMessageBox(self.notes[0])
        dlg.setWindowTitle('Status')
        dlg.setIcon(QMessageBox.Information)
        dlg.setText(status)
        dlg.resize(300, 50)

        screenGeometry = self.app.desktop().screenGeometry()
        x = (screenGeometry.width() - dlg.width()) / 2
        y = (screenGeometry.height() - dlg.height()) / 2
        dlg.move(x, y - 100)

        dlg.exec_()

    def stopSync(self):

        reply = QMessageBox.question(self.notes[0], 'Stop Synchronization',
                                     "Are you sure to stop Dropbox synchronization?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.No:
            return

        self.LogFile("CONTROLLER:  Stopping synchronization")
        self.dropbox.bd.isConnected = False
        self.dropbox.client = None

        try:
            os.remove(self.pcPath)
        except OSError as e:
            self.LogFile("CONTROLLER: StopSync. OSError error({0}): {1}".format(e.errno, e.strerror))

        self.closeCurrentNotes(0)
        self.notes[0].updateStatusBar("Disconnected from Dropbox")
        self.trayIcon.showMessage("Synchronization", "Stopping synchronization with Dropbox", icon=QSystemTrayIcon.Warning, msecs=3000)

    def Sync(self):

        if self.dropbox.client is not None:
            self.LogFile("CONTROLLER: You are already connected to Drobox")
            self.trayIcon.showMessage("Synchronization", "You are already connected to Drobox", icon=QSystemTrayIcon.Warning, msecs=3000)
            return False

        # Start Authentication
        for m in self.notes:
            m.updateStatusBar('Authenticating ...')

        authorize_url = self.dropbox.start_connection()
        ok = self.start_dropbox(authorize_url)

        return ok

    def start_dropbox(self, url):

        click_url = QLabel()
        click_url.setTextFormat(Qt.RichText)
        click_url.setTextInteractionFlags(Qt.TextBrowserInteraction)
        click_url.setTextInteractionFlags(Qt.LinksAccessibleByMouse)
        click_url.setOpenExternalLinks(True)
        click_url.setText('1. Go to: <a target="_blank" href="{}">Dropbox Authentication Link</a><br>'
                          '2. Click "Allow" (you might have to log in first)<br>'
                          '3. Copy the authorization code.<br><br>'
                          'Enter the authorization code here: '.format(url))

        dlg = QInputDialog(self.notes[0])
        dlg.setWindowTitle('Dropbox Authorization')
        dlg.setInputMode(QInputDialog.TextInput)
        dlg.setLabelText(click_url.text())
        dlg.resize(500, 50)

        screenGeometry = self.app.desktop().screenGeometry()
        x = (screenGeometry.width() - dlg.width()) / 2
        y = (screenGeometry.height() - dlg.height()) / 2
        dlg.move(x, y - 100)

        ok = dlg.exec_()
        code = dlg.textValue()

        if ok:
            for m in self.notes:
                m.updateStatusBar('Connecting ...')

            c = self.dropbox.connect(FIRST_TIME, code)

            if c == 0:
                reply = QMessageBox.question(self.notes[0], 'Note Addition',
                                             "Current notes will be closed. Do you want to continue?",
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

                if reply == QMessageBox.Yes:
                    self.closeCurrentNotes(0)
                    self.dropbox.startBG_Dropbox_Thread()
                else:
                    self.LogFile("CONTROLLER: start_dropbox. Connection cancelled")
                    for m in self.notes:
                        m.updateStatusBar('Connection cancelled')

                    self.dropbox.client = None
                    return False
            else:
                for m in self.notes:
                    m.updateStatusBar('Failed connection to Dropbox')

                self.dropbox.client = None
                return False

        else:
            for m in self.notes:
                m.updateStatusBar('Connection cancelled')

            self.dropbox.client = None
            return False

        return True

    def closeCurrentNotes(self, _index):

        temp_m = None

        for m in self.notes:
            if m.myIndex == _index:
                temp_m = m
            else:
                m.close()

        self.notes.clear()
        self.counter_noteID = 1
        temp_m.noteItself.clear()
        temp_m.myIndex = 0
        temp_m.noteID = 1
        self.notes.append(temp_m)

    def update(self, _id, _noteText):
        self.LogFile("CONTROLLER: Updating note {}".format(_id))

        # Update the biggest ID
        if self.counter_noteID < _id:
            self.counter_noteID = _id

        index = self.getIndex(_id)

        if index == -1:
            self.addNote(_id)
            index = len(self.notes) - 1

        self.notes[index].updateNote(_noteText)
        self.notes[index].noteItself.setDisabled(False)
        self.notes[index].updateStatusBar('Connected to Dropbox')

    def getIndex(self, _id):

        i = 0
        for mainw in self.notes:
            if mainw.noteID == _id:
                # self.LogFile("CONTROLLER: Index found: ", i, " ( NodeID = ", _id, ")")
                return i
            else:
                i += 1

        # self.LogFile("CONTROLLER: Index no found")
        return -1

    def lookForTheBiggest(self):

        biggest = 1
        for m in self.notes:
            if m.noteID > biggest:
                biggest = m.noteID

        self.LogFile("CONTROLLER: The new biggest is {}".format(biggest))
        return biggest

    def LogFile(self, string):
        try:
            now = time.strftime("%c")
            Final_str = '%s' % now + " - %s" % string + "\n"
            self.logFileDescriptor.write(Final_str)
            self.logFileDescriptor.flush()
        except IOError as e:
            self.trayIcon.showMessage("LogFile Error", e.strerror, icon=QSystemTrayIcon.Critical, msecs=3000)
            self.appQuit()


