import os
import sqlite3
import time
from typing import List, Dict

DB_PATH = os.path.join("data", "app.db")
os.makedirs("data", exist_ok=True)

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.executescript(
    """
    CREATE TABLE IF NOT EXISTS rl_state (
        word TEXT PRIMARY KEY,
        weight REAL NOT NULL DEFAULT 0,
        avg_latency REAL NOT NULL DEFAULT 0,
        avg_reward REAL NOT NULL DEFAULT 0,
        seen INTEGER NOT NULL DEFAULT 0,
        updated_at REAL NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS interaction_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT NOT NULL,
        correct INTEGER NOT NULL,
        latency REAL NOT NULL DEFAULT 0,
        semantic_score REAL NOT NULL DEFAULT 0,
        pronunciation_score REAL NOT NULL DEFAULT 0,
        reward REAL NOT NULL DEFAULT 0,
        created_at REAL NOT NULL DEFAULT 0
    );
    """
)
conn.commit()


def _now() -> float:
    return time.time()


def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def get_state(word: str) -> Dict:
    cur.execute("SELECT * FROM rl_state WHERE word = ?", (word,))
    row = cur.fetchone()
    return dict(row) if row else {"word": word, "weight": 0.0, "avg_latency": 0.0, "avg_reward": 0.0, "seen": 0, "updated_at": 0.0}


def record_interaction(
    word: str,
    correct: bool,
    latency: float,
    semantic_score: float = 0.0,
    pronunciation_score: float = 0.0,
) -> Dict:
    state = get_state(word)
    reward = (1.0 if correct else -1.0)
    reward += float(semantic_score) * 0.7
    reward += float(pronunciation_score) * 0.5
    reward -= min(float(latency), 12.0) / 12.0

    new_weight = _clip(float(state["weight"]) + 0.15 * reward, -3.0, 3.0)
    new_avg_latency = (float(state["avg_latency"]) * float(state["seen"]) + float(latency)) / (float(state["seen"]) + 1.0)
    new_avg_reward = (float(state["avg_reward"]) * float(state["seen"]) + float(reward)) / (float(state["seen"]) + 1.0)

    cur.execute(
        """
        INSERT INTO rl_state(word, weight, avg_latency, avg_reward, seen, updated_at)
        VALUES (?, ?, ?, ?, 1, ?)
        ON CONFLICT(word) DO UPDATE SET
            weight = excluded.weight,
            avg_latency = excluded.avg_latency,
            avg_reward = excluded.avg_reward,
            seen = rl_state.seen + 1,
            updated_at = excluded.updated_at
        """,
        (word, new_weight, new_avg_latency, new_avg_reward, _now()),
    )

    cur.execute(
        """
        INSERT INTO interaction_log(word, correct, latency, semantic_score, pronunciation_score, reward, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (word, int(correct), float(latency), float(semantic_score), float(pronunciation_score), float(reward), _now()),
    )

    conn.commit()
    return get_state(word)


def priority_score(word_row: dict) -> float:
    """
    Higher score = review earlier.
    """
    state = get_state(word_row["word"])
    ease = float(word_row.get("ease", 2.5))
    wrong = int(word_row.get("wrong", 0))
    correct = int(word_row.get("correct", 0))
    reps = int(word_row.get("reps", 0))
    next_review = float(word_row.get("next_review", 0))
    now = _now()

    overdue = max(0.0, now - next_review) / 86400.0
    base = 1.0 + wrong * 0.35 - correct * 0.08 + max(0, 3 - reps) * 0.25 + max(0, 2.6 - ease)
    return base * (1.0 + max(0.0, float(state["weight"]))) + overdue


def rank_words(words: List[dict]) -> List[dict]:
    return sorted(words, key=priority_score, reverse=True)


def top_weak_words(limit: int = 10) -> List[dict]:
    cur.execute(
        """
        SELECT w.*
        FROM words w
        LEFT JOIN rl_state r ON r.word = w.word
        ORDER BY w.wrong DESC, w.ease ASC, COALESCE(r.weight, 0) DESC, w.next_review ASC
        LIMIT ?
        """,
        (limit,),
    )
    return [dict(r) for r in cur.fetchall()]


def interaction_history(days: int = 30) -> List[dict]:
    cur.execute(
        """
        SELECT *
        FROM interaction_log
        WHERE created_at >= ?
        ORDER BY created_at ASC
        """,
        (_now() - days * 86400,),
    )
    return [dict(r) for r in cur.fetchall()]