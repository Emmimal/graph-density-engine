"""Phase 0: TF-IDF adversarial validation set, per experiment.md §8.1.
Documents the known limitation: lexical overlap, not semantic
contradiction (occurred vs. avoided).
"""
from relationship_density.metrics.tfidf import pairwise_similarity


def test_near_duplicate_phrasing_scores_high():
    sim = pairwise_similarity(
        "Database timeout occurred", "Database timeout happened"
    )
    assert sim > 0.4, f"expected high similarity for near-duplicate phrasing, got {sim}"


def test_negation_scores_high_lexically_despite_opposite_meaning():
    """Documented limitation: TF-IDF cannot distinguish this from a
    true near-duplicate. This test exists to make that limitation
    explicit and regression-tested, not to fix it."""
    sim = pairwise_similarity(
        "Database timeout occurred", "Database timeout was avoided"
    )
    assert sim > 0.3, (
        f"expected TF-IDF to still score this pair as lexically similar "
        f"despite opposite meaning (documented limitation), got {sim}"
    )


def test_related_but_distinct_topic_scores_medium():
    sim_related = pairwise_similarity("Database timeout occurred", "Redis cache timeout")
    sim_unrelated = pairwise_similarity("Database timeout occurred", "The API returned 500")
    assert sim_related > sim_unrelated, (
        f"expected the shared-vocabulary pair ({sim_related}) to score higher "
        f"than the unrelated pair ({sim_unrelated})"
    )


def test_unrelated_topic_scores_low():
    sim = pairwise_similarity("Database timeout occurred", "The API returned 500")
    assert sim < 0.3, f"expected low similarity for unrelated facts, got {sim}"


def test_identical_text_scores_maximal():
    sim = pairwise_similarity("Database timeout occurred", "Database timeout occurred")
    assert sim > 0.99, f"expected near-1.0 similarity for identical text, got {sim}"
