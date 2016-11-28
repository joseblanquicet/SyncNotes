#  coding=utf-8
__author__ = 'Jose Blanquicet'

# Include the Dropbox SDK libraries
from dropbox import client, rest
from PyQt5.QtCore import QObject, QThread, pyqtSignal

import background_dropbox
import controller
import main

# Get your app key and secret from the Dropbox developer website
APP_KEY = 's1pj9vty19ov8sk'
APP_SECRET = 'dbcjssxld8xmr7m'
MAIN_DIRECTORY = '/Apps/SharedNotes/'


class Dropbox(QObject):

    logFile = pyqtSignal(str)

    def __init__(self, c):
        super().__init__()

        self.controller = c
        self.client = None
        self.bd = background_dropbox.Background_Dropbox()

    def __del__(self):
        self.logFile.emit("Dropbox: Closing dropbox controller")

    def start_connection(self):
        """
        Initialize Dropbox connection
        """
        self.flow = client.DropboxOAuth2FlowNoRedirect(APP_KEY, APP_SECRET)

        # Have the user sign in and authorize this token
        authorize_url = self.flow.start()
        return authorize_url

    def connect(self, type, code):
        """
        Connect to Dropbox
        """

        if type == controller.FIRST_TIME:
            try:
                # This will fail if the user enters an invalid authorization code
                access_token, user_id = self.flow.finish(code)
            except rest.ErrorResponse as e:
                self.logFile.emit('Dropbox: You have to authorize the app to use your dropbox: '.format(str(e.error_msg)))
                return 1

            # Store access token to file
            try:
                path = main.getAccessTokenPath()
                f = open(path, 'w')
                f.write(access_token)
                self.logFile.emit("Dropbox: connect. {}".format(access_token))
                f.close()
            except IOError as e:
                self.logFile.emit("Dropbox: connect. I/O error({0}): {1}".format(e.errno, e.strerror))
                return 1

        else:
            access_token = code

        self.client = client.DropboxClient(access_token)
        self.logFile.emit('Dropbox: linked account: '.format(self.client.account_info()))

        return 0

    def startBG_Dropbox_Thread(self):

        # Start running dropbox thread
        self.bd.setClient(self.client)
        self.objThread = QThread()
        self.bd.moveToThread(self.objThread)
        self.objThread.started.connect(self.bd.longRunning)
        self.objThread.start()

    def put_file(self, note_id, text):
        """
        This function is call once the user save the modification in any note
        :type note_id int : it is the identifier of the just modified note
        :type text str: it is the complete text of the note noteID
        """

        filename = 'note{}.txt'.format(note_id)
        path = MAIN_DIRECTORY + filename

        f = open('filename.txt', 'w')
        f.write(text)
        f.close()
        f = open('filename.txt', 'rb')

        try:
            self.client.put_file(path, f, True)
        except rest.ErrorResponse as e:
            self.logFile.emit('Dropbox: Error saving file: '.format(str(e.error_msg)))
            f.close()
            return

        f.close()

        # self.logFile.emit("Dropbox: Uploaded:", response)

    def deleteFile(self, note_id):

        filename = 'note{}.txt'.format(note_id)
        path = MAIN_DIRECTORY + filename

        self.logFile.emit("Dropbox: Deleting file ".format(path))

        try:
            self.client.file_delete(path)
        except rest.ErrorResponse as e:
            self.logFile.emit('Dropbox: Error deleting file. Error: '.format(str(e.error_msg)))
            return False

        self.logFile.emit("Dropbox: Deleting completed")
        return True

