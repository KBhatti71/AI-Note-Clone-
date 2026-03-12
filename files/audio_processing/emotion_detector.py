"""
NeuroApp - Emotion Detector
Detects emotions from audio using various acoustic features.
"""

import numpy as np
from typing import Any, Dict, Optional


class EmotionDetector:
    """
    Detects emotions from audio signals.
    
    Recognizes: happy, sad, angry, fearful, surprised, neutral
    """
    
    # Emotion-to-importance boost mapping
    EMOTION_IMPORTANCE = {
        'fearful': 8,      # Fear/anxiety = important
        'angry': 9,        # Anger = very important
        'surprised': 6,    # Surprise = moderately important
        'happy': 3,        # Happiness = less critical
        'sad': 5,          # Sadness = moderately important
        'neutral': 0       # Neutral = baseline
    }
    
    def __init__(self):
        """Initialize emotion detector."""
        self.emotions = list(self.EMOTION_IMPORTANCE.keys())
    
    def detect_emotion(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000
    ) -> Dict[str, Any]:
        """
        Detect emotion from audio samples.
        
        Args:
            audio: Audio samples (numpy array)
            sample_rate: Sample rate in Hz
            
        Returns:
            Dictionary with detected emotion and importance boost
        """
        try:
            # Extract acoustic features for emotion
            emotion_scores = self._extract_emotion_features(audio, sample_rate)
            
            # Get dominant emotion
            detected_emotion = max(emotion_scores, key=emotion_scores.get)
            confidence = emotion_scores[detected_emotion]
            
            return {
                'emotion': detected_emotion,
                'confidence': confidence,
                'scores': emotion_scores,
                'importance_boost': self.EMOTION_IMPORTANCE[detected_emotion]
            }
        except Exception as e:
            # Return neutral if detection fails
            return {
                'emotion': 'neutral',
                'confidence': 0.0,
                'scores': {e: 0.0 for e in self.emotions},
                'importance_boost': 0
            }
    
    def _extract_emotion_features(
        self,
        audio: np.ndarray,
        sample_rate: int
    ) -> Dict[str, float]:
        """
        Extract acoustic features for emotion classification.
        
        Uses simplified heuristics based on:
        - Mean energy (loudness)
        - Energy variance (expressiveness)
        - Zero crossing rate (fricatives/unvoiced sounds)
        """
        # Normalize audio
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio))
        
        # Compute frame-based features
        frame_length = int(0.025 * sample_rate)  # 25ms frames
        hop_length = int(0.010 * sample_rate)    # 10ms hop
        
        frames = [
            audio[i:i+frame_length]
            for i in range(0, len(audio) - frame_length, hop_length)
        ]
        
        if not frames:
            return {e: 0.0 for e in self.emotions}
        
        # Extract energy features
        energies = [np.sum(frame**2) for frame in frames]
        mean_energy = np.mean(energies)
        energy_variance = np.var(energies)
        
        # Extract zero-crossing rate
        zcr = [
            np.sum(np.abs(np.diff(np.sign(frame)))) / (2 * len(frame))
            for frame in frames
        ]
        mean_zcr = np.mean(zcr)
        
        # Heuristic-based emotion classification
        scores = {e: 0.0 for e in self.emotions}
        
        # High energy + high variance = excited/angry/happy
        if mean_energy > 0.3:
            if energy_variance > 0.05:
                scores['angry'] += 0.7
                scores['happy'] += 0.3
            else:
                scores['happy'] += 0.5
        
        # Low energy + low variance = sad
        elif mean_energy < 0.1:
            scores['sad'] += 0.6
            scores['neutral'] += 0.4
        
        # Medium energy = neutral or fearful
        else:
            scores['neutral'] += 0.5
            if mean_zcr > 0.15:
                scores['fearful'] += 0.3
        
        # High ZCR can indicate surprise or fear
        if mean_zcr > 0.2:
            scores['surprised'] += 0.5
            scores['fearful'] += 0.3
        
        # Normalize scores to 0-1
        total = sum(scores.values())
        if total > 0:
            scores = {e: s / total for e, s in scores.items()}
        else:
            scores['neutral'] = 1.0
        
        return scores


def demo():
    """Demonstrate emotion detection."""
    print("😊 NeuroApp Emotion Detector Demo")
    print("=" * 50)
    
    # Create synthetic audio samples with different characteristics
    sample_rate = 16000
    duration = 2.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    test_cases = [
        {
            'name': 'Angry (high energy, rapid)',
            'frequency': 250,
            'amplitude': 0.8,
            'modulation': 0.5
        },
        {
            'name': 'Sad (low energy, slow)',
            'frequency': 100,
            'amplitude': 0.2,
            'modulation': 0.1
        },
        {
            'name': 'Happy (medium energy, bright)',
            'frequency': 200,
            'amplitude': 0.5,
            'modulation': 0.3
        }
    ]
    
    detector = EmotionDetector()
    
    for case in test_cases:
        # Generate synthetic speech
        frequency = case['frequency'] + case['modulation'] * 50 * np.sin(2 * np.pi * 2 * t)
        audio = case['amplitude'] * np.sin(2 * np.pi * frequency * t)
        
        # Detect emotion
        result = detector.detect_emotion(audio, sample_rate)
        
        print(f"\n{case['name']}")
        print(f"  Detected: {result['emotion']} (confidence: {result['confidence']:.2f})")
        print(f"  Importance boost: +{result['importance_boost']}")


if __name__ == "__main__":
    demo()
