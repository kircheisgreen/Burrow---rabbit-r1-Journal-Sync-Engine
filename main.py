import tkinter as tk
from rabbit_sync.app_gui import RabbitSyncApp

if __name__ == "__main__":
    root = tk.Tk()
    app = RabbitSyncApp(root)
    root.mainloop()
