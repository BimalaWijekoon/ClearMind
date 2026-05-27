"""
ClearMind Pydantic Schemas

Defines all request/response models for the API using Pydantic v2.
These schemas enforce type safety across the entire pipeline.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class BiasType(str, Enum):
    """Enumeration of all detectable cognitive bias types."""
    CONFIRMATION = "confirmation_bias"
    ANCHORING = "anchoring_bias"
    AVAILABILITY = "availability_heuristic"
    SYCOPHANCY = "sycophancy_bias"
    OVERCONFIDENCE = "overconfidence_bias"
    FRAMING = "framing_effect"
    RECENCY = "recency_bias"
    BANDWAGON = "bandwagon_effect"
    NO_BIAS = "no_bias"


class PipelineStep(str, Enum):
    """Steps in the ClearMind processing pipeline."""
    BASE_AGENT = "base_agent"
    MONITOR_AGENT = "monitor_agent"
    DEBIAS_AGENT = "debias_agent"
    POST_CHECK = "post_check_monitor"
    COMPLETE = "complete"


# ─── Request Schemas ──────────────────────────────────────────────────────────


class AnalyzeRequest(BaseModel):
    """Request body for the /analyze endpoint."""
    query: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="The user's question to analyze for cognitive biases",
        examples=["Is nuclear energy safe for the environment?"],
    )
    enable_recursive_check: bool = Field(
        default=True,
        description="Whether to run a second monitor pass on the debiased output",
    )


# ─── Bias Detail Schemas ─────────────────────────────────────────────────────


class BiasDetail(BaseModel):
    """A single detected bias with metadata."""
    bias_type: BiasType
    confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Calibrated confidence score (0-1) for this bias detection",
    )
    evidence: str = Field(
        ...,
        description="Explanation of why this bias was detected in the reasoning",
    )
    detection_method: str = Field(
        ...,
        description="Which detector flagged this bias (e.g., 'rule_based', 'classifier')",
    )
    severity: str = Field(
        default="medium",
        description="Severity level: low, medium, high",
    )


class BiasReport(BaseModel):
    """Complete bias analysis report from the monitor agent."""
    biases_detected: list[BiasDetail] = Field(default_factory=list)
    overall_bias_score: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Aggregate bias score across all detectors",
    )
    is_biased: bool = Field(
        default=False,
        description="Whether any bias was detected above the threshold",
    )
    classifier_available: bool = Field(
        default=False,
        description="Whether the RoBERTa classifier was used (vs rule-based only)",
    )


# ─── Pipeline Step Schemas ───────────────────────────────────────────────────


class StepUpdate(BaseModel):
    """Real-time pipeline step update sent via WebSocket."""
    step: PipelineStep
    status: str = Field(..., description="'started', 'complete', or 'error'")
    data: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ─── Response Schemas ────────────────────────────────────────────────────────


class AnalyzeResponse(BaseModel):
    """Full response from the /analyze endpoint."""
    query: str
    base_answer: str = Field(..., description="Raw answer from the base LLM agent")
    cot_trace: str = Field(..., description="Chain-of-thought reasoning trace")
    bias_report: BiasReport
    corrected_answer: Optional[str] = Field(
        None, description="Debiased answer (None if no bias detected)"
    )
    correction_strategy: Optional[str] = Field(
        None, description="Description of the correction approach used"
    )
    residual_bias_report: Optional[BiasReport] = Field(
        None, description="Bias report from the recursive post-check"
    )
    semantic_similarity: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="Cosine similarity between base and corrected answers",
    )
    pipeline_steps: list[StepUpdate] = Field(default_factory=list)
    processing_time_ms: float = Field(
        ..., description="Total pipeline processing time in milliseconds"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ─── History & Metrics ───────────────────────────────────────────────────────


class HistoryRecord(BaseModel):
    """A single record from query history."""
    id: int
    query: str
    base_answer: str
    corrected_answer: Optional[str]
    biases_detected: list[str]
    overall_bias_score: float
    semantic_similarity: Optional[float]
    processing_time_ms: float
    created_at: datetime


class MetricsResponse(BaseModel):
    """Aggregated metrics from evaluation history."""
    total_queries: int
    biased_queries: int
    bias_rate: float
    avg_processing_time_ms: float
    bias_type_frequency: dict[str, int]
    avg_semantic_similarity: Optional[float]
    avg_bias_score: float
