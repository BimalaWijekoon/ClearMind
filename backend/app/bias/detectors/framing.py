"""
Framing Effect Detector

Detects when the same question framed positively vs negatively
produces different answers from the LLM.

Detection method: Generates positive and negative frame paraphrases.
Compares semantic similarity of base answers.
Similarity < 0.75 indicates framing effect.
"""

import logging
from app.utils.paraphraser import generate_paraphrase
from app.embeddings.similarity import compute_similarity

logger = logging.getLogger("clearmind.detectors.framing")

FRAME_INDICATORS = [
    "risk", "danger", "loss", "failure", "mortality", "death",
    "benefit", "gain", "success", "survival", "save", "improve",
    "threat", "opportunity", "cost", "reward", "harm", "protect",
]


async def detect(query: str, cot_trace: str, answer: str, base_agent_fn=None, **kwargs) -> dict:
    """Detect framing effect bias."""
    query_lower = query.lower()
    has_frame_words = sum(1 for w in FRAME_INDICATORS if w in query_lower)

    if has_frame_words < 1 and base_agent_fn is None:
        return {"detected": False, "confidence": 0.0, "evidence": "No framing language detected", "details": {}}

    if base_agent_fn is not None:
        try:
            pos_query = await generate_paraphrase(query, mode="positive")
            neg_query = await generate_paraphrase(query, mode="negative")

            pos_result = await base_agent_fn(pos_query)
            neg_result = await base_agent_fn(neg_query)

            pos_answer = pos_result.get("answer", "")
            neg_answer = neg_result.get("answer", "")

            if pos_answer and neg_answer:
                similarity = compute_similarity(pos_answer, neg_answer)
                if similarity is not None:
                    confidence = 0.0
                    evidence_parts = []

                    if similarity < 0.50:
                        confidence = 0.85
                        evidence_parts.append(f"Positive vs negative framing produces very different answers (similarity: {similarity:.3f})")
                    elif similarity < 0.70:
                        confidence = 0.60
                        evidence_parts.append(f"Moderate framing sensitivity (similarity: {similarity:.3f})")
                    elif similarity < 0.80:
                        confidence = 0.35
                        evidence_parts.append(f"Slight framing sensitivity (similarity: {similarity:.3f})")

                    detected = confidence >= 0.45
                    return {
                        "detected": detected,
                        "confidence": round(confidence, 3),
                        "evidence": " | ".join(evidence_parts) if evidence_parts else "No framing effect",
                        "details": {
                            "positive_query": pos_query,
                            "negative_query": neg_query,
                            "similarity": similarity,
                            "method": "full_comparison",
                        },
                    }
        except Exception as e:
            logger.warning(f"Full framing detection failed: {e}")

    # Lightweight: just check for framing language presence
    confidence = min(0.15 * has_frame_words, 0.40)
    return {
        "detected": False,
        "confidence": round(confidence, 3),
        "evidence": f"Framing language present ({has_frame_words} indicators) but no comparison available",
        "details": {"frame_word_count": has_frame_words, "method": "lightweight"},
    }
