import json
import os
from datetime import datetime
from utils.model import predict

FILE = "data/stats.json"

def load():
    if not os.path.exists(FILE):
        return {}
    return json.load(open(FILE))

def save(data):
    json.dump(data, open(FILE, "w"), indent=2)

def update(word, correct):
    data = load()

    if word not in data:
        data[word] = {
            "correct": 0,
            "wrong": 0,
            "ef": 2.5,
            "interval": 1,
            "due": 0
        }

    if correct:
        data[word]["correct"] += 1
        data[word]["interval"] *= data[word]["ef"]
    else:
        data[word]["wrong"] += 1
        data[word]["interval"] = 1

    data[word]["due"] = data[word]["interval"]
    save(data)

def difficulty(word):
    d = load().get(word, {"correct":0,"wrong":0})
    return predict(d["correct"], d["wrong"], 1)