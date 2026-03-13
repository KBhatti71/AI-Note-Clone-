"""
Action Item Extractor for NeuroApp (Work Mode)
Extracts action items, decisions, and blockers from meeting transcripts.
"""

import os
import re
import json
import logging
from dataclasses import dataclass, field
from typing import Optional
from datetime import date

logger = logging.getLogger(__name__)


@dataclass
class ActionItem:
    task: str
    owner: str
    deadline: Optional[str]    # ISO date string or None
    priority: str              # HIGH / MEDIUM / LOW
    source_text: str
    importance_score: int


@dataclass
class Decision:
    what: str
    when: str
    who_agreed: list[str]
    source_text: str
    importance_score: int


@dataclass
class Blocker:
    description: str
    blocking_what: str
    raised_by: str
    source_text: str
    importance_score: int


@dataclass
class WorkSummary:
    action_items: list[ActionItem] = field(default_factory=list)
    decisions: list[Decision] = field(default_factory=list)
    blockers: list[Blocker] = field(default_factory=list)
    high_priority_count: int = 0


class ActionExtractor:
    """
    Extracts structured work artifacts from meeting segments.
    Uses GPT-4o when available; falls back to regex pattern matching.
    """

    SYSTEM_PROMPT = (
        "You are an expert meeting analyst. Given a transcript segment from a work meeting, "
        "extract any action items, decisions, or blockers. "
        "Return JSON with keys: "
        "'action_items' (list of {task, owner, deadline, priority}), "
        "'decisions' (list of {what, when, who_agreed}), "
        "'blockers' (list of {description, blocking_what, raised_by}). "
        "Use null for unknown values. Priority: HIGH/MEDIUM/LOW."
    )

    # Commitment patterns (indicates an action item)
    COMMITMENT_PATTERNS = [
        r"\b(i will|i'll|i'm going to|i need to|i should)\b",
        r"\b(we will|we'll|we're going to|we need to)\b",
        r"\b(you will|you'll|please|make sure|ensure|don't forget)\b",
        r"\b(action item|todo|to-do|follow up|follow-up)\b",
        r"\b(by (monday|tuesday|wednesday|thursday|friday|eod|tomorrow|next week))\b",
        r"\b(will (send|update|create|review|fix|add|check|schedule|call|email))\b",
    ]

    DECISION_PATTERNS = [
        r"\b(we decided|we agreed|decision is|we're going with|let's go with)\b",
        r"\b(approved|rejected|signed off|confirmed|finalized)\b",
        r"\b(the answer is|we'll use|we won't|we're not going to)\b",
    ]

    BLOCKER_PATTERNS = [
        r"\b(blocked|blocking|blocker|can't proceed|waiting on|dependency)\b",
        r"\b(stuck|issue|problem|obstacle|impediment)\b",
        r"\b(need.{1,30}before|waiting for|depends on|requires.{1,30}first)\b",
    ]

    DATE_PATTERNS = {
        "today": 0, "tomorrow": 1, "eod": 0,
        "monday": None, "tuesday": None, "wednesday": None,
        "thursday": None, "friday": None,
        "next week": 7, "end of week": 4, "eow": 4,
    }

    def __init__(self, model: str = "gpt-4o", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._client = None
        self._compiled = {
            "commitment": [re.compile(p, re.I) for p in self.COMMITMENT_PATTERNS],
            "decision": [re.compile(p, re.I) for p in self.DECISION_PATTERNS],
            "blocker": [re.compile(p, re.I) for p in self.BLOCKER_PATTERNS],
        }

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                logger.warning("openai not installed. Using pattern-matching fallback.")
        return self._client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_action_items(self, segments: list) -> list[ActionItem]:
        """Extract action items from HIGH/MEDIUM importance segments."""
        items = []
        for seg in segments:
            score = _get_score(seg)
            if score < 40:
                continue
            text = _get_text(seg)
            speaker = _get_speaker(seg)
            if self._matches_any(text, "commitment"):
                item = self._extract_single_action(text, speaker, score)
                if item:
                    items.append(item)
        return items

    def extract_decisions(self, segments: list) -> list[Decision]:
        """Extract decisions from segments."""
        decisions = []
        for seg in segments:
            text = _get_text(seg)
            score = _get_score(seg)
            if score < 50:
                continue
            if self._matches_any(text, "decision"):
                d = self._extract_single_decision(text, score)
                if d:
                    decisions.append(d)
        return decisions

    def extract_blockers(self, segments: list) -> list[Blocker]:
        """Extract blockers/impediments from segments."""
        blockers = []
        for seg in segments:
            text = _get_text(seg)
            score = _get_score(seg)
            if self._matches_any(text, "blocker"):
                b = self._extract_single_blocker(text, _get_speaker(seg), score)
                if b:
                    blockers.append(b)
        return blockers

    def extract_all(self, segments: list) -> WorkSummary:
        """Run full extraction and return a WorkSummary."""
        client = self._get_client()
        if client:
            return self._llm_extract_all(segments, client)

        summary = WorkSummary(
            action_items=self.extract_action_items(segments),
            decisions=self.extract_decisions(segments),
            blockers=self.extract_blockers(segments),
        )
        summary.high_priority_count = sum(
            1 for a in summary.action_items if a.priority == "HIGH"
        )
        return summary

    # ------------------------------------------------------------------
    # LLM extraction
    # ------------------------------------------------------------------

    def _llm_extract_all(self, segments: list, client) -> WorkSummary:
        high_segs = [s for s in segments if _get_score(s) >= 60]
        if not high_segs:
            return WorkSummary()

        full_text = "\n".join(
            f"[{_get_score(s)}/100] {_get_text(s)}" for s in high_segs[:20]
        )

        try:
            resp = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": full_text},
                ],
                temperature=0.2,
                max_tokens=1000,
                response_format={"type": "json_object"},
            )
            data = json.loads(resp.choices[0].message.content)
        except Exception as exc:
            logger.warning(f"LLM extraction failed: {exc}. Falling back to patterns.")
            return WorkSummary(
                action_items=self.extract_action_items(segments),
                decisions=self.extract_decisions(segments),
                blockers=self.extract_blockers(segments),
            )

        actions = [
            ActionItem(
                task=a.get("task", ""),
                owner=a.get("owner") or "TBD",
                deadline=a.get("deadline"),
                priority=a.get("priority", "MEDIUM"),
                source_text="",
                importance_score=80,
            )
            for a in data.get("action_items", [])
            if a.get("task")
        ]
        decisions = [
            Decision(
                what=d.get("what", ""),
                when=d.get("when") or "TBD",
                who_agreed=d.get("who_agreed") or [],
                source_text="",
                importance_score=80,
            )
            for d in data.get("decisions", [])
            if d.get("what")
        ]
        blockers = [
            Blocker(
                description=b.get("description", ""),
                blocking_what=b.get("blocking_what") or "Unknown",
                raised_by=b.get("raised_by") or "Unknown",
                source_text="",
                importance_score=70,
            )
            for b in data.get("blockers", [])
            if b.get("description")
        ]

        summary = WorkSummary(
            action_items=actions,
            decisions=decisions,
            blockers=blockers,
        )
        summary.high_priority_count = sum(1 for a in actions if a.priority == "HIGH")
        return summary

    # ------------------------------------------------------------------
    # Pattern-based fallbacks
    # ------------------------------------------------------------------

    def _extract_single_action(
        self, text: str, speaker: str, score: int
    ) -> Optional[ActionItem]:
        task = self._clean_task(text)
        if not task:
            return None
        deadline = self._extract_deadline(text)
        priority = "HIGH" if score >= 70 else "MEDIUM" if score >= 40 else "LOW"
        return ActionItem(
            task=task,
            owner=speaker or "TBD",
            deadline=deadline,
            priority=priority,
            source_text=text,
            importance_score=score,
        )

    def _extract_single_decision(self, text: str, score: int) -> Optional[Decision]:
        # Find the part after the decision signal
        for pattern in self._compiled["decision"]:
            m = pattern.search(text)
            if m:
                what = text[m.end():].strip()[:200]
                return Decision(
                    what=what or text[:200],
                    when=self._extract_deadline(text) or "This meeting",
                    who_agreed=[],
                    source_text=text,
                    importance_score=score,
                )
        return None

    def _extract_single_blocker(
        self, text: str, speaker: str, score: int
    ) -> Optional[Blocker]:
        return Blocker(
            description=text[:200],
            blocking_what="Unknown",
            raised_by=speaker or "Unknown",
            source_text=text,
            importance_score=score,
        )

    def _matches_any(self, text: str, category: str) -> bool:
        return any(p.search(text) for p in self._compiled[category])

    @staticmethod
    def _clean_task(text: str) -> str:
        # Remove filler preamble
        text = re.sub(r"^(so|yeah|ok|okay|right|well|um|uh)[,\s]+", "", text, flags=re.I)
        # Truncate at sentence boundary
        sentences = re.split(r"[.!?]", text)
        return sentences[0].strip()[:200] if sentences else ""

    @staticmethod
    def _extract_deadline(text: str) -> Optional[str]:
        # Look for "by <day>" or "by <date>"
        m = re.search(
            r"\bby\s+(monday|tuesday|wednesday|thursday|friday|eod|eow|tomorrow|next week|\d{1,2}/\d{1,2})\b",
            text, re.I
        )
        if m:
            return m.group(1).capitalize()
        return None


# ------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------

def _get_score(seg) -> int:
    if isinstance(seg, dict):
        return seg.get("importance_score", 0)
    return getattr(seg, "importance_score", 0)


def _get_text(seg) -> str:
    if isinstance(seg, dict):
        return seg.get("text", "")
    return getattr(seg, "text", "")


def _get_speaker(seg) -> str:
    if isinstance(seg, dict):
        return seg.get("speaker", "")
    return getattr(seg, "speaker", "")


# ------------------------------------------------------------------
# Demo
# ------------------------------------------------------------------

def demo():
    print("=== ActionExtractor Demo ===\n")
    extractor = ActionExtractor()

    segments = [
        {"text": "I'll send the updated spec to the team by Friday.", "importance_score": 85, "speaker": "Alice"},
        {"text": "We decided to go with PostgreSQL over MySQL for the new service.", "importance_score": 92, "speaker": "Bob"},
        {"text": "We're blocked on the API credentials — can't proceed until DevOps provides them.", "importance_score": 88, "speaker": "Charlie"},
        {"text": "Make sure to update the Jira tickets before end of day.", "importance_score": 75, "speaker": "Alice"},
        {"text": "Yeah so anyway the weather was nice.", "importance_score": 12, "speaker": "Bob"},
    ]

    summary = extractor.extract_all(segments)

    print(f"Action Items ({len(summary.action_items)}):")
    for item in summary.action_items:
        print(f"  [{item.priority}] {item.task[:80]} — owner: {item.owner}, due: {item.deadline}")

    print(f"\nDecisions ({len(summary.decisions)}):")
    for d in summary.decisions:
        print(f"  {d.what[:80]}")

    print(f"\nBlockers ({len(summary.blockers)}):")
    for b in summary.blockers:
        print(f"  {b.description[:80]} (raised by {b.raised_by})")


if __name__ == "__main__":
    demo()
