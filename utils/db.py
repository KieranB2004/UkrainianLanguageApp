import os
import sqlite3
import time
from typing import Dict, Iterable, List, Optional

DB_PATH = os.path.join("data", "app.db")
os.makedirs("data", exist_ok=True)

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.executescript(
    """
    PRAGMA journal_mode=WAL;

    CREATE TABLE IF NOT EXISTS words (
        word TEXT PRIMARY KEY,
        translation TEXT NOT NULL,
        deck TEXT NOT NULL DEFAULT 'My Words',
        level TEXT NOT NULL DEFAULT 'A1',
        correct INTEGER NOT NULL DEFAULT 0,
        wrong INTEGER NOT NULL DEFAULT 0,
        ease REAL NOT NULL DEFAULT 2.5,
        interval_days INTEGER NOT NULL DEFAULT 1,
        reps INTEGER NOT NULL DEFAULT 0,
        lapses INTEGER NOT NULL DEFAULT 0,
        next_review REAL NOT NULL DEFAULT 0,
        created_at REAL NOT NULL DEFAULT 0,
        updated_at REAL NOT NULL DEFAULT 0,
        last_seen REAL NOT NULL DEFAULT 0,
        source TEXT NOT NULL DEFAULT 'manual'
    );

    CREATE TABLE IF NOT EXISTS progress (
        level TEXT PRIMARY KEY,
        xp INTEGER NOT NULL DEFAULT 0,
        correct INTEGER NOT NULL DEFAULT 0,
        total INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS review_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT NOT NULL,
        reviewed_at REAL NOT NULL,
        correct INTEGER NOT NULL,
        latency REAL NOT NULL DEFAULT 0,
        semantic_score REAL NOT NULL DEFAULT 0,
        pronunciation_score REAL NOT NULL DEFAULT 0,
        reward REAL NOT NULL DEFAULT 0,
        FOREIGN KEY(word) REFERENCES words(word)
    );

    CREATE TABLE IF NOT EXISTS mastery (
        level TEXT PRIMARY KEY,
        seen INTEGER NOT NULL DEFAULT 0,
        mastered INTEGER NOT NULL DEFAULT 0,
        due INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS rl_state (
        word TEXT PRIMARY KEY,
        weight REAL NOT NULL DEFAULT 0,
        avg_latency REAL NOT NULL DEFAULT 0,
        avg_reward REAL NOT NULL DEFAULT 0,
        seen INTEGER NOT NULL DEFAULT 0,
        updated_at REAL NOT NULL DEFAULT 0
    );
    """
)
conn.commit()


def _now() -> float:
    return time.time()


def _infer_level(deck_or_level: str) -> str:
    s = (deck_or_level or "").strip()
    levels = ("A1", "A2", "B1", "B2", "C1", "C2")
    if s in levels:
        return s
    if s[:2] in levels:
        return s[:2]
    return "A1"


def _ensure_mastery(level: str) -> None:
    cur.execute(
        "INSERT OR IGNORE INTO mastery(level, seen, mastered, due) VALUES (?, 0, 0, 0)",
        (level,),
    )
    conn.commit()


def add_word(word: str, translation: str, deck: str = "My Words", level: str = "A1", source: str = "manual") -> None:
    word = word.strip()
    translation = translation.strip()
    deck = deck.strip() or "My Words"
    level = _infer_level(level or deck)
    now = _now()

    if not word or not translation:
        return

    cur.execute(
        """
        INSERT OR IGNORE INTO words
        (word, translation, deck, level, created_at, updated_at, last_seen, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (word, translation, deck, level, now, now, now, source),
    )
    _ensure_mastery(level)
    conn.commit()


def seed_words(records: Dict[str, List[tuple]]) -> int:
    count = 0
    for deck, items in records.items():
        level = _infer_level(deck)
        for ua, en in items:
            add_word(ua, en, deck=deck, level=level, source="seed")
            count += 1
    return count


def get_word(word: str):
    cur.execute("SELECT * FROM words WHERE word = ?", (word,))
    row = cur.fetchone()
    return dict(row) if row else None


def get_all_words() -> List[dict]:
    cur.execute("SELECT * FROM words ORDER BY deck COLLATE NOCASE, level, word COLLATE NOCASE")
    return [dict(r) for r in cur.fetchall()]


def list_decks() -> List[dict]:
    now = _now()
    cur.execute(
        """
        SELECT
            deck,
            level,
            COUNT(*) AS total,
            SUM(CASE WHEN next_review <= ? THEN 1 ELSE 0 END) AS due,
            AVG(ease) AS avg_ease
        FROM words
        GROUP BY deck, level
        ORDER BY level, deck COLLATE NOCASE
        """,
        (now,),
    )
    return [dict(r) for r in cur.fetchall()]


def get_due_words(deck: Optional[str] = None, focus_word: Optional[str] = None, limit: Optional[int] = None) -> List[dict]:
    now = _now()
    sql = "SELECT * FROM words WHERE 1=1"
    params = []

    if deck and deck != "All":
        sql += " AND deck = ?"
        params.append(deck)

    sql += " AND next_review <= ?"
    params.append(now)

    sql += " ORDER BY next_review ASC, ease ASC, wrong DESC, word COLLATE NOCASE ASC"

    if limit:
        sql += " LIMIT ?"
        params.append(limit)

    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]

    if not rows:
        cur.execute("SELECT * FROM words WHERE 1=1" + (" AND deck = ?" if deck and deck != "All" else "") + " ORDER BY ease ASC, wrong DESC, word COLLATE NOCASE ASC" + (" LIMIT ?" if limit else ""),
                    ([deck] if deck and deck != "All" else []) + ([limit] if limit else []))
        rows = [dict(r) for r in cur.fetchall()]

    if focus_word:
        for i, row in enumerate(rows):
            if row["word"] == focus_word:
                rows.insert(0, rows.pop(i))
                break

    return rows


def update_word(word: str, correct: bool, latency: float = 0.0, semantic_score: float = 0.0, pronunciation_score: float = 0.0) -> dict:
    row = get_word(word)
    if not row:
        return {}

    ease = float(row["ease"])
    interval = int(row["interval_days"])
    reps = int(row["reps"])
    lapses = int(row["lapses"])

    if correct:
        if reps == 0:
            interval = 1
        elif reps == 1:
            interval = 3
        else:
            interval = max(1, int(round(interval * ease)))
        ease = max(1.3, ease + 0.05)
        reps += 1
    else:
        interval = 1
        ease = max(1.3, ease - 0.20)
        lapses += 1
        reps = 0

    now = _now()
    next_review = now + interval * 86400

    cur.execute(
        """
        UPDATE words
        SET correct = correct + ?,
            wrong = wrong + ?,
            ease = ?,
            interval_days = ?,
            reps = ?,
            lapses = ?,
            next_review = ?,
            updated_at = ?,
            last_seen = ?
        WHERE word = ?
        """,
        (
            1 if correct else 0,
            0 if correct else 1,
            ease,
            interval,
            reps,
            lapses,
            next_review,
            now,
            now,
            word,
        ),
    )

    reward = (1.0 if correct else -1.0)
    reward += float(semantic_score) * 0.6
    reward += float(pronunciation_score) * 0.4
    reward -= min(float(latency), 12.0) / 12.0

    cur.execute(
        """
        INSERT INTO review_history(word, reviewed_at, correct, latency, semantic_score, pronunciation_score, reward)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (word, now, int(correct), float(latency), float(semantic_score), float(pronunciation_score), float(reward)),
    )

    level = row["level"]
    _ensure_mastery(level)
    cur.execute(
        """
        UPDATE mastery
        SET seen = seen + 1,
            mastered = mastered + ?,
            due = due + ?
        WHERE level = ?
        """,
        (1 if correct and reps >= 3 and interval >= 21 else 0, 1 if next_review <= now else 0, level),
    )

    conn.commit()
    return get_word(word) or {}


def add_xp(level: str, correct: bool, bonus: int = 0) -> None:
    level = _infer_level(level)
    _ensure_mastery(level)
    xp_gain = (12 if correct else 3) + int(bonus)

    cur.execute("SELECT xp, correct, total FROM progress WHERE level = ?", (level,))
    row = cur.fetchone()
    if row:
        cur.execute(
            """
            UPDATE progress
            SET xp = xp + ?,
                correct = correct + ?,
                total = total + 1
            WHERE level = ?
            """,
            (xp_gain, 1 if correct else 0, level),
        )
    else:
        cur.execute(
            """
            INSERT INTO progress(level, xp, correct, total)
            VALUES (?, ?, ?, ?)
            """,
            (level, xp_gain, 1 if correct else 0, 1),
        )

    conn.commit()


def get_progress() -> List[dict]:
    cur.execute("SELECT * FROM progress ORDER BY level")
    return [dict(r) for r in cur.fetchall()]


def get_mastery() -> List[dict]:
    cur.execute("SELECT * FROM mastery ORDER BY level")
    return [dict(r) for r in cur.fetchall()]


def get_history(days: int = 90) -> List[dict]:
    cur.execute(
        """
        SELECT reviewed_at, word, correct, latency, semantic_score, pronunciation_score, reward
        FROM review_history
        WHERE reviewed_at >= ?
        ORDER BY reviewed_at ASC
        """,
        (_now() - days * 86400,),
    )
    return [dict(r) for r in cur.fetchall()]


def get_summary() -> dict:
    now = _now()
    cur.execute(
        """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN next_review <= ? THEN 1 ELSE 0 END) AS due,
            AVG(ease) AS avg_ease,
            SUM(correct) AS total_correct,
            SUM(wrong) AS total_wrong
        FROM words
        """,
        (now,),
    )
    row = dict(cur.fetchone())
    total = int(row["total"] or 0)
    correct = int(row["total_correct"] or 0)
    wrong = int(row["total_wrong"] or 0)
    mastered = len([w for w in get_all_words() if int(w["reps"]) >= 3 and int(w["interval_days"]) >= 21])
    return {
        "total": total,
        "due": int(row["due"] or 0),
        "avg_ease": float(row["avg_ease"] or 0.0),
        "correct": correct,
        "wrong": wrong,
        "mastered": mastered,
    }


def get_weak_words(limit: int = 12) -> List[dict]:
    cur.execute(
        """
        SELECT *
        FROM words
        ORDER BY wrong DESC, ease ASC, reps ASC, next_review ASC
        LIMIT ?
        """,
        (limit,),
    )
    return [dict(r) for r in cur.fetchall()]


def import_words(records: Iterable[dict], default_deck: str = "Imported") -> int:
    count = 0
    for item in records:
        if not isinstance(item, dict):
            continue
        word = str(item.get("word") or item.get("ua") or "").strip()
        translation = str(item.get("translation") or item.get("en") or "").strip()
        deck = str(item.get("deck") or default_deck).strip()
        level = str(item.get("level") or _infer_level(deck))
        if word and translation:
            add_word(word, translation, deck=deck, level=level, source="import")
            count += 1
    return count