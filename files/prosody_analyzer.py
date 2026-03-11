"""
NeuroApp - Prosody Analyzer
Extracts vocal features that indicate importance from audio segments.
"""

import numpy as np
import parselmouth
from parselmouth.praat import call
from scipy.signal import find_peaks
import librosa
from typing import Dict, Tuple, List


class ProsodyAnalyzer:
    """Analyzes audio prosody to detect emphasis and importance signals."""
    
    def __init__(
        self,
        sample_rate: int = 16000,
        pitch_floor: float = 75.0,  # Hz - lower bound for human voice
        pitch_ceiling: float = 500.0,  # Hz - upper bound for human voice
    ):
        self.sample_rate = sample_rate
        self.pitch_floor = pitch_floor
        self.pitch_ceiling = pitch_ceiling
    
    def analyze_segment(
        self, 
        audio: np.ndarray,
        start_time: float = 0.0
    ) -> Dict[str, float]:
        """
        Extract prosody features from an audio segment.
        
        Args:
            audio: Audio samples (numpy array)
            start_time: Start time in seconds (for context)
            
        Returns:
            Dictionary of prosody features with importance indicators
        """
        # Convert numpy array to Praat Sound object
        duration = len(audio) / self.sample_rate
        sound = parselmouth.Sound(audio, sampling_frequency=self.sample_rate)
        
        # Extract features
        pitch_data = self._extract_pitch(sound)
        intensity_data = self._extract_intensity(sound)
        speaking_rate = self._estimate_speaking_rate(sound)
        pauses = self._detect_pauses(audio)
        
        # Calculate importance indicators
        pitch_variation = np.std(pitch_data['values'])
        pitch_range = pitch_data['max'] - pitch_data['min']
        mean_intensity = np.mean(intensity_data['values'])
        intensity_peaks = self._count_intensity_peaks(intensity_data['values'])
        
        return {
            # Raw measurements
            'duration': duration,
            'pitch_mean': pitch_data['mean'],
            'pitch_std': pitch_variation,
            'pitch_range': pitch_range,
            'pitch_max': pitch_data['max'],
            'pitch_min': pitch_data['min'],
            'intensity_mean': mean_intensity,
            'intensity_max': intensity_data['max'],
            'intensity_peaks': intensity_peaks,
            'speaking_rate': speaking_rate,
            'pause_count': len(pauses),
            'total_pause_duration': sum(p[1] - p[0] for p in pauses),
            
            # Importance indicators (0-100 scale)
            'vocal_emphasis_score': self._calculate_emphasis_score(
                pitch_variation, intensity_peaks, pitch_range
            ),
            'speaking_pattern_score': self._calculate_pattern_score(
                speaking_rate, len(pauses)
            ),
        }
    
    def _extract_pitch(self, sound: parselmouth.Sound) -> Dict[str, float]:
        """Extract pitch (F0) contour using Praat."""
        pitch = call(sound, "To Pitch", 0.0, self.pitch_floor, self.pitch_ceiling)
        
        # Get pitch values at regular intervals
        pitch_values = []
        for t in np.arange(sound.xmin, sound.xmax, 0.01):  # Every 10ms
            value = call(pitch, "Get value at time", t, "Hertz", "Linear")
            if value and not np.isnan(value):  # Only voiced segments
                pitch_values.append(value)
        
        if not pitch_values:
            return {
                'values': np.array([]),
                'mean': 0.0,
                'max': 0.0,
                'min': 0.0
            }
        
        pitch_array = np.array(pitch_values)
        return {
            'values': pitch_array,
            'mean': np.mean(pitch_array),
            'max': np.max(pitch_array),
            'min': np.min(pitch_array)
        }
    
    def _extract_intensity(self, sound: parselmouth.Sound) -> Dict[str, float]:
        """Extract intensity (volume) contour."""
        intensity = call(sound, "To Intensity", 75, 0.0, "yes")
        
        intensity_values = []
        for t in np.arange(sound.xmin, sound.xmax, 0.01):
            value = call(intensity, "Get value at time", t, "Cubic")
            if value and not np.isnan(value):
                intensity_values.append(value)
        
        if not intensity_values:
            return {
                'values': np.array([]),
                'max': 0.0
            }
        
        intensity_array = np.array(intensity_values)
        return {
            'values': intensity_array,
            'max': np.max(intensity_array)
        }
    
    def _estimate_speaking_rate(self, sound: parselmouth.Sound) -> float:
        """
        Estimate speaking rate (syllables per second).
        Uses intensity peaks as proxy for syllables.
        """
        intensity = call(sound, "To Intensity", 75, 0.0, "yes")
        intensity_values = []
        
        for t in np.arange(sound.xmin, sound.xmax, 0.01):
            value = call(intensity, "Get value at time", t, "Cubic")
            if value and not np.isnan(value):
                intensity_values.append(value)
        
        if len(intensity_values) < 10:
            return 0.0
        
        # Find peaks in intensity (approximates syllables)
        peaks, _ = find_peaks(
            intensity_values,
            height=np.mean(intensity_values),
            distance=5  # Min 50ms between syllables
        )
        
        duration = sound.duration
        syllables_per_second = len(peaks) / duration if duration > 0 else 0
        
        return syllables_per_second
    
    def _detect_pauses(
        self, 
        audio: np.ndarray,
        silence_threshold: float = 0.02,
        min_pause_duration: float = 0.3
    ) -> List[Tuple[float, float]]:
        """
        Detect pauses/silences in speech.
        
        Returns:
            List of (start_time, end_time) tuples for each pause
        """
        # Calculate energy
        frame_length = int(0.025 * self.sample_rate)  # 25ms frames
        hop_length = int(0.010 * self.sample_rate)    # 10ms hop
        
        energy = np.array([
            np.sum(audio[i:i+frame_length]**2)
            for i in range(0, len(audio) - frame_length, hop_length)
        ])
        
        # Normalize
        energy = energy / (np.max(energy) + 1e-10)
        
        # Find silent frames
        is_silent = energy < silence_threshold
        
        # Group consecutive silent frames into pauses
        pauses = []
        in_pause = False
        pause_start = 0
        
        for i, silent in enumerate(is_silent):
            time = i * hop_length / self.sample_rate
            
            if silent and not in_pause:
                pause_start = time
                in_pause = True
            elif not silent and in_pause:
                pause_duration = time - pause_start
                if pause_duration >= min_pause_duration:
                    pauses.append((pause_start, time))
                in_pause = False
        
        return pauses
    
    def _count_intensity_peaks(
        self, 
        intensity_values: np.ndarray,
        prominence: float = 5.0
    ) -> int:
        """Count significant peaks in intensity (loud moments)."""
        if len(intensity_values) < 3:
            return 0
        
        peaks, _ = find_peaks(intensity_values, prominence=prominence)
        return len(peaks)
    
    def _calculate_emphasis_score(
        self,
        pitch_variation: float,
        intensity_peaks: int,
        pitch_range: float
    ) -> float:
        """
        Calculate vocal emphasis score (0-100).
        High score = speaker is emphasizing this segment.
        """
        score = 0.0
        
        # Pitch variation (0-40 points)
        # High variation = emphasis
        if pitch_variation > 50:  # Hz
            score += 40
        elif pitch_variation > 30:
            score += 25
        elif pitch_variation > 15:
            score += 10
        
        # Intensity peaks (0-30 points)
        # More loud moments = emphasis
        if intensity_peaks > 5:
            score += 30
        elif intensity_peaks > 3:
            score += 20
        elif intensity_peaks > 1:
            score += 10
        
        # Pitch range (0-30 points)
        # Wide range = expressive/emphatic
        if pitch_range > 100:  # Hz
            score += 30
        elif pitch_range > 60:
            score += 20
        elif pitch_range > 30:
            score += 10
        
        return min(score, 100)
    
    def _calculate_pattern_score(
        self,
        speaking_rate: float,
        pause_count: int
    ) -> float:
        """
        Calculate speaking pattern score (0-100).
        Looks for patterns that indicate importance.
        """
        score = 0.0
        
        # Slower speech = important detail (0-50 points)
        # Normal rate is ~3-5 syllables/second
        if speaking_rate < 2.5:  # Very slow = important
            score += 50
        elif speaking_rate < 3.5:  # Moderate slow
            score += 30
        
        # Pauses before/after = thinking/emphasis (0-50 points)
        if pause_count >= 3:
            score += 50
        elif pause_count >= 2:
            score += 30
        elif pause_count >= 1:
            score += 15
        
        return min(score, 100)


def demo():
    """Demonstrate prosody analysis on a test audio file."""
    print("🎙️  NeuroApp Prosody Analyzer Demo")
    print("=" * 50)
    
    # This would normally load a real audio file
    # For demo, we'll create synthetic audio
    sample_rate = 16000
    duration = 3.0  # 3 seconds
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Simulate speech with varying pitch
    # Low pitch (~150 Hz) that increases (emphasis)
    frequency = 150 + 50 * np.sin(2 * np.pi * 0.5 * t)
    audio = 0.3 * np.sin(2 * np.pi * frequency * t)
    
    # Analyze
    analyzer = ProsodyAnalyzer(sample_rate=sample_rate)
    features = analyzer.analyze_segment(audio)
    
    print("\n📊 Prosody Features:")
    print(f"   Duration: {features['duration']:.2f}s")
    print(f"   Pitch (mean): {features['pitch_mean']:.1f} Hz")
    print(f"   Pitch variation: {features['pitch_std']:.1f} Hz")
    print(f"   Pitch range: {features['pitch_range']:.1f} Hz")
    print(f"   Speaking rate: {features['speaking_rate']:.1f} syllables/sec")
    print(f"   Intensity peaks: {features['intensity_peaks']}")
    print(f"   Pause count: {features['pause_count']}")
    
    print("\n⭐ Importance Indicators:")
    print(f"   Vocal emphasis score: {features['vocal_emphasis_score']:.0f}/100")
    print(f"   Speaking pattern score: {features['speaking_pattern_score']:.0f}/100")
    
    # Overall importance
    overall = (features['vocal_emphasis_score'] + features['speaking_pattern_score']) / 2
    print(f"\n🎯 Overall Importance: {overall:.0f}/100")
    
    if overall >= 70:
        print("   ⭐⭐⭐ HIGH IMPORTANCE - This segment needs attention!")
    elif overall >= 40:
        print("   ⭐⭐ MEDIUM IMPORTANCE - Worth noting")
    else:
        print("   ⭐ LOW IMPORTANCE - Routine content")


if __name__ == "__main__":
    demo()
