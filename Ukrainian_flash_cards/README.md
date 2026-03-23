# Ukrainian AI Trainer

An adaptive Ukrainian flashcards platform built with Python, Tkinter, SQLite, PyTorch, Whisper-based pronunciation scoring, Sentence Transformers semantic grading, and reinforcement-style review adaptation.

## Features

- CEFR-aligned vocabulary from A1 to C2
- Spaced repetition with SM-2 style scheduling
- SQLite persistence for words, progress, and review history
- XP system by CEFR level
- Semantic answer checking with Sentence Transformers
- Whisper-based pronunciation scoring
- Fine-tunable transformer error classifier for learner feedback
- Real-time difficulty adaptation using a lightweight reinforcement policy
- Analytics dashboard with mastery, accuracy, latency, and review trends
- Custom word import and management

## Stack

- Python
- Tkinter
- SQLite
- PyTorch
- faster-whisper
- Sentence Transformers
- Hugging Face Transformers
- Matplotlib

## Install

```bash
pip install -r requirements.txt