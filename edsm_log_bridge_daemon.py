from pathlib import Path
import os, json, sys, glob
from time import sleep
from threading import Thread, Lock

JOURNAL_DIR = os.path.join(Path.home(), 'Saved Games', 'Frontier Developments', 'Elite Dangerous')
CONFIG_DIR = os.path.join(Path.home(), 'AppData', 'local', 'EDWatcher')
CONFIG_FILE = 'edwatcher.conf'
CONFIG_PATH = os.path.join(CONFIG_DIR, CONFIG_FILE)

class DirectoryWatcher:

    def __init__(self, dir, set_hook):
        self.dir = dir
        self.terminate = False
        self.set_hook = set_hook

    def terminate(self):
        self.terminate = True

    def loop(self):
        while not self.terminate:
            # get last modified file
            current_latest_file = max(glob.glob(os.path.join(self.dir, '*')), key=os.path.getctime)
            self.set_hook(current_latest_file)
            sleep(1)

class FileWatcher:

    def __init__(self, path, commit_hook, last_committed_hook):
        self.path = path
        self.commit_hook = commit_hook
        self.terminate = False
        self.last_committed_hook = last_committed_hook

    def terminate(self):
        self.terminate = True

    def loop(self):
        while not self.terminate:
            committed = True
            with open(self.path, 'r') as f:
                for line in f.readlines():
                    if not committed:
                        self.commit_hook(line)
                    last_committed, lock = self.last_committed_hook()
                    if line == last_committed:
                        committed = False
                    lock.release()
            sleep(1)

class SubmitWatcher:

    def __init__(self, set_last_entry_hook):
        self.commit_entries = []
        self.terminate = False
        self.set_last_entry = set_last_entry_hook

    def commit(self, entries):
        self.commit_entries = list(entries)
        return self.commit_entries

    def loop(self):
        while not self.terminate:
            if len(self.commit_entries) > 0:
                last_entry = None
                for entry in self.commit_entries:
                    print('commit entry: %s' % entry)
                    last_entry = entry
                self.commit_entries = []
                self.set_last_entry(last_entry)
            sleep(5)

class EDWatcher:
    '''
    EDWatcher provides a interface to ED pilots journal and submits data to ED pilots database webapi.
    '''

    def __init__(self):
        print('starting ED watcher...')

        self.terminate = False

        # test if config path and file exists
        Path(CONFIG_DIR).mkdir(exist_ok=True, parents=True)
        if not Path(CONFIG_PATH).exists():
            with open(CONFIG_PATH, 'w') as f:
                f.write(json.dumps({
                    'last_submitted': ''
                }))
        self.conf = None
        try:
            with open(CONFIG_PATH, 'r') as f:
                self.conf = json.loads(f.read())
        except:
            print('ERROR: Can not parse config file.')
            sys.exit(1)
        print('last submitted entry was %s' % self.conf['last_submitted'])
        self.watch_file = None
        self.entries_to_commit = []
        self.commit_entry_lock = Lock()
        self.last_committed_lock = Lock()
        self.file_watcher = None
        self.submit_watcher = SubmitWatcher(self.update_last_submitted)
        Thread(target=self.submit_watcher.loop).start()

    def add_commit_entry(self, entry):
        self.commit_entry_lock.acquire()
        if entry not in self.entries_to_commit:
            print('adding new submit entry: %s' % entry)
            self.entries_to_commit.append(entry)
        self.commit_entry_lock.release()

    def set_watch_file(self, path):
        if self.watch_file != path:
            print('new file watching is: %s' % path)
            self.watch_file = path
            if self.file_watcher:
                print('stopping old file watcher')
                self.file_watcher.terminate()
            print('starting new file watcher')
            fw = FileWatcher(path, self.add_commit_entry, self.get_last_committed)
            Thread(target=fw.loop).start()

    def get_last_committed(self):
        self.last_committed_lock.acquire()
        return self.conf['last_submitted'], self.last_committed_lock

    def update_last_submitted(self, obj):
        self.conf['last_submitted'] = obj
        with open(CONFIG_PATH, 'w') as f:
            f.write(json.dumps(self.conf))

    def loop(self):
        while not self.terminate:
            self.commit_entry_lock.acquire()
            queued = self.submit_watcher.commit(self.entries_to_commit)
            self.entries_to_commit = [n for n in self.entries_to_commit if n not in queued]
            self.commit_entry_lock.release()
            sleep(10)

    def run(self):

        # parse all files for not submitted entries
        files = glob.glob(os.path.join(JOURNAL_DIR, '*'))
        submitted = True
        if self.conf['last_submitted'] == '':
            submitted = False
        for file in files:
            with open(file, 'r') as f:
                for line in f.readlines():
                    if not submitted:
                        self.add_commit_entry(line)
                    if line == self.conf['last_submitted']:
                        submitted = False


        directory_watcher = DirectoryWatcher(JOURNAL_DIR, self.set_watch_file)
        directory_watcher_thread = Thread(target=directory_watcher.loop)
        directory_watcher_thread.start()

        self.loop()

if __name__ == '__main__':
    app = EDWatcher()
    app.run()
