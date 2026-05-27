"""
ClearMind API Routes

Defines all FastAPI REST endpoints:
- POST /analyze  — Run the full ClearMind pipeline
- GET  /history  — Retrieve past query results
- GET  /metrics  — Aggregated bias detection metrics
"""

import logging
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.database import get_session
from app.db.crud import save_query_result, get_history, get_metrics_summary
from app.models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    HistoryRecord,
    MetricsResponse,
)
from app.agents.orchestrator import run_pipeline

logger = logging.getLogger("clearmind.api")
router = APIRouter(tags=["ClearMind"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_query(
    request: AnalyzeRequest,
    session: AsyncSession = Depends(get_session),
):
    """Run the full ClearMind bias detection and correction pipeline.

    1. Base agent generates answer with CoT reasoning
    2. Monitor agent analyzes reasoning for cognitive biases
    3. Debias agent applies bias-specific corrections (if biases found)
    4. Post-check monitor verifies correction didn't introduce new biases
    """
    settings = get_settings()

    if not settings.google_api_key or settings.google_api_key == "your_gemini_api_key_here":
        raise HTTPException(
            status_code=503,
            detail="Gemini API key not configured. Set GOOGLE_API_KEY in .env",
        )

    try:
        response = await run_pipeline(
            query=request.query,
            enable_recursive_check=request.enable_recursive_check,
        )

        # Save to database
        try:
            await save_query_result(session, response)
        except Exception as e:
            logger.warning(f"Failed to save query result to DB: {e}")

        return response

    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


@router.get("/history", response_model=list[HistoryRecord])
async def query_history(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """Retrieve past query results with bias detection history."""
    try:
        return await get_history(session, limit=limit, offset=offset)
    except Exception as e:
        logger.error(f"Failed to fetch history: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/metrics", response_model=MetricsResponse)
async def metrics_summary(
    session: AsyncSession = Depends(get_session),
):
    """Get aggregated bias detection metrics and statistics."""
    try:
        return await get_metrics_summary(session)
    except Exception as e:
        logger.error(f"Failed to fetch metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
