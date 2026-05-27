"""
Tests for Calibration Module

Tests ECE computation, temperature scaling, and Platt scaling.
"""

import pytest
import numpy as np

from app.calibration.temperature_scaling import TemperatureScaler
from app.calibration.platt_scaling import PlattScaler
from app.calibration.evaluator import compute_ece


def test_ece_perfect_calibration():
    """Perfect calibration should have ECE near 0."""
    n = 1000
    confidences = np.random.uniform(0.5, 1.0, n)
    # Make accuracy match confidence (perfect calibration)
    accuracies = (np.random.random(n) < confidences).astype(float)

    result = compute_ece(confidences, accuracies, n_bins=10)
    assert result["ece"] < 0.15  # Allow some noise
    assert result["n_samples"] == n


def test_ece_overconfident():
    """Overconfident model should have high ECE."""
    n = 500
    confidences = np.full(n, 0.95)  # Always says 95%
    accuracies = np.random.choice([0, 1], n, p=[0.5, 0.5])  # Only 50% correct

    result = compute_ece(confidences, accuracies, n_bins=10)
    assert result["ece"] > 0.3


def test_temperature_scaler_fit():
    """Temperature scaling should learn a temperature > 1 for overconfident model."""
    np.random.seed(42)
    n_samples = 200
    n_classes = 9

    # Simulate overconfident logits
    logits = np.random.randn(n_samples, n_classes) * 3  # High variance = overconfident
    labels = np.random.randint(0, n_classes, n_samples)

    scaler = TemperatureScaler()
    result = scaler.fit(logits, labels)

    assert result["temperature"] > 1.0  # Should cool down confidence
    assert result["nll_after"] <= result["nll_before"]


def test_temperature_scaler_calibrate():
    """Calibrated probabilities should sum to 1."""
    scaler = TemperatureScaler()
    scaler.temperature = 2.0

    logits = np.array([2.0, 1.0, 0.5, -1.0, 0.0, 0.3, -0.5, 0.1, 1.5])
    probs = scaler.calibrate(logits)

    assert abs(probs.sum() - 1.0) < 1e-6
    assert all(p >= 0 for p in probs)


def test_platt_scaler_fit():
    """Platt scaling should fit and produce valid probabilities."""
    np.random.seed(42)
    n_samples = 200
    n_classes = 9

    logits = np.random.randn(n_samples, n_classes)
    labels = np.random.randint(0, n_classes, n_samples)

    scaler = PlattScaler()
    result = scaler.fit(logits, labels)

    assert "accuracy" in result
    assert result["accuracy"] >= 0.0

    # Test calibration output
    test_logits = np.random.randn(n_classes)
    probs = scaler.calibrate(test_logits)

    assert abs(probs.sum() - 1.0) < 1e-6
    assert len(probs) == n_classes
