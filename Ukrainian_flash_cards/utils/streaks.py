import sqlite3
import datetime

conn = sqlite3.connect("data/app.db")
cur = conn.cursor()

def get_streak():
    cur.execute("SELECT date FROM sessions ORDER BY date DESC")
    dates = [row[0] for row in cur.fetchall()]

    streak = 0
    today = datetime.date.today()

    for i, d in enumerate(dates):
        if datetime.date.fromisoformat(d) == today - datetime.timedelta(days=i):
            streak += 1
        else:
            break

    return streak