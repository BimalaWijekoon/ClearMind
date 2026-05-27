"""
ClearMind SQLAlchemy ORM Models

Defines PostgreSQL table schemas for persisting query results,
bias detection history, and evaluation records.
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    Boolean,
    DateTime,
    JSON,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy declarative base class."""
    pass


class QueryRecord(Base):
    """Stores each query processed through the ClearMind pipeline."""

    __tablename__ = "query_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query_text = Column(Text, nullable=False, index=True)
    base_answer = Column(Text, nullable=False)
    cot_trace = Column(Text, nullable=True)
    corrected_answer = Column(Text, nullable=True)
    correction_strategy = Column(Text, nullable=True)

    # Bias detection results
    is_biased = Column(Boolean, default=False)
    overall_bias_score = Column(Float, default=0.0)
    biases_detected = Column(JSON, default=list)  # List of bias type strings
    bias_report_json = Column(JSON, default=dict)  # Full BiasReport serialized
    residual_bias_report_json = Column(JSON, nullable=True)

    # Similarity & performance
    semantic_similarity = Column(Float, nullable=True)
    processing_time_ms = Column(Float, nullable=False, default=0.0)

    # Metadata
    classifier_used = Column(Boolean, default=False)
    gemini_model = Column(String(100), default="gemini-2.0-flash")

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return f"<QueryRecord(id={self.id}, biased={self.is_biased}, score={self.overall_bias_score:.2f})>"


class EvaluationRecord(Base):
    """Stores evaluation benchmark results."""

    __tablename__ = "evaluation_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    benchmark_name = Column(String(100), nullable=False)  # e.g., "TruthfulQA", "BBQ"
    metric_name = Column(String(100), nullable=False)      # e.g., "accuracy", "f1", "ece"
    base_value = Column(Float, nullable=True)              # Base LLM score
    clearmind_value = Column(Float, nullable=True)         # ClearMind-corrected score
    delta = Column(Float, nullable=True)                   # Improvement delta
    details = Column(JSON, nullable=True)                  # Additional metric details
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<EvaluationRecord({self.benchmark_name}/{self.metric_name}: {self.clearmind_value})>"
