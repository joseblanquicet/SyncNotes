#  coding=utf-8
__author__ = 'Jose Blanquicet'

from PyQt5.QtWidgets import QSystemTrayIcon, QMenu
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal


class SystemTrayIcon(QSystemTrayIcon):

    status = pyqtSignal()
    newNote = pyqtSignal(int)
    synchronized = pyqtSignal()
    stop = pyqtSignal()
    quited = pyqtSignal()
    showAll = pyqtSignal()
    hideAll = pyqtSignal()

    def __init__(self, _w):
        QSystemTrayIcon.__init__(self, QIcon('img/systray.png'), _w)

        self.showed = False
        self.activated.connect(self.clickEvent)

        self.menu = QMenu("System Tray Menu")

        NewAction = self.menu.addAction("New note")
        NewAction.triggered.connect(self.emitNewNote)

        self.menu.addSeparator()

        showAllAction = self.menu.addAction("Show All")
        showAllAction.triggered.connect(self.emitShowAll)

        hideAllAction = self.menu.addAction("Hide All")
        hideAllAction.triggered.connect(self.emitHideAll)

        self.menu.addSeparator()

        statusAction = self.menu.addAction("Status")
        statusAction.triggered.connect(self.emitStatus)

        syncAction = self.menu.addAction("Synchronize")
        syncAction.triggered.connect(self.emitSync)

        stopSyncAction = self.menu.addAction("Stop Sync")
        stopSyncAction.triggered.connect(self.emitStop)

        self.menu.addSeparator()

        exitAction = self.menu.addAction("Exit")
        exitAction.triggered.connect(self.emitQuit)

        self.setContextMenu(self.menu)
        self.show()

    def clickEvent(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.showed is False:
                self.showAll.emit()
                self.showed = True
            else:
                self.hideAll.emit()
                self.showed = False

    def emitNewNote(self):
        self.newNote.emit(-1)

    def emitStatus(self):
        self.status.emit()

    def emitSync(self):
        self.synchronized.emit()

    def emitStop(self):
        self.stop.emit()

    def emitQuit(self):
        self.quited.emit()

    def emitShowAll(self):
        self.showAll.emit()
        self.showed = True

    def emitHideAll(self):
        self.hideAll.emit()
        self.showed = False
