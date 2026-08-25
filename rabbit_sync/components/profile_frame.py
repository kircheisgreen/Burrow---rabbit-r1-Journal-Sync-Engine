import tkinter as tk
from tkinter import ttk

def create_profile_panel(parent, app):
    frame = ttk.LabelFrame(parent, text="👤 User Profile Setup Manager")
    frame.pack(fill="x", padx=10, pady=5, side="top")
    
    row = ttk.Frame(frame)
    row.pack(fill="x", padx=5, pady=5)
    
    ttk.Label(row, text="Active Profile:", font=("Arial", 9, "bold")).pack(side="left", padx=5)
    
    app.state.profile_dropdown = ttk.Combobox(
        row, 
        textvariable=app.state.active_profile_var, 
        values=["Default Profile"], 
        width=20
    )
    app.state.profile_dropdown.pack(side="left", padx=5)
    
    btn_save = ttk.Button(row, text="💾 Save Current Config", command=app.handlers.save_current_profile)
    btn_save.pack(side="left", padx=5)
    
    app.state.profile_dropdown.bind("<<ComboboxSelected>>", app.handlers.load_selected_profile)
    app.handlers.refresh_profile_combobox_list()
    return frame
