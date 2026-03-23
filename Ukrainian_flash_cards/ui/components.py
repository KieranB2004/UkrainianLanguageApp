import tkinter as tk

def make_button(parent, text, command):
    btn = tk.Label(parent, text=text, fg="white", bg="#1c1c1c",
                   bd=2, relief="solid", padx=12, pady=8)
    btn.bind("<Button-1>", command)
    btn.bind("<Enter>", lambda e: btn.config(bg="#333333"))
    btn.bind("<Leave>", lambda e: btn.config(bg="#1c1c1c"))
    return btn