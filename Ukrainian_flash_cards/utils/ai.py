from utils.db import conn
from utils.model import predict

def prioritize(words):
    cur = conn.cursor()
    ranked = []

    for w in words:
        cur.execute("SELECT correct, wrong FROM words WHERE word=?", (w[0],))
        row = cur.fetchone()

        if row:
            score = predict(row[0], row[1], 1)
        else:
            score = 0.5

        ranked.append((score, w))

    ranked.sort(reverse=True)
    return [w for _, w in ranked]