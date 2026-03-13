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
import asyncio
import threading
from pathlib import Path
from collections import Counter

import numpy as np
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add backend root to path so audio_processing imports work from any cwd
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger("neuroapp")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(title="NeuroApp API", version="0.1.0")

# Fix CORS: only allow localhost in dev, restrict in production
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]
if os.getenv("ENV") != "development":
    ALLOWED_ORIGINS = []  # Production: explicitly configure via env vars

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type"],
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
# Lazy model / pipeline loading with thread safety
# ---------------------------------------------------------------------------

_whisper = None
_whisper_lock = threading.Lock()  # Thread lock for Whisper initialization
_pipelines: dict = {}   # context_str -> AudioIntelligencePipeline
_pipeline_lock = threading.Lock()  # Thread lock for pipeline cache


def get_whisper():
    """Get or load Whisper model with thread safety."""
    global _whisper
    if _whisper is not None:
        return _whisper

    with _whisper_lock:
        # Double-check pattern
        if _whisper is not None:
            return _whisper

        try:
            import whisper
            model_name = os.getenv("WHISPER_MODEL", "base")
            logger.info(f"Loading Whisper model '{model_name}'...")
            _whisper = whisper.load_model(model_name)
            logger.info("Whisper ready.")
            return _whisper
        except ImportError:
            logger.error("openai-whisper not installed. Run: pip install openai-whisper")
            return None
        except Exception as exc:
            logger.error(f"Failed to load Whisper model: {exc}")
            return None


def get_pipeline(context_str: str):
    """Return (or create) a cached pipeline for the given context string, thread-safe."""
    global _pipelines
    if context_str in _pipelines:
        return _pipelines[context_str]

    with _pipeline_lock:
        # Double-check pattern
        if context_str in _pipelines:
            return _pipelines[context_str]

        try:
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
        except Exception as exc:
            logger.error(f"Failed to create pipeline: {exc}")
            return None


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
    """Health check endpoint."""
    return {"status": "ok", "service": "neuroapp"}


def _validate_audio_file(filename: str) -> str:
    """
    Validate audio file format and return safe suffix.

    Args:
        filename: Original filename from upload

    Returns:
        Safe suffix for tempfile (e.g., '.wav', '.mp3', '.m4a')

    Raises:
        HTTPException: If file format is not supported
    """
    allowed_formats = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}
    suffix = (Path(filename or "audio.wav").suffix or ".wav").lower()

    if suffix not in allowed_formats:
        raise HTTPException(
            400,
            f"Unsupported audio format '{suffix}'. "
            f"Supported: {', '.join(allowed_formats)}"
        )
    return suffix


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_audio(
    file: UploadFile = File(...),
    context: str = Form("work"),
):
    """
    Analyze uploaded audio file: transcribe, score importance, detect emotions.

    Args:
        file: Audio file upload
        context: Analysis context ('school', 'work', or 'general')

    Returns:
        AnalyzeResponse with segments and summary

    Raises:
        HTTPException: On validation or processing errors
    """
    logger.info(f"Received analyze request: filename={file.filename}, context={context}")

    if context not in ("school", "work", "general"):
        logger.warning(f"Invalid context: {context}")
        raise HTTPException(400, "context must be 'school', 'work', or 'general'")

    # Validate audio file format
    try:
        suffix = _validate_audio_file(file.filename)
    except HTTPException:
        raise

    # Create temp file with proper error handling
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            if not content:
                raise HTTPException(400, "Uploaded file is empty")
            tmp.write(content)
            tmp_path = tmp.name
        logger.info(f"Temp file created: {tmp_path}")

        return await _run_pipeline(tmp_path, context)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error during analysis: {exc}")
        raise HTTPException(500, f"Analysis failed: {str(exc)}")
    finally:
        # Clean up temp file
        if tmp_path:
            try:
                os.unlink(tmp_path)
                logger.debug(f"Temp file deleted: {tmp_path}")
            except OSError as exc:
                logger.warning(f"Failed to delete temp file {tmp_path}: {exc}")


# ---------------------------------------------------------------------------
# Pipeline execution
# ---------------------------------------------------------------------------

async def _run_pipeline(audio_path: str, context: str) -> AnalyzeResponse:
    """
    Run the full analysis pipeline: load audio, transcribe, analyze segments.

    Args:
        audio_path: Path to audio file
        context: Analysis context

    Returns:
        AnalyzeResponse with complete analysis

    Raises:
        HTTPException: On processing errors
    """
    logger.info(f"Pipeline starting: {audio_path}, context={context}")

    # Load audio asynchronously to avoid blocking
    try:
        audio_samples, sr = await _load_audio_async(audio_path)
    except ImportError:
        raise HTTPException(503, "librosa not installed. Run: pip install librosa")
    except Exception as exc:
        logger.error(f"Failed to load audio: {exc}")
        raise HTTPException(400, f"Failed to load audio file: {str(exc)}")

    duration = float(len(audio_samples) / sr)
    logger.info(f"Audio loaded: duration={duration:.2f}s, sr={sr}Hz")

    # Transcribe with Whisper (with error handling)
    try:
        whisper_model = get_whisper()
        if whisper_model is None:
            raise HTTPException(
                503,
                "Whisper unavailable. Run: pip install openai-whisper"
            )

        result = await _transcribe_async(whisper_model, audio_path)
        whisper_segments = result.get("segments", [])
        if not whisper_segments:
            whisper_segments = [
                {"start": 0.0, "end": duration, "text": result.get("text", "")}
            ]
        logger.info(f"Transcription complete: {len(whisper_segments)} segments")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Transcription failed: {exc}")
        raise HTTPException(500, f"Transcription failed: {str(exc)}")

    # Get context-aware pipeline (cached per context string)
    pipeline = get_pipeline(context)
    if pipeline is None:
        raise HTTPException(500, "Failed to initialize analysis pipeline")

    scored_segments: list[SegmentResponse] = []
    analyzed_list = []   # List[AnalyzedSegment] for generate_summary()
    speaker_map = {}     # Track unique speakers for speaker separation

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

        # Simple speaker tracking: use detected speaker or assign sequential
        speaker = wseg.get("speaker", None) or "speaker_0"
        if speaker not in speaker_map:
            speaker_map[speaker] = f"speaker_{len(speaker_map)}"
        speaker = speaker_map[speaker]

        # Analyze segment with error handling
        try:
            analyzed = pipeline.analyze_segment(
                audio=seg_audio,
                transcript=text,
                start_time=start,
                end_time=end,
                speaker=speaker,
            )
            analyzed_list.append(analyzed)

            prosody = analyzed.prosody_features or {}
            scored_segments.append(SegmentResponse(
                id=str(uuid.uuid4()),
                text=analyzed.text,
                start_time=analyzed.start_time,
                end_time=analyzed.end_time,
                speaker=analyzed.speaker or speaker,
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
                score_breakdown={k: float(v) for k, v in (analyzed.breakdown or {}).items()},
                recommendations=analyzed.recommendations or [],
            ))
        except Exception as exc:
            logger.error(f"Segment analysis failed: {exc}")
            # Continue processing other segments instead of failing completely
            continue

    # Generate summary
    try:
        raw_summary = pipeline.generate_summary(analyzed_list)
        summary = _build_summary(raw_summary, scored_segments)
    except Exception as exc:
        logger.error(f"Summary generation failed: {exc}")
        raise HTTPException(500, f"Summary generation failed: {str(exc)}")

    logger.info(f"Pipeline complete: {len(scored_segments)} segments analyzed")

    return AnalyzeResponse(
        meeting_id=str(uuid.uuid4()),
        context=context,
        duration=duration,
        segments=scored_segments,
        summary=summary,
    )


async def _load_audio_async(audio_path: str) -> tuple[np.ndarray, int]:
    """
    Load audio asynchronously using asyncio.to_thread() to avoid blocking.

    Args:
        audio_path: Path to audio file

    Returns:
        Tuple of (audio_samples, sample_rate)
    """
    def _load():
        import librosa
        return librosa.load(audio_path, sr=16000, mono=True)

    return await asyncio.to_thread(_load)


async def _transcribe_async(whisper_model, audio_path: str) -> dict:
    """
    Transcribe audio asynchronously using asyncio.to_thread() to avoid blocking.

    Args:
        whisper_model: Loaded Whisper model
        audio_path: Path to audio file

    Returns:
        Transcription result dict
    """
    def _transcribe():
        return whisper_model.transcribe(audio_path, language="en")

    return await asyncio.to_thread(_transcribe)


def _build_summary(raw: dict, segments: list[SegmentResponse]) -> SummaryResponse:
    """
    Convert pipeline.generate_summary() dict into SummaryResponse Pydantic model.

    Args:
        raw: Raw summary dict from pipeline
        segments: List of analyzed segments

    Returns:
        SummaryResponse with formatted data
    """
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
