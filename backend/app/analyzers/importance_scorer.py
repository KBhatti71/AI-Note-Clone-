import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class Context(Enum):
    SCHOOL = "school"
    WORK = "work"
    GENERAL = "general"

@dataclass
class TranscriptSegment:
    text: str
    start_time: float
    end_time: float
    speaker: Optional[str] = None

class ImportanceScorer:
    # Context-specific keywords
    KEYWORDS = {
        Context.SCHOOL: {
            'critical': ['exam', 'test', 'quiz', 'midterm', 'final', 'important', 'remember', 'key concept', 'fundamental', 'will be on'],
            'high': ['understand', 'practice', 'study', 'review', 'homework', 'assignment', 'due', 'definition', 'theorem'],
            'medium': ['example', 'for instance', 'notice', 'observe', 'think about']
        },
        Context.WORK: {
            'critical': ['deadline', 'critical', 'urgent', 'blocker', 'decision', 'must', 'need to', 'action item', 'committed'],
            'high': ['should', 'recommend', 'suggest', 'concern', 'issue', 'risk', 'follow up', 'next steps'],
            'medium': ['update', 'status', 'progress', 'discuss', 'consider']
        },
        Context.GENERAL: {
            'critical': ['important', 'critical', 'remember', 'key point'],
            'high': ['note', 'mention', 'emphasize', 'highlight'],
            'medium': ['think', 'consider', 'maybe', 'perhaps']
        }
    }
    
    def __init__(self, context: Context = Context.GENERAL):
        self.context = context
        self.keyword_weights: Dict[str, int] = {
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
        scores: Dict[str, float] = {}
        
        # 1. Vocal Emphasis (30 points max)
        vocal_score = min(30.0, float(prosody_features.get('vocal_emphasis_score', 0)) * 0.3)
        scores['vocal_emphasis'] = vocal_score
        
        # 2. Keyword Matching (20 points max)
        keyword_score = self._score_keywords(transcript.text)
        scores['keywords'] = keyword_score
        
        # 3. Repetition Patterns (20 points max)
        repetition_score = 0.0
        if window_transcripts:
            repetition_score = self._score_repetition(transcript, window_transcripts)
        scores['repetition'] = float(repetition_score)
        
        # 4. Emotion Signals (15 points max)
        emotion_score = 0.0
        if emotion_result:
            emotion_score = min(15.0, float(emotion_result.get('importance_boost', 0)))
        scores['emotion'] = emotion_score
        
        # 5. Context-Specific Signals (15 points max)
        context_score = self._score_context_signals(transcript, prosody_features)
        scores['context'] = context_score
        
        if user_highlighted:
            scores['user_highlight'] = 15.0
        
        total = float(sum(scores.values()))
        total = min(100.0, total)
        
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
        text_lower = text.lower()
        score: float = 0.0
        keywords = self.KEYWORDS[self.context]
        
        for category, keyword_list in keywords.items():
            for keyword in keyword_list:
                if keyword in text_lower:
                    score = float(score) + float(self.keyword_weights[category])
        return min(20.0, float(score))
    
    def _score_repetition(self, segment: TranscriptSegment, window: List[TranscriptSegment], max_window: int = 5) -> float:
        # Avoid slicing error on some pyre versions by using list comprehension
        start_idx = max(0, len(window) - max_window)
        recent = [window[i] for i in range(start_idx, len(window))]
        current_phrases = self._extract_phrases(segment.text, min_words=3)
        repetition_count: int = 0
        
        for other in recent:
            if other.text == segment.text:
                continue
            other_phrases = self._extract_phrases(other.text, min_words=3)
            for phrase in current_phrases:
                for other_phrase in other_phrases:
                    if self._phrases_similar(phrase, other_phrase):
                        repetition_count = int(repetition_count) + 1
                        
        if int(repetition_count) >= 3:
            return 20.0
        elif repetition_count == 2:
            return 15.0
        elif repetition_count == 1:
            return 10.0
        return 0.0
    
    def _score_context_signals(self, segment: TranscriptSegment, prosody: Dict[str, float]) -> float:
        score = 0.0
        if self.context == Context.SCHOOL:
            speaking_rate = float(prosody.get('speaking_rate', 4.0))
            if speaking_rate < 2.5:
                score += 15.0
            elif speaking_rate < 3.5:
                score += 8.0
            if '?' in segment.text:
                score += 5.0
        elif self.context == Context.WORK:
            if self._detect_disagreement(segment.text):
                score += 15.0
            if self._detect_commitment(segment.text):
                score += 10.0
        return min(15.0, score)
    
    def _extract_phrases(self, text: str, min_words: int = 3) -> List[str]:
        words = text.lower().split()
        phrases: List[str] = []
        
        for i in range(len(words) - min_words + 1):
            phrase_words = [words[j] for j in range(i, min(len(words), i + min_words))]
            phrase = ' '.join(phrase_words)
            phrases.append(phrase)
        
        return phrases
    
    def _phrases_similar(self, phrase1: str, phrase2: str, threshold: float = 0.7) -> bool:
        words1 = set(phrase1.split())
        words2 = set(phrase2.split())
        if not words1 or not words2:
            return False
        overlap = len(words1 & words2)
        min_length = min(len(words1), len(words2))
        similarity = overlap / min_length if min_length > 0 else 0
        return similarity >= threshold
    
    def _detect_disagreement(self, text: str) -> bool:
        disagreement_patterns = [
            r'\bbut\b', r'\bhowever\b', r'\bactually\b',
            r"\bdon't agree\b", r"\bdisagree\b", r"\bconcern\b",
            r"\bnot sure\b", r"\bworried\b"
        ]
        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in disagreement_patterns)
    
    def _detect_commitment(self, text: str) -> bool:
        commitment_patterns = [
            r"\bi'll\b", r"\bi will\b", r"\bcommit\b",
            r"\bpromise\b", r"\bguarantee\b", r"\bensure\b"
        ]
        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in commitment_patterns)
