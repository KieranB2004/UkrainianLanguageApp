import sqlite3

conn = sqlite3.connect("data/app.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS progress(
    level TEXT,
    xp INTEGER DEFAULT 0,
    correct INTEGER DEFAULT 0,
    total INTEGER DEFAULT 0,
    PRIMARY KEY(level)
)
""")

conn.commit()

def add_xp(level, correct):
    xp_gain = 10 if correct else 2

    cur.execute("SELECT xp, correct, total FROM progress WHERE level=?", (level,))
    row = cur.fetchone()

    if row:
        xp, c, t = row
        cur.execute("""
        UPDATE progress SET xp=?, correct=?, total=?
        WHERE level=?
        """, (xp + xp_gain, c + (1 if correct else 0), t + 1, level))
    else:
        cur.execute("""
        INSERT INTO progress VALUES (?,?,?,?)
        """, (level, xp_gain, 1 if correct else 0, 1))

    conn.commit()

def get_progress():
    cur.execute("SELECT * FROM progress")
    return cur.fetchall()