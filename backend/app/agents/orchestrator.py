"""
ClearMind LangGraph Orchestrator

Defines the multi-agent state graph connecting Base Agent → Monitor Agent →
Debias Agent → Post-Check Monitor. State is passed between nodes carrying
the full pipeline data.

This gives full observability of every state transition, enabling:
- WebSocket streaming of pipeline steps to the frontend
- Replay and debugging of any pipeline run
- Clean separation of concerns between agents
"""

import logging
import time
from datetime import datetime
from typing import Annotated, TypedDict, Optional

from langgraph.graph import StateGraph, END

from app.agents.base_agent import BaseAgent
from app.agents.monitor_agent import MonitorAgent
from app.agents.debias_agent import DebiasAgent
from app.embeddings.similarity import compute_similarity
from app.models.schemas import (
    BiasReport,
    AnalyzeResponse,
    StepUpdate,
    PipelineStep,
)

logger = logging.getLogger("clearmind.orchestrator")


# ─── Pipeline State Schema ───────────────────────────────────────────────────

class PipelineState(TypedDict):
    """State that flows through the LangGraph pipeline."""
    # Input
    query: str
    enable_recursive_check: bool

    # Base agent output
    base_answer: str
    cot_trace: str
    raw_base_response: str

    # Monitor output
    bias_report: Optional[dict]

    # Debias output
    corrected_answer: Optional[str]
    correction_strategy: Optional[str]

    # Post-check output
    residual_bias_report: Optional[dict]

    # Similarity
    semantic_similarity: Optional[float]

    # Pipeline metadata
    steps: list[dict]
    start_time: float
    step_callback: Optional[object]  # Async callback for WebSocket streaming


# ─── Node Functions ──────────────────────────────────────────────────────────

async def base_agent_node(state: PipelineState) -> dict:
    """Node 1: Run the base LLM agent with CoT."""
    callback = state.get("step_callback")
    if callback:
        await callback(StepUpdate(
            step=PipelineStep.BASE_AGENT, status="started"
        ))

    agent = BaseAgent()
    result = await agent.run(state["query"])

    step = StepUpdate(
        step=PipelineStep.BASE_AGENT,
        status="complete",
        data={
            "answer_preview": result["answer"][:200],
            "cot_length": len(result["cot_trace"]),
        },
    )

    if callback:
        await callback(step)

    return {
        "base_answer": result["answer"],
        "cot_trace": result["cot_trace"],
        "raw_base_response": result["raw_response"],
        "steps": state.get("steps", []) + [step.model_dump(mode="json")],
    }


async def monitor_agent_node(state: PipelineState) -> dict:
    """Node 2: Run the metacognitive monitor on the CoT trace."""
    callback = state.get("step_callback")
    if callback:
        await callback(StepUpdate(
            step=PipelineStep.MONITOR_AGENT, status="started"
        ))

    monitor = MonitorAgent()
    report = await monitor.run(
        query=state["query"],
        cot_trace=state["cot_trace"],
        answer=state["base_answer"],
    )

    step = StepUpdate(
        step=PipelineStep.MONITOR_AGENT,
        status="complete",
        data={
            "is_biased": report.is_biased,
            "bias_count": len(report.biases_detected),
            "overall_score": report.overall_bias_score,
            "biases": [
                {"type": b.bias_type.value, "confidence": b.confidence}
                for b in report.biases_detected
            ],
        },
    )

    if callback:
        await callback(step)

    return {
        "bias_report": report.model_dump(mode="json"),
        "steps": state.get("steps", []) + [step.model_dump(mode="json")],
    }


async def debias_agent_node(state: PipelineState) -> dict:
    """Node 3: Apply bias-specific corrections if biases detected."""
    callback = state.get("step_callback")
    bias_report_data = state.get("bias_report", {})
    report = BiasReport(**bias_report_data) if bias_report_data else BiasReport()

    if not report.is_biased:
        step = StepUpdate(
            step=PipelineStep.DEBIAS_AGENT,
            status="complete",
            data={"action": "skipped", "reason": "no biases detected"},
        )
        if callback:
            await callback(step)
        return {
            "corrected_answer": None,
            "correction_strategy": "No correction needed",
            "steps": state.get("steps", []) + [step.model_dump(mode="json")],
        }

    if callback:
        await callback(StepUpdate(
            step=PipelineStep.DEBIAS_AGENT, status="started"
        ))

    agent = DebiasAgent()
    result = await agent.run(query=state["query"], bias_report=report)

    # Compute semantic similarity
    similarity = None
    if result["corrected_answer"]:
        similarity = compute_similarity(
            state["base_answer"], result["corrected_answer"]
        )

    step = StepUpdate(
        step=PipelineStep.DEBIAS_AGENT,
        status="complete",
        data={
            "corrected": result["corrected_answer"] is not None,
            "strategy": result["correction_strategy"],
            "similarity": similarity,
        },
    )

    if callback:
        await callback(step)

    return {
        "corrected_answer": result["corrected_answer"],
        "correction_strategy": result["correction_strategy"],
        "semantic_similarity": similarity,
        "steps": state.get("steps", []) + [step.model_dump(mode="json")],
    }


async def post_check_node(state: PipelineState) -> dict:
    """Node 4: Recursive bias check on the debiased output (novel contribution).

    Re-runs the monitor on the corrected answer to verify the debiasing
    didn't introduce new biases.
    """
    callback = state.get("step_callback")

    if not state.get("corrected_answer") or not state.get("enable_recursive_check", True):
        step = StepUpdate(
            step=PipelineStep.POST_CHECK,
            status="complete",
            data={"action": "skipped", "reason": "no corrected answer or check disabled"},
        )
        if callback:
            await callback(step)
        return {
            "residual_bias_report": None,
            "steps": state.get("steps", []) + [step.model_dump(mode="json")],
        }

    if callback:
        await callback(StepUpdate(
            step=PipelineStep.POST_CHECK, status="started"
        ))

    monitor = MonitorAgent()
    report = await monitor.run(
        query=state["query"],
        cot_trace=state.get("corrected_answer", ""),
        answer=state.get("corrected_answer", ""),
    )

    step = StepUpdate(
        step=PipelineStep.POST_CHECK,
        status="complete",
        data={
            "residual_biases_found": report.is_biased,
            "residual_count": len(report.biases_detected),
        },
    )

    if callback:
        await callback(step)

    return {
        "residual_bias_report": report.model_dump(mode="json"),
        "steps": state.get("steps", []) + [step.model_dump(mode="json")],
    }


# ─── Graph Construction ─────────────────────────────────────────────────────

def should_debias(state: PipelineState) -> str:
    """Conditional edge: decide whether to run debiasing."""
    bias_report_data = state.get("bias_report", {})
    if bias_report_data and bias_report_data.get("is_biased", False):
        return "debias"
    return "skip_to_complete"


def build_pipeline() -> StateGraph:
    """Build the ClearMind LangGraph pipeline.

    Graph structure:
        base_agent → monitor_agent → [conditional] → debias_agent → post_check → END
                                         ↘ (no bias) → END
    """
    graph = StateGraph(PipelineState)

    # Add nodes
    graph.add_node("base_agent", base_agent_node)
    graph.add_node("monitor_agent", monitor_agent_node)
    graph.add_node("debias_agent", debias_agent_node)
    graph.add_node("post_check", post_check_node)

    # Set entry point
    graph.set_entry_point("base_agent")

    # Add edges
    graph.add_edge("base_agent", "monitor_agent")

    # Conditional: debias only if biases detected
    graph.add_conditional_edges(
        "monitor_agent",
        should_debias,
        {
            "debias": "debias_agent",
            "skip_to_complete": END,
        },
    )

    graph.add_edge("debias_agent", "post_check")
    graph.add_edge("post_check", END)

    return graph


# Compiled pipeline (reusable)
_pipeline = None


def get_pipeline():
    """Get or create the compiled pipeline."""
    global _pipeline
    if _pipeline is None:
        graph = build_pipeline()
        _pipeline = graph.compile()
    return _pipeline


async def run_pipeline(
    query: str,
    enable_recursive_check: bool = True,
    step_callback=None,
) -> AnalyzeResponse:
    """Run the full ClearMind pipeline on a query.

    Args:
        query: User question to analyze.
        enable_recursive_check: Whether to run post-check on debiased output.
        step_callback: Optional async function called with StepUpdate for streaming.

    Returns:
        Complete AnalyzeResponse with all pipeline results.
    """
    start_time = time.time()
    pipeline = get_pipeline()

    initial_state = {
        "query": query,
        "enable_recursive_check": enable_recursive_check,
        "base_answer": "",
        "cot_trace": "",
        "raw_base_response": "",
        "bias_report": None,
        "corrected_answer": None,
        "correction_strategy": None,
        "residual_bias_report": None,
        "semantic_similarity": None,
        "steps": [],
        "start_time": start_time,
        "step_callback": step_callback,
    }

    # Run the pipeline
    final_state = await pipeline.ainvoke(initial_state)

    elapsed_ms = (time.time() - start_time) * 1000

    # Build response
    bias_report = BiasReport(**(final_state.get("bias_report") or {}))
    residual_report = None
    if final_state.get("residual_bias_report"):
        residual_report = BiasReport(**final_state["residual_bias_report"])

    # Parse steps
    steps = []
    for s in final_state.get("steps", []):
        try:
            steps.append(StepUpdate(**s))
        except Exception:
            pass

    # Complete step
    complete_step = StepUpdate(
        step=PipelineStep.COMPLETE,
        status="complete",
        data={"processing_time_ms": round(elapsed_ms, 2)},
    )
    steps.append(complete_step)

    if step_callback:
        await step_callback(complete_step)

    return AnalyzeResponse(
        query=query,
        base_answer=final_state.get("base_answer", ""),
        cot_trace=final_state.get("cot_trace", ""),
        bias_report=bias_report,
        corrected_answer=final_state.get("corrected_answer"),
        correction_strategy=final_state.get("correction_strategy"),
        residual_bias_report=residual_report,
        semantic_similarity=final_state.get("semantic_similarity"),
        pipeline_steps=steps,
        processing_time_ms=round(elapsed_ms, 2),
    )
