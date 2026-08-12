"""Pure-Python TF-IDF vectorizer and cosine similarity — no numpy or
scikit-learn, per the zero-external-dependency stance. This module is
deliberately standalone and has no dependency on State/Context/Metric
so it can be unit-tested with plain strings (see experiment.md §8.1
and tests/test_tfidf_redundancy.py).
"""
import math
import re
from collections import Counter

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class TFIDFVectorizer:
    """Fit on a small corpus of documents (strings), then vectorize
    any document against that corpus's vocabulary and IDF weights.
    """

    def __init__(self, documents: list[str]):
        self.documents = documents
        tokenized = [tokenize(doc) for doc in documents]
        self.vocabulary = sorted({token for doc in tokenized for token in doc})

        doc_count = len(documents)
        doc_freq = Counter()
        for doc_tokens in tokenized:
            for token in set(doc_tokens):
                doc_freq[token] += 1

        # Standard smoothed IDF: idf(t) = ln((1 + N) / (1 + df(t))) + 1
        self.idf = {
            token: math.log((1 + doc_count) / (1 + doc_freq[token])) + 1.0
            for token in self.vocabulary
        }

    def vectorize(self, text: str) -> dict[str, float]:
        tokens = tokenize(text)
        if not tokens:
            return {}
        term_freq = Counter(tokens)
        max_freq = max(term_freq.values())
        return {
            token: (count / max_freq) * self.idf.get(token, 0.0)
            for token, count in term_freq.items()
        }


def cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    if not vec_a or not vec_b:
        return 0.0
    shared_keys = set(vec_a) & set(vec_b)
    dot = sum(vec_a[k] * vec_b[k] for k in shared_keys)
    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def pairwise_similarity(text_a: str, text_b: str) -> float:
    """Convenience function for the two-document case (e.g. unit
    tests, or scoring one new fact against one prior fact). Fits a
    vectorizer on exactly the two documents given.
    """
    vectorizer = TFIDFVectorizer([text_a, text_b])
    return cosine_similarity(vectorizer.vectorize(text_a), vectorizer.vectorize(text_b))
