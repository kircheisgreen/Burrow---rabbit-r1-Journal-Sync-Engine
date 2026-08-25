import tkinter as tk
from tkinter import ttk


def create_collapsible_frame(parent, title, expanded=True, expanded_var=None):
    frame = ttk.LabelFrame(parent, text=title)
    frame.pack(fill="x", padx=10, pady=5)

    header = ttk.Frame(frame)
    header.pack(fill="x", padx=4, pady=2)
    content = ttk.Frame(frame)
    toggle_button = ttk.Button(frame, width=3)

    def set_expanded(is_expanded):
        if is_expanded and not content.winfo_manager():
            content.pack(fill="x", padx=5, pady=5)
            toggle_button.configure(text="-")
        elif not is_expanded and content.winfo_manager():
            content.pack_forget()
            toggle_button.configure(text="+")

    def toggle():
        is_expanded = bool(content.winfo_manager())
        if expanded_var is not None:
            expanded_var.set(not is_expanded)
        else:
            set_expanded(not is_expanded)

    toggle_button.configure(text="-" if expanded else "+", command=toggle)
    toggle_button.configure(command=toggle)
    toggle_button.pack(in_=header, side="right")
    set_expanded(expanded_var.get() if expanded_var is not None else expanded)
    if expanded_var is not None:
        expanded_var.trace_add("write", lambda *_: set_expanded(bool(expanded_var.get())))

    return frame, content
