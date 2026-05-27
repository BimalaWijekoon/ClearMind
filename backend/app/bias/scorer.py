"""
ClearMind Bias Scorer

Combines rule-based detector signals (0-1 scores) with the RoBERTa
classifier output. Applies calibration to produce a final BiasReport
with ECE-calibrated confidence per bias type.
"""

import logging
from typing import Optional

from app.models.schemas import BiasDetail, BiasReport, BiasType
from app.bias import classifier
from app.bias.detectors import ALL_DETECTORS

logger = logging.getLogger("clearmind.scorer")

# Confidence threshold for flagging a bias
BIAS_THRESHOLD = 0.40

# Severity thresholds
SEVERITY_THRESHOLDS = {
    "high": 0.75,
    "medium": 0.45,
    "low": 0.0,
}


def _get_severity(confidence: float) -> str:
    """Map confidence score to severity level."""
    if confidence >= SEVERITY_THRESHOLDS["high"]:
        return "high"
    elif confidence >= SEVERITY_THRESHOLDS["medium"]:
        return "medium"
    return "low"


async def compute_bias_report(
    query: str,
    cot_trace: str,
    answer: str,
    base_agent_fn=None,
    calibrator=None,
) -> BiasReport:
    """Run all detectors and classifier to produce a comprehensive BiasReport.

    Args:
        query: Original user question.
        cot_trace: Chain-of-thought reasoning trace.
        answer: Base agent answer.
        base_agent_fn: Optional async fn to query the base agent (for sycophancy/framing).
        calibrator: Optional calibration model to apply to classifier logits.

    Returns:
        Complete BiasReport with all detected biases.
    """
    biases_detected = []

    # --- 1. Run all rule-based detectors ---
    for bias_name, detect_fn in ALL_DETECTORS.items():
        try:
            result = await detect_fn(
                query=query,
                cot_trace=cot_trace,
                answer=answer,
                base_agent_fn=base_agent_fn,
            )

            if result.get("detected", False):
                bias_type = BiasType(bias_name)
                biases_detected.append(BiasDetail(
                    bias_type=bias_type,
                    confidence=result["confidence"],
                    evidence=result.get("evidence", "Detected by rule-based analysis"),
                    detection_method="rule_based",
                    severity=_get_severity(result["confidence"]),
                ))

        except Exception as e:
            logger.warning(f"Detector {bias_name} failed: {e}")

    # --- 2. Run RoBERTa classifier (if available) ---
    classifier_available = classifier.is_available()
    if classifier_available:
        cls_result = classifier.predict(f"{query}\n\n{cot_trace}")
        if cls_result and cls_result["bias_type"] != "no_bias":
            cls_confidence = cls_result["confidence"]

            # Apply calibration if available
            if calibrator is not None and cls_result.get("logits"):
                try:
                    calibrated = calibrator.calibrate(cls_result["logits"])
                    cls_confidence = float(max(calibrated))
                except Exception:
                    pass

            if cls_confidence >= BIAS_THRESHOLD:
                # Check if this bias was already detected by a rule-based detector
                cls_bias_type = BiasType(cls_result["bias_type"])
                existing = next(
                    (b for b in biases_detected if b.bias_type == cls_bias_type),
                    None,
                )

                if existing:
                    # Boost confidence if both classifier and rule-based agree
                    boosted = min((existing.confidence + cls_confidence) / 1.5, 0.98)
                    existing.confidence = round(boosted, 3)
                    existing.detection_method = "combined"
                    existing.severity = _get_severity(boosted)
                else:
                    biases_detected.append(BiasDetail(
                        bias_type=cls_bias_type,
                        confidence=round(cls_confidence, 3),
                        evidence=f"Classified by RoBERTa model (scores: {cls_result['all_scores']})",
                        detection_method="classifier",
                        severity=_get_severity(cls_confidence),
                    ))

    # --- 3. Compute overall score ---
    if biases_detected:
        overall_score = max(b.confidence for b in biases_detected)
    else:
        overall_score = 0.0

    # Sort by confidence descending
    biases_detected.sort(key=lambda b: b.confidence, reverse=True)

    return BiasReport(
        biases_detected=biases_detected,
        overall_bias_score=round(overall_score, 3),
        is_biased=len(biases_detected) > 0,
        classifier_available=classifier_available,
    )
