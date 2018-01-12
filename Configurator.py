from tkinter import *
from tkinter import ttk
from threading import Thread

class Config_App(Thread):
    def __init__(self, save_hook, config, *args, **kwargs):
        super(Config_App, self).__init__(*args, **kwargs)
        self.window = Tk()
        self.window.title = "EDWatcher - Configuration"
        self.save_hook = save_hook
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
        self.enable_edsm_upload = BooleanVar()
        self.enable_edsm_upload.set(self.config['enable_edsm_upload'])

        ttk.Label(mainframe, text='Enable notifications').grid(column=0, row=0, sticky=(W, E))
        ttk.Label(mainframe, text='Enable upload to EDSM').grid(column=0, row=1, sticky=(W, E))
        ttk.Label(mainframe, text='EDSM API key').grid(column=0, row=2, sticky=(W, E))

        ttk.Checkbutton(mainframe, variable=self.enable_notifications).grid(column=1, row=0, sticky=(W, E))
        ttk.Checkbutton(mainframe, variable=self.enable_edsm_upload).grid(column=1, row=1, sticky=(W, E))

        self.api_key_field = ttk.Entry(mainframe, width=15, textvariable=self.api_key).grid(column=1, row=2, sticky=(W,E))


        ttk.Button(mainframe, text='save', command=self.save_config).grid(column=1, row=3, sticky=(W, E))

    def save_config(self, *args):
        self.config['notifications'] = self.enable_notifications.get()
        self.config['enable_edsm_upload'] = self.enable_edsm_upload.get()
        self.config['edsm_api_key'] = self.api_key.get()
        self.save_hook(self.config)
        self.window.destroy()


    def start(self, *args, **kwargs):
        super(Config_App, self).start(*args, **kwargs)
        self.window.mainloop()