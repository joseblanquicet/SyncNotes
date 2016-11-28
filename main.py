#  coding=utf-8
__author__ = 'Jose Blanquicet'

import os
import sys
import controller
from PyQt5.QtWidgets import QApplication

if __name__ == '__main__':
    app = QApplication(sys.argv)
    c = controller.Controller(app)
    sys.exit(app.exec_())


def getAccessTokenPath():
    return os.path.join(os.path.dirname(__file__), '.SharedNotes')


def getLogFilePath():
    return os.path.join(os.path.dirname(__file__), '.LogFile.log')
