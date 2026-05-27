"""
Calibration Evaluator

Computes Expected Calibration Error (ECE), generates reliability diagrams,
and produces calibration curves for the bias classifier.
"""

import logging
import io
import base64
from typing import Optional

import numpy as np

logger = logging.getLogger("clearmind.calibration.evaluator")


def compute_ece(
    confidences: np.ndarray,
    accuracies: np.ndarray,
    n_bins: int = 10,
) -> dict:
    """Compute Expected Calibration Error (ECE).

    ECE measures the difference between predicted confidence and actual
    accuracy across bucketed confidence ranges. Lower is better.

    Args:
        confidences: Predicted confidence scores, shape (N,).
        accuracies: Binary accuracy indicators (1=correct, 0=wrong), shape (N,).
        n_bins: Number of bins for calibration.

    Returns:
        Dict with 'ece', 'bin_data' (for plotting).
    """
    confidences = np.array(confidences)
    accuracies = np.array(accuracies)

    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_data = []
    ece = 0.0

    for i in range(n_bins):
        lower = bin_boundaries[i]
        upper = bin_boundaries[i + 1]
        mask = (confidences > lower) & (confidences <= upper)
        count = mask.sum()

        if count == 0:
            bin_data.append({
                "bin_lower": round(lower, 2),
                "bin_upper": round(upper, 2),
                "avg_confidence": 0.0,
                "avg_accuracy": 0.0,
                "count": 0,
            })
            continue

        avg_conf = confidences[mask].mean()
        avg_acc = accuracies[mask].mean()
        bin_ece = abs(avg_acc - avg_conf) * (count / len(confidences))
        ece += bin_ece

        bin_data.append({
            "bin_lower": round(lower, 2),
            "bin_upper": round(upper, 2),
            "avg_confidence": round(float(avg_conf), 4),
            "avg_accuracy": round(float(avg_acc), 4),
            "count": int(count),
            "gap": round(float(abs(avg_acc - avg_conf)), 4),
        })

    return {
        "ece": round(float(ece), 4),
        "n_bins": n_bins,
        "n_samples": len(confidences),
        "bin_data": bin_data,
    }


def plot_reliability_diagram(
    ece_result: dict,
    title: str = "Reliability Diagram",
) -> Optional[str]:
    """Generate a reliability diagram as a base64 PNG.

    Args:
        ece_result: Output from compute_ece().
        title: Plot title.

    Returns:
        Base64-encoded PNG string, or None if matplotlib fails.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        bins = ece_result["bin_data"]
        confidences = [b["avg_confidence"] for b in bins if b["count"] > 0]
        accuracies = [b["avg_accuracy"] for b in bins if b["count"] > 0]
        counts = [b["count"] for b in bins if b["count"] > 0]

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8), gridspec_kw={"height_ratios": [3, 1]})

        # Reliability diagram
        ax1.plot([0, 1], [0, 1], "k--", label="Perfect calibration", alpha=0.5)
        ax1.bar(
            confidences, accuracies,
            width=1.0 / ece_result["n_bins"],
            alpha=0.7, color="#7C3AED", edgecolor="#0d1117",
            label=f"ECE = {ece_result['ece']:.4f}",
        )
        ax1.set_xlabel("Mean Predicted Confidence")
        ax1.set_ylabel("Fraction of Positives (Accuracy)")
        ax1.set_title(title)
        ax1.legend(loc="upper left")
        ax1.set_xlim(0, 1)
        ax1.set_ylim(0, 1)

        # Histogram of predictions
        ax2.bar(
            confidences, counts,
            width=1.0 / ece_result["n_bins"],
            alpha=0.7, color="#06B6D4", edgecolor="#0d1117",
        )
        ax2.set_xlabel("Mean Predicted Confidence")
        ax2.set_ylabel("Count")

        plt.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)

        return base64.b64encode(buf.read()).decode("utf-8")

    except Exception as e:
        logger.warning(f"Reliability diagram generation failed: {e}")
        return None
