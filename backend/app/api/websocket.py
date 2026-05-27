"""
ClearMind WebSocket Endpoint

Streams pipeline steps to the frontend in real-time as JSON events.
Each step produces a message like:
    {"step": "base_agent", "status": "complete", "data": {...}}

This is what makes the demo visually impressive — users see
the system thinking, detecting biases, and correcting in real time.
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import get_settings
from app.models.schemas import StepUpdate, AnalyzeRequest
from app.agents.orchestrator import run_pipeline

logger = logging.getLogger("clearmind.websocket")
router = APIRouter()


@router.websocket("/ws/analyze")
async def websocket_analyze(websocket: WebSocket):
    """WebSocket endpoint for streaming bias analysis pipeline.

    Protocol:
    1. Client connects
    2. Client sends JSON: {"query": "...", "enable_recursive_check": true}
    3. Server streams step updates as JSON messages
    4. Server sends final complete response
    5. Connection closes
    """
    await websocket.accept()
    logger.info("WebSocket client connected")

    try:
        # Receive query from client
        data = await websocket.receive_text()
        request_data = json.loads(data)

        query = request_data.get("query", "")
        enable_recursive_check = request_data.get("enable_recursive_check", True)

        if not query or len(query) < 3:
            await websocket.send_json({
                "error": "Query must be at least 3 characters long"
            })
            await websocket.close()
            return

        settings = get_settings()
        if not settings.google_api_key or settings.google_api_key == "your_gemini_api_key_here":
            await websocket.send_json({
                "error": "Gemini API key not configured"
            })
            await websocket.close()
            return

        # Define step callback for streaming
        async def stream_step(step: StepUpdate):
            """Send a pipeline step update to the WebSocket client."""
            try:
                await websocket.send_json(step.model_dump(mode="json"))
            except Exception as e:
                logger.warning(f"Failed to send step update: {e}")

        # Run pipeline with streaming
        response = await run_pipeline(
            query=query,
            enable_recursive_check=enable_recursive_check,
            step_callback=stream_step,
        )

        # Send final complete response
        await websocket.send_json({
            "type": "result",
            "data": response.model_dump(mode="json"),
        })

        logger.info(f"Pipeline complete for WebSocket client (query: '{query[:50]}...')")

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except json.JSONDecodeError:
        await websocket.send_json({"error": "Invalid JSON"})
        await websocket.close()
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({"error": str(e)})
            await websocket.close()
        except Exception:
            pass
