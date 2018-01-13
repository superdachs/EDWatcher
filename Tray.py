from threading import Thread

import pystray
from PIL import Image


class Tray:
    def __init__(self, icon_path, conf, queue, rqueue):
        self.conf = conf
        self.queue = queue
        self.rqueue = rqueue
        self.icon_image = Image.open(icon_path)
        self.exit_item = pystray.MenuItem(enabled=True, text='Exit', action=self.exit_action)
        self.config_item = pystray.MenuItem(enabled=True, text='Configuration', action=self.open_configurator_action)
        self.tray_menu = pystray.Menu(self.config_item, self.exit_item)
        self.icon = pystray.Icon(name='EDWatcher',
                                 icon=self.icon_image,
                                 title="EDWatcher", menu=self.tray_menu)

    def start(self):
        t = Thread(target=self.queue_listener,
                   args=(self.rqueue,),
                   daemon=True)
        t.start()
        def setup_icon(icon):
            icon.visible = True

        # icon.run blocks itself
        self.icon.run(setup_icon)

    def open_configurator_action(self, *args):
        self.queue.put(('open_configurator',))

    def exit_action(self, *args):
        self.icon.visible = False
        self.icon.stop()
        self.queue.put(('exit',))


    def update_config(self, config):
        self.conf = config
        self.icon.update_menu()

    def queue_listener(self, queue):
        while True:
            function, *args = queue.get()
            getattr(self, function)(*args)
