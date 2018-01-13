import pystray
from PIL import Image


class Tray:
    def __init__(self, icon_path, conf, queue):
        self.conf = conf
        self.queue = queue
        self.icon_image = Image.open(icon_path)
        self.exit_item = pystray.MenuItem(enabled=True, text='Exit', action=self.exit_action)
        self.notification_item = pystray.MenuItem(enabled=True, text='Notifications',
                                                  action=self.toggle_notifications_action,
                                                  checked=lambda item: self.conf['notifications'])
        self.config_item = pystray.MenuItem(enabled=True, text='Configuration', action=self.open_configurator_action)
        self.tray_menu = pystray.Menu(self.notification_item, self.config_item, self.exit_item)
        self.icon = pystray.Icon(name='EDWatcher',
                                 icon=self.icon_image,
                                 title="EDWatcher", menu=self.tray_menu)

    def start(self):
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

    def toggle_notifications_action(self, *args):
        self.conf['notifications'] = not self.conf['notifications']
        self.queue.put(('toggle_notifications', self.conf))
