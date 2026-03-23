# data/user_words.py

import json
import os

FILE = "data/user_words.json"

def load_words():
    if not os.path.exists(FILE):
        return []
    with open(FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_words(words):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=2)

def add_word(ua, en, level="A1"):
    words = load_words()
    words.append({
        "ua": ua,
        "en": en,
        "level": level,
        "xp": 0,
        "correct": 0,
        "incorrect": 0
    })
    save_words(words)