#  coding=utf-8
__author__ = 'Jose Blanquicet'

import time
import requests
import ntpath
import controller_dropbox

from PyQt5.QtCore import QObject, pyqtSignal
from dropbox import rest


class Background_Dropbox(QObject):

    uploaded = pyqtSignal(int, str)
    logFile = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.client = None
        self.isConnected = False

    def longRunning(self):
        cursor = None
        changes = False

        while self.isConnected:
            result = self.client.delta(cursor)
            cursor = result['cursor']
            l = len(controller_dropbox.MAIN_DIRECTORY)

            for path, metadata in result['entries']:
                if path[:l] == controller_dropbox.MAIN_DIRECTORY.lower():
                    # TODO: Missing check if filename is one of our files called (note1.txt, note2.txt ... noteN.txt)
                    if metadata is not None:
                        # TODO: Update the notes
                        self.logFile.emit('Background Dropbox: %s was created/updated' % path)
                        noteID = self.getnoteID(path)
                        self.get_file(noteID)

                    else:
                        # TODO: Deletion of app files
                        # I MUST notify the deletion of file
                        # Then the user decide if delete completely the note or write the file again
                        self.logFile.emit('Background Dropbox: %s was deleted' % path)

            # if has_more is true, call delta again immediately
            if not result['has_more']:
                changes = False

            # poll until there are changes
            while not changes:
                response = requests.get('https://api-notify.dropbox.com/1/longpoll_delta',
                                        params={'cursor': cursor,  # latest cursor from delta call
                                                'timeout': 120})

                data = response.json()
                changes = data['changes']

            if not changes:
                self.logFile.emit('Background Dropbox: Timeout, polling again...')

            backoff = data.get('backoff', None)

            if backoff is not None:
                self.logFile.emit('Background Dropbox: Backoff requested. Sleeping for %d seconds...' % backoff)
                time.sleep(backoff)

            # self.logFile.emit('Background Dropbox: Resuming polling...')

    def getnoteID(self, path):

        head, tail = ntpath.split(path)
        filename = tail or ntpath.basename(head)
        point = filename.index('.')
        _id = filename[4:point]
        return _id

    def get_file(self, note_id):
        """
        This function is call once we detect there was an update in another device
        :argument  path is the absolute path in the Dropbox directory
        """

        filename = 'note{}.txt'.format(note_id)
        path = controller_dropbox.MAIN_DIRECTORY + filename

        try:
            f = self.client.get_file(path)
            noteText = f.read().decode("utf-8")
            self.uploaded.emit(int(note_id), noteText)

        except rest.ErrorResponse as e:
            self.logFile.emit('Background Dropbox: get_file. Error getting the file {}: {} '.format(path, str(e.error_msg)))
            return None

    def setClient(self, c):
        self.client = c
        self.isConnected = True

    def stopRunning(self):
        self.isConnected = False
