# tools/kb_search.py
import json
from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

KB: List[Dict] = []
_vectorizer = None
_tfidf_matrix = None

def _make_text(item: Dict) -> str:
    # Join title, symptoms, and content into a single searchable string
    return " ".join([item.get("title",""), " ".join(item.get("symptoms",[])), item.get("content","")])

def load_kb(path: str) -> List[Dict]:
    """
    Load the KB and build a TF-IDF matrix for fast semantic-ish search.
    """
    global KB, _vectorizer, _tfidf_matrix
    with open(path, 'r', encoding='utf-8') as f:
        KB = json.load(f)

    corpus = [_make_text(it) for it in KB]
    _vectorizer = TfidfVectorizer(stop_words='english')
    if corpus:
        _tfidf_matrix = _vectorizer.fit_transform(corpus)
    else:
        _tfidf_matrix = None
    return KB

def search_kb_topk(description: str, topk: int = 3) -> List[Dict]:
    """
    Return top-k KB entries ordered by cosine similarity between TF-IDF vectors.
    Each returned dict contains an added 'match_score' field (float between 0 and 1).
    """
    global KB, _vectorizer, _tfidf_matrix
    if not KB:
        return []

    # Fallback: if the TF-IDF matrix isn't built, do keyword overlap scoring
    if _tfidf_matrix is None:
        desc = description.lower()
        scored = []
        for it in KB:
            text = _make_text(it).lower()
            score = 1.0 if any(tok in text for tok in desc.split()) else 0.0
            scored.append((it, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        hits = []
        for it, sc in scored[:topk]:
            hit = dict(it)
            hit['match_score'] = round(float(sc), 3)
            hits.append(hit)
        return hits

    q = _vectorizer.transform([description])
    sims = cosine_similarity(q, _tfidf_matrix)[0]  # array of similarities
    idxs = sims.argsort()[::-1][:topk]
    hits = []
    for idx in idxs:
        it = KB[idx].copy()
        it['match_score'] = float(round(float(sims[idx]), 3))
        hits.append(it)
    return hits
