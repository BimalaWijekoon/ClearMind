"""
ClearMind Monitor Agent

The metacognitive monitor that analyzes the base agent's CoT reasoning trace.
Runs all 8 rule-based bias detectors and the RoBERTa classifier,
then combines results into a unified BiasReport.

This agent acts as a "bias auditor" reading the base agent's thinking process.
"""

import logging
from typing import Optional

from app.bias.scorer import compute_bias_report
from app.models.schemas import BiasReport

logger = logging.getLogger("clearmind.agents.monitor")


class MonitorAgent:
    """Metacognitive monitor agent for bias detection."""

    def __init__(self, base_agent_fn=None, calibrator=None):
        """Initialize the monitor.

        Args:
            base_agent_fn: Optional async function to query the base agent
                          (needed for sycophancy and framing detection).
            calibrator: Optional calibration model for classifier outputs.
        """
        self.base_agent_fn = base_agent_fn
        self.calibrator = calibrator

    async def run(
        self,
        query: str,
        cot_trace: str,
        answer: str,
    ) -> BiasReport:
        """Analyze a reasoning trace for cognitive biases.

        Args:
            query: Original user question.
            cot_trace: Chain-of-thought reasoning from base agent.
            answer: Final answer from base agent.

        Returns:
            BiasReport with all detected biases and calibrated confidence scores.
        """
        logger.info(f"Monitor analyzing trace for query: '{query[:60]}...'")

        try:
            report = await compute_bias_report(
                query=query,
                cot_trace=cot_trace,
                answer=answer,
                base_agent_fn=self.base_agent_fn,
                calibrator=self.calibrator,
            )

            if report.is_biased:
                bias_names = [b.bias_type.value for b in report.biases_detected]
                logger.info(
                    f"Biases detected: {bias_names} "
                    f"(overall score: {report.overall_bias_score:.3f})"
                )
            else:
                logger.info("No biases detected")

            return report

        except Exception as e:
            logger.error(f"Monitor agent failed: {e}")
            return BiasReport(
                biases_detected=[],
                overall_bias_score=0.0,
                is_biased=False,
                classifier_available=False,
            )
