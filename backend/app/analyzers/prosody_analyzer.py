import numpy as np
import parselmouth
from parselmouth.praat import call
from scipy.signal import find_peaks
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
        """
        # Use audio.size instead of shape or len for some pyre constraints
        duration = float(audio.size) / self.sample_rate
        sound = parselmouth.Sound(audio, sampling_frequency=self.sample_rate)
        
        pitch_data = self._extract_pitch(sound)
        intensity_data = self._extract_intensity(sound)
        speaking_rate = self._estimate_speaking_rate(sound)
        pauses = self._detect_pauses(audio)
        
        pitch_variation = np.std(pitch_data['values']) if len(pitch_data['values']) > 0 else 0
        pitch_range = pitch_data['max'] - pitch_data['min']
        mean_intensity = np.mean(intensity_data['values']) if len(intensity_data['values']) > 0 else 0
        intensity_peaks = self._count_intensity_peaks(intensity_data['values'])
        
        return {
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
            'total_pause_duration': self._calculate_total_pause(pauses),
            'vocal_emphasis_score': self._calculate_emphasis_score(
                pitch_variation, intensity_peaks, pitch_range
            ),
            'speaking_pattern_score': self._calculate_pattern_score(
                speaking_rate, len(pauses)
            ),
        }
    
    def _extract_pitch(self, sound: parselmouth.Sound) -> Dict[str, float]:
        pitch = call(sound, "To Pitch", 0.0, self.pitch_floor, self.pitch_ceiling)
        pitch_values = []
        for t in np.arange(sound.xmin, sound.xmax, 0.01):
            value = call(pitch, "Get value at time", t, "Hertz", "Linear")
            if value and not np.isnan(value):
                pitch_values.append(value)
        
        if not pitch_values:
            return {'values': np.array([]), 'mean': 0.0, 'max': 0.0, 'min': 0.0}
        
        pitch_array = np.array(pitch_values)
        return {
            'values': pitch_array,
            'mean': np.mean(pitch_array),
            'max': np.max(pitch_array),
            'min': np.min(pitch_array)
        }
    
    def _extract_intensity(self, sound: parselmouth.Sound) -> Dict[str, float]:
        intensity = call(sound, "To Intensity", 75, 0.0, "yes")
        intensity_values = []
        for t in np.arange(sound.xmin, sound.xmax, 0.01):
            value = call(intensity, "Get value at time", t, "Cubic")
            if value and not np.isnan(value):
                intensity_values.append(value)
        
        if not intensity_values:
            return {'values': np.array([]), 'max': 0.0}
        
        intensity_array = np.array(intensity_values)
        return {
            'values': intensity_array,
            'max': np.max(intensity_array)
        }
    
    def _estimate_speaking_rate(self, sound: parselmouth.Sound) -> float:
        intensity = call(sound, "To Intensity", 75, 0.0, "yes")
        intensity_values = []
        for t in np.arange(sound.xmin, sound.xmax, 0.01):
            value = call(intensity, "Get value at time", t, "Cubic")
            if value and not np.isnan(value):
                intensity_values.append(value)
        
        if len(intensity_values) < 10:
            return 0.0
        
        peaks, _ = find_peaks(
            intensity_values,
            height=np.mean(intensity_values),
            distance=5
        )
        
        duration = sound.duration
        return len(peaks) / duration if duration > 0 else 0
    
    def _detect_pauses(self, audio: np.ndarray, silence_threshold: float = 0.02, min_pause_duration: float = 0.3) -> List[Tuple[float, float]]:
        frame_length = int(0.025 * self.sample_rate)
        hop_length = int(0.010 * self.sample_rate)
        
        energy = np.array([
            np.sum(audio[i:i+frame_length]**2)
            for i in range(0, int(audio.size) - frame_length, hop_length)
        ])
        
        energy = energy / (np.max(energy) + 1e-10)
        is_silent = energy < silence_threshold
        
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
                    pauses.append((float(pause_start), float(time)))
                in_pause = False

        if in_pause:
            end_time = float(audio.size) / self.sample_rate
            pause_duration = end_time - pause_start
            if pause_duration >= min_pause_duration:
                pauses.append((float(pause_start), float(end_time)))

        return pauses
    
    def _calculate_total_pause(self, pauses: List[Tuple[float, float]]) -> float:
        total = 0.0
        for p in pauses:
            total = total + (p[1] - p[0])
        return total
    
    def _count_intensity_peaks(self, intensity_values: np.ndarray, prominence: float = 5.0) -> int:
        if len(intensity_values) < 3:
            return 0
        peaks, _ = find_peaks(intensity_values, prominence=prominence)
        return len(peaks)
    
    def _calculate_emphasis_score(self, pitch_variation: float, intensity_peaks: int, pitch_range: float) -> float:
        score = 0.0
        
        if pitch_variation > 50:
            score += 40
        elif pitch_variation > 30:
            score += 25
        elif pitch_variation > 15:
            score += 10
            
        if intensity_peaks > 5:
            score += 30
        elif intensity_peaks > 3:
            score += 20
        elif intensity_peaks > 1:
            score += 10
            
        if pitch_range > 100:
            score += 30
        elif pitch_range > 60:
            score += 20
        elif pitch_range > 30:
            score += 10
            
        return min(score, 100)
    
    def _calculate_pattern_score(self, speaking_rate: float, pause_count: int) -> float:
        score = 0.0
        
        if speaking_rate < 2.5:
            score += 50
        elif speaking_rate < 3.5:
            score += 30
            
        if pause_count >= 3:
            score += 50
        elif pause_count >= 2:
            score += 30
        elif pause_count >= 1:
            score += 15
            
        return min(score, 100)
