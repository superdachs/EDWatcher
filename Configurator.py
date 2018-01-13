from time import sleep
from tkinter import *
from tkinter import ttk
from threading import Thread


class Configurator:
    def __init__(self, config, queue, rqueue):
        self.queue = queue
        self.rqueue = rqueue
        self.window = Tk()
        self.window.title = "EDWatcher - Configuration"
        self.config = config

        mainframe = ttk.Frame(self.window, padding="10 10 15 15")
        mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(0, weight=1)

        self.EDSM_api_key = StringVar()
        self.api_key = StringVar()
        self.api_key.set(self.config['edsm_api_key'])
        self.enable_notifications = BooleanVar()
        self.enable_notifications.set(self.config['notifications'])
        self.enable_edsm_upload = IntVar()
        self.enable_edsm_upload.set(self.config['enable_edsm_upload'])

        ttk.Label(mainframe, text='Enable notifications').grid(column=0, row=0, sticky=(W, E))
        ttk.Label(mainframe, text='Enable upload to EDSM').grid(column=0, row=1, sticky=(W, E))
        ttk.Label(mainframe, text='EDSM API key').grid(column=0, row=2, sticky=(W, E))

        self.notification_checkbox = ttk.Checkbutton(mainframe, variable=self.enable_notifications)
        self.notification_checkbox.grid(column=1, row=0, sticky=(W, E))
        ttk.Checkbutton(mainframe, variable=self.enable_edsm_upload).grid(column=1, row=1, sticky=(W, E))

        self.api_key_field = ttk.Entry(mainframe, width=15, textvariable=self.api_key)
        self.api_key_field.grid(column=1, row=2, sticky=(W, E))
        ttk.Button(mainframe, text='save', command=self.save_action).grid(column=1, row=3, sticky=(W, E))

        self.window.protocol("WM_DELETE_WINDOW", self.stop)

    def save_action(self):
        self.local_update_config()
        self.queue.put(('update_config', self.config))
        self.queue.put(('save_config',))
        self.stop()

    def local_update_config(self):
        self.config['notifications'] = True if self.enable_notifications.get() == 1 else False
        self.config['enable_edsm_upload'] = self.enable_edsm_upload.get()
        self.config['edsm_api_key'] = self.api_key.get()

    def local_update_widgets(self):
        self.enable_notifications.set(1 if self.config['notifications'] else 0)
        self.enable_edsm_upload.set(self.config['enable_edsm_upload'])
        self.api_key.set(self.config['edsm_api_key'])

    def start(self):
        t = Thread(target=self.queue_listener,
                   args=(self.rqueue,),
                   daemon=True)
        t.start()
        self.window.mainloop()

    def stop(self):
        self.queue.put(('close_configurator',))
        self.window.destroy()

    def update_config(self, config):
        self.conf = config
        self.local_update_widgets()

    def queue_listener(self, queue):
        while True:
            function, *args = queue.get()
            getattr(self, function)(*args)
