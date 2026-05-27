"""
Temperature Scaling Calibration

Post-hoc calibration method: divides logits by a learned scalar temperature T
before softmax. If T > 1, model becomes less confident (better calibrated).
T is trained on a held-out validation set to minimize NLL.
"""

import logging
import pickle
from pathlib import Path
from typing import Optional

import numpy as np
from scipy.optimize import minimize
from scipy.special import softmax

logger = logging.getLogger("clearmind.calibration.temperature")


class TemperatureScaler:
    """Learns and applies temperature scaling to model logits."""

    def __init__(self):
        self.temperature: float = 1.0
        self._fitted = False

    def fit(self, logits: np.ndarray, labels: np.ndarray) -> dict:
        """Learn optimal temperature T on validation set.

        Args:
            logits: Raw model logits, shape (N, C) where C is num classes.
            labels: True class labels, shape (N,).

        Returns:
            Dict with 'temperature', 'nll_before', 'nll_after'.
        """
        nll_before = self._nll(1.0, logits, labels)

        result = minimize(
            self._nll,
            x0=1.5,
            args=(logits, labels),
            method="L-BFGS-B",
            bounds=[(0.1, 10.0)],
        )

        self.temperature = float(result.x[0])
        self._fitted = True
        nll_after = self._nll(self.temperature, logits, labels)

        logger.info(f"Temperature scaling: T={self.temperature:.4f}, NLL {nll_before:.4f} → {nll_after:.4f}")

        return {
            "temperature": self.temperature,
            "nll_before": round(nll_before, 4),
            "nll_after": round(nll_after, 4),
        }

    def calibrate(self, logits) -> np.ndarray:
        """Apply temperature scaling to logits.

        Args:
            logits: Raw logits, shape (C,) or (N, C).

        Returns:
            Calibrated probabilities after softmax(logits / T).
        """
        logits = np.array(logits, dtype=np.float64)
        scaled = logits / self.temperature
        return softmax(scaled, axis=-1)

    def save(self, path: str) -> None:
        """Save the fitted scaler to disk."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({"temperature": self.temperature, "fitted": self._fitted}, f)

    def load(self, path: str) -> bool:
        """Load a fitted scaler from disk."""
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
            self.temperature = data["temperature"]
            self._fitted = data["fitted"]
            logger.info(f"Loaded temperature scaler: T={self.temperature:.4f}")
            return True
        except Exception as e:
            logger.warning(f"Failed to load temperature scaler: {e}")
            return False

    @staticmethod
    def _nll(temperature: float, logits: np.ndarray, labels: np.ndarray) -> float:
        """Compute negative log-likelihood with temperature scaling."""
        scaled = logits / temperature
        probs = softmax(scaled, axis=1)
        log_probs = np.log(probs[np.arange(len(labels)), labels] + 1e-10)
        return -log_probs.mean()
