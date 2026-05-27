"""
ClearMind Semantic Similarity Module

Loads the all-mpnet-base-v2 sentence embedding model and provides
cosine similarity computation between text pairs.
Used to compare base answers vs debiased answers — high divergence
indicates the bias correction made a meaningful change.
"""

import logging
from typing import Optional
from functools import lru_cache

import numpy as np

logger = logging.getLogger("clearmind.similarity")

# Lazy-loaded model instance
_model = None


def _get_model():
    """Lazy-load the sentence transformer model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading sentence-transformers model: all-mpnet-base-v2...")
            _model = SentenceTransformer("all-mpnet-base-v2")
            logger.info("✅ Sentence transformer model loaded")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load sentence-transformers model: {e}")
            _model = None
    return _model


def compute_similarity(text_a: str, text_b: str) -> Optional[float]:
    """Compute cosine similarity between two text strings using sentence embeddings.

    Args:
        text_a: First text (e.g., base LLM answer).
        text_b: Second text (e.g., debiased answer).

    Returns:
        Cosine similarity score (0.0 to 1.0), or None if model not available.
    """
    model = _get_model()
    if model is None:
        return None

    try:
        embeddings = model.encode([text_a, text_b], normalize_embeddings=True)
        similarity = float(np.dot(embeddings[0], embeddings[1]))
        # Clamp to [0, 1] range
        similarity = max(0.0, min(1.0, similarity))
        logger.debug(f"Semantic similarity: {similarity:.4f}")
        return round(similarity, 4)
    except Exception as e:
        logger.error(f"Similarity computation failed: {e}")
        return None


def compute_batch_similarity(
    texts_a: list[str],
    texts_b: list[str],
) -> list[Optional[float]]:
    """Compute cosine similarity for multiple text pairs efficiently.

    Args:
        texts_a: List of first texts.
        texts_b: List of second texts (must be same length as texts_a).

    Returns:
        List of cosine similarity scores.
    """
    assert len(texts_a) == len(texts_b), "Input lists must have equal length"

    model = _get_model()
    if model is None:
        return [None] * len(texts_a)

    try:
        embeddings_a = model.encode(texts_a, normalize_embeddings=True)
        embeddings_b = model.encode(texts_b, normalize_embeddings=True)

        similarities = []
        for ea, eb in zip(embeddings_a, embeddings_b):
            sim = float(np.dot(ea, eb))
            sim = max(0.0, min(1.0, sim))
            similarities.append(round(sim, 4))

        return similarities
    except Exception as e:
        logger.error(f"Batch similarity computation failed: {e}")
        return [None] * len(texts_a)
