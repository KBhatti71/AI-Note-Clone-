import re
from typing import Any, Dict, List


def _split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _extract_action_items(sentences: List[str]) -> List[str]:
    patterns = [
        r"\bneed to\b",
        r"\bshould\b",
        r"\bmust\b",
        r"\baction item\b",
        r"\bdeadline\b",
        r"\bdue\b",
        r"\btodo\b",
    ]
    items = []
    for s in sentences:
        if any(re.search(p, s, re.IGNORECASE) for p in patterns):
            items.append(s)
    return items


def generate_notes(transcript: str, scored_segments: List[Dict[str, Any]], context: str) -> Dict[str, Any]:
    sentences = _split_sentences(transcript)

    scored_sorted = sorted(scored_segments, key=lambda s: float(s.get("score", 0)), reverse=True)
    key_points = [s.get("text", "") for s in scored_sorted[:5] if s.get("text")]

    summary_candidates = [s.get("text", "") for s in scored_sorted[:3] if s.get("text")]
    if not summary_candidates:
        summary_candidates = sentences[:3]

    action_items = _extract_action_items(sentences)
    questions = [s for s in sentences if s.endswith("?")]

    title = {
        "school": "Class Notes",
        "work": "Meeting Notes",
        "general": "Notes",
    }.get(context, "Notes")

    return {
        "title": title,
        "summary": summary_candidates,
        "key_points": key_points,
        "action_items": action_items,
        "questions": questions,
    }

