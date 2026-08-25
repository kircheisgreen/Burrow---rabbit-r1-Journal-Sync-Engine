import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext

def create_actions_and_logs(parent, app):
    frame = ttk.Frame(parent)
    frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    row_opts = ttk.LabelFrame(frame, text="5. Output Preferences")
    row_opts.pack(fill="x", pady=5)
    
    # Dropdowns selectors configurations
    ttk.Label(row_opts, text="Doc Format:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
    ttk.Combobox(row_opts, textvariable=app.state.format_mode_var, values=["Google Doc", "Markdown", "PDF"], state="readonly", width=12).grid(row=0, column=1, padx=5, pady=2)
    
    ttk.Label(row_opts, text="Mind Mapping Image Format:").grid(row=0, column=2, padx=5, pady=2, sticky="w")
    ttk.Combobox(row_opts, textvariable=app.state.image_mode_var, values=["PNG", "SVG", "PDF"], state="readonly", width=8).grid(row=0, column=3, padx=5, pady=2)
    
    ttk.Checkbutton(row_opts, text="Dedup Profiles Content", variable=app.state.dedup_enabled_var).grid(row=0, column=4, padx=15, pady=2)
    
    row_btns = ttk.Frame(frame)
    row_btns.pack(fill="x", pady=5)
    
    app.state.btn_start = ttk.Button(row_btns, text="Start Sync Process", command=lambda: app.handlers.start_sync_thread(force=False))
    app.state.btn_start.pack(side="left", padx=5)
    
    app.state.btn_force = ttk.Button(row_btns, text="⚠️ Force Override Sync All", command=lambda: app.handlers.start_sync_thread(force=True))
    app.state.btn_force.pack(side="left", padx=5)
    
    lbl_log = ttk.Label(frame, text="System Process Logs Console Terminal:", font=("Arial", 9, "bold"))
    lbl_log.pack(anchor="w", pady=(5,0))
    
    app.state.log_area = scrolledtext.ScrolledText(frame, height=12, state="disabled", bg="#1e1e1e", fg="#d4d4d4", insertbackground="white")
    app.state.log_area.pack(fill="both", expand=True, pady=5)
    return frame
