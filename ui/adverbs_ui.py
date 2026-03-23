import tkinter as tk
from data.adverbs import adverbs

class AdverbsPage(tk.Frame):
    def __init__(self, parent, go_home):
        super().__init__(parent, bg="black")

        tk.Button(self, text="Home", command=go_home).pack()

        for a, e in adverbs:
            tk.Label(self, text=f"{a} - {e}", fg="white", bg="black").pack()