"""
ClearMind Bias Classifier

Loads the fine-tuned RoBERTa model for multi-class bias type classification.
Falls back gracefully if model weights are not found (pre-training state).

Input: LLM reasoning trace text
Output: bias_type label and confidence score with raw logits
"""

import logging
from pathlib import Path
from typing import Optional

import numpy as np

from app.config import get_settings

logger = logging.getLogger("clearmind.classifier")

# Lazy-loaded model components
_model = None
_tokenizer = None
_labels = [
    "confirmation_bias", "anchoring_bias", "availability_heuristic",
    "sycophancy_bias", "overconfidence_bias", "framing_effect",
    "recency_bias", "bandwagon_effect", "no_bias",
]


def _load_model():
    """Attempt to load the fine-tuned RoBERTa model."""
    global _model, _tokenizer
    settings = get_settings()
    model_path = Path(settings.bias_classifier_path)

    if not model_path.exists():
        logger.info(f"Classifier model not found at {model_path} — using rule-based only")
        return False

    try:
        from transformers import RobertaTokenizer, RobertaForSequenceClassification
        import torch

        _tokenizer = RobertaTokenizer.from_pretrained(str(model_path))
        _model = RobertaForSequenceClassification.from_pretrained(str(model_path))
        _model.eval()
        logger.info("✅ RoBERTa bias classifier loaded")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Failed to load classifier: {e}")
        return False


def is_available() -> bool:
    """Check if the classifier model is loaded and available."""
    if _model is None:
        _load_model()
    return _model is not None


def predict(text: str, max_length: int = 512) -> Optional[dict]:
    """Run bias classification on text.

    Args:
        text: The reasoning trace or answer text to classify.
        max_length: Maximum token length for input.

    Returns:
        Dict with 'bias_type', 'confidence', 'logits', 'all_scores'
        or None if model is not available.
    """
    if not is_available():
        return None

    try:
        import torch

        inputs = _tokenizer(
            text,
            return_tensors="pt",
            max_length=max_length,
            truncation=True,
            padding=True,
        )

        with torch.no_grad():
            outputs = _model(**inputs)
            logits = outputs.logits[0].numpy()

        # Softmax for probabilities
        exp_logits = np.exp(logits - np.max(logits))
        probabilities = exp_logits / exp_logits.sum()

        predicted_idx = int(np.argmax(probabilities))
        predicted_label = _labels[predicted_idx]
        confidence = float(probabilities[predicted_idx])

        all_scores = {
            label: round(float(prob), 4)
            for label, prob in zip(_labels, probabilities)
        }

        return {
            "bias_type": predicted_label,
            "confidence": round(confidence, 4),
            "logits": logits.tolist(),
            "all_scores": all_scores,
        }

    except Exception as e:
        logger.error(f"Classifier prediction failed: {e}")
        return None
