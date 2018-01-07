from pathlib import Path
import os
from time import time
from threading import Thread

JOURNAL_PATH = os.path.join(Path.home(), 'Saved Games', 'Frontier Developments', 'Elite Dangerous')

class DirWatcher(Thread):
    '''
    Finds the newest file and attach file watcher to it
    '''
    def __init__(self, file_watcher):
        self.file_watcher = file_watcher
        super(DirWatcher, self).__init__()

    def start(self):
        self.terminate = False
        self.loop()

    def loop(self):
        while not self.terminate:
            files = os.listdir(JOURNAL_PATH)


class FileWatcher:
    '''
    Watchies journal files for change and fire reader when file changes.
    '''
    def __init__(self, file):
        self.file = file