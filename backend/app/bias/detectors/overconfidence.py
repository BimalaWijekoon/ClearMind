"""
Overconfidence Bias Detector

Detects when the LLM expresses certainty on uncertain or contested topics.

Detection method: Parses hedging language frequency. Topics known to be
contested (from a curated list) trigger overconfidence check if the model
uses absolute language ("definitely", "always", "100%", etc.).
"""

import logging
from app.utils.text_utils import (
    count_hedging_words,
    is_contested_topic,
    ABSOLUTE_WORDS,
)

logger = logging.getLogger("clearmind.detectors.overconfidence")


async def detect(query: str, cot_trace: str, answer: str, **kwargs) -> dict:
    """Detect overconfidence bias."""
    combined = f"{cot_trace} {answer}"
    hedging_stats = count_hedging_words(combined)
    contested = is_contested_topic(query)

    confidence = 0.0
    evidence_parts = []

    # High certainty language
    if hedging_stats["certainty_score"] > 0.75:
        confidence += 0.35
        evidence_parts.append(
            f"High certainty language (score: {hedging_stats['certainty_score']:.2f}, "
            f"{hedging_stats['absolute_count']} absolute terms)"
        )

    # Contested topic with high certainty
    if contested and hedging_stats["certainty_score"] > 0.50:
        confidence += 0.35
        evidence_parts.append("Contested topic discussed with high certainty")
    elif contested:
        confidence += 0.15
        evidence_parts.append("Topic is contested")

    # No hedging at all on any topic
    if hedging_stats["hedging_count"] == 0 and hedging_stats["absolute_count"] >= 2:
        confidence += 0.20
        evidence_parts.append("Zero hedging language with multiple absolute claims")

    confidence = min(confidence, 0.95)
    detected = confidence >= 0.45

    return {
        "detected": detected,
        "confidence": round(confidence, 3),
        "evidence": " | ".join(evidence_parts) if evidence_parts else "No overconfidence detected",
        "details": {
            "hedging_stats": hedging_stats,
            "is_contested_topic": contested,
        },
    }
