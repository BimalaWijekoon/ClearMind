"""
Platt Scaling Calibration

Alternative calibration using logistic regression on raw logits.
Maps raw model scores to calibrated probabilities.
"""

import logging
import pickle
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression

logger = logging.getLogger("clearmind.calibration.platt")


class PlattScaler:
    """Platt scaling using sklearn LogisticRegression on raw logits."""

    def __init__(self):
        self.model = LogisticRegression(max_iter=1000, solver="lbfgs", multi_class="multinomial")
        self._fitted = False

    def fit(self, logits: np.ndarray, labels: np.ndarray) -> dict:
        """Fit logistic regression on validation logits.

        Args:
            logits: Raw model logits, shape (N, C).
            labels: True class labels, shape (N,).

        Returns:
            Dict with training accuracy.
        """
        self.model.fit(logits, labels)
        self._fitted = True
        accuracy = self.model.score(logits, labels)
        logger.info(f"Platt scaling fitted. Validation accuracy: {accuracy:.4f}")
        return {"accuracy": round(accuracy, 4)}

    def calibrate(self, logits) -> np.ndarray:
        """Apply Platt scaling to logits.

        Args:
            logits: Raw logits, shape (C,) or (N, C).

        Returns:
            Calibrated probabilities.
        """
        logits = np.array(logits, dtype=np.float64)
        if logits.ndim == 1:
            logits = logits.reshape(1, -1)
        return self.model.predict_proba(logits)[0]

    def save(self, path: str) -> None:
        """Save fitted Platt scaler."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({"model": self.model, "fitted": self._fitted}, f)

    def load(self, path: str) -> bool:
        """Load a fitted Platt scaler."""
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
            self.model = data["model"]
            self._fitted = data["fitted"]
            logger.info("Loaded Platt scaler")
            return True
        except Exception as e:
            logger.warning(f"Failed to load Platt scaler: {e}")
            return False
