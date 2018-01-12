from pathlib import Path
import os, json, sys, glob
from time import sleep
from threading import Thread, Lock
from PIL import Image

import pystray
from win10toast import ToastNotifier

JOURNAL_DIR = os.path.join(Path.home(), 'Saved Games', 'Frontier Developments', 'Elite Dangerous')
CONFIG_DIR = os.path.join(Path.home(), 'AppData', 'local', 'EDWatcher')
CONFIG_FILE = 'edwatcher.conf'
CONFIG_PATH = os.path.join(CONFIG_DIR, CONFIG_FILE)


def resource_path(relative):
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative)


ICON_PATH = resource_path('icon.ico')
print(ICON_PATH)


class DirectoryWatcher:
    terminate = False

    def __init__(self, dir, set_hook):
        self.dir = dir
        self.terminate = False
        self.set_hook = set_hook

    def loop(self):
        while not self.terminate:
            # get last modified file
            current_latest_file = max(glob.glob(os.path.join(self.dir, '*')), key=os.path.getctime)
            self.set_hook(current_latest_file)
            sleep(1)
        print('directory watcher exits')


class FileWatcher:
    terminate = False

    def __init__(self, path, submit_hook, last_submitted_hook):
        self.path = path
        self.submit_hook = submit_hook
        self.terminate = False
        self.last_submitted_hook = last_submitted_hook

    def loop(self):
        while not self.terminate:
            submitted = True
            with open(self.path, 'r') as f:
                for line in f.readlines():
                    if not submitted:
                        self.submit_hook(line)
                    last_submitted, lock = self.last_submitted_hook()
                    if line == last_submitted:
                        submitted = False
                    lock.release()
            sleep(1)
        print('file watcher exits')


class SubmitWatcher:
    terminate = False

    def __init__(self, set_last_entry_hook, notifier, notify):
        self.submit_entries = []
        self.terminate = False
        self.set_last_entry = set_last_entry_hook
        self.notifier = notifier
        self.notify = notify

    def submit(self, entries):
        self.submit_entries = list(entries)
        return self.submit_entries

    def loop(self):
        while not self.terminate:
            if len(self.submit_entries) > 0:
                last_entry = None
                for entry in self.submit_entries:
                    print('submit entry: %s' % entry)
                    last_entry = entry
                if self.notify: self.notifier.show_toast(
                    "EDWatch",
                    "Submitted %d events catched from ED" % len(self.submit_entries),
                    icon_path=ICON_PATH,
                    duration=5
                )
                self.submit_entries = []
                self.set_last_entry(last_entry)
            sleep(5)
        print('submit watcher exits')


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
                    'last_submitted': '',
                    'notifications': True,
                }))
        self.conf = None
        try:
            with open(CONFIG_PATH, 'r') as f:
                self.conf = json.loads(f.read())
        except:
            print('ERROR: Can not parse config file.')
            quit(1)

        print('last submitted entry was %s' % self.conf['last_submitted'])
        self.watch_file = None
        self.entries_to_submit = []
        self.submit_entry_lock = Lock()
        self.last_submitted_lock = Lock()
        self.file_watcher = None
        self.notifier = ToastNotifier()
        self.submit_watcher = SubmitWatcher(self.update_last_submitted, self.notifier, self.conf['notifications'])
        t = Thread(target=self.submit_watcher.loop)
        self.threads = [t]
        t.start()

        icon_image = Image.open(ICON_PATH)
        exit_item = pystray.MenuItem(enabled=True, text='Exit', action=self.exit)
        notification_item = pystray.MenuItem(enabled=True, text='Notifications', action=self.toggle_notifications,
                                             checked=lambda item: self.conf['notifications'])
        tray_menu = pystray.Menu(exit_item, notification_item)
        self.icon = pystray.Icon(name='EDWatcher',
                                 icon=icon_image,
                                 title="EDWatcher", menu=tray_menu)

    def start_config(self):
        config_window = ConfigWindow()
        config_window.run()

    def toggle_notifications(self, *args, **kwargs):
        self.conf['notifications'] = not self.conf['notifications']
        if self.conf['notifications']:
            state = 'on'
        else:
            state = 'off'
        print('setting notifications to %s' % state)

    def add_submit_entry(self, entry):
        self.submit_entry_lock.acquire()
        if entry not in self.entries_to_submit:
            print('adding new submit entry: %s' % entry)
            self.entries_to_submit.append(entry)
        self.submit_entry_lock.release()

    def set_watch_file(self, path):
        if self.watch_file != path:
            print('new file watching is: %s' % path)
            self.watch_file = path
            if self.file_watcher:
                print('stopping old file watcher')
                self.file_watcher.terminate()
            print('starting new file watcher')
            self.file_watcher = FileWatcher(path, self.add_submit_entry, self.get_last_submitted)
            t = Thread(target=self.file_watcher.loop)
            self.threads.append(t)
            t.start()

    def get_last_submitted(self):
        self.last_submitted_lock.acquire()
        return self.conf['last_submitted'], self.last_submitted_lock

    def update_last_submitted(self, obj):
        self.conf['last_submitted'] = obj
        with open(CONFIG_PATH, 'w') as f:
            f.write(json.dumps(self.conf))

    def loop(self):
        while not self.terminate:
            self.submit_entry_lock.acquire()
            queued = self.submit_watcher.submit(self.entries_to_submit)
            self.entries_to_submit = [n for n in self.entries_to_submit if n not in queued]
            self.submit_entry_lock.release()
            sleep(10)

    def exit(self, *args, **kwargs):
        print('shut down EDWatcher')
        self.terminate = True
        self.directory_watcher.terminate = True
        self.file_watcher.terminate = True
        self.submit_watcher.terminate = True
        print('threads terminated')
        print('joining threads')
        exit_threads = []
        for t in self.threads:
            et = Thread(target=t.join)
            et.start()
            exit_threads.append(et)
        for et in exit_threads:
            if et: et.join()
        print('saving config')
        with open(CONFIG_PATH, 'w') as f:
            f.write(json.dumps(self.conf))
        self.icon.stop()

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
                        self.add_submit_entry(line)
                    if line == self.conf['last_submitted']:
                        submitted = False

        self.directory_watcher = DirectoryWatcher(JOURNAL_DIR, self.set_watch_file)
        directory_watcher_thread = Thread(target=self.directory_watcher.loop)
        directory_watcher_thread.start()
        self.threads.append(directory_watcher_thread)

        # running loop in a thread to start tray icon from main thread so this possibly runs also on mac os
        Thread(target=self.loop).start()

        def setup_icon(icon):
            icon.visible = True

        # icon.run blocks itself
        self.icon.run(setup_icon)
        print('goodbye')
        sys.exit(0)


if __name__ == '__main__':
    app = EDWatcher()
    app.run()
