import tkinter as tk
from data.verbs import verb_prefixes
from utils.scroll import create_scrollable_area

class PrefixesPage(tk.Frame):
    def __init__(self, parent, go_home):
        super().__init__(parent, bg="black")

        tk.Button(self, text="Home", command=go_home).pack(pady=5)

        canvas, vsb, content = create_scrollable_area(self)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        for p, desc in verb_prefixes:
            fr = tk.Frame(content, bg="#1c1c1c", bd=1, relief="solid", padx=8, pady=8)
            fr.pack(fill="x", padx=12, pady=6)

            tk.Label(fr, text=p, fg="white", bg="#1c1c1c",
                     font=("Segoe UI", 14, "bold")).pack(anchor="w")

            tk.Label(fr, text=desc, fg="#dddddd", bg="#1c1c1c",
                     wraplength=500, justify="left").pack(anchor="w")