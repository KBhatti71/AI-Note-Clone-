import os
import tempfile
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

from app.analyzers.emotion_detector import EmotionDetector
from app.analyzers.importance_scorer import Context, ImportanceScorer
from app.analyzers.prosody_analyzer import ProsodyAnalyzer
from app.services.notes import generate_notes
from app.services.transcription import load_audio, segments_from_whisper, transcribe_file

app = FastAPI(title="NeuroApp Backend", description="Importance Scoring Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/analyze")
async def analyze_audio(
    audio: UploadFile = File(...),
    context: str = Form("general"),
    use_mock_emotion: bool = Form(True),
    whisper_model: str = Form("base"),
):
    context_value = context.strip().lower()
    if context_value not in {"school", "work", "general"}:
        context_value = "general"
    suffix = os.path.splitext(audio.filename or "audio.wav")[1] or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name

    result = transcribe_file(tmp_path, model_name=whisper_model)
    transcript = str(result.get("text", "")).strip()
    segments = segments_from_whisper(result)

    audio_array, sr = load_audio(tmp_path, sample_rate=16000)

    scorer = ImportanceScorer(context=Context(context_value))
    prosody = ProsodyAnalyzer(sample_rate=sr)
    emotion = EmotionDetector(use_mock=use_mock_emotion)

    scored_segments = []
    for seg in segments:
        start_idx = int(seg.start_time * sr)
        end_idx = int(seg.end_time * sr)
        segment_audio = audio_array[start_idx:end_idx] if end_idx > start_idx else audio_array[:1]
        prosody_features = prosody.analyze_segment(segment_audio)
        emotion_result = emotion.detect_emotion(segment_audio, sample_rate=sr) if segment_audio.size > 0 else None
        scored = scorer.score_segment(seg, prosody_features, emotion_result=emotion_result)
        scored_segments.append(scored)

    notes = generate_notes(transcript, scored_segments, context=context_value)

    return {
        "transcript": transcript,
        "segments": scored_segments,
        "notes": notes,
    }
