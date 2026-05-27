"""
ClearMind CRUD Operations

Database operations for saving query results, retrieving history,
and computing aggregated metrics.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import QueryRecord, EvaluationRecord
from app.models.schemas import (
    AnalyzeResponse,
    BiasReport,
    HistoryRecord,
    MetricsResponse,
)

logger = logging.getLogger("clearmind.crud")


async def save_query_result(
    session: AsyncSession,
    response: AnalyzeResponse,
) -> QueryRecord:
    """Save a completed pipeline result to the database."""
    record = QueryRecord(
        query_text=response.query,
        base_answer=response.base_answer,
        cot_trace=response.cot_trace,
        corrected_answer=response.corrected_answer,
        correction_strategy=response.correction_strategy,
        is_biased=response.bias_report.is_biased,
        overall_bias_score=response.bias_report.overall_bias_score,
        biases_detected=[
            b.bias_type.value for b in response.bias_report.biases_detected
        ],
        bias_report_json=response.bias_report.model_dump(),
        residual_bias_report_json=(
            response.residual_bias_report.model_dump()
            if response.residual_bias_report
            else None
        ),
        semantic_similarity=response.semantic_similarity,
        processing_time_ms=response.processing_time_ms,
        classifier_used=response.bias_report.classifier_available,
        created_at=response.created_at,
    )
    session.add(record)
    await session.flush()
    logger.info(f"Saved query record id={record.id}")
    return record


async def get_history(
    session: AsyncSession,
    limit: int = 50,
    offset: int = 0,
) -> list[HistoryRecord]:
    """Retrieve query history ordered by most recent first."""
    stmt = (
        select(QueryRecord)
        .order_by(desc(QueryRecord.created_at))
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    records = result.scalars().all()

    return [
        HistoryRecord(
            id=r.id,
            query=r.query_text,
            base_answer=r.base_answer,
            corrected_answer=r.corrected_answer,
            biases_detected=r.biases_detected or [],
            overall_bias_score=r.overall_bias_score,
            semantic_similarity=r.semantic_similarity,
            processing_time_ms=r.processing_time_ms,
            created_at=r.created_at,
        )
        for r in records
    ]


async def get_metrics_summary(session: AsyncSession) -> MetricsResponse:
    """Compute aggregated metrics from all stored query results."""
    # Total and biased query counts
    total_stmt = select(func.count(QueryRecord.id))
    biased_stmt = select(func.count(QueryRecord.id)).where(
        QueryRecord.is_biased == True
    )

    total = (await session.execute(total_stmt)).scalar() or 0
    biased = (await session.execute(biased_stmt)).scalar() or 0

    # Averages
    avg_time_stmt = select(func.avg(QueryRecord.processing_time_ms))
    avg_sim_stmt = select(func.avg(QueryRecord.semantic_similarity)).where(
        QueryRecord.semantic_similarity.isnot(None)
    )
    avg_score_stmt = select(func.avg(QueryRecord.overall_bias_score))

    avg_time = (await session.execute(avg_time_stmt)).scalar() or 0.0
    avg_sim = (await session.execute(avg_sim_stmt)).scalar()
    avg_score = (await session.execute(avg_score_stmt)).scalar() or 0.0

    # Bias type frequency
    all_records_stmt = select(QueryRecord.biases_detected).where(
        QueryRecord.biases_detected.isnot(None)
    )
    all_records = (await session.execute(all_records_stmt)).scalars().all()

    bias_freq: dict[str, int] = {}
    for biases_list in all_records:
        if biases_list:
            for bias_type in biases_list:
                bias_freq[bias_type] = bias_freq.get(bias_type, 0) + 1

    return MetricsResponse(
        total_queries=total,
        biased_queries=biased,
        bias_rate=biased / total if total > 0 else 0.0,
        avg_processing_time_ms=round(avg_time, 2),
        bias_type_frequency=bias_freq,
        avg_semantic_similarity=round(avg_sim, 4) if avg_sim else None,
        avg_bias_score=round(avg_score, 4),
    )
