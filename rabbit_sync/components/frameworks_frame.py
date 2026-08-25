import tkinter as tk
from tkinter import ttk
from rabbit_sync.components.collapsible_frame import create_collapsible_frame

def create_frameworks_panel(parent, app):
    frame, content = create_collapsible_frame(parent, "2. Select Additional Note-Taking Frameworks Doc Output", expanded=True, expanded_var=app.state.frameworks_expanded_var)

    grid = ttk.Frame(content)
    grid.pack(fill="x")
    
    idx = 0
    for name, var in app.state.frameworks.items():
        r = idx // 2
        c = idx % 2
        cb = ttk.Checkbutton(grid, text=name, variable=var)
        cb.grid(row=r, column=c, sticky="w", padx=15, pady=5)
        idx += 1
        
    return frame
