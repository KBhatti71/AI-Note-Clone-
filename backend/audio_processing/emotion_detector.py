"""
Emotion Detector for NeuroApp
Detects 6 emotions from audio using Wav2Vec2-based classification.
Emotions: angry, happy, sad, neutral, fearful, surprised
"""

import numpy as np
import logging
from dataclasses import dataclass
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)


class Emotion(str, Enum):
    ANGRY = "angry"
    HAPPY = "happy"
    SAD = "sad"
    NEUTRAL = "neutral"
    FEARFUL = "fearful"
    SURPRISED = "surprised"


# Importance weight for each emotion (used by ImportanceScorer)
EMOTION_IMPORTANCE_WEIGHTS = {
    Emotion.ANGRY: 15,       # Critical issue
    Emotion.SURPRISED: 12,   # Revelation / unexpected info
    Emotion.HAPPY: 10,       # Excitement / positive emphasis
    Emotion.FEARFUL: 8,      # Concern / risk
    Emotion.SAD: 5,          # Negative but lower urgency
    Emotion.NEUTRAL: 0,      # No emotional signal
}


@dataclass
class EmotionResult:
    emotion: Emotion
    confidence: float          # 0.0 - 1.0
    all_scores: dict           # {emotion_name: score}
    importance_weight: int     # contribution to importance score (0-15)


class EmotionDetector:
    """
    Wav2Vec2-based emotion classifier.

    In production: loads 'ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition'
    or similar. Falls back to a prosody-heuristic stub when torch/transformers
    are not installed so the rest of the pipeline can run in lightweight
    environments (e.g. CI, demo mode).
    """

    # HuggingFace model IDs to try in order
    MODEL_IDS = [
        "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition",
        "superb/wav2vec2-base-superb-er",
    ]
    EMOTIONS = [e.value for e in Emotion]

    def __init__(self, model_id: Optional[str] = None, device: str = "cpu"):
        self.device = device
        self._model = None
        self._processor = None
        self._model_id = model_id or self.MODEL_IDS[0]
        self._loaded = False
        self._stub_mode = False

    # ------------------------------------------------------------------
    # Lazy model loading
    # ------------------------------------------------------------------

    def _ensure_loaded(self) -> bool:
        """Try to load the model once; return True if succeeded."""
        if self._loaded:
            return not self._stub_mode

        try:
            from transformers import (
                Wav2Vec2ForSequenceClassification,
                Wav2Vec2Processor,
            )
            import torch  # noqa: F401

            self._processor = Wav2Vec2Processor.from_pretrained(self._model_id)
            self._model = Wav2Vec2ForSequenceClassification.from_pretrained(
                self._model_id
            ).to(self.device)
            self._model.eval()
            self._loaded = True
            self._stub_mode = False
            logger.info(f"Emotion model loaded: {self._model_id}")
            return True

        except Exception as exc:
            logger.warning(
                f"Could not load emotion model ({exc}). "
                "Running in heuristic stub mode."
            )
            self._loaded = True
            self._stub_mode = True
            return False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(
        self,
        audio_samples: np.ndarray,
        sample_rate: int = 16000,
    ) -> EmotionResult:
        """
        Detect emotion from raw audio samples.

        Args:
            audio_samples: 1-D float32 array, mono, any duration.
            sample_rate: Hz. Model expects 16 kHz; resampled automatically.

        Returns:
            EmotionResult with dominant emotion, confidence, and all scores.
        """
        if len(audio_samples) == 0:
            return self._neutral_result()

        # Resample to 16 kHz if needed
        audio_16k = self._maybe_resample(audio_samples, sample_rate, 16000)

        if self._ensure_loaded():
            return self._ml_detect(audio_16k)
        else:
            return self._heuristic_detect(audio_16k)

    # ------------------------------------------------------------------
    # ML-based detection
    # ------------------------------------------------------------------

    def _ml_detect(self, audio_16k: np.ndarray) -> EmotionResult:
        import torch

        inputs = self._processor(
            audio_16k.astype(np.float32),
            sampling_rate=16000,
            return_tensors="pt",
            padding=True,
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            logits = self._model(**inputs).logits

        probs = torch.softmax(logits, dim=-1).squeeze().cpu().numpy()

        # Map model label indices to our Emotion enum
        id2label = self._model.config.id2label
        scores = {}
        for idx, prob in enumerate(probs):
            raw_label = id2label.get(idx, "neutral").lower()
            # Normalize label to our set
            emotion_label = self._normalize_label(raw_label)
            scores[emotion_label] = float(scores.get(emotion_label, 0.0) + prob)

        # Fill any missing emotions with 0
        for e in self.EMOTIONS:
            scores.setdefault(e, 0.0)

        dominant = max(scores, key=scores.get)
        emotion = Emotion(dominant)

        return EmotionResult(
            emotion=emotion,
            confidence=scores[dominant],
            all_scores=scores,
            importance_weight=EMOTION_IMPORTANCE_WEIGHTS[emotion],
        )

    # ------------------------------------------------------------------
    # Heuristic stub (no ML dependencies required)
    # ------------------------------------------------------------------

    def _heuristic_detect(self, audio_16k: np.ndarray) -> EmotionResult:
        """
        Estimates emotion from basic signal features when the ML model
        is unavailable.  Less accurate but always available.
        """
        if len(audio_16k) == 0:
            return self._neutral_result()

        rms = float(np.sqrt(np.mean(audio_16k ** 2)))
        # Crude zero-crossing rate as proxy for arousal
        zcr = float(np.mean(np.abs(np.diff(np.sign(audio_16k)))) / 2)

        # Very rough heuristic buckets
        if rms > 0.15 and zcr > 0.15:
            emotion, confidence = Emotion.ANGRY, 0.55
        elif rms > 0.10 and zcr > 0.10:
            emotion, confidence = Emotion.HAPPY, 0.50
        elif rms < 0.03:
            emotion, confidence = Emotion.SAD, 0.45
        elif zcr > 0.20:
            emotion, confidence = Emotion.SURPRISED, 0.48
        elif rms < 0.02:
            emotion, confidence = Emotion.FEARFUL, 0.40
        else:
            emotion, confidence = Emotion.NEUTRAL, 0.60

        scores = {e: 0.05 for e in self.EMOTIONS}
        scores[emotion.value] = confidence

        return EmotionResult(
            emotion=emotion,
            confidence=confidence,
            all_scores=scores,
            importance_weight=EMOTION_IMPORTANCE_WEIGHTS[emotion],
        )

    def detect_emotion(
        self,
        audio_samples: np.ndarray,
        sample_rate: int = 16000,
    ) -> dict:
        """
        Compatibility wrapper used by pipeline.py.
        Returns dict with keys: 'emotion', 'confidence', 'all_scores', 'importance_weight'.
        """
        result = self.detect(audio_samples, sample_rate)
        return {
            "emotion": result.emotion.value,
            "confidence": result.confidence,
            "all_scores": result.all_scores,
            "importance_weight": result.importance_weight,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _neutral_result(self) -> EmotionResult:
        scores = {e: 0.0 for e in self.EMOTIONS}
        scores[Emotion.NEUTRAL.value] = 1.0
        return EmotionResult(
            emotion=Emotion.NEUTRAL,
            confidence=1.0,
            all_scores=scores,
            importance_weight=0,
        )

    @staticmethod
    def _maybe_resample(
        audio: np.ndarray, src_rate: int, tgt_rate: int
    ) -> np.ndarray:
        if src_rate == tgt_rate:
            return audio
        try:
            import librosa
            return librosa.resample(audio.astype(np.float32), orig_sr=src_rate, target_sr=tgt_rate)
        except ImportError:
            # Naive linear resample fallback
            ratio = tgt_rate / src_rate
            new_len = int(len(audio) * ratio)
            indices = np.linspace(0, len(audio) - 1, new_len)
            return np.interp(indices, np.arange(len(audio)), audio).astype(np.float32)

    @staticmethod
    def _normalize_label(raw: str) -> str:
        mapping = {
            "ang": "angry", "anger": "angry",
            "hap": "happy", "happiness": "happy", "joy": "happy",
            "sad": "sad", "sadness": "sad",
            "neu": "neutral",
            "fea": "fearful", "fear": "fearful",
            "sur": "surprised", "surprise": "surprised", "dis": "surprised",
        }
        for key, val in mapping.items():
            if key in raw:
                return val
        # If already a valid emotion name, use it
        for e in [e.value for e in Emotion]:
            if e in raw:
                return e
        return "neutral"


# ------------------------------------------------------------------
# Demo / smoke test
# ------------------------------------------------------------------

def demo():
    print("=== EmotionDetector Demo ===\n")
    detector = EmotionDetector()

    # Synthetic test signals
    sr = 16000
    duration = 2.0  # seconds
    t = np.linspace(0, duration, int(sr * duration))

    samples = {
        "Loud energetic signal (→ angry/happy)": (np.sin(2 * np.pi * 300 * t) * 0.3).astype(np.float32),
        "Quiet monotone signal (→ neutral/sad)": (np.sin(2 * np.pi * 100 * t) * 0.01).astype(np.float32),
        "High-freq noisy signal (→ surprised)": (np.random.randn(len(t)) * 0.25).astype(np.float32),
    }

    for label, audio in samples.items():
        result = detector.detect(audio, sr)
        print(f"{label}")
        print(f"  Detected: {result.emotion.value.upper()} "
              f"(confidence={result.confidence:.2f}, "
              f"importance_weight={result.importance_weight})")
        top3 = sorted(result.all_scores.items(), key=lambda x: -x[1])[:3]
        print(f"  Top-3 scores: {', '.join(f'{k}={v:.2f}' for k, v in top3)}\n")


if __name__ == "__main__":
    demo()
