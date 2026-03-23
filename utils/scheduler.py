from utils.db import conn

def get_due_words():
    cur = conn.cursor()
    cur.execute("SELECT word, translation FROM words WHERE due <= 1")
    return cur.fetchall()