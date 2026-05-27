"""
ClearMind Debias Agent

Takes the original query plus detected biases and applies bias-specific
correction strategies. Re-queries Gemini with a corrected prompt approach
to produce a debiased answer.

Key design: each bias type maps to a specific correction prompt template,
ensuring targeted rather than generic debiasing.
"""

import logging
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import get_settings
from app.models.schemas import BiasReport, BiasType

logger = logging.getLogger("clearmind.agents.debias")


# ─── Bias-Specific Correction Templates ─────────────────────────────────────

CORRECTION_TEMPLATES = {
    BiasType.CONFIRMATION: """The previous answer showed confirmation bias — it only cited evidence supporting one side.

INSTRUCTIONS: Answer the following question by FIRST listing at least 2-3 counterarguments or opposing evidence, THEN listing supporting evidence, and FINALLY reaching a balanced conclusion that weighs both sides fairly.

Question: {query}""",

    BiasType.ANCHORING: """The previous answer was influenced by specific numbers mentioned in the question (anchoring bias).

INSTRUCTIONS: Answer the following question while IGNORING any specific numbers or values mentioned. Base your answer purely on the underlying factual question, not on any numerical anchors provided.

Question: {query}""",

    BiasType.AVAILABILITY: """The previous answer relied on dramatic or commonly cited examples rather than representative ones (availability heuristic).

INSTRUCTIONS: Answer the following question using STATISTICALLY REPRESENTATIVE examples, not just the most memorable or dramatic ones. Cite diverse evidence from multiple sources or contexts.

Question: {query}""",

    BiasType.SYCOPHANCY: """The previous answer appeared to agree with the implied stance in the question rather than providing an objective analysis (sycophancy).

INSTRUCTIONS: Answer the following question with COMPLETE OBJECTIVITY. Present evidence from BOTH sides neutrally, regardless of what the question implies or what stance the asker seems to hold. Reach your conclusion based purely on evidence.

Question: {query}""",

    BiasType.OVERCONFIDENCE: """The previous answer expressed too much certainty on a topic where uncertainty is warranted (overconfidence).

INSTRUCTIONS: Answer the following question while being EXPLICITLY honest about uncertainty. Use appropriate hedging language (e.g., "likely", "evidence suggests", "approximately"). Quantify your confidence level where possible. Acknowledge what is unknown or debated.

Question: {query}""",

    BiasType.FRAMING: """The previous answer was influenced by how the question was framed rather than the underlying facts (framing effect).

INSTRUCTIONS: First, identify the framing in the question below. Then, rephrase the core question in NEUTRAL terms and answer the neutrally-framed version. Ensure your answer would be the same regardless of positive or negative framing.

Question: {query}""",

    BiasType.RECENCY: """The previous answer disproportionately emphasized recent events while neglecting historical context (recency bias).

INSTRUCTIONS: Answer the following question by considering evidence PROPORTIONALLY across all relevant time periods. Do not overweight recent events just because they are more available. Include historical context and long-term trends.

Question: {query}""",

    BiasType.BANDWAGON: """The previous answer appealed to popular opinion rather than evidence (bandwagon effect).

INSTRUCTIONS: Answer the following question by citing SPECIFIC EVIDENCE rather than popular consensus. Avoid phrases like "most people believe" or "it is widely accepted". Instead, reference specific studies, data, or logical arguments.

Question: {query}""",
}


DEBIAS_SYSTEM_PROMPT = """You are a careful, unbiased AI assistant. A previous version of your answer was found to contain cognitive biases. You must now provide a CORRECTED answer following the specific debiasing instructions given.

RULES:
1. Follow the debiasing instructions precisely
2. Show your reasoning step by step
3. Be balanced, evidence-based, and appropriately uncertain
4. Do not introduce new biases in your correction
5. Format your response as:

### Corrected Reasoning:
[Step-by-step corrected reasoning]

### Corrected Answer:
[Your debiased answer]"""


class DebiasAgent:
    """Debiasing agent that applies bias-specific correction strategies."""

    def __init__(self, model: Optional[ChatGoogleGenerativeAI] = None):
        settings = get_settings()
        self.model = model or ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.google_api_key,
            temperature=0.4,  # Lower temp for more careful corrections
            max_output_tokens=settings.gemini_max_tokens,
        )

    async def run(
        self,
        query: str,
        bias_report: BiasReport,
    ) -> dict:
        """Generate a debiased answer using bias-specific correction strategies.

        Args:
            query: Original user question.
            bias_report: BiasReport from the monitor agent.

        Returns:
            Dict with 'corrected_answer', 'correction_strategy', 'raw_response'.
        """
        if not bias_report.is_biased:
            return {
                "corrected_answer": None,
                "correction_strategy": "No correction needed — no biases detected",
                "raw_response": "",
            }

        # Get the highest-confidence bias for primary correction strategy
        primary_bias = bias_report.biases_detected[0]
        template = CORRECTION_TEMPLATES.get(primary_bias.bias_type)

        if template is None:
            logger.warning(f"No correction template for bias: {primary_bias.bias_type}")
            template = CORRECTION_TEMPLATES[BiasType.CONFIRMATION]  # Fallback

        # Build correction prompt
        correction_prompt = template.format(query=query)

        # Add info about other detected biases
        if len(bias_report.biases_detected) > 1:
            other_biases = [
                f"- {b.bias_type.value} (confidence: {b.confidence:.2f})"
                for b in bias_report.biases_detected[1:]
            ]
            correction_prompt += (
                f"\n\nADDITIONAL BIASES TO AVOID:\n"
                + "\n".join(other_biases)
            )

        try:
            messages = [
                SystemMessage(content=DEBIAS_SYSTEM_PROMPT),
                HumanMessage(content=correction_prompt),
            ]

            response = await self.model.ainvoke(messages)
            raw = response.content.strip()

            # Parse corrected answer
            corrected_answer = self._parse_corrected(raw)

            strategy = (
                f"Applied {primary_bias.bias_type.value} correction strategy "
                f"(primary bias confidence: {primary_bias.confidence:.2f})"
            )

            logger.info(f"Debias agent corrected for: {primary_bias.bias_type.value}")

            return {
                "corrected_answer": corrected_answer,
                "correction_strategy": strategy,
                "raw_response": raw,
            }

        except Exception as e:
            logger.error(f"Debias agent failed: {e}")
            return {
                "corrected_answer": None,
                "correction_strategy": f"Correction failed: {str(e)}",
                "raw_response": "",
            }

    def _parse_corrected(self, raw: str) -> str:
        """Extract the corrected answer from the debiased response."""
        if "### Corrected Answer:" in raw:
            return raw.split("### Corrected Answer:", 1)[1].strip()
        elif "**Corrected Answer:**" in raw:
            return raw.split("**Corrected Answer:**", 1)[1].strip()
        elif "Corrected Answer:" in raw:
            return raw.split("Corrected Answer:", 1)[1].strip()
        return raw
