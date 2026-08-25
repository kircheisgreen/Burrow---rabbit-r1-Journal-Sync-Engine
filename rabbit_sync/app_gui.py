# CODE REFACTOR GENERATION: PROMPT SEMANTIC VERSION v0.5.2
import os
import json
import tkinter as tk
from tkinter import ttk

from rabbit_sync.gui_state import AppState
from rabbit_sync.gui_handlers import GUIEventHandlers
from rabbit_sync.auth_crawler import DUMP_FILE
from rabbit_sync.version import __version__  # Dynamic version import

# Import modular user interface component panels
import rabbit_sync.components.profile_frame as profile_ui
import rabbit_sync.components.auth_frame as auth_ui
import rabbit_sync.components.frameworks_frame as frame_ui
import rabbit_sync.components.google_frame as google_ui
import rabbit_sync.components.scheduler_frame as sched_ui
import rabbit_sync.components.actions_frame as action_ui

class RabbitSyncApp:
    def __init__(self, root):
        self.root = root
        
        # DYNAMIC v0.5.2: Populate title template using imported tracking state
        self.root.title(f"Burrow v{__version__} - Journal Sync Engine")
        self.root.geometry("800x1000")
        
        self.state = AppState()
        self.handlers = GUIEventHandlers(self)
        
        self.assemble_modular_layout()
        self.load_cached_token_on_startup()

    def assemble_modular_layout(self):
        """Assemble the panels inside a viewport that can scroll in both directions."""
        viewport = ttk.Frame(self.root)
        viewport.pack(fill="both", expand=True)

        self.layout_canvas = tk.Canvas(viewport, highlightthickness=0)
        vertical_scrollbar = ttk.Scrollbar(
            viewport, orient="vertical", command=self.layout_canvas.yview
        )
        horizontal_scrollbar = ttk.Scrollbar(
            viewport, orient="horizontal", command=self.layout_canvas.xview
        )
        self.layout_canvas.configure(
            yscrollcommand=vertical_scrollbar.set,
            xscrollcommand=horizontal_scrollbar.set,
        )

        vertical_scrollbar.grid(row=0, column=1, sticky="ns")
        horizontal_scrollbar.grid(row=1, column=0, sticky="ew")
        self.layout_canvas.grid(row=0, column=0, sticky="nsew")
        viewport.grid_rowconfigure(0, weight=1)
        viewport.grid_columnconfigure(0, weight=1)

        self.layout_content = ttk.Frame(self.layout_canvas)
        self.layout_window = self.layout_canvas.create_window(
            (0, 0), window=self.layout_content, anchor="nw"
        )
        self.layout_content.bind(
            "<Configure>",
            lambda event: self.layout_canvas.configure(
                scrollregion=self.layout_canvas.bbox("all")
            ),
        )
        self.layout_canvas.bind(
            "<Configure>",
            lambda event: self.layout_canvas.itemconfigure(
                self.layout_window, width=max(event.width, self.layout_content.winfo_reqwidth())
            ),
        )

        profile_ui.create_profile_panel(self.layout_content, self)
        auth_ui.create_auth_panel(self.layout_content, self)
        frame_ui.create_frameworks_panel(self.layout_content, self)
        google_ui.create_google_panel(self.layout_content, self)
        sched_ui.create_scheduler_frame(self.layout_content, self)
        action_ui.create_actions_and_logs(self.layout_content, self)

    def load_cached_token_on_startup(self):
        """Loads previous context logs if active on the local disk system."""
        if os.path.exists(DUMP_FILE):
            try:
                self.state.access_token_var.set("BROWSER_COOKIE_AUTHENTICATED_SESSION_OK")
                self.log("Loaded active Rabbit Hole database data from local file cache storage.")
            except Exception: 
                pass

    def log(self, message):
        """Thread-safe logging console entry proxy."""
        self.root.after(0, self._safe_log_render, message)

    def _safe_log_render(self, message):
        try:
            if self.state.log_area and self.state.log_area.winfo_exists():
                self.state.log_area.config(state="normal")
                self.state.log_area.insert("end", str(message) + "\n")
                self.state.log_area.see("end")
                self.state.log_area.config(state="disabled")
        except Exception: 
            pass
