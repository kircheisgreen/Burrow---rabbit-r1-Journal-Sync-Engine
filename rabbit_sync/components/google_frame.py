import tkinter as tk
from tkinter import ttk
from rabbit_sync.components.collapsible_frame import create_collapsible_frame

def create_google_panel(parent, app):
    frame, content = create_collapsible_frame(parent, "3. Target Directory Folder Structure Settings", expanded=False, expanded_var=app.state.google_expanded_var)
    
    row_secret = ttk.Frame(content)
    row_secret.pack(fill="x", padx=5, pady=2)
    ttk.Label(row_secret, text="OAuth Client Secret:", width=15).pack(side="left", padx=5)
    ttk.Entry(row_secret, textvariable=app.state.client_secret_var, width=35).pack(side="left", padx=5)
    ttk.Button(row_secret, text="Browse...", command=app.handlers.browse_credentials).pack(side="left", padx=5)
    
    row_fld = ttk.Frame(content)
    row_fld.pack(fill="x", padx=5, pady=5)
    ttk.Label(row_fld, text="Google Drive Folder:", font=("Arial", 9, "bold")).pack(side="left", padx=5)
    
    app.state.folder_dropdown = ttk.Combobox(
        row_fld, 
        textvariable=app.state.selected_folder_name, 
        values=["My Drive (Root)"], 
        state="readonly", 
        width=25
    )
    app.state.folder_dropdown.pack(side="left", padx=5)
    
    btn_load = ttk.Button(row_fld, text="🔄 Load Folders", command=app.handlers.trigger_load_folders)
    btn_load.pack(side="left", padx=5)
    return frame
