import tkinter as tk

from ui.app import AppShell
from utils.db import seed_words
from data.categories import study_categories

root = tk.Tk()
root.title("Ukrainian AI Trainer")
root.geometry("1240x860")
root.minsize(1080, 720)
root.configure(bg="#0d0d0f")

# Seed once if empty
seed_words(study_categories)

app = AppShell(root)
app.pack(fill="both", expand=True)

root.mainloop()