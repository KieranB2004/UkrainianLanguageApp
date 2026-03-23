import tkinter as tk
from utils.config import CARD_RATIO

def apply_flashcard_resize(frame, card_label):
    w = frame.winfo_width()
    h = frame.winfo_height()

    if w < 50 or h < 50:
        return

    card_w = int(w * 0.8)
    card_h = int(card_w * CARD_RATIO)

    if card_h > int(h * 0.5):
        card_h = int(h * 0.5)
        card_w = int(card_h / CARD_RATIO)

    font_size = max(16, int(card_h * 0.2))

    card_label.config(
        font=("Segoe UI", font_size, "bold"),
        wraplength=int(card_w * 0.9)
    )