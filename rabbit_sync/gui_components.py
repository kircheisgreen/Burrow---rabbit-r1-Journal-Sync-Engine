import tkinter as tk
from tkinter import ttk

def build_auth_frame(parent, app):
    """1. Rabbit Hole Automated Authentication Panel Component."""
    frame = ttk.LabelFrame(parent, text="1. Rabbit Hole Automated Authentication")
    frame.pack(fill="x", padx=10, pady=5)
    
    row_btn = ttk.Frame(frame)
    row_btn.pack(fill="x", padx=5, pady=5)
    ttk.Button(row_btn, text="🔄 Auto-Fetch Token from Browser", 
               command=app.trigger_auto_auth_thread).pack(side="left", padx=5)
    
    ttk.Entry(frame, textvariable=app.access_token_var, show="*", width=75).pack(padx=5, pady=5)
    return frame

def build_frameworks_frame(parent, app):
    """2. Note-Taking Framework Custom Checkbuttons Component."""
    frame = ttk.LabelFrame(parent, text="2. Note-Taking Framework Workflows")
    frame.pack(fill="x", padx=10, pady=5)
    
    for name, var in app.frameworks.items():
        ttk.Checkbutton(frame, text=name, variable=var).pack(anchor="w", padx=10, pady=2)
    return frame

def build_google_frame(parent, app):
    """3. Google Cloud API Credentials and Directory Chooser Dropdown Component."""
    frame = ttk.LabelFrame(parent, text="3. Google API & Folder Destination Configuration")
    frame.pack(fill="x", padx=10, pady=5)
    
    row_cred = ttk.Frame(frame)
    row_cred.pack(fill="x", padx=5, pady=2)
    ttk.Entry(row_cred, textvariable=app.client_secret_var, width=52).pack(side="left", padx=2)
    ttk.Button(row_cred, text="Browse", command=app.browse_credentials).pack(side="left", padx=2)
    
    row_drop = ttk.Frame(frame)
    row_drop.pack(fill="x", padx=5, pady=5)
    ttk.Label(row_drop, text="Parent Drive Folder:").pack(side="left", padx=5)
    
    app.folder_dropdown = ttk.Combobox(row_drop, textvariable=app.selected_folder_name, width=35, state="readonly")
    app.folder_dropdown.pack(side="left", padx=2)
    app.folder_dropdown['values'] = ["My Drive (Root)"]
    
    ttk.Button(row_drop, text="🔍 Load Folders", command=app.trigger_load_folders_thread).pack(side="left", padx=5)
    return frame

def build_scheduler_frame(parent, app):
    """4. Windows Task Scheduler Service Settings Component."""
    frame = ttk.LabelFrame(parent, text="4. Background Engine & Schedule Tasks")
    frame.pack(fill="x", padx=10, pady=5)
    
    row_toggle = ttk.Frame(frame)
    row_toggle.pack(fill="x", padx=5, pady=5)
    ttk.Checkbutton(row_toggle, text="Run as background service in Windows 11", 
                    variable=app.run_bg_var, command=app.toggle_scheduler_ui).pack(side="left")
    
    app.time_frame = ttk.Frame(frame)
    ttk.Label(app.time_frame, text="Daily Sync Time (24h format):").pack(side="left", padx=5)
    ttk.Spinbox(app.time_frame, from_=0, to=23, format="%02.0f", width=3, textvariable=app.sync_hour_var).pack(side="left")
    ttk.Label(app.time_frame, text=":").pack(side="left")
    ttk.Spinbox(app.time_frame, from_=0, to=59, format="%02.0f", width=3, textvariable=app.sync_minute_var).pack(side="left")
    
    app.btn_register_task = ttk.Button(frame, text="Update Windows Task Schedule", command=app.modify_windows_scheduler)
    return frame

def build_action_and_logs(parent, app):
    """5. Sync Trigger Buttons and Real-Time Diagnostic Text Window Monitor."""
    f_actions = ttk.Frame(parent)
    f_actions.pack(fill="x", padx=10, pady=10)
    
    app.btn_start = ttk.Button(f_actions, text="Start Sync Process", command=lambda: app.start_sync_thread(force=False))
    app.btn_start.pack(side="left", expand=True, fill="x", padx=5)
    
    app.btn_force = ttk.Button(f_actions, text="⚠️ Force Override Sync All", command=lambda: app.start_sync_thread(force=True))
    app.btn_force.pack(side="left", expand=True, fill="x", padx=5)
    
    f_log = ttk.LabelFrame(parent, text="System Process Logs")
    f_log.pack(fill="both", expand=True, padx=10, pady=5)
    app.log_area = tk.Text(f_log, wrap="word", height=8, state="disabled")
    app.log_area.pack(fill="both", expand=True, padx=5, pady=5)
