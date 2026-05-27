"""
ClearMind Text Utilities

Text cleaning, tokenization helpers, hedging language detection,
and temporal reference extraction used across bias detectors.
"""

import re
from typing import Optional


# ─── Hedging / Certainty Language ────────────────────────────────────────────

HEDGING_WORDS = {
    "maybe", "perhaps", "possibly", "might", "could", "may",
    "seems", "appears", "likely", "unlikely", "probably",
    "suggest", "suggests", "indicate", "indicates",
    "approximately", "roughly", "around", "about",
    "uncertain", "unclear", "debatable", "arguably",
    "it depends", "in some cases", "to some extent",
}

ABSOLUTE_WORDS = {
    "definitely", "certainly", "absolutely", "always", "never",
    "undoubtedly", "unquestionably", "without a doubt",
    "100%", "guaranteed", "proven", "fact", "obvious",
    "clearly", "everyone knows", "it is certain",
    "there is no question", "beyond doubt", "indisputable",
    "no doubt", "inevitably", "invariably",
}

CONSENSUS_PHRASES = [
    "most people", "everyone knows", "widely believed",
    "widely accepted", "popular opinion", "mainstream view",
    "experts agree", "common knowledge", "general consensus",
    "it is well known", "universally accepted",
    "the majority", "most experts", "conventional wisdom",
    "broadly speaking", "it goes without saying",
]

# ─── Contested Topics ───────────────────────────────────────────────────────

CONTESTED_TOPICS = [
    "climate change", "global warming", "gun control",
    "abortion", "death penalty", "immigration policy",
    "nuclear energy", "gmo", "genetic modification",
    "artificial intelligence safety", "cryptocurrency",
    "universal basic income", "minimum wage",
    "vaccine", "vaccination", "alternative medicine",
    "religion", "god", "evolution vs creationism",
    "socialism", "capitalism", "communism",
    "free will", "consciousness", "simulation theory",
    "diet", "keto", "vegan", "intermittent fasting",
    "political correctness", "censorship",
    "space exploration funding", "military spending",
]


def clean_text(text: str) -> str:
    """Remove extra whitespace and normalize text."""
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_sentences(text: str) -> list[str]:
    """Split text into sentences using regex-based heuristic."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def count_hedging_words(text: str) -> dict:
    """Count hedging vs absolute language in text.

    Returns dict with 'hedging_count', 'absolute_count', 'hedging_ratio'.
    """
    text_lower = text.lower()
    words = text_lower.split()

    hedging_count = sum(1 for w in HEDGING_WORDS if w in text_lower)
    absolute_count = sum(1 for w in ABSOLUTE_WORDS if w in text_lower)

    total = hedging_count + absolute_count
    hedging_ratio = hedging_count / total if total > 0 else 0.5

    return {
        "hedging_count": hedging_count,
        "absolute_count": absolute_count,
        "hedging_ratio": hedging_ratio,
        "certainty_score": 1.0 - hedging_ratio,
    }


def detect_consensus_language(text: str) -> list[str]:
    """Find consensus/bandwagon phrases in text."""
    text_lower = text.lower()
    found = [phrase for phrase in CONSENSUS_PHRASES if phrase in text_lower]
    return found


def is_contested_topic(text: str) -> bool:
    """Check if the text relates to a known contested topic."""
    text_lower = text.lower()
    return any(topic in text_lower for topic in CONTESTED_TOPICS)


def extract_numbers(text: str) -> list[str]:
    """Extract all numerical values from text using regex."""
    pattern = r'\b\d+(?:,\d{3})*(?:\.\d+)?%?\b'
    numbers = re.findall(pattern, text)
    return numbers


def detect_temporal_references(text: str) -> dict:
    """Detect year references and categorize as recent vs historical.

    Returns dict with 'years_found', 'recent_count', 'historical_count', 'recency_ratio'.
    """
    year_pattern = r'\b(1[0-9]{3}|20[0-2][0-9])\b'
    years = [int(y) for y in re.findall(year_pattern, text)]

    if not years:
        return {
            "years_found": [],
            "recent_count": 0,
            "historical_count": 0,
            "recency_ratio": 0.0,
        }

    current_year = 2026
    recent_threshold = current_year - 5  # Last 5 years

    recent = [y for y in years if y >= recent_threshold]
    historical = [y for y in years if y < recent_threshold]

    return {
        "years_found": sorted(set(years)),
        "recent_count": len(recent),
        "historical_count": len(historical),
        "recency_ratio": len(recent) / len(years) if years else 0.0,
    }
