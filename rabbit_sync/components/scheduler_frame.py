import tkinter as tk
from tkinter import ttk
from rabbit_sync.components.collapsible_frame import create_collapsible_frame

def create_scheduler_frame(parent, app):
    frame, content = create_collapsible_frame(parent, "4. Automation Cron Background Task Settings", expanded=False, expanded_var=app.state.scheduler_expanded_var)
    
    row_bg = ttk.Frame(content)
    row_bg.pack(fill="x", padx=5, pady=5)
    ttk.Checkbutton(
        row_bg, 
        text="Enable Background Automation Service Routine Flow Loop Run", 
        variable=app.state.run_bg_var, 
        command=app.handlers.toggle_scheduler_ui
    ).pack(side="left", padx=5)
    
    app.state.time_frame = ttk.Frame(content)
    ttk.Label(app.state.time_frame, text="Daily Execution Sync Target Time Window:").pack(side="left", padx=5)
    ttk.Spinbox(app.state.time_frame, from_=0, to=23, wrap=True, textvariable=app.state.sync_hour_var, width=3, format="%02.0f").pack(side="left", padx=2)
    ttk.Label(app.state.time_frame, text=":").pack(side="left")
    ttk.Spinbox(app.state.time_frame, from_=0, to=59, wrap=True, textvariable=app.state.sync_minute_var, width=3, format="%02.0f").pack(side="left", padx=2)
    
    app.state.interval_options_frame = ttk.Frame(content)
    ttk.Label(app.state.interval_options_frame, text="Recurrence Frequency:").pack(side="left", padx=5)
    ttk.Combobox(app.state.interval_options_frame, textvariable=app.state.bg_interval_mode_var, values=["Daily", "Hourly", "Minute"], state="readonly", width=10).pack(side="left", padx=5)
    ttk.Spinbox(app.state.interval_options_frame, from_=1, to=60, textvariable=app.state.bg_interval_value_var, width=4).pack(side="left", padx=2)
    
    app.state.btn_register_task = ttk.Button(
        content, 
        text="💾 Save Automation Task Registry", 
        command=app.handlers.modify_windows_scheduler
    )

    app.state.btn_disable_task = ttk.Button(
        content,
        text="Disable Background Automation Service",
        command=app.handlers.disable_windows_scheduler,
    )
    
    app.handlers.toggle_scheduler_ui()
    return frame
