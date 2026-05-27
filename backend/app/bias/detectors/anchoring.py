"""
Anchoring Bias Detector

Detects when the LLM over-relies on the first number or name mentioned
in the prompt, producing answers that are derivative of those specific values
even when they are contextually irrelevant.

Detection method: spaCy NER extracts CARDINAL/MONEY/QUANTITY entities from
the input question, then checks if the answer contains or is heavily
influenced by those exact numerical anchors.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger("clearmind.detectors.anchoring")

# Lazy-loaded spaCy model
_nlp = None


def _get_nlp():
    """Lazy-load spaCy English model."""
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_sm")
            logger.info("✅ spaCy model loaded for anchoring detector")
        except Exception as e:
            logger.warning(f"⚠️ spaCy not available for anchoring detection: {e}")
    return _nlp


# Entity types that represent numerical anchors
ANCHOR_ENTITY_TYPES = {"CARDINAL", "MONEY", "QUANTITY", "PERCENT", "ORDINAL"}


async def detect(
    query: str,
    cot_trace: str,
    answer: str,
    **kwargs,
) -> dict:
    """Detect anchoring bias in the LLM output.

    Extracts numerical entities from the input query using spaCy NER,
    then checks if those same values appear in the answer or reasoning.

    Args:
        query: Original user question.
        cot_trace: Chain-of-thought reasoning from the base agent.
        answer: Final answer from the base agent.

    Returns:
        Detection result dict.
    """
    nlp = _get_nlp()

    if nlp is None:
        # Fallback to regex-based number extraction
        return await _detect_regex_fallback(query, cot_trace, answer)

    # Extract numerical entities from the query
    query_doc = nlp(query)
    anchor_entities = [
        ent for ent in query_doc.ents
        if ent.label_ in ANCHOR_ENTITY_TYPES
    ]

    if not anchor_entities:
        return _no_bias("No numerical anchors found in input query")

    # Extract anchor values
    anchor_values = []
    for ent in anchor_entities:
        # Normalize: remove $, commas, %, etc.
        value = re.sub(r'[,$%]', '', ent.text).strip()
        if value:
            anchor_values.append({
                "text": ent.text,
                "normalized": value,
                "label": ent.label_,
            })

    if not anchor_values:
        return _no_bias("No valid numerical anchors extracted")

    # Check if anchors appear in the answer or CoT
    answer_lower = answer.lower()
    trace_lower = cot_trace.lower()

    anchors_in_answer = []
    anchors_in_trace = []

    for anchor in anchor_values:
        norm = anchor["normalized"].lower()
        text = anchor["text"].lower()

        if norm in answer_lower or text in answer_lower:
            anchors_in_answer.append(anchor["text"])
        if norm in trace_lower or text in trace_lower:
            anchors_in_trace.append(anchor["text"])

    # --- Compute confidence ---
    confidence = 0.0
    evidence_parts = []

    # High signal: anchor value appears directly in answer
    if anchors_in_answer:
        anchor_ratio = len(anchors_in_answer) / len(anchor_values)
        confidence += 0.45 * anchor_ratio
        evidence_parts.append(
            f"Anchor values {anchors_in_answer} from query appear directly in the answer"
        )

    # Medium signal: anchor dominates the reasoning
    if anchors_in_trace:
        # Count occurrences in trace
        total_mentions = sum(
            trace_lower.count(a["normalized"].lower()) +
            trace_lower.count(a["text"].lower())
            for a in anchor_values
        )
        if total_mentions >= 3:
            confidence += 0.30
            evidence_parts.append(
                f"Anchor values mentioned {total_mentions} times in reasoning trace"
            )
        elif total_mentions >= 1:
            confidence += 0.15
            evidence_parts.append(
                f"Anchor values referenced {total_mentions} time(s) in reasoning"
            )

    # Check if answer contains numbers very close to anchor (derivative)
    answer_numbers = re.findall(r'\b\d+(?:\.\d+)?\b', answer)
    for anchor in anchor_values:
        try:
            anchor_num = float(re.sub(r'[^\d.]', '', anchor["normalized"]))
            for ans_num_str in answer_numbers:
                ans_num = float(ans_num_str)
                if ans_num != 0 and anchor_num != 0:
                    ratio = ans_num / anchor_num
                    if 0.8 <= ratio <= 1.2 and ans_num_str not in anchor["text"]:
                        confidence += 0.20
                        evidence_parts.append(
                            f"Answer number {ans_num_str} is derivative of "
                            f"anchor {anchor['text']} (ratio: {ratio:.2f})"
                        )
                        break
        except (ValueError, ZeroDivisionError):
            continue

    confidence = min(confidence, 0.95)
    detected = confidence >= 0.40

    return {
        "detected": detected,
        "confidence": round(confidence, 3),
        "evidence": " | ".join(evidence_parts) if evidence_parts else "Anchors present but not influencing output",
        "details": {
            "anchor_entities": [a["text"] for a in anchor_values],
            "anchors_in_answer": anchors_in_answer,
            "anchors_in_trace": anchors_in_trace,
            "total_anchors": len(anchor_values),
        },
    }


async def _detect_regex_fallback(
    query: str, cot_trace: str, answer: str
) -> dict:
    """Fallback detection using regex when spaCy is not available."""
    from app.utils.text_utils import extract_numbers

    query_numbers = extract_numbers(query)
    if not query_numbers:
        return _no_bias("No numerical anchors found (regex fallback)")

    answer_lower = answer.lower()
    found_in_answer = [n for n in query_numbers if n.lower() in answer_lower]

    if found_in_answer:
        confidence = min(0.5 * len(found_in_answer) / len(query_numbers), 0.70)
        return {
            "detected": confidence >= 0.40,
            "confidence": round(confidence, 3),
            "evidence": f"Query numbers {found_in_answer} appear in answer (regex fallback)",
            "details": {
                "query_numbers": query_numbers,
                "found_in_answer": found_in_answer,
                "method": "regex_fallback",
            },
        }

    return _no_bias("Anchors not found in answer (regex fallback)")


def _no_bias(reason: str = "") -> dict:
    return {
        "detected": False,
        "confidence": 0.0,
        "evidence": reason or "No anchoring bias detected",
        "details": {},
    }
