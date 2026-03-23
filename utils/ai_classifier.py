from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("all-MiniLM-L6-v2")

# anchor words per level
anchors = {
    "A1": ["hello", "water", "food"],
    "A2": ["travel", "daily", "city"],
    "B1": ["emotion", "communication"],
    "B2": ["technology", "society"],
    "C1": ["analysis", "theory"],
    "C2": ["ambiguity", "debate"]
}

anchor_embeddings = {
    k: model.encode(v, convert_to_tensor=True)
    for k, v in anchors.items()
}

def classify(word):
    emb = model.encode(word, convert_to_tensor=True)

    best = "A1"
    best_score = 0

    for level, anchor_emb in anchor_embeddings.items():
        score = util.cos_sim(emb, anchor_emb).mean().item()
        if score > best_score:
            best_score = score
            best = level

    return best