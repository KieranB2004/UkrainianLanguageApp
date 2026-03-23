import tkinter as tk
from tkinter import ttk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from utils.db import get_summary, get_progress, get_history, get_mastery, get_weak_words
from utils.reinforcement import interaction_history, top_weak_words

CEFR = ["A1", "A2", "B1", "B2", "C1", "C2"]


class DashboardUI:
    def __init__(self, root, on_close=None):
        self.root = root
        self.on_close = on_close
        self.win = tk.Toplevel(root)
        self.win.title("Dashboard")
        self.win.geometry("1240x860")
        self.win.configure(bg="#0d0d0f")

        self._build()

    def _build(self):
        top = tk.Frame(self.win, bg="#0d0d0f")
        top.pack(fill="x", padx=18, pady=(18, 10))

        tk.Label(top, text="Analytics Dashboard", fg="white", bg="#0d0d0f", font=("Segoe UI", 22, "bold")).pack(side="left")
        tk.Button(top, text="Close", command=self.close, bg="#1c1f26", fg="white", relief="flat", padx=12, pady=8).pack(side="right")

        s = get_summary()
        summary = tk.Frame(self.win, bg="#0d0d0f")
        summary.pack(fill="x", padx=18, pady=(0, 12))

        cards = [
            ("Total cards", str(s["total"])),
            ("Due now", str(s["due"])),
            ("Mastered", str(s["mastered"])),
            ("Correct", str(s["correct"])),
            ("Wrong", str(s["wrong"])),
            ("Avg ease", f'{s["avg_ease"]:.2f}'),
        ]

        for i, (t, v) in enumerate(cards):
            box = tk.Frame(summary, bg="#151922", highlightbackground="#2a3140", highlightthickness=1, padx=14, pady=14)
            box.grid(row=0, column=i, padx=6, sticky="nsew")
            tk.Label(box, text=t, fg="#aeb6c6", bg="#151922", font=("Segoe UI", 9)).pack(anchor="w")
            tk.Label(box, text=v, fg="white", bg="#151922", font=("Segoe UI", 18, "bold")).pack(anchor="w")
            summary.grid_columnconfigure(i, weight=1)

        master = tk.Frame(self.win, bg="#0d0d0f")
        master.pack(fill="x", padx=18, pady=(0, 12))
        self._cefr_bar(master, s)

        body = tk.Frame(self.win, bg="#0d0d0f")
        body.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        left = tk.Frame(body, bg="#0d0d0f")
        left.pack(side="left", fill="both", expand=True)

        right = tk.Frame(body, bg="#0d0d0f", width=340)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        self._chart_frame(left, "XP by CEFR level", self._plot_xp_by_level)
        self._chart_frame(left, "Accuracy over time", self._plot_accuracy)
        self._chart_frame(left, "Latency and reward", self._plot_latency_reward)

        weak = tk.LabelFrame(right, text="Weak words", bg="#0d0d0f", fg="white", padx=10, pady=10)
        weak.pack(fill="both", expand=True)

        for w in top_weak_words(12):
            row = tk.Frame(weak, bg="#151922", padx=8, pady=8)
            row.pack(fill="x", pady=4)
            tk.Label(row, text=f"{w['word']} → {w['translation']}", fg="white", bg="#151922", font=("Segoe UI", 10, "bold")).pack(anchor="w")
            tk.Label(row, text=f"wrong {w['wrong']} · ease {float(w['ease']):.2f} · level {w['level']}", fg="#aeb6c6", bg="#151922", font=("Segoe UI", 9)).pack(anchor="w")

        ai = tk.LabelFrame(right, text="RL summary", bg="#0d0d0f", fg="white", padx=10, pady=10)
        ai.pack(fill="x", pady=(10, 0))
        self.rl_text = tk.Text(ai, height=8, bg="#111318", fg="white", relief="flat", wrap="word")
        self.rl_text.pack(fill="x")
        self._refresh_rl_text()

    def _refresh_rl_text(self):
        items = interaction_history(30)
        if not items:
            text = "No interaction data yet."
        else:
            avg_reward = sum(i["reward"] for i in items) / len(items)
            avg_sem = sum(i["semantic_score"] for i in items) / len(items)
            avg_pron = sum(i["pronunciation_score"] for i in items) / len(items)
            text = (
                f"30-day interactions: {len(items)}\n"
                f"Avg reward: {avg_reward:.2f}\n"
                f"Avg semantic: {avg_sem:.2f}\n"
                f"Avg pronunciation: {avg_pron:.2f}\n\n"
                "The review policy now reweights harder cards more often."
            )
        self.rl_text.delete("1.0", "end")
        self.rl_text.insert("1.0", text)
        self.rl_text.config(state="disabled")

    def _cefr_bar(self, parent, s):
        row = tk.Frame(parent, bg="#0d0d0f")
        row.pack(fill="x")

        mastered = s["mastered"]
        max_words = 5000
        prog = min(mastered / max_words, 1.0)

        box = tk.Frame(row, bg="#151922", highlightbackground="#2a3140", highlightthickness=1, padx=14, pady=14)
        box.pack(fill="x")

        tk.Label(box, text="CEFR progress", fg="white", bg="#151922", font=("Segoe UI", 12, "bold")).pack(anchor="w")

        canvas = tk.Canvas(box, height=44, bg="#151922", highlightthickness=0)
        canvas.pack(fill="x", pady=(8, 0))
        width = 980
        canvas.configure(width=width)
        canvas.create_rectangle(0, 10, width, 28, fill="#222733", outline="")
        canvas.create_rectangle(0, 10, int(width * prog), 28, fill="#43d39e", outline="")

        for i, label in enumerate(CEFR):
            x = int((i / (len(CEFR) - 1)) * width)
            canvas.create_line(x, 8, x, 32, fill="#444a5a")
            canvas.create_text(x, 38, text=label, fill="#aeb6c6", font=("Segoe UI", 9))

        canvas.create_text(6, 0, text=f"{mastered} mastered", fill="white", anchor="w", font=("Segoe UI", 10, "bold"))

    def _chart_frame(self, parent, title, plot_fn):
        box = tk.Frame(parent, bg="#151922", highlightbackground="#2a3140", highlightthickness=1, padx=10, pady=10)
        box.pack(fill="both", expand=True, pady=(0, 12))
        tk.Label(box, text=title, fg="white", bg="#151922", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        fig = plot_fn()
        canvas = FigureCanvasTkAgg(fig, master=box)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _plot_xp_by_level(self):
        data = {r["level"]: r["xp"] for r in get_progress()}
        fig, ax = plt.subplots(figsize=(8.5, 2.6), dpi=100)
        xs = CEFR
        ys = [data.get(level, 0) for level in xs]
        ax.bar(xs, ys)
        ax.set_title("XP by level")
        ax.set_ylabel("XP")
        return fig

    def _plot_accuracy(self):
        hist = get_history(60)
        fig, ax = plt.subplots(figsize=(8.5, 2.6), dpi=100)
        if not hist:
            ax.text(0.5, 0.5, "No history", ha="center", va="center")
            return fig

        correct = [int(h["correct"]) for h in hist]
        cum = []
        total = 0
        good = 0
        for c in correct:
            total += 1
            good += c
            cum.append(good / total)

        ax.plot(cum)
        ax.set_ylim(0, 1)
        ax.set_title("Accuracy over time")
        ax.set_ylabel("Accuracy")
        ax.set_xlabel("Review index")
        return fig

    def _plot_latency_reward(self):
        hist = interaction_history(60)
        fig, ax = plt.subplots(figsize=(8.5, 2.6), dpi=100)
        if not hist:
            ax.text(0.5, 0.5, "No interaction data", ha="center", va="center")
            return fig

        latency = [h["latency"] for h in hist]
        reward = [h["reward"] for h in hist]
        ax.plot(latency, label="latency")
        ax.plot(reward, label="reward")
        ax.legend()
        ax.set_title("Latency and reward")
        return fig

    def close(self):
        if self.on_close:
            self.on_close()
        self.win.destroy()