"""
ClearMind Base Agent

The primary LLM agent that takes a user query and returns an answer
plus a full Chain-of-Thought (CoT) reasoning trace.

Uses Gemini 2.0 Flash with a system prompt that forces step-by-step
reasoning. The CoT trace is critical — it's what the monitor agent
analyzes for cognitive biases.
"""

import logging
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import get_settings

logger = logging.getLogger("clearmind.agents.base")


COT_SYSTEM_PROMPT = """You are a knowledgeable AI assistant. For every question you receive, you MUST think through your answer step by step before giving your final response.

## MANDATORY FORMAT:

### Reasoning:
Step 1: [Your first reasoning step]
Step 2: [Your second reasoning step]
Step 3: [Continue as needed...]
...

### Answer:
[Your final, clear answer based on the reasoning above]

## RULES:
1. ALWAYS show your complete reasoning process — every assumption, every piece of evidence you consider
2. Be thorough in your reasoning — consider multiple angles
3. If you are uncertain about something, explicitly state your uncertainty
4. Do not skip steps — the reasoning trace must be complete
5. Cite specific evidence or knowledge when making claims
6. Consider potential counterarguments when relevant"""


class BaseAgent:
    """Base LLM agent with Chain-of-Thought reasoning."""

    def __init__(self, model: Optional[ChatGoogleGenerativeAI] = None):
        settings = get_settings()
        self.model = model or ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.google_api_key,
            temperature=settings.gemini_temperature,
            max_output_tokens=settings.gemini_max_tokens,
        )

    async def run(self, query: str) -> dict:
        """Process a query and return answer with CoT trace.

        Args:
            query: The user's question.

        Returns:
            Dict with 'answer', 'cot_trace', 'raw_response'.
        """
        try:
            messages = [
                SystemMessage(content=COT_SYSTEM_PROMPT),
                HumanMessage(content=query),
            ]

            response = await self.model.ainvoke(messages)
            raw = response.content.strip()

            # Parse CoT trace and answer
            cot_trace, answer = self._parse_response(raw)

            logger.info(f"Base agent processed query: '{query[:60]}...'")

            return {
                "answer": answer,
                "cot_trace": cot_trace,
                "raw_response": raw,
            }

        except Exception as e:
            logger.error(f"Base agent failed: {e}")
            return {
                "answer": f"Error: {str(e)}",
                "cot_trace": "",
                "raw_response": "",
            }

    def _parse_response(self, raw: str) -> tuple[str, str]:
        """Parse the raw LLM response into CoT trace and final answer.

        Returns:
            Tuple of (cot_trace, answer).
        """
        # Try to split on ### Answer: marker
        if "### Answer:" in raw:
            parts = raw.split("### Answer:", 1)
            cot_trace = parts[0].replace("### Reasoning:", "").strip()
            answer = parts[1].strip()
        elif "**Answer:**" in raw:
            parts = raw.split("**Answer:**", 1)
            cot_trace = parts[0].strip()
            answer = parts[1].strip()
        elif "Answer:" in raw:
            parts = raw.split("Answer:", 1)
            cot_trace = parts[0].strip()
            answer = parts[1].strip()
        else:
            # Fallback: treat entire response as both trace and answer
            cot_trace = raw
            answer = raw

        return cot_trace, answer


async def run_base_agent(query: str) -> dict:
    """Convenience function for running the base agent."""
    agent = BaseAgent()
    return await agent.run(query)
