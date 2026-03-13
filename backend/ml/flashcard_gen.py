"""
Flashcard Generator for NeuroApp (School Mode)
Generates question/answer flashcard pairs from high-importance transcript segments
using GPT-4o (or Claude as fallback).
"""

import os
import re
import json
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Flashcard:
    question: str
    answer: str
    importance_score: int
    source_text: str
    tags: list[str]


@dataclass
class StudyGuide:
    title: str
    sections: list[dict]     # [{"heading": str, "content": str, "cards": list[Flashcard]}]
    total_cards: int


class FlashcardGenerator:
    """
    Generates flashcards and study guides from high-importance transcript segments.
    Requires an OpenAI API key in OPENAI_API_KEY env var.
    Falls back to rule-based extraction when LLM is unavailable.
    """

    SYSTEM_PROMPT = (
        "You are an expert study aid creator. Given a passage from a lecture or class, "
        "generate a concise flashcard with a clear question on one side and a precise "
        "answer on the other. Output JSON only with keys 'question' and 'answer'."
    )

    QUIZ_SYSTEM_PROMPT = (
        "You are an expert quiz writer. Given a passage from a lecture or class, "
        "generate one multiple-choice question with 4 options (A-D) and indicate the "
        "correct answer. Output JSON with keys: 'question', 'options' (list of 4 strings), "
        "'correct' (index 0-3), 'explanation' (one sentence)."
    )

    def __init__(self, model: str = "gpt-4o", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                logger.warning("openai package not installed. Using rule-based fallback.")
        return self._client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_flashcards(
        self,
        high_importance_segments: list,
        min_score: int = 70,
    ) -> list[Flashcard]:
        """
        Generate one flashcard per high-importance segment.

        Args:
            high_importance_segments: list of segment dicts or SegmentResponse objects
            min_score: only process segments >= this importance score

        Returns:
            List of Flashcard objects
        """
        cards = []
        for seg in high_importance_segments:
            score = _get_score(seg)
            text = _get_text(seg)
            if score < min_score or len(text.strip()) < 20:
                continue
            card = self._make_flashcard(text, score)
            if card:
                cards.append(card)
        return cards

    def generate_quiz(self, segments: list, n_questions: int = 5) -> list[dict]:
        """Generate multiple-choice quiz questions from segments."""
        top = sorted(segments, key=lambda s: -_get_score(s))[:n_questions]
        questions = []
        for seg in top:
            text = _get_text(seg)
            if len(text.strip()) < 20:
                continue
            q = self._make_quiz_question(text)
            if q:
                questions.append(q)
        return questions

    def generate_study_guide(
        self,
        segments: list,
        title: str = "Study Guide",
    ) -> StudyGuide:
        """Build a structured study guide from all segments."""
        # Sort by time, then bucket by importance
        sorted_segs = sorted(segments, key=lambda s: _get_start(s))
        high = [s for s in sorted_segs if _get_score(s) >= 70]
        medium = [s for s in sorted_segs if 40 <= _get_score(s) < 70]

        sections = []
        if high:
            cards = self.generate_flashcards(high, min_score=70)
            sections.append({
                "heading": "Key Concepts (High Importance)",
                "content": " ".join(_get_text(s) for s in high[:5]),
                "cards": cards,
            })
        if medium:
            cards = self.generate_flashcards(medium, min_score=40)
            sections.append({
                "heading": "Supporting Concepts (Medium Importance)",
                "content": " ".join(_get_text(s) for s in medium[:5]),
                "cards": cards,
            })

        total = sum(len(sec["cards"]) for sec in sections)
        return StudyGuide(title=title, sections=sections, total_cards=total)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _make_flashcard(self, text: str, score: int) -> Optional[Flashcard]:
        client = self._get_client()
        tags = _extract_tags(text)

        if client:
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": f"Passage: {text}"},
                    ],
                    temperature=0.3,
                    max_tokens=200,
                    response_format={"type": "json_object"},
                )
                data = json.loads(response.choices[0].message.content)
                return Flashcard(
                    question=data.get("question", ""),
                    answer=data.get("answer", ""),
                    importance_score=score,
                    source_text=text,
                    tags=tags,
                )
            except Exception as exc:
                logger.warning(f"LLM flashcard generation failed: {exc}. Using fallback.")

        # Rule-based fallback
        return self._rule_based_card(text, score, tags)

    def _make_quiz_question(self, text: str) -> Optional[dict]:
        client = self._get_client()
        if client:
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.QUIZ_SYSTEM_PROMPT},
                        {"role": "user", "content": f"Passage: {text}"},
                    ],
                    temperature=0.4,
                    max_tokens=300,
                    response_format={"type": "json_object"},
                )
                return json.loads(response.choices[0].message.content)
            except Exception as exc:
                logger.warning(f"LLM quiz generation failed: {exc}")
        return None

    @staticmethod
    def _rule_based_card(text: str, score: int, tags: list[str]) -> Flashcard:
        """Very simple rule-based fallback: turn the first sentence into Q&A."""
        sentences = re.split(r"[.!?]", text.strip())
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        if not sentences:
            return Flashcard(
                question="What is the key point?",
                answer=text[:200],
                importance_score=score,
                source_text=text,
                tags=tags,
            )

        first = sentences[0]
        # Remove common filler starts
        question = re.sub(r"^(so|now|basically|essentially|remember that)\s+", "", first, flags=re.I)
        question = question[0].upper() + question[1:] if question else first
        answer = ". ".join(sentences[1:3]) if len(sentences) > 1 else first

        return Flashcard(
            question=f"What does the following mean: '{question[:100]}'?",
            answer=answer[:300],
            importance_score=score,
            source_text=text,
            tags=tags,
        )


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


def _get_start(seg) -> float:
    if isinstance(seg, dict):
        return seg.get("start_time", 0.0)
    return getattr(seg, "start_time", 0.0)


def _extract_tags(text: str) -> list[str]:
    """Extract likely topic tags from text."""
    # Capitalize proper nouns / long words as tags
    words = re.findall(r"\b[A-Z][a-z]{3,}\b", text)
    return list(dict.fromkeys(words))[:5]


# ------------------------------------------------------------------
# Demo
# ------------------------------------------------------------------

def demo():
    print("=== FlashcardGenerator Demo ===\n")
    gen = FlashcardGenerator()

    segments = [
        {"text": "The mitochondria is the powerhouse of the cell and produces ATP through oxidative phosphorylation.", "importance_score": 88, "start_time": 10.0},
        {"text": "Remember, the exam will definitely cover the Krebs cycle and electron transport chain.", "importance_score": 95, "start_time": 45.0},
        {"text": "So yeah, anyway, moving on.", "importance_score": 15, "start_time": 60.0},
        {"text": "Action potential propagation requires sodium-potassium pumps maintaining the resting membrane potential.", "importance_score": 72, "start_time": 90.0},
    ]

    cards = gen.generate_flashcards(segments)
    print(f"Generated {len(cards)} flashcards:\n")
    for i, card in enumerate(cards, 1):
        print(f"Card {i} (score={card.importance_score}):")
        print(f"  Q: {card.question}")
        print(f"  A: {card.answer[:100]}...")
        print(f"  Tags: {card.tags}\n")


if __name__ == "__main__":
    demo()
