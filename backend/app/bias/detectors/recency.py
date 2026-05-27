"""
Recency Bias Detector

Detects when the LLM overweights recent events relative to their
actual importance in historical context.

Detection method: Extracts date references from the CoT using regex
and spaCy DATE entities. If >70% of cited dates are within the last
5 years on a question involving historical context, flags recency bias.
"""

import logging
from app.utils.text_utils import detect_temporal_references

logger = logging.getLogger("clearmind.detectors.recency")

HISTORICAL_INDICATORS = [
    "history", "historical", "over time", "throughout",
    "evolution of", "development of", "origins",
    "traditionally", "in the past", "decades",
    "century", "centuries", "ancient", "medieval",
    "since", "progression", "timeline",
]


async def detect(query: str, cot_trace: str, answer: str, **kwargs) -> dict:
    """Detect recency bias in reasoning."""
    query_lower = query.lower()
    is_historical = any(ind in query_lower for ind in HISTORICAL_INDICATORS)

    temporal = detect_temporal_references(cot_trace)

    if not temporal["years_found"]:
        return {"detected": False, "confidence": 0.0, "evidence": "No temporal references found", "details": temporal}

    confidence = 0.0
    evidence_parts = []

    if temporal["recency_ratio"] > 0.70 and is_historical:
        confidence += 0.50
        evidence_parts.append(
            f"{temporal['recency_ratio']:.0%} of year references are within last 5 years "
            f"on a historical topic ({temporal['recent_count']} recent, "
            f"{temporal['historical_count']} historical)"
        )
    elif temporal["recency_ratio"] > 0.70:
        confidence += 0.25
        evidence_parts.append(f"High recency ratio ({temporal['recency_ratio']:.0%}) in year references")

    if is_historical and temporal["historical_count"] == 0 and temporal["recent_count"] >= 2:
        confidence += 0.30
        evidence_parts.append("Historical question but zero pre-2021 year citations")

    confidence = min(confidence, 0.95)
    detected = confidence >= 0.45

    return {
        "detected": detected,
        "confidence": round(confidence, 3),
        "evidence": " | ".join(evidence_parts) if evidence_parts else "No recency bias detected",
        "details": {**temporal, "is_historical_query": is_historical},
    }
