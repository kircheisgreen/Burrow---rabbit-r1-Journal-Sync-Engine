# SEMANTIC VERSION v0.4.0
import tkinter as tk
from tkinter import ttk

def create_auth_panel(parent, app):
    frame = ttk.LabelFrame(parent, text="1. Input Data Source Settings")
    frame.pack(fill="x", padx=10, pady=5)
    
    # Source Selection Row
    row_src = ttk.Frame(frame)
    row_src.pack(fill="x", padx=5, pady=5)
    ttk.Label(row_src, text="Data Source:", font=("Arial", 9, "bold")).pack(side="left", padx=5)
    
    cb_source = ttk.Combobox(
        row_src, 
        textvariable=app.state.source_mode_var, 
        values=["Rabbit Hole", "Google Mail"], 
        state="readonly", 
        width=15
    )
    cb_source.pack(side="left", padx=5)
    
    app.pasting_zone = ttk.Frame(frame)
    
    row_user = ttk.Frame(app.pasting_zone)
    row_user.pack(fill="x", padx=5, pady=2)
    ttk.Label(row_user, text="Username / Email:", width=15).pack(side="left", padx=5)
    ttk.Entry(row_user, textvariable=app.state.rabbit_username_var, width=35).pack(side="left", padx=5)
    
    row_pass = ttk.Frame(app.pasting_zone)
    row_pass.pack(fill="x", padx=5, pady=2)
    ttk.Label(row_pass, text="Account Password:", width=15).pack(side="left", padx=5)
    ttk.Entry(row_pass, textvariable=app.state.rabbit_password_var, show="*", width=35).pack(side="left", padx=5)
    
    # NEW v0.4.0: Interactive Radio Button Grid Wrapper
    row_radio = ttk.LabelFrame(app.pasting_zone, text="Post-Fetch Automation Sub-Routine Chaining")
    row_radio.pack(fill="x", padx=5, pady=5)
    
    r_none = ttk.Radiobutton(row_radio, text="Manual Sync (Default Stopped state)", variable=app.state.post_fetch_action_var, value="NONE")
    r_none.pack(anchor="w", padx=10, pady=2)
    
    r_sync = ttk.Radiobutton(row_radio, text="Run Sync After Fetch (Auto-executes 'Start Sync Process')", variable=app.state.post_fetch_action_var, value="SYNC")
    r_sync.pack(anchor="w", padx=10, pady=2)
    
    r_force = ttk.Radiobutton(row_radio, text="Run Force Override Sync (Auto-executes 'Force Override Sync All')", variable=app.state.post_fetch_action_var, value="FORCE")
    r_force.pack(anchor="w", padx=10, pady=2)
    
    def trigger_automated_browser_fetch():
        btn_fetch.config(state="disabled")
        app.log("Contacting automated background Chromium execution thread...")
        app.handlers.trigger_auto_auth()
        frame.after(1500, lambda: btn_fetch.config(state="normal"))

    ttk.Checkbutton(
        app.pasting_zone,
        text="Only Unfetched Dates",
        variable=app.state.only_unfetched_dates_var,
    ).pack(anchor="w", padx=10, pady=(2, 0))
    
    btn_fetch = ttk.Button(
        app.pasting_zone, 
        text="🔄 Programmatic Auto-Fetch Journals (Headless Routing)", 
        command=trigger_automated_browser_fetch
    )
    btn_fetch.pack(anchor="w", padx=10, pady=8)

    row_cleanup = ttk.Frame(frame)
    row_cleanup.pack(fill="x", padx=10, pady=(0, 8))
    ttk.Button(row_cleanup, text="Clear Cache", command=app.handlers.clear_cache).pack(side="left", padx=(0, 5))
    ttk.Button(row_cleanup, text="Clear Session", command=app.handlers.clear_session).pack(side="left", padx=5)
    ttk.Button(row_cleanup, text="Clear Log", command=app.handlers.clear_logs).pack(side="left", padx=5)
    
    def on_source_changed(event=None):
        if app.state.source_mode_var.get() == "Rabbit Hole":
            app.pasting_zone.pack(fill="x", pady=2)
        else:
            app.pasting_zone.pack_forget()
            app.state.access_token_var.set("GMAIL_OAUTH_CONNECTED")
            
    cb_source.bind("<<ComboboxSelected>>", on_source_changed)
    on_source_changed() 
    return frame
