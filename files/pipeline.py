"""
NeuroApp - Complete Audio Intelligence Pipeline
Integrates prosody analysis, emotion detection, and importance scoring.
"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from audio_processing.prosody_analyzer import ProsodyAnalyzer
from audio_processing.emotion_detector import EmotionDetector
from audio_processing.importance_scorer import ImportanceScorer, Context, TranscriptSegment


@dataclass
class AnalyzedSegment:
    """Complete analysis result for a transcript segment."""
    text: str
    start_time: float
    end_time: float
    speaker: Optional[str]
    importance_score: float
    importance_level: str
    prosody_features: Dict
    emotion: Optional[str]
    breakdown: Dict
    recommendations: List[str]


class AudioIntelligencePipeline:
    """
    Complete pipeline for analyzing audio and determining importance.
    
    Pipeline stages:
    1. Audio → Prosody Analysis (pitch, volume, rate, pauses)
    2. Audio → Emotion Detection (6 emotions)
    3. Text + Prosody + Emotion → Importance Scoring (0-100)
    4. Generate recommendations (flashcards, action items, etc.)
    """
    
    def __init__(
        self,
        context: Context = Context.GENERAL,
        sample_rate: int = 16000,
        enable_emotion: bool = True
    ):
        """
        Initialize the pipeline.
        
        Args:
            context: Context mode (school, work, general)
            sample_rate: Audio sample rate
            enable_emotion: Whether to use emotion detection (slower but more accurate)
        """
        print("🚀 Initializing NeuroApp Audio Intelligence Pipeline...")
        
        self.context = context
        self.sample_rate = sample_rate
        
        # Initialize components
        self.prosody_analyzer = ProsodyAnalyzer(sample_rate=sample_rate)
        self.importance_scorer = ImportanceScorer(context=context)
        
        self.emotion_detector = None
        if enable_emotion:
            # Emotion detection is optional (adds latency)
            try:
                self.emotion_detector = EmotionDetector()
            except Exception as e:
                print(f"⚠️  Emotion detection disabled: {e}")
        
        # Keep history for repetition detection
        self.segment_history: List[TranscriptSegment] = []
        
        print("✅ Pipeline ready!")
    
    def analyze_segment(
        self,
        audio: np.ndarray,
        transcript: str,
        start_time: float,
        end_time: float,
        speaker: Optional[str] = None,
        user_highlighted: bool = False
    ) -> AnalyzedSegment:
        """
        Analyze a single audio segment with transcript.
        
        Args:
            audio: Audio samples
            transcript: Transcribed text
            start_time: Segment start time (seconds)
            end_time: Segment end time (seconds)
            speaker: Speaker name (if known)
            user_highlighted: Whether user manually flagged this
            
        Returns:
            Complete analysis with importance score
        """
        # Create transcript segment
        segment = TranscriptSegment(
            text=transcript,
            start_time=start_time,
            end_time=end_time,
            speaker=speaker
        )
        
        # Stage 1: Prosody Analysis
        prosody_features = self.prosody_analyzer.analyze_segment(audio, start_time)
        
        # Stage 2: Emotion Detection (optional)
        emotion_result = None
        if self.emotion_detector is not None:
            try:
                emotion_result = self.emotion_detector.detect_emotion(audio, self.sample_rate)
            except Exception as e:
                print(f"⚠️  Emotion detection failed: {e}")
        
        # Stage 3: Importance Scoring
        score_result = self.importance_scorer.score_segment(
            transcript=segment,
            prosody_features=prosody_features,
            emotion_result=emotion_result,
            user_highlighted=user_highlighted,
            window_transcripts=self.segment_history[-10:]  # Last 10 segments for context
        )
        
        # Stage 4: Generate Recommendations
        recommendations = self._generate_recommendations(
            score_result, segment, prosody_features, emotion_result
        )
        
        # Add to history
        self.segment_history.append(segment)
        
        # Create result
        return AnalyzedSegment(
            text=transcript,
            start_time=start_time,
            end_time=end_time,
            speaker=speaker,
            importance_score=score_result['score'],
            importance_level=score_result['level'],
            prosody_features=prosody_features,
            emotion=emotion_result['emotion'] if emotion_result else None,
            breakdown=score_result['breakdown'],
            recommendations=recommendations
        )
    
    def analyze_conversation(
        self,
        segments: List[Dict]
    ) -> List[AnalyzedSegment]:
        """
        Analyze entire conversation (multiple segments).
        
        Args:
            segments: List of dicts with 'audio', 'transcript', 'start_time', 'end_time'
            
        Returns:
            List of analyzed segments with importance scores
        """
        results = []
        
        print(f"\n🎙️  Analyzing {len(segments)} segments...")
        
        for i, seg in enumerate(segments, 1):
            result = self.analyze_segment(
                audio=seg['audio'],
                transcript=seg['transcript'],
                start_time=seg['start_time'],
                end_time=seg['end_time'],
                speaker=seg.get('speaker'),
                user_highlighted=seg.get('user_highlighted', False)
            )
            results.append(result)
            
            # Progress indicator
            if i % 10 == 0:
                print(f"   Processed {i}/{len(segments)} segments...")
        
        print("✅ Analysis complete!")
        return results
    
    def _generate_recommendations(
        self,
        score_result: Dict,
        segment: TranscriptSegment,
        prosody: Dict,
        emotion: Optional[Dict]
    ) -> List[str]:
        """Generate action recommendations based on analysis."""
        recommendations = []
        score = score_result['score']
        
        if score >= 70:  # HIGH importance
            if self.context == Context.SCHOOL:
                recommendations.append("📝 Add to flashcards")
                recommendations.append("⭐ Mark for exam review")
                recommendations.append("🎯 Create practice question")
            elif self.context == Context.WORK:
                recommendations.append("✅ Create action item")
                recommendations.append("📅 Schedule follow-up")
                recommendations.append("📢 Share with team")
        
        elif score >= 40:  # MEDIUM importance
            if self.context == Context.SCHOOL:
                recommendations.append("📚 Include in study guide")
            elif self.context == Context.WORK:
                recommendations.append("📝 Note in summary")
        
        # Emotion-specific recommendations
        if emotion and emotion['emotion'] in ['angry', 'fearful']:
            recommendations.append("⚠️  Flag for immediate attention")
        
        # Speaking pattern recommendations
        if prosody.get('speaking_rate', 4) < 2.5:
            recommendations.append("🔍 Complex concept - needs review")
        
        return recommendations
    
    def generate_summary(self, results: List[AnalyzedSegment]) -> Dict:
        """
        Generate summary of analyzed conversation.
        
        Returns:
            Summary with key insights
        """
        high_importance = [r for r in results if r.importance_score >= 70]
        medium_importance = [r for r in results if 40 <= r.importance_score < 70]
        low_importance = [r for r in results if r.importance_score < 40]
        
        # Extract key moments
        top_moments = sorted(results, key=lambda x: x.importance_score, reverse=True)[:5]
        
        # Emotion distribution
        emotions = [r.emotion for r in results if r.emotion]
        emotion_dist = {}
        if emotions:
            for emotion in set(emotions):
                emotion_dist[emotion] = emotions.count(emotion) / len(emotions)
        
        return {
            'total_segments': len(results),
            'high_importance_count': len(high_importance),
            'medium_importance_count': len(medium_importance),
            'low_importance_count': len(low_importance),
            'top_moments': [
                {
                    'text': m.text,
                    'score': m.importance_score,
                    'timestamp': m.start_time
                }
                for m in top_moments
            ],
            'emotion_distribution': emotion_dist,
            'average_importance': np.mean([r.importance_score for r in results]),
            'recommendations': self._generate_summary_recommendations(results)
        }
    
    def _generate_summary_recommendations(self, results: List[AnalyzedSegment]) -> List[str]:
        """Generate overall recommendations for the conversation."""
        high_count = sum(1 for r in results if r.importance_score >= 70)
        
        recommendations = []
        
        if self.context == Context.SCHOOL:
            if high_count >= 5:
                recommendations.append("📚 Create comprehensive study guide")
                recommendations.append("🎯 Schedule review session")
            recommendations.append(f"📝 {high_count} concepts need flashcards")
        
        elif self.context == Context.WORK:
            if high_count >= 3:
                recommendations.append("📅 Send follow-up meeting invite")
                recommendations.append("✅ Track action items in Asana")
            recommendations.append(f"📝 {high_count} decisions documented")
        
        return recommendations


def demo():
    """Demonstrate the complete pipeline."""
    print("🧠 NeuroApp Complete Pipeline Demo")
    print("=" * 60)
    
    # Simulate a lecture scenario
    print("\n📚 Scenario: Computer Science Lecture on Recursion")
    print("=" * 60)
    
    # Create synthetic test data
    sample_rate = 16000
    
    test_segments = [
        {
            'audio': np.random.randn(sample_rate * 2),  # 2 seconds
            'transcript': "Today we're covering recursion in computer science.",
            'start_time': 0.0,
            'end_time': 2.0,
            'speaker': 'Professor'
        },
        {
            'audio': np.random.randn(sample_rate * 3),  # 3 seconds
            'transcript': "This is THE most important concept for your midterm exam. Remember this.",
            'start_time': 120.0,
            'end_time': 123.0,
            'speaker': 'Professor',
            'user_highlighted': True
        },
        {
            'audio': np.random.randn(sample_rate * 2),
            'transcript': "A recursive function calls itself with a smaller problem.",
            'start_time': 125.0,
            'end_time': 127.0,
            'speaker': 'Professor'
        },
        {
            'audio': np.random.randn(sample_rate * 2),
            'transcript': "What's the difference between base case and recursive case?",
            'start_time': 200.0,
            'end_time': 202.0,
            'speaker': 'Student'
        }
    ]
    
    # Initialize pipeline in school mode
    pipeline = AudioIntelligencePipeline(
        context=Context.SCHOOL,
        enable_emotion=False  # Disabled for demo speed
    )
    
    # Analyze all segments
    results = pipeline.analyze_conversation(test_segments)
    
    # Display results
    print("\n" + "=" * 60)
    print("ANALYSIS RESULTS")
    print("=" * 60)
    
    for i, result in enumerate(results, 1):
        print(f"\n{'─' * 60}")
        print(f"Segment {i}")
        print(f"{'─' * 60}")
        print(f"📝 Text: \"{result.text}\"")
        print(f"🗣️  Speaker: {result.speaker}")
        print(f"⏱️  Time: {result.start_time:.1f}s - {result.end_time:.1f}s")
        print(f"\n⭐ Importance: {result.importance_level} ({result.importance_score:.0f}/100)")
        
        print(f"\n📊 Score Breakdown:")
        for component, value in result.breakdown.items():
            print(f"   • {component:20} → {value:5.1f} points")
        
        if result.recommendations:
            print(f"\n💡 Recommendations:")
            for rec in result.recommendations:
                print(f"   {rec}")
    
    # Generate summary
    summary = pipeline.generate_summary(results)
    
    print(f"\n{'=' * 60}")
    print("CONVERSATION SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total Segments: {summary['total_segments']}")
    print(f"High Importance: {summary['high_importance_count']}")
    print(f"Medium Importance: {summary['medium_importance_count']}")
    print(f"Low Importance: {summary['low_importance_count']}")
    print(f"Average Importance: {summary['average_importance']:.1f}/100")
    
    print(f"\n🏆 Top 3 Most Important Moments:")
    for i, moment in enumerate(summary['top_moments'][:3], 1):
        print(f"\n   {i}. [{moment['timestamp']:.1f}s] Score: {moment['score']:.0f}/100")
        print(f"      \"{moment['text']}\"")
    
    print(f"\n📋 Overall Recommendations:")
    for rec in summary['recommendations']:
        print(f"   {rec}")
    
    print(f"\n{'=' * 60}")
    print("✅ Pipeline Demo Complete!")
    print(f"{'=' * 60}")
    
    print("\n🎯 What Just Happened:")
    print("   1. Analyzed audio prosody (pitch, volume, rate, pauses)")
    print("   2. Scored keywords and patterns in transcript")
    print("   3. Combined signals into importance scores (0-100)")
    print("   4. Generated context-aware recommendations")
    print("\n   This is the CORE of NeuroApp's competitive advantage!")


if __name__ == "__main__":
    demo()
