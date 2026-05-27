"""
Availability Heuristic Detector

Detects when the LLM overweights dramatic or frequently seen examples
from training data, leading to a lack of example diversity in reasoning.

Detection method: TF-IDF on example phrases in the CoT trace.
If top terms account for >60% of example weight, the reasoning
shows low diversity — a signal of availability bias.
"""

import logging
import re
from typing import Optional

from sklearn.feature_extraction.text import TfidfVectorizer

from app.utils.text_utils import extract_sentences

logger = logging.getLogger("clearmind.detectors.availability")

# Phrases that introduce examples in reasoning
EXAMPLE_MARKERS = [
    "for example", "for instance", "such as", "like",
    "consider the case", "take the example", "e.g.",
    "a notable example", "one example", "another example",
    "similar to", "reminiscent of", "comparable to",
]


async def detect(
    query: str,
    cot_trace: str,
    answer: str,
    **kwargs,
) -> dict:
    """Detect availability heuristic in reasoning.

    Checks if the reasoning cites only one type of example repeatedly
    using TF-IDF to measure example diversity.

    Args:
        query: Original user question.
        cot_trace: Chain-of-thought reasoning.
        answer: Final answer.

    Returns:
        Detection result dict.
    """
    trace_lower = cot_trace.lower()
    sentences = extract_sentences(cot_trace)

    if len(sentences) < 3:
        return _no_bias("Too few sentences for availability analysis")

    # --- 1. Extract example-containing sentences ---
    example_sentences = []
    for sent in sentences:
        sent_lower = sent.lower()
        if any(marker in sent_lower for marker in EXAMPLE_MARKERS):
            example_sentences.append(sent)

    if len(example_sentences) < 2:
        return _no_bias("Too few examples in reasoning to assess diversity")

    # --- 2. TF-IDF diversity analysis ---
    try:
        vectorizer = TfidfVectorizer(
            max_features=50,
            stop_words="english",
            min_df=1,
            max_df=0.95,
        )
        tfidf_matrix = vectorizer.fit_transform(example_sentences)
        feature_names = vectorizer.get_feature_names_out()

        # Get average TF-IDF scores across example sentences
        avg_scores = tfidf_matrix.mean(axis=0).A1
        sorted_indices = avg_scores.argsort()[::-1]

        # Check concentration: do top-3 terms dominate?
        total_score = avg_scores.sum()
        if total_score == 0:
            return _no_bias("TF-IDF analysis yielded zero total score")

        top_3_score = sum(avg_scores[sorted_indices[:3]])
        concentration_ratio = top_3_score / total_score

        top_terms = [feature_names[i] for i in sorted_indices[:5]]

    except Exception as e:
        logger.warning(f"TF-IDF analysis failed: {e}")
        return _no_bias(f"TF-IDF analysis failed: {str(e)}")

    # --- 3. Check for repeated specific examples ---
    # Count unique named entities / proper nouns in examples
    unique_subjects = set()
    for sent in example_sentences:
        # Extract capitalized phrases (likely proper nouns / specific examples)
        proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', sent)
        unique_subjects.update(proper_nouns)

    subject_diversity = len(unique_subjects) / len(example_sentences) if example_sentences else 1.0

    # --- 4. Combine signals ---
    confidence = 0.0
    evidence_parts = []

    if concentration_ratio > 0.60:
        confidence += 0.40
        evidence_parts.append(
            f"Top-3 terms account for {concentration_ratio:.0%} of TF-IDF weight "
            f"(threshold: 60%): {top_terms[:3]}"
        )
    elif concentration_ratio > 0.45:
        confidence += 0.20
        evidence_parts.append(
            f"Moderate term concentration: {concentration_ratio:.0%} in top-3 terms"
        )

    if subject_diversity < 0.5:
        confidence += 0.30
        evidence_parts.append(
            f"Low example diversity: {len(unique_subjects)} unique subjects "
            f"across {len(example_sentences)} examples (ratio: {subject_diversity:.2f})"
        )

    if len(example_sentences) >= 3 and len(set(
        s.lower()[:30] for s in example_sentences
    )) < len(example_sentences) * 0.5:
        confidence += 0.20
        evidence_parts.append("Repetitive example patterns detected")

    confidence = min(confidence, 0.95)
    detected = confidence >= 0.45

    return {
        "detected": detected,
        "confidence": round(confidence, 3),
        "evidence": " | ".join(evidence_parts) if evidence_parts else "Examples show adequate diversity",
        "details": {
            "example_count": len(example_sentences),
            "concentration_ratio": round(concentration_ratio, 3),
            "subject_diversity": round(subject_diversity, 3),
            "top_terms": top_terms[:5],
            "unique_subjects": list(unique_subjects)[:10],
        },
    }


def _no_bias(reason: str = "") -> dict:
    return {
        "detected": False,
        "confidence": 0.0,
        "evidence": reason or "No availability heuristic detected",
        "details": {},
    }
