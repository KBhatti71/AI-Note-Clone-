import numpy as np
from transformers import pipeline


class EmotionDetector:
    """
    Detects emotion from audio using a Wav2Vec2-based model.
    Maps emotions to an importance_boost score.
    """

    DEFAULT_MODEL = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"

    def __init__(self, use_mock: bool = False, model_name: str = DEFAULT_MODEL, device: int = -1):
        self.use_mock = use_mock
        self.model_name = model_name
        self.device = device
        self._pipeline = None

    def _get_pipeline(self):
        if self._pipeline is None:
            try:
                self._pipeline = pipeline(
                    task="audio-classification",
                    model=self.model_name,
                    device=self.device,
                )
            except Exception as exc:
                raise RuntimeError(
                    "Failed to initialize emotion model. Ensure dependencies are installed "
                    "and the model can be downloaded."
                ) from exc
        return self._pipeline

    def detect_emotion(self, audio: np.ndarray, sample_rate: int = 16000) -> dict:
        """
        Detect emotion from raw audio array and return the result + importance boost.
        """
        # In mock mode, return a deterministic heuristic for tests.
        if self.use_mock:
            mean_amplitude = np.mean(np.abs(audio)) if len(audio) > 0 else 0

            if mean_amplitude > 0.05:
                emotion = "fearful"
                boost = 15
            elif mean_amplitude > 0.02:
                emotion = "angry"
                boost = 8
            else:
                emotion = "neutral"
                boost = 0

            return {
                "emotion": emotion,
                "importance_boost": boost,
            }

        classifier = self._get_pipeline()
        results = classifier({"array": audio.astype(np.float32), "sampling_rate": sample_rate})
        if not results:
            return {"emotion": "neutral", "importance_boost": 0}

        top = results[0]
        label = str(top.get("label", "neutral")).lower()
        importance_boost = self._map_emotion_boost(label)

        return {
            "emotion": label,
            "importance_boost": importance_boost,
            "confidence": float(top.get("score", 0.0)),
        }

    def _map_emotion_boost(self, label: str) -> int:
        mapping = {
            "angry": 12,
            "fear": 15,
            "fearful": 15,
            "sad": 6,
            "happy": 8,
            "excited": 12,
            "neutral": 0,
            "calm": 0,
        }
        return int(mapping.get(label, 0))
