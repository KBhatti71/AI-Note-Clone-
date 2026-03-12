"""
NeuroApp - Importance Scorer
Combines prosody, emotion, keywords, and context to score segment importance.
"""

import re
import numpy as np
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class Context(Enum):
    """Context mode for the conversation."""
    SCHOOL = "school"
    WORK = "work"
    GENERAL = "general"


@dataclass
class TranscriptSegment:
    """A segment of transcript with timing information."""
    text: str
    start_time: float
    end_time: float
    speaker: Optional[str] = None


class ImportanceScorer:
    """
    Scores transcript segments for importance (0-100).
    
    Combines multiple signals:
    - Prosody features (30%)
    - Emotion detection (15%)
    - Keyword matching (20%)
    - Repetition patterns (20%)
    - Context signals (15%)
    """
    
    # Context-specific keywords
    KEYWORDS = {
        Context.SCHOOL: {
            'critical': ['exam', 'test', 'quiz', 'midterm', 'final', 'important', 
                        'remember', 'key concept', 'fundamental', 'will be on'],
            'high': ['understand', 'practice', 'study', 'review', 'homework',
                    'assignment', 'due', 'definition', 'theorem'],
            'medium': ['example', 'for instance', 'notice', 'observe', 'think about']
        },
        Context.WORK: {
            'critical': ['deadline', 'critical', 'urgent', 'blocker', 'decision',
                        'must', 'need to', 'action item', 'committed'],
            'high': ['should', 'recommend', 'suggest', 'concern', 'issue',
                    'risk', 'follow up', 'next steps'],
            'medium': ['update', 'status', 'progress', 'discuss', 'consider']
        },
        Context.GENERAL: {
            'critical': ['important', 'critical', 'remember', 'key point'],
            'high': ['note', 'mention', 'emphasize', 'highlight'],
            'medium': ['think', 'consider', 'maybe', 'perhaps']
        }
    }
    
    def __init__(self, context: Context = Context.GENERAL):
        """
        Initialize importance scorer.
        
        Args:
            context: Context mode (school, work, or general)
        """
        self.context = context
        self.keyword_weights = {
            'critical': 20,
            'high': 10,
            'medium': 5
        }
    
    def score_segment(
        self,
        transcript: TranscriptSegment,
        prosody_features: Dict[str, float],
        emotion_result: Optional[Dict] = None,
        user_highlighted: bool = False,
        window_transcripts: Optional[List[TranscriptSegment]] = None
    ) -> Dict[str, Any]:
        """
        Calculate importance score for a transcript segment.
        
        Args:
            transcript: Transcript segment with text and timing
            prosody_features: Features from ProsodyAnalyzer
            emotion_result: Result from EmotionDetector (optional)
            user_highlighted: Whether user manually flagged this
            window_transcripts: Recent segments for context (for repetition detection)
            
        Returns:
            Dictionary with score and breakdown
        """
        scores = {}
        
        # 1. Vocal Emphasis (30 points max)
        vocal_score = min(30, prosody_features.get('vocal_emphasis_score', 0) * 0.3)
        scores['vocal_emphasis'] = vocal_score
        
        # 2. Keyword Matching (20 points max)
        keyword_score = self._score_keywords(transcript.text)
        scores['keywords'] = keyword_score
        
        # 3. Repetition Patterns (20 points max)
        repetition_score = 0
        if window_transcripts:
            repetition_score = self._score_repetition(transcript, window_transcripts)
        scores['repetition'] = repetition_score
        
        # 4. Emotion Signals (15 points max)
        emotion_score = 0
        if emotion_result:
            emotion_score = min(15, emotion_result.get('importance_boost', 0))
        scores['emotion'] = emotion_score
        
        # 5. Context-Specific Signals (15 points max)
        context_score = self._score_context_signals(
            transcript, prosody_features
        )
        scores['context'] = context_score
        
        # User manual highlights get bonus
        if user_highlighted:
            scores['user_highlight'] = 15
        
        # Total score
        total = sum(scores.values())
        total = min(100, total)  # Cap at 100
        
        # Determine importance level
        if total >= 70:
            level = "HIGH"
            stars = "⭐⭐⭐"
        elif total >= 40:
            level = "MEDIUM"
            stars = "⭐⭐"
        else:
            level = "LOW"
            stars = "⭐"
        
        return {
            'score': total,
            'level': level,
            'stars': stars,
            'breakdown': scores,
            'text': transcript.text,
            'timestamp': transcript.start_time,
            'duration': transcript.end_time - transcript.start_time
        }
    
    def _score_keywords(self, text: str) -> float:
        """
        Score text based on keyword matching.
        
        Returns:
            Keyword score (0-20)
        """
        text_lower = text.lower()
        score = 0
        
        keywords = self.KEYWORDS[self.context]
        
        # Check each keyword category
        for category, keyword_list in keywords.items():
            for keyword in keyword_list:
                if keyword in text_lower:
                    score += self.keyword_weights[category]
        
        return min(20, score)
    
    def _score_repetition(
        self,
        segment: TranscriptSegment,
        window: List[TranscriptSegment],
        max_window: int = 5
    ) -> float:
        """
        Score based on repetition of similar phrases.
        If something is said multiple times, it's important.
        
        Returns:
            Repetition score (0-20)
        """
        # Use last N segments for context
        recent = window[-max_window:] if len(window) > max_window else window
        
        # Extract key phrases (3+ word sequences)
        current_phrases = self._extract_phrases(segment.text, min_words=3)
        
        # Count how many times similar phrases appear
        repetition_count = 0
        for other in recent:
            if other.text == segment.text:
                continue
            
            other_phrases = self._extract_phrases(other.text, min_words=3)
            
            # Check for overlaps
            for phrase in current_phrases:
                for other_phrase in other_phrases:
                    if self._phrases_similar(phrase, other_phrase):
                        repetition_count += 1
        
        # Score based on repetition
        if repetition_count >= 3:
            return 20  # Said 3+ times = very important
        elif repetition_count == 2:
            return 15
        elif repetition_count == 1:
            return 10
        
        return 0
    
    def _score_context_signals(
        self,
        segment: TranscriptSegment,
        prosody: Dict[str, float]
    ) -> float:
        """
        Score based on context-specific signals.
        
        Returns:
            Context score (0-15)
        """
        score = 0
        
        if self.context == Context.SCHOOL:
            # Professor slowing down = explaining important concept
            speaking_rate = prosody.get('speaking_rate', 4.0)
            if speaking_rate < 2.5:  # Very slow
                score += 15
            elif speaking_rate < 3.5:  # Moderately slow
                score += 8
            
            # Questions indicate confusion/important clarification
            if '?' in segment.text:
                score += 5
        
        elif self.context == Context.WORK:
            # Check for disagreement/debate patterns
            if self._detect_disagreement(segment.text):
                score += 15
            
            # Check for commitment language
            if self._detect_commitment(segment.text):
                score += 10
        
        return min(15, score)
    
    def _extract_phrases(self, text: str, min_words: int = 3) -> List[str]:
        """Extract n-gram phrases from text."""
        words = text.lower().split()
        phrases = []
        
        for i in range(len(words) - min_words + 1):
            phrase = ' '.join(words[i:i + min_words])
            phrases.append(phrase)
        
        return phrases
    
    def _phrases_similar(self, phrase1: str, phrase2: str, threshold: float = 0.7) -> bool:
        """Check if two phrases are similar (simple word overlap)."""
        words1 = set(phrase1.split())
        words2 = set(phrase2.split())
        
        if not words1 or not words2:
            return False
        
        overlap = len(words1 & words2)
        min_length = min(len(words1), len(words2))
        
        similarity = overlap / min_length if min_length > 0 else 0
        return similarity >= threshold
    
    def _detect_disagreement(self, text: str) -> bool:
        """Detect disagreement patterns in text."""
        disagreement_patterns = [
            r'\bbut\b', r'\bhowever\b', r'\bactually\b',
            r"\bdon't agree\b", r"\bdisagree\b", r"\bconcern\b",
            r"\bnot sure\b", r"\bworried\b"
        ]
        
        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in disagreement_patterns)
    
    def _detect_commitment(self, text: str) -> bool:
        """Detect commitment/promise patterns."""
        commitment_patterns = [
            r"\bi'll\b", r"\bi will\b", r"\bcommit\b",
            r"\bpromise\b", r"\bguarantee\b", r"\bensure\b"
        ]
        
        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in commitment_patterns)


def demo():
    """Demonstrate importance scoring."""
    print("🎯 NeuroApp Importance Scorer Demo")
    print("=" * 50)
    
    # Create test segments
    test_segments = [
        # School mode examples
        {
            'context': Context.SCHOOL,
            'segment': TranscriptSegment(
                text="This concept will be on the midterm exam. Remember this.",
                start_time=120.0,
                end_time=125.0
            ),
            'prosody': {
                'vocal_emphasis_score': 60,  # High emphasis
                'speaking_rate': 2.3  # Slow (important)
            }
        },
        {
            'context': Context.SCHOOL,
            'segment': TranscriptSegment(
                text="For example, if we consider a simple case here.",
                start_time=45.0,
                end_time=48.0
            ),
            'prosody': {
                'vocal_emphasis_score': 20,  # Low emphasis
                'speaking_rate': 4.5  # Normal speed
            }
        },
        # Work mode examples
        {
            'context': Context.WORK,
            'segment': TranscriptSegment(
                text="I'm concerned about the deadline. This is a critical blocker.",
                start_time=300.0,
                end_time=304.0,
                speaker="Sarah"
            ),
            'prosody': {
                'vocal_emphasis_score': 75,  # Very high emphasis
                'speaking_rate': 2.8  # Slightly slow
            },
            'emotion': {
                'emotion': 'fearful',
                'importance_boost': 8
            }
        },
        {
            'context': Context.WORK,
            'segment': TranscriptSegment(
                text="I'll commit to finishing the spec by Friday.",
                start_time=450.0,
                end_time=453.0,
                speaker="Mike"
            ),
            'prosody': {
                'vocal_emphasis_score': 55,
                'speaking_rate': 3.2
            },
            'emotion': {
                'emotion': 'neutral',
                'importance_boost': 0
            }
        }
    ]
    
    # Score each segment
    for i, test in enumerate(test_segments, 1):
        print(f"\n{'='*50}")
        print(f"Test Case {i}: {test['context'].value.upper()} MODE")
        print(f"{'='*50}")
        
        scorer = ImportanceScorer(context=test['context'])
        result = scorer.score_segment(
            transcript=test['segment'],
            prosody_features=test['prosody'],
            emotion_result=test.get('emotion')
        )
        
        print(f"\n📝 Transcript:")
        print(f"   \"{result['text']}\"")
        if test['segment'].speaker:
            print(f"   Speaker: {test['segment'].speaker}")
        
        print(f"\n⭐ Importance: {result['stars']} {result['level']}")
        print(f"   Score: {result['score']:.0f}/100")
        
        print(f"\n📊 Score Breakdown:")
        for component, score in result['breakdown'].items():
            print(f"   {component:20} → {score:5.1f} points")
        
        print(f"\n⏱️  Timing:")
        print(f"   Start: {result['timestamp']:.1f}s")
        print(f"   Duration: {result['duration']:.1f}s")
    
    print(f"\n{'='*50}")
    print("✅ Demo Complete")
    print(f"{'='*50}")
    
    print("\n💡 Key Takeaways:")
    print("   • High importance → Auto-generate flashcards/action items")
    print("   • Medium importance → Include in summary")
    print("   • Low importance → Background context only")
    print("\n   This is the SECRET SAUCE that makes NeuroApp different!")


if __name__ == "__main__":
    demo()
