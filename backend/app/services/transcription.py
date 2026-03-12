import tempfile
from typing import Dict, List, Tuple

import librosa
import numpy as np
import whisper

from app.analyzers.importance_scorer import TranscriptSegment

_MODEL_CACHE: Dict[str, whisper.Whisper] = {}


def _get_model(model_name: str) -> whisper.Whisper:
    if model_name not in _MODEL_CACHE:
        _MODEL_CACHE[model_name] = whisper.load_model(model_name)
    return _MODEL_CACHE[model_name]


def transcribe_file(path: str, model_name: str = "base") -> Dict:
    model = _get_model(model_name)
    return model.transcribe(path)


def load_audio(path: str, sample_rate: int = 16000) -> Tuple[np.ndarray, int]:
    audio, sr = librosa.load(path, sr=sample_rate, mono=True)
    return audio, sr


def segments_from_whisper(result: Dict) -> List[TranscriptSegment]:
    segments: List[TranscriptSegment] = []
    for seg in result.get("segments", []):
        segments.append(
            TranscriptSegment(
                text=str(seg.get("text", "")).strip(),
                start_time=float(seg.get("start", 0.0)),
                end_time=float(seg.get("end", 0.0)),
            )
        )
    return segments

