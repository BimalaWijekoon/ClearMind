"""
Bandwagon Effect Detector

Detects when the LLM defers to majority opinion or popular belief
over empirical evidence.

Detection method: Pattern match for consensus phrases like "most people",
"everyone knows", "widely believed" in reasoning trace when the question
is about empirical or factual claims.
"""

import logging
from app.utils.text_utils import detect_consensus_language

logger = logging.getLogger("clearmind.detectors.bandwagon")

EMPIRICAL_INDICATORS = [
    "evidence", "study", "studies", "research", "data",
    "statistics", "experiment", "finding", "findings",
    "scientific", "measured", "observed", "tested",
    "survey", "analysis", "empirical", "peer-reviewed",
]


async def detect(query: str, cot_trace: str, answer: str, **kwargs) -> dict:
    """Detect bandwagon effect in reasoning."""
    combined_lower = f"{cot_trace} {answer}".lower()
    consensus_found = detect_consensus_language(cot_trace + " " + answer)

    # Check if the question is empirical in nature
    query_lower = query.lower()
    is_empirical = any(ind in query_lower for ind in EMPIRICAL_INDICATORS)

    # Check for evidence language in the reasoning
    has_evidence_language = any(ind in combined_lower for ind in EMPIRICAL_INDICATORS)

    confidence = 0.0
    evidence_parts = []

    if len(consensus_found) >= 3:
        confidence += 0.50
        evidence_parts.append(f"Multiple consensus phrases found: {consensus_found[:5]}")
    elif len(consensus_found) >= 1:
        confidence += 0.25
        evidence_parts.append(f"Consensus phrases detected: {consensus_found}")

    # Bandwagon on empirical question without citing evidence
    if consensus_found and is_empirical and not has_evidence_language:
        confidence += 0.30
        evidence_parts.append("Appeals to popularity on empirical question without citing evidence")

    # Consensus language without specific citations
    if consensus_found and not has_evidence_language:
        confidence += 0.15
        evidence_parts.append("Consensus claims without supporting evidence")

    confidence = min(confidence, 0.95)
    detected = confidence >= 0.45

    return {
        "detected": detected,
        "confidence": round(confidence, 3),
        "evidence": " | ".join(evidence_parts) if evidence_parts else "No bandwagon effect detected",
        "details": {
            "consensus_phrases": consensus_found,
            "is_empirical_query": is_empirical,
            "has_evidence_language": has_evidence_language,
        },
    }
