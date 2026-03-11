import pytest
import numpy as np
from app.analyzers.emotion_detector import EmotionDetector

def test_emotion_detector_initialization():
    detector = EmotionDetector(use_mock=True)
    assert detector.use_mock is True

def test_detect_emotion_mock_high_energy():
    detector = EmotionDetector(use_mock=True)
    # High amplitude = fearful/angry in our stub
    audio = np.ones(16000) * 0.1
    result = detector.detect_emotion(audio)
    
    assert result['emotion'] == 'fearful'
    assert result['importance_boost'] == 15

def test_detect_emotion_mock_low_energy():
    detector = EmotionDetector(use_mock=True)
    # Low amplitude = neutral in our stub
    audio = np.zeros(16000)
    result = detector.detect_emotion(audio)
    
    assert result['emotion'] == 'neutral'
    assert result['importance_boost'] == 0
