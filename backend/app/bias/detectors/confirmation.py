"""
Confirmation Bias Detector

Detects when the LLM's reasoning only cites evidence supporting
one side of an argument while ignoring counterevidence.

Detection method: VADER sentiment analysis on the CoT reasoning trace.
If sentiment is strongly one-sided and the trace lacks counterargument
indicators, confirmation bias is flagged.
"""

import logging
from typing import Optional

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from app.utils.text_utils import extract_sentences

logger = logging.getLogger("clearmind.detectors.confirmation")

# Initialize VADER
_analyzer = SentimentIntensityAnalyzer()

# Counterargument indicators — presence of these suggests balanced reasoning
COUNTER_INDICATORS = [
    "however", "on the other hand", "conversely", "in contrast",
    "nevertheless", "despite", "although", "while some argue",
    "critics point out", "opponents argue", "counter to this",
    "an alternative view", "some disagree", "it should be noted",
    "the opposing", "a different perspective", "but also consider",
    "not everyone agrees", "there are concerns", "drawbacks include",
]

# Pro-confirmation indicators — one-sided reasoning patterns
ONESIDED_INDICATORS = [
    "clearly shows", "proves that", "confirms that",
    "all evidence points to", "research supports",
    "studies consistently show", "there is no doubt",
    "the data confirms", "overwhelming evidence",
    "it is well established",
]


async def detect(
    query: str,
    cot_trace: str,
    answer: str,
    **kwargs,
) -> dict:
    """Detect confirmation bias in the reasoning trace.

    Args:
        query: Original user question.
        cot_trace: Chain-of-thought reasoning from the base agent.
        answer: Final answer from the base agent.

    Returns:
        Detection result dict with 'detected', 'confidence', 'evidence', 'details'.
    """
    trace_lower = cot_trace.lower()
    sentences = extract_sentences(cot_trace)

    # --- 1. Sentiment polarity analysis ---
    sentiments = [_analyzer.polarity_scores(s) for s in sentences]
    compound_scores = [s["compound"] for s in sentiments]

    if not compound_scores:
        return _no_bias()

    avg_sentiment = sum(compound_scores) / len(compound_scores)
    sentiment_variance = (
        sum((s - avg_sentiment) ** 2 for s in compound_scores) / len(compound_scores)
    )

    # Strong one-sided sentiment (all positive or all negative) with low variance
    sentiment_onesided = abs(avg_sentiment) > 0.3 and sentiment_variance < 0.15

    # --- 2. Counterargument presence check ---
    counter_count = sum(1 for ind in COUNTER_INDICATORS if ind in trace_lower)
    onesided_count = sum(1 for ind in ONESIDED_INDICATORS if ind in trace_lower)

    has_counter_evidence = counter_count >= 2
    has_onesided_language = onesided_count >= 2

    # --- 3. Combine signals ---
    confidence = 0.0
    evidence_parts = []

    if sentiment_onesided:
        confidence += 0.35
        direction = "positive" if avg_sentiment > 0 else "negative"
        evidence_parts.append(
            f"Reasoning trace has strongly {direction} one-sided sentiment "
            f"(avg compound={avg_sentiment:.2f}, variance={sentiment_variance:.3f})"
        )

    if not has_counter_evidence:
        confidence += 0.30
        evidence_parts.append(
            f"No counterarguments detected in reasoning "
            f"(found {counter_count} counter-indicators, minimum 2 expected)"
        )

    if has_onesided_language:
        confidence += 0.25
        evidence_parts.append(
            f"One-sided language patterns detected "
            f"({onesided_count} confirmation phrases found)"
        )

    # Cap at 0.95
    confidence = min(confidence, 0.95)

    detected = confidence >= 0.45

    return {
        "detected": detected,
        "confidence": round(confidence, 3),
        "evidence": " | ".join(evidence_parts) if evidence_parts else "No confirmation bias signals detected",
        "details": {
            "avg_sentiment": round(avg_sentiment, 3),
            "sentiment_variance": round(sentiment_variance, 4),
            "counter_indicators_found": counter_count,
            "onesided_indicators_found": onesided_count,
            "sentence_count": len(sentences),
        },
    }


def _no_bias() -> dict:
    """Return a clean no-bias result."""
    return {
        "detected": False,
        "confidence": 0.0,
        "evidence": "Insufficient reasoning trace for confirmation bias analysis",
        "details": {},
    }
