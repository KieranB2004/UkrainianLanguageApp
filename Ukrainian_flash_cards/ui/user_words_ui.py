import tkinter as tk
from data.user_words import load_words, save_words, get_due_words, update_word
import pyttsx3

engine = pyttsx3.init()

class UserWordsPage(tk.Frame):
    def __init__(self, parent, go_home):
        super().__init__(parent, bg="black")

        self.words = load_words()
        self.index = 0
        self.show_en = False
        self.go_home = go_home

        top = tk.Frame(self, bg="black")
        top.pack(fill="x")

        tk.Button(top, text="Home", command=go_home).pack(side="left")
        tk.Button(top, text="+ Add", command=self.add_popup).pack(side="right")

        tk.Button(top, text="🔊", command=self.speak).pack(side="right")

        self.card = tk.Label(self, fg="white", bg="#111111",
                             font=("Segoe UI", 28))
        self.card.pack(expand=True, fill="both", padx=40, pady=40)

        controls = tk.Frame(self, bg="black")
        controls.pack()

        tk.Button(controls, text="Again", command=lambda: self.rate(2)).pack(side="left")
        tk.Button(controls, text="Good", command=lambda: self.rate(4)).pack(side="left")
        tk.Button(controls, text="Easy", command=lambda: self.rate(5)).pack(side="left")

        self.bind_all("<space>", lambda e: self.flip())

        self.due_words = get_due_words(self.words)
        self.render()

    def render(self):
        if not self.due_words:
            self.card.config(text="No words due")
            return

        w = self.due_words[self.index]
        text = w["ua"] if not self.show_en else w["en"]
        self.card.config(text=text)

    def flip(self):
        self.show_en = not self.show_en
        self.render()

    def rate(self, q):
        word = self.due_words[self.index]
        update_word(word, q)
        save_words(self.words)

        self.index = (self.index + 1) % len(self.due_words)
        self.show_en = False
        self.render()

    def speak(self):
        if not self.due_words:
            return
        engine.say(self.due_words[self.index]["ua"])
        engine.runAndWait()

    def add_popup(self):
        top = tk.Toplevel(self)

        ua = tk.Entry(top)
        en = tk.Entry(top)
        
        ua.pack()
        en.pack()

        def save():
            self.words.append({
                "ua": ua.get(),
                "en": en.get(),
                "ease": 2.5,
                "interval": 1,
                "due": 0
            })
            save_words(self.words)
            top.destroy()

        tk.Button(top, text="Save", command=save).pack()
