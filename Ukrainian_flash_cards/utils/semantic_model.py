from functools import lru_cache
from difflib import SequenceMatcher
import os
import re

from sentence_transformers import SentenceTransformer, util

MODEL_NAME = os.getenv("SEMANTIC_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")


def normalize(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


@lru_cache(maxsize=1)
def get_model():
    return SentenceTransformer(MODEL_NAME)


def similarity(a: str, b: str) -> float:
    a_n = normalize(a)
    b_n = normalize(b)

    if not a_n or not b_n:
        return 0.0

    lexical = SequenceMatcher(None, a_n, b_n).ratio()
    try:
        emb = get_model()
        sem = util.cos_sim(emb.encode(a_n, convert_to_tensor=True), emb.encode(b_n, convert_to_tensor=True)).item()
        sem = max(0.0, min(1.0, (sem + 1.0) / 2.0))
    except Exception:
        sem = lexical

    return max(0.0, min(1.0, 0.55 * lexical + 0.45 * sem))


def is_correct(user_text: str, target_text: str, threshold: float = 0.72) -> bool:
    return similarity(user_text, target_text) >= threshold