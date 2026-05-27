"""
ClearMind Bias Detectors Package

Each detector module exports a detect() async function with the signature:
    detect(query: str, cot_trace: str, answer: str, **kwargs) -> dict

Returns a dict with:
    - detected: bool
    - confidence: float (0-1)
    - evidence: str
    - details: dict (detector-specific data)
"""

from app.bias.detectors.confirmation import detect as detect_confirmation
from app.bias.detectors.anchoring import detect as detect_anchoring
from app.bias.detectors.availability import detect as detect_availability
from app.bias.detectors.sycophancy import detect as detect_sycophancy
from app.bias.detectors.overconfidence import detect as detect_overconfidence
from app.bias.detectors.framing import detect as detect_framing
from app.bias.detectors.recency import detect as detect_recency
from app.bias.detectors.bandwagon import detect as detect_bandwagon

ALL_DETECTORS = {
    "confirmation_bias": detect_confirmation,
    "anchoring_bias": detect_anchoring,
    "availability_heuristic": detect_availability,
    "sycophancy_bias": detect_sycophancy,
    "overconfidence_bias": detect_overconfidence,
    "framing_effect": detect_framing,
    "recency_bias": detect_recency,
    "bandwagon_effect": detect_bandwagon,
}
