import json
from pathlib import Path
from multiprocessing import Process, Queue
from threading import Thread
from time import sleep

import os

import sys

from Configurator import Configurator
from Tray import Tray

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


class EDWatcher:
    def __init__(self):
        Path(CONFIG_DIR).mkdir(exist_ok=True, parents=True)
        if not Path(CONFIG_PATH).exists():
            with open(CONFIG_PATH, 'w') as f:
                f.write(json.dumps({
                    'last_submitted': '',
                    'notifications': True,
                    'edsm_api_key': '',
                    'enable_edsm_upload': False,
                }))
        self.conf = None
        try:
            with open(CONFIG_PATH, 'r') as f:
                self.conf = json.loads(f.read())
        except:
            print('ERROR: Can not parse config file.')
            quit(1)

        self.threads = []
        self.stop_queue_listeners = False
        self.stop_task_listener = False
        self.stop_config_listener = False

        self.config_window_open = False

    def run_tray_icon(self, q):
        tray = Tray(ICON_PATH, self.conf, q)
        tray.start()

    def run_config_window(self, q):
        config_window = Configurator(self.conf, q)
        config_window.start()

    def queue_listener(self, queue, stop_listener, stop_listeners):
        while not stop_listener and not stop_listeners:
            function, *args = queue.get()
            getattr(self, function)(*args)
            sleep(0.1)

    def run(self):
        self.config_process = None
        self.tray_queue = Queue()
        t = Thread(target=self.queue_listener,
                   args=(self.tray_queue, getattr(self, 'stop_task_listener'), getattr(self, 'stop_queue_listeners'),),
                   daemon=True)
        t.start()
        self.tray_process = Process(target=self.run_tray_icon, args=(self.tray_queue,))
        self.tray_process.start()
        t.join()

    def exit(self):
        if self.config_process:
            self.config_process.terminate()
        self.tray_process.terminate()
        self.stop_queue_listeners = True
        sys.exit(0)

    def toggle_notifications(self, config):
        self.conf['notifications'] = config['notifications']
        self.save_config()

    def update_config(self, config):
        self.conf = config

    def save_config(self):
        with open(CONFIG_PATH, 'w') as f:
            f.write(json.dumps(self.conf))

    def open_configurator(self):
        if not self.config_window_open:
            self.config_window_open = True
            self.config_queue = Queue()
            t = Thread(target=self.queue_listener,
                       args=(
                           self.config_queue, getattr(self, 'stop_config_listener'),
                           getattr(self, 'stop_queue_listeners'),),
                       daemon=True)
            t.start()
            self.config_process = Process(target=self.run_config_window, args=(self.config_queue,))
            self.config_process.start()
            self.config_process.join()
            self.config_window_open = False

class QueueListener(Thread):
    def __init__(self):
        super(QueueListener, self).__init__()


if __name__ == '__main__':
    EDWatcher().run()
