import tkinter as tk

def create_scrollable_area(parent):
    canvas = tk.Canvas(parent, bg="black", highlightthickness=0)
    vsb = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)

    inner = tk.Frame(canvas, bg="black")
    canvas.create_window((0, 0), window=inner, anchor="nw")

    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    return canvas, vsb, inner