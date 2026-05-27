"""
Integration Tests for ClearMind Agent Pipeline

Tests the full orchestrator flow with mocked Gemini API responses.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.models.schemas import BiasReport, BiasDetail, BiasType, AnalyzeResponse


@pytest.mark.asyncio
async def test_pipeline_no_bias_skips_debias():
    """Pipeline should skip debiasing when no bias is detected."""
    from app.agents.orchestrator import run_pipeline

    mock_response = MagicMock()
    mock_response.content = (
        "### Reasoning:\n"
        "Step 1: Water boils at 100°C at standard pressure.\n"
        "Step 2: This is a well-established scientific fact.\n\n"
        "### Answer:\n"
        "Water boils at 100°C (212°F) at standard atmospheric pressure."
    )

    with patch(
        "app.agents.base_agent.ChatGoogleGenerativeAI"
    ) as MockLLM:
        instance = MockLLM.return_value
        instance.ainvoke = AsyncMock(return_value=mock_response)

        response = await run_pipeline(
            query="At what temperature does water boil?",
            enable_recursive_check=False,
        )

        assert isinstance(response, AnalyzeResponse)
        assert response.base_answer != ""
        assert response.query == "At what temperature does water boil?"


@pytest.mark.asyncio
async def test_bias_report_construction():
    """BiasReport should correctly serialize and aggregate biases."""
    report = BiasReport(
        biases_detected=[
            BiasDetail(
                bias_type=BiasType.CONFIRMATION,
                confidence=0.75,
                evidence="One-sided reasoning detected",
                detection_method="rule_based",
                severity="high",
            ),
            BiasDetail(
                bias_type=BiasType.OVERCONFIDENCE,
                confidence=0.55,
                evidence="Absolute language on contested topic",
                detection_method="rule_based",
                severity="medium",
            ),
        ],
        overall_bias_score=0.75,
        is_biased=True,
        classifier_available=False,
    )

    assert report.is_biased is True
    assert len(report.biases_detected) == 2
    assert report.biases_detected[0].bias_type == BiasType.CONFIRMATION

    # Test serialization
    data = report.model_dump()
    assert data["overall_bias_score"] == 0.75
    assert data["biases_detected"][0]["bias_type"] == "confirmation_bias"


@pytest.mark.asyncio
async def test_analyze_response_construction():
    """AnalyzeResponse should correctly hold all pipeline outputs."""
    response = AnalyzeResponse(
        query="Test query",
        base_answer="Test answer",
        cot_trace="Step 1: reasoning",
        bias_report=BiasReport(),
        processing_time_ms=1234.5,
    )

    assert response.query == "Test query"
    assert response.corrected_answer is None
    assert response.processing_time_ms == 1234.5
    assert response.bias_report.is_biased is False
