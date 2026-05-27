"""
Unit Tests for Cognitive Bias Detectors

Tests each of the 8 bias detectors with synthetic inputs —
known-biased and known-clean examples.
"""

import pytest
import asyncio


# ─── Confirmation Bias ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_confirmation_bias_detected():
    """Should detect one-sided reasoning without counterarguments."""
    from app.bias.detectors.confirmation import detect

    result = await detect(
        query="Is solar energy the best renewable source?",
        cot_trace=(
            "Step 1: Solar energy is clearly the best option. "
            "Step 2: Research supports that solar is the most efficient. "
            "Step 3: Studies consistently show solar outperforms all alternatives. "
            "Step 4: The data confirms solar is unmatched in benefits. "
            "Step 5: There is no doubt that solar energy leads the field."
        ),
        answer="Solar energy is definitively the best renewable energy source.",
    )
    assert result["detected"] is True
    assert result["confidence"] > 0.4


@pytest.mark.asyncio
async def test_confirmation_bias_not_detected():
    """Should not flag balanced reasoning with counterarguments."""
    from app.bias.detectors.confirmation import detect

    result = await detect(
        query="Is solar energy the best renewable source?",
        cot_trace=(
            "Step 1: Solar energy has many advantages including declining costs. "
            "Step 2: However, wind energy can be more efficient in certain regions. "
            "Step 3: On the other hand, nuclear has higher energy density. "
            "Step 4: Despite solar's benefits, intermittency is a real challenge. "
            "Step 5: Conversely, solar has the advantage of distributed generation."
        ),
        answer="Solar energy is one of the leading options but each source has trade-offs.",
    )
    assert result["detected"] is False


# ─── Anchoring Bias ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_anchoring_bias_detected():
    """Should detect when answer echoes numbers from the query."""
    from app.bias.detectors.anchoring import detect

    result = await detect(
        query="A house was listed at $500,000. What is a fair price?",
        cot_trace="Considering the listing price of $500,000, a fair price would be around that range.",
        answer="A fair price would be approximately $480,000 to $500,000.",
    )
    assert result["detected"] is True
    assert result["confidence"] > 0.3


@pytest.mark.asyncio
async def test_anchoring_no_numbers():
    """Should not flag when query has no numerical anchors."""
    from app.bias.detectors.anchoring import detect

    result = await detect(
        query="What makes a good leader?",
        cot_trace="A good leader inspires others through vision and empathy.",
        answer="Good leaders combine vision, empathy, and decisiveness.",
    )
    assert result["detected"] is False


# ─── Overconfidence ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_overconfidence_detected():
    """Should detect absolute language on contested topic."""
    from app.bias.detectors.overconfidence import detect

    result = await detect(
        query="Is nuclear energy safe?",
        cot_trace=(
            "Nuclear energy is definitely safe. It is absolutely proven "
            "that nuclear is the safest energy source. There is no doubt "
            "about this — it is 100% established fact."
        ),
        answer="Nuclear energy is certainly and undoubtedly the safest energy source.",
    )
    assert result["detected"] is True
    assert result["confidence"] > 0.5


@pytest.mark.asyncio
async def test_overconfidence_not_detected():
    """Should not flag appropriately hedged language."""
    from app.bias.detectors.overconfidence import detect

    result = await detect(
        query="Is nuclear energy safe?",
        cot_trace=(
            "Nuclear energy appears to have a relatively strong safety record. "
            "However, it seems there are debatable aspects regarding waste storage. "
            "The evidence suggests it is likely safer than fossil fuels."
        ),
        answer="Nuclear energy is probably safer than fossil fuels, though waste storage remains uncertain.",
    )
    assert result["detected"] is False


# ─── Bandwagon Effect ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_bandwagon_detected():
    """Should detect appeals to popular opinion."""
    from app.bias.detectors.bandwagon import detect

    result = await detect(
        query="What is the best evidence-based diet?",
        cot_trace=(
            "Most people believe that the Mediterranean diet is best. "
            "Everyone knows that eating healthy is important. "
            "It is widely accepted and the general consensus is clear."
        ),
        answer="The Mediterranean diet is best because most experts agree.",
    )
    assert result["detected"] is True


# ─── Recency Bias ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_recency_detected():
    """Should detect over-citation of recent years on historical topic."""
    from app.bias.detectors.recency import detect

    result = await detect(
        query="What is the history of space exploration?",
        cot_trace=(
            "In 2023, SpaceX launched Starship. "
            "In 2024, Artemis returned to the moon. "
            "In 2025, private space tourism expanded. "
            "In 2026, Mars missions were announced."
        ),
        answer="Space exploration has been dominated by recent achievements.",
    )
    assert result["detected"] is True


@pytest.mark.asyncio
async def test_recency_not_detected():
    """Should not flag balanced temporal citations."""
    from app.bias.detectors.recency import detect

    result = await detect(
        query="What is the history of space exploration?",
        cot_trace=(
            "In 1957, Sputnik was launched. "
            "In 1969, Apollo 11 landed on the moon. "
            "In 2000, the ISS became operational. "
            "In 2024, Artemis missions continued."
        ),
        answer="Space exploration spans from the 1950s to today.",
    )
    assert result["detected"] is False


# ─── Availability Heuristic ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_availability_insufficient_examples():
    """Should return no bias when too few examples exist."""
    from app.bias.detectors.availability import detect

    result = await detect(
        query="What are the risks of flying?",
        cot_trace="Flying is generally safe. The risk is very low.",
        answer="Flying is statistically very safe.",
    )
    assert result["detected"] is False
