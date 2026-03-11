import numpy as np
import pytest
from app.analyzers.prosody_analyzer import ProsodyAnalyzer

def test_prosody_initialization():
    analyzer = ProsodyAnalyzer(sample_rate=16000)
    assert analyzer.sample_rate == 16000
    assert analyzer.pitch_floor == 75.0
    assert analyzer.pitch_ceiling == 500.0

def test_analyze_segment_basic():
    analyzer = ProsodyAnalyzer()
    
    # Create fake 1s audio array (sine wave)
    t = np.linspace(0, 1.0, 16000)
    audio = 0.5 * np.sin(2 * np.pi * 200 * t)  # 200 Hz tone
    
    # Analyze
    features = analyzer.analyze_segment(audio)
    
    assert features['duration'] == 1.0
    assert features['pitch_mean'] > 0
    assert features['intensity_mean'] >= 0
    
    # We expect some emphasis scores to be calculated
    assert 0 <= features['vocal_emphasis_score'] <= 100
    assert 0 <= features['speaking_pattern_score'] <= 100

def test_pauses_detection():
    analyzer = ProsodyAnalyzer()
    
    # Create 2 seconds of silence
    audio = np.zeros(32000)
    
    pauses = analyzer._detect_pauses(audio)
    assert len(pauses) > 0  # Should detect the silence as a pause
