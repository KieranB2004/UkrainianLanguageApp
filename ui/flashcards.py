import time
import tkinter as tk
from tkinter import messagebox

from utils.db import get_due_words, update_word, add_xp, get_summary
from utils.semantic_model import similarity
from utils.pronunciation import score_pronunciation
from utils.reinforcement import record_interaction, rank_words
from utils.error_classifier import classify_error
from utils.audio import speak


class FlashcardUI:
    def __init__(self, root, deck_name=None, focus_word=None):
        self.root = root
        self.deck_name = deck_name
        self.focus_word = focus_word

        self.words = get_due_words(deck=deck_name, focus_word=focus_word)
        self.words = rank_words(self.words)

        self.index = 0
        self.revealed = False
        self.session_started = time.monotonic()
        self.card_shown_at = time.monotonic()

        self.frame = tk.Frame(root, bg="#0d0d0f")
        self.frame.pack(fill="both", expand=True)

        self._build()
        self.render()

    def _build(self):
        top = tk.Frame(self.frame, bg="#0d0d0f")
        top.pack(fill="x", padx=18, pady=(18, 8))

        tk.Button(top, text="Home", command=self.go_home, bg="#1c1f26", fg="white", relief="flat", padx=12, pady=8).pack(side="left")
        self.title = tk.Label(top, text="Study Session", fg="white", bg="#0d0d0f", font=("Segoe UI", 18, "bold"))
        self.title.pack(side="left", padx=12)

        body = tk.Frame(self.frame, bg="#0d0d0f")
        body.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        left = tk.Frame(body, bg="#0d0d0f")
        left.pack(side="left", fill="both", expand=True)

        right = tk.Frame(body, bg="#0d0d0f", width=320)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        self.card = tk.Frame(left, bg="#151922", highlightbackground="#2a3140", highlightthickness=1, padx=18, pady=18)
        self.card.pack(fill="both", expand=True)

        self.word_label = tk.Label(
            self.card,
            text="",
            fg="white",
            bg="#151922",
            font=("Segoe UI", 30, "bold"),
            wraplength=640,
            justify="center",
        )
        self.word_label.pack(expand=True, fill="both", pady=(18, 6))

        self.meta_label = tk.Label(self.card, text="", fg="#aeb6c6", bg="#151922", font=("Segoe UI", 10))
        self.meta_label.pack(pady=(0, 10))

        self.feedback = tk.Label(self.card, text="", fg="#ffcb6b", bg="#151922", font=("Segoe UI", 11, "bold"), wraplength=640, justify="center")
        self.feedback.pack(pady=(0, 12))

        self.entry = tk.Entry(self.card, font=("Segoe UI", 14), relief="flat")
        self.entry.pack(fill="x", padx=18, pady=(0, 12), ipady=8)

        btn_row1 = tk.Frame(self.card, bg="#151922")
        btn_row1.pack(fill="x", pady=(0, 8))

        self._btn(btn_row1, "Submit", self.submit).pack(side="left", padx=4)
        self._btn(btn_row1, "Pronounce", self.pronounce).pack(side="left", padx=4)
        self._btn(btn_row1, "Speak Word", self.speak_word).pack(side="left", padx=4)
        self._btn(btn_row1, "AI Explain", self.ai_explain).pack(side="left", padx=4)

        btn_row2 = tk.Frame(self.card, bg="#151922")
        btn_row2.pack(fill="x")

        self._btn(btn_row2, "Again", lambda: self.rate(2), accent="#ff6b6b").pack(side="left", padx=4)
        self._btn(btn_row2, "Hard", lambda: self.rate(3), accent="#ffb020").pack(side="left", padx=4)
        self._btn(btn_row2, "Good", lambda: self.rate(4), accent="#31c48d").pack(side="left", padx=4)
        self._btn(btn_row2, "Easy", lambda: self.rate(5), accent="#43d39e").pack(side="left", padx=4)

        nav = tk.Frame(left, bg="#0d0d0f")
        nav.pack(fill="x", pady=(10, 0))

        self._btn(nav, "Prev", self.prev_card).pack(side="left", padx=4)
        self._btn(nav, "Flip", self.flip).pack(side="left", padx=4)
        self._btn(nav, "Next", self.next_card).pack(side="left", padx=4)
        self._btn(nav, "Refresh Due", self.refresh_session).pack(side="left", padx=4)
        self._btn(nav, "Dashboard", self.open_dashboard).pack(side="left", padx=4)

        info = tk.LabelFrame(right, text="Session", bg="#0d0d0f", fg="white", padx=10, pady=10)
        info.pack(fill="x", pady=(0, 10))

        self.session_label = tk.Label(info, text="", fg="#d8deea", bg="#0d0d0f", justify="left", anchor="w", wraplength=280)
        self.session_label.pack(fill="x")

        ai = tk.LabelFrame(right, text="AI Feedback", bg="#0d0d0f", fg="white", padx=10, pady=10)
        ai.pack(fill="both", expand=True)

        self.ai_text = tk.Text(ai, bg="#111318", fg="white", relief="flat", wrap="word")
        self.ai_text.pack(fill="both", expand=True)
        self.ai_text.insert("1.0", "AI feedback appears here.")
        self.ai_text.config(state="disabled")

        self.status = tk.Label(self.frame, text="", bg="#0d0d0f", fg="#aeb6c6")
        self.status.pack(fill="x", padx=18, pady=(0, 12))

        self.root.bind("<Left>", lambda e: self.prev_card())
        self.root.bind("<Right>", lambda e: self.next_card())
        self.root.bind("<space>", lambda e: self.flip())
        self.root.bind("<Escape>", lambda e: self.go_home())

    def _btn(self, parent, text, command, accent="#1c1f26"):
        fg = "white"
        if accent in ("#31c48d", "#43d39e", "#ffb020", "#ff6b6b"):
            fg = "#111111"
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=accent,
            fg=fg,
            activebackground=accent,
            activeforeground=fg,
            relief="flat",
            padx=12,
            pady=8,
            font=("Segoe UI", 10, "bold"),
        )

    def current(self):
        if not self.words:
            return None
        return self.words[self.index % len(self.words)]

    def render(self):
        if not self.words:
            self.word_label.config(text="No cards available")
            self.meta_label.config(text="Load categories or add words.")
            self.session_label.config(text="")
            return

        w = self.current()
        display = w["translation"] if self.revealed else w["word"]

        self.word_label.config(text=display)
        self.meta_label.config(
            text=f"{self.index + 1}/{len(self.words)} · Deck: {w['deck']} · Level: {w['level']} · due {self._due_text(w['next_review'])}"
        )
        self.session_label.config(
            text=(
                f"Correct: {w['correct']}\n"
                f"Wrong: {w['wrong']}\n"
                f"Ease: {float(w['ease']):.2f}\n"
                f"Interval: {int(w['interval_days'])} day(s)\n"
                f"Reps: {int(w['reps'])}\n"
                f"Lapses: {int(w['lapses'])}"
            )
        )
        self.status.config(text="Left/Right = navigation · Space = flip · Escape = home")
        self.card_shown_at = time.monotonic()

    def _due_text(self, due_ts: float) -> str:
        return "now" if due_ts <= time.time() else "later"

    def flip(self):
        self.revealed = not self.revealed
        self.render()

    def next_card(self):
        if not self.words:
            return
        self.index = (self.index + 1) % len(self.words)
        self.revealed = False
        self.render()

    def prev_card(self):
        if not self.words:
            return
        self.index = (self.index - 1) % len(self.words)
        self.revealed = False
        self.render()

    def refresh_session(self):
        self.words = rank_words(get_due_words(deck=self.deck_name, focus_word=self.focus_word))
        self.index = 0
        self.revealed = False
        self.render()

    def _record(self, correct: bool, semantic_score: float = 0.0, pronunciation_score: float = 0.0, user_text: str = ""):
        w = self.current()
        if not w:
            return

        latency = time.monotonic() - self.card_shown_at
        update_word(w["word"], correct, latency=latency, semantic_score=semantic_score, pronunciation_score=pronunciation_score)
        add_xp(w["level"], correct, bonus=int(semantic_score * 5 + pronunciation_score * 5))
        record_interaction(w["word"], correct, latency, semantic_score, pronunciation_score)

        classifier = classify_error(user_text or "", w["translation"])
        feedback = (
            f"{'Correct' if correct else 'Incorrect'}\n"
            f"Semantic score: {semantic_score:.2f}\n"
            f"Pronunciation score: {pronunciation_score:.2f}\n"
            f"Classifier: {classifier['label']} ({classifier['confidence']:.2f})\n"
            f"Advice: {classifier['advice']}"
        )
        self._set_ai_feedback(feedback)

    def _set_ai_feedback(self, text: str):
        self.ai_text.config(state="normal")
        self.ai_text.delete("1.0", "end")
        self.ai_text.insert("1.0", text)
        self.ai_text.config(state="disabled")

    def submit(self):
        w = self.current()
        if not w:
            return

        user = self.entry.get().strip()
        if not user:
            return

        sem = similarity(user, w["translation"])
        correct = sem >= 0.72
        self._record(correct=correct, semantic_score=sem, user_text=user)

        self.feedback.config(
            text="Correct" if correct else f"Target: {w['translation']}",
            fg="#31c48d" if correct else "#ff6b6b",
        )
        self.entry.delete(0, tk.END)
        self.root.after(650, self.next_card)

    def pronounce(self):
        w = self.current()
        if not w:
            return

        try:
            result = score_pronunciation(w["word"])
            pron = float(result["score"])
            correct = pron >= 0.70
            sem = similarity(result.get("transcript", ""), w["word"])
            self._record(correct=correct, semantic_score=sem, pronunciation_score=pron, user_text=result.get("transcript", ""))

            self.feedback.config(
                text=f"{result['feedback']} | Heard: {result.get('transcript', '')}",
                fg="#31c48d" if correct else "#ffb020",
            )
            self.root.after(800, self.next_card)
        except Exception as e:
            messagebox.showerror("Pronunciation", str(e))

    def speak_word(self):
        w = self.current()
        if w:
            speak(w["word"])

    def ai_explain(self):
        w = self.current()
        if not w:
            return

        result = classify_error(self.entry.get().strip(), w["translation"])
        self._set_ai_feedback(
            f"Target: {w['translation']}\n"
            f"Classifier: {result['label']}\n"
            f"Confidence: {result['confidence']:.2f}\n\n"
            f"{result['advice']}"
        )

    def rate(self, quality: int):
        w = self.current()
        if not w:
            return

        correct = quality >= 4
        sem = 1.0 if correct else 0.0
        self._record(correct=correct, semantic_score=sem, pronunciation_score=0.0, user_text=self.entry.get().strip())
        self.root.after(650, self.next_card)

    def open_dashboard(self):
        from ui.dashboard import DashboardUI
        DashboardUI(self.root, on_close=None)

    def go_home(self):
        self.frame.destroy()
        from ui.home import HomePage
        HomePage(self.root, controller=self.root.app_controller)