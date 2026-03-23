import tkinter as tk
from tkinter import filedialog, messagebox

from utils.db import get_summary, list_decks, seed_words, import_words, get_mastery, get_weak_words
from utils.reinforcement import top_weak_words
from ui.dashboard import DashboardUI

# Keep your existing CEFR category dictionary in data/categories.py
from data.categories import study_categories


class HomePage:
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller

        self.frame = tk.Frame(root, bg="#0d0d0f")
        self.frame.pack(fill="both", expand=True)

        self.search_var = tk.StringVar()
        self._build()

    def _build(self):
        top = tk.Frame(self.frame, bg="#0d0d0f")
        top.pack(fill="x", padx=18, pady=(18, 10))

        tk.Label(top, text="Ukrainian AI Trainer", fg="white", bg="#0d0d0f", font=("Segoe UI", 24, "bold")).pack(anchor="w")
        tk.Label(top, text="CEFR curriculum · adaptive review · pronunciation scoring · semantic checking", fg="#aeb6c6", bg="#0d0d0f").pack(anchor="w", pady=(4, 0))

        actions = tk.Frame(top, bg="#0d0d0f")
        actions.pack(anchor="e", pady=(10, 0))
        self._btn(actions, "Load CEFR words", self.load_seed).pack(side="left", padx=4)
        self._btn(actions, "Dashboard", self.open_dashboard).pack(side="left", padx=4)
        self._btn(actions, "Study due", lambda: self.controller.show_study()).pack(side="left", padx=4)
        self._btn(actions, "Add words", self.controller.show_words).pack(side="left", padx=4)

        search = tk.Entry(self.frame, textvariable=self.search_var, font=("Segoe UI", 12), relief="flat")
        search.pack(fill="x", padx=18, pady=(0, 12), ipady=8)
        self.search_var.trace_add("write", lambda *_: self.refresh())

        self.summary_box = tk.Frame(self.frame, bg="#151922", highlightbackground="#2a3140", highlightthickness=1, padx=14, pady=14)
        self.summary_box.pack(fill="x", padx=18, pady=(0, 12))

        self.deck_area = tk.Frame(self.frame, bg="#0d0d0f")
        self.deck_area.pack(fill="both", expand=True, padx=18, pady=(0, 12))

        self.weak_area = tk.Frame(self.frame, bg="#0d0d0f")
        self.weak_area.pack(fill="x", padx=18, pady=(0, 18))

        self.refresh()

    def _btn(self, parent, text, cmd, accent="#1c1f26"):
        return tk.Button(parent, text=text, command=cmd, bg=accent, fg="white", relief="flat", padx=12, pady=8)

    def load_seed(self):
        count = seed_words(study_categories)
        messagebox.showinfo("Loaded", f"Seeded {count} words into SQLite.")
        self.refresh()

    def open_dashboard(self):
        DashboardUI(self.root)

    def refresh(self):
        q = self.search_var.get().strip().lower()
        for w in self.deck_area.winfo_children():
            w.destroy()

        s = get_summary()
        for w in self.summary_box.winfo_children():
            w.destroy()

        cards = [
            ("Total", s["total"]),
            ("Due", s["due"]),
            ("Mastered", s["mastered"]),
            ("Correct", s["correct"]),
            ("Wrong", s["wrong"]),
            ("Avg ease", f'{s["avg_ease"]:.2f}'),
        ]
        for i, (title, val) in enumerate(cards):
            box = tk.Frame(self.summary_box, bg="#151922", padx=12, pady=10)
            box.grid(row=0, column=i, padx=6, sticky="nsew")
            tk.Label(box, text=title, fg="#aeb6c6", bg="#151922").pack(anchor="w")
            tk.Label(box, text=str(val), fg="white", bg="#151922", font=("Segoe UI", 16, "bold")).pack(anchor="w")
            self.summary_box.grid_columnconfigure(i, weight=1)

        tk.Label(self.deck_area, text="Decks", fg="white", bg="#0d0d0f", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 8))

        decks = list_decks()
        rows = [d for d in decks if not q or q in d["deck"].lower() or q in d["level"].lower()]
        grid = tk.Frame(self.deck_area, bg="#0d0d0f")
        grid.pack(fill="x")

        for i, deck in enumerate(rows):
            card = tk.Frame(grid, bg="#151922", highlightbackground="#2a3140", highlightthickness=1, padx=14, pady=14)
            card.grid(row=i // 3, column=i % 3, sticky="nsew", padx=6, pady=6)

            title = f"{deck['deck']} ({deck['level']})"
            tk.Label(card, text=title, fg="white", bg="#151922", font=("Segoe UI", 12, "bold")).pack(anchor="w")
            tk.Label(
                card,
                text=f"{deck['total']} words · {deck['due']} due · ease {float(deck['avg_ease'] or 0):.2f}",
                fg="#aeb6c6",
                bg="#151922",
            ).pack(anchor="w", pady=(4, 0))

            card.bind("<Button-1>", lambda e, d=deck["deck"]: self.controller.show_study(deck_name=d))
            for child in card.winfo_children():
                child.bind("<Button-1>", lambda e, d=deck["deck"]: self.controller.show_study(deck_name=d))

            grid.grid_columnconfigure(i % 3, weight=1)

        tk.Label(self.weak_area, text="Weakest cards", fg="white", bg="#0d0d0f", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 8))
        weak_grid = tk.Frame(self.weak_area, bg="#0d0d0f")
        weak_grid.pack(fill="x")
        for i, w in enumerate(top_weak_words(8)):
            box = tk.Frame(weak_grid, bg="#151922", padx=10, pady=10)
            box.grid(row=0, column=i, sticky="nsew", padx=4)
            tk.Label(box, text=w["word"], fg="white", bg="#151922", font=("Segoe UI", 10, "bold")).pack(anchor="w")
            tk.Label(box, text=f"→ {w['translation']}", fg="#aeb6c6", bg="#151922").pack(anchor="w")
            weak_grid.grid_columnconfigure(i, weight=1)