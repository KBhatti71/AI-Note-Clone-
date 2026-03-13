"""
NeuroApp FastAPI Backend
Endpoints:
  POST /api/analyze  - Upload audio, transcribe, score, return segments
  GET  /api/health   - Health check
  /api/meetings/...  - CRUD via sub-router
"""

import os
import sys
import uuid
import tempfile
import logging
from pathlib import Path
from collections import Counter

import numpy as np
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add backend root to path so audio_processing imports work from any cwd
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger("neuroapp")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="NeuroApp API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.routes.meetings import router as meetings_router  # noqa: E402
from api.routes.folders import router as folders_router    # noqa: E402
from api.routes.notes import router as notes_router        # noqa: E402
from api.routes.search import router as search_router      # noqa: E402
from api.routes.ocr import router as ocr_router            # noqa: E402

app.include_router(meetings_router, prefix="/api/meetings", tags=["meetings"])
app.include_router(folders_router, prefix="/api/folders", tags=["folders"])
app.include_router(notes_router, prefix="/api/notes", tags=["notes"])
app.include_router(search_router, prefix="/api/search", tags=["search"])
app.include_router(ocr_router, prefix="/api/ocr", tags=["ocr"])


# ---------------------------------------------------------------------------
# Lazy model / pipeline loading
# ---------------------------------------------------------------------------

_whisper = None
_pipelines: dict = {}   # context_str -> AudioIntelligencePipeline


def get_whisper():
    global _whisper
    if _whisper is None:
        try:
            import whisper
            model_name = os.getenv("WHISPER_MODEL", "base")
            logger.info(f"Loading Whisper model '{model_name}'...")
            _whisper = whisper.load_model(model_name)
            logger.info("Whisper ready.")
        except ImportError:
            logger.warning("openai-whisper not installed. Run: pip install openai-whisper")
    return _whisper


def get_pipeline(context_str: str):
    """Return (or create) a cached pipeline for the given context string."""
    global _pipelines
    if context_str not in _pipelines:
        from audio_processing.pipeline import AudioIntelligencePipeline
        from audio_processing.importance_scorer import Context as CtxEnum
        ctx_map = {
            "school":  CtxEnum.SCHOOL,
            "work":    CtxEnum.WORK,
            "general": CtxEnum.GENERAL,
        }
        ctx = ctx_map.get(context_str, CtxEnum.GENERAL)
        logger.info(f"Creating pipeline for context={context_str}")
        _pipelines[context_str] = AudioIntelligencePipeline(context=ctx)
    return _pipelines[context_str]


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class ProsodyFeatures(BaseModel):
    pitch_mean: float = 0.0
    pitch_std: float = 0.0
    intensity_mean: float = 0.0
    speaking_rate: float = 0.0
    pause_count: int = 0
    vocal_emphasis_score: float = 0.0
    speaking_pattern_score: float = 0.0


class SegmentResponse(BaseModel):
    id: str
    text: str
    start_time: float
    end_time: float
    speaker: str
    importance_score: int
    importance_level: str
    emotion: str
    prosody: ProsodyFeatures
    score_breakdown: dict
    recommendations: list[str]


class SummaryResponse(BaseModel):
    total_segments: int
    high_importance_count: int
    medium_importance_count: int
    low_importance_count: int
    average_importance: float
    dominant_emotion: str
    top_moments: list[dict]
    recommendations: list[str]


class AnalyzeResponse(BaseModel):
    meeting_id: str
    context: str
    duration: float
    segments: list[SegmentResponse]
    summary: SummaryResponse


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "neuroapp"}


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_audio(
    file: UploadFile = File(...),
    context: str = Form("work"),
):
    if context not in ("school", "work", "general"):
        raise HTTPException(400, "context must be 'school', 'work', or 'general'")

    suffix = Path(file.filename or "audio.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        return await _run_pipeline(tmp_path, context)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Pipeline execution
# ---------------------------------------------------------------------------

async def _run_pipeline(audio_path: str, context: str) -> AnalyzeResponse:
    try:
        import librosa
    except ImportError:
        raise HTTPException(503, "librosa not installed. Run: pip install librosa")

    # Load mono 16 kHz audio
    audio_samples, sr = librosa.load(audio_path, sr=16000, mono=True)
    duration = float(len(audio_samples) / sr)

    # Transcribe with Whisper
    whisper_model = get_whisper()
    if whisper_model is None:
        raise HTTPException(503, "Whisper unavailable. Run: pip install openai-whisper")

    result = whisper_model.transcribe(audio_path, language="en")
    whisper_segments = result.get("segments", [])
    if not whisper_segments:
        whisper_segments = [{"start": 0.0, "end": duration, "text": result.get("text", "")}]

    # Get context-aware pipeline (cached per context string)
    pipeline = get_pipeline(context)

    scored_segments: list[SegmentResponse] = []
    analyzed_list = []   # List[AnalyzedSegment] for generate_summary()

    for wseg in whisper_segments:
        text  = wseg.get("text", "").strip()
        start = float(wseg.get("start", 0.0))
        end   = float(wseg.get("end", start + 0.5))

        # Slice audio for this segment
        s_idx = int(start * sr)
        e_idx = min(int(end * sr), len(audio_samples))
        seg_audio = (
            audio_samples[s_idx:e_idx]
            if e_idx > s_idx
            else np.zeros(int(sr * 0.5), dtype=np.float32)
        )

        # Correct signature: analyze_segment(audio, transcript, start_time, end_time, speaker)
        analyzed = pipeline.analyze_segment(
            audio=seg_audio,
            transcript=text,
            start_time=start,
            end_time=end,
            speaker="speaker_0",
        )
        analyzed_list.append(analyzed)

        prosody = analyzed.prosody_features or {}
        scored_segments.append(SegmentResponse(
            id=str(uuid.uuid4()),
            text=analyzed.text,
            start_time=analyzed.start_time,
            end_time=analyzed.end_time,
            speaker=analyzed.speaker or "speaker_0",
            importance_score=int(analyzed.importance_score),
            importance_level=analyzed.importance_level,
            emotion=analyzed.emotion or "neutral",
            prosody=ProsodyFeatures(
                pitch_mean=float(prosody.get("pitch_mean", 0.0)),
                pitch_std=float(prosody.get("pitch_std", 0.0)),
                intensity_mean=float(prosody.get("intensity_mean", 0.0)),
                speaking_rate=float(prosody.get("speaking_rate", 0.0)),
                pause_count=int(prosody.get("pause_count", 0)),
                vocal_emphasis_score=float(prosody.get("vocal_emphasis_score", 0.0)),
                speaking_pattern_score=float(prosody.get("speaking_pattern_score", 0.0)),
            ),
            # AnalyzedSegment stores field as .breakdown (not .score_breakdown)
            score_breakdown={k: float(v) for k, v in (analyzed.breakdown or {}).items()},
            recommendations=analyzed.recommendations or [],
        ))

    # generate_summary() signature: takes List[AnalyzedSegment], returns dict
    raw_summary = pipeline.generate_summary(analyzed_list)
    summary = _build_summary(raw_summary, scored_segments)

    return AnalyzeResponse(
        meeting_id=str(uuid.uuid4()),
        context=context,
        duration=duration,
        segments=scored_segments,
        summary=summary,
    )


def _build_summary(raw: dict, segments: list[SegmentResponse]) -> SummaryResponse:
    """Convert pipeline.generate_summary() dict into SummaryResponse Pydantic model."""
    emotion_counts = Counter(s.emotion for s in segments)
    dominant = emotion_counts.most_common(1)[0][0] if emotion_counts else "neutral"

    top_moments = [
        {
            "text":       m.get("text", "")[:120],
            "score":      m.get("score", 0),
            "start_time": float(m.get("timestamp", 0.0)),
        }
        for m in raw.get("top_moments", [])
    ]

    avg = raw.get("average_importance", 0.0)
    if hasattr(avg, "item"):   # handle numpy scalar
        avg = avg.item()

    return SummaryResponse(
        total_segments=int(raw.get("total_segments", len(segments))),
        high_importance_count=int(raw.get("high_importance_count", 0)),
        medium_importance_count=int(raw.get("medium_importance_count", 0)),
        low_importance_count=int(raw.get("low_importance_count", 0)),
        average_importance=float(avg),
        dominant_emotion=dominant,
        top_moments=top_moments,
        recommendations=raw.get("recommendations", []),
    )
