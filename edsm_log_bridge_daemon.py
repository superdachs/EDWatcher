from pathlib import Path
import os, json, sys, glob
from time import sleep
from threading import Thread

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
        #TODO: parse all files and queue not submitted entries

    def set_watch_file(self, path):
        if self.watch_file != path:
            print('new file watching is: %s' % path)
            self.watch_file = path

    def update_last_submitted(self, obj):
        self.conf['last_submitted'] = obj
        with open(CONFIG_PATH, 'w') as f:
            f.write(json.dumps(self.conf))

    def loop(self):
        while not self.terminate:
            sleep(1)

    def run(self):
        directory_watcher = DirectoryWatcher(JOURNAL_DIR, self.set_watch_file)
        directory_watcher_thread = Thread(target=directory_watcher.loop)
        directory_watcher_thread.start()

        self.loop()

if __name__ == '__main__':
    app = EDWatcher()
    app.run()
