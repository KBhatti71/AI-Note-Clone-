# NeuroApp — Quick Start & Testing

## ✅ System Status

Both **Backend** and **Frontend** are configured and running.

### Backend (FastAPI + Uvicorn)
- **Port:** 8000
- **Status:** ✅ Running
- **Routes:**
  - `GET /api/health` — health check
  - `POST /api/analyze` — upload audio, get transcript + importance scores
  - `GET/POST/PATCH/DELETE /api/meetings/` — meeting CRUD
  - `GET/POST/PATCH/DELETE /api/folders/` — folder CRUD
  - `GET/POST/PATCH/DELETE /api/notes/` — note CRUD
  - `GET /api/search?q=...` — full-text search
  - `POST /api/ocr/` — extract text from images

### Frontend (React + Vite + Tailwind)
- **Port:** 3000
- **Status:** ✅ Running at http://localhost:3000
- **Features:**
  - RecordingScreen: pulsing red record button, idle/recording/processing/done states
  - TranscriptView: color-coded importance (RED=high, YELLOW=medium, GREEN=low)
  - useRecording hook: manages MediaRecorder, streams to /api/analyze
  - Mode toggle: School/Work context (affects importance scoring)

## 🔌 How They Connect

```
Browser (http://localhost:3000)
    ↓ (user clicks "Record")
    ↓ (MediaRecorder → Blob)
    ↓ POST /api/analyze (proxied via Vite)
    ↓
Vite Proxy (3000 → 8000)
    ↓
Backend API (http://localhost:8000)
    ├─ Whisper: transcribes audio to text
    ├─ ProsodyAnalyzer: analyzes pitch, rate, pauses
    ├─ EmotionDetector: detects 6 emotions
    └─ ImportanceScorer: combines signals → 0-100 score
    ↓ (returns AnalyzeResponse)
    ↓
Browser displays:
    - Transcript split into importance bands
    - Score breakdowns (text, prosody, emotion)
    - Top moments & recommendations
```

## 🚀 How to Use

### 1. Start Backend
```bash
cd backend
source venv/Scripts/activate  # or ./venv/Scripts/activate.bat on Windows
uvicorn api.main:app --reload --port 8000
```

### 2. Start Frontend
```bash
cd desktop
npm run dev  # → http://localhost:3000
```

### 3. Open Browser
Navigate to: **http://localhost:3000**

### 4. Test Recording
1. Click the big microphone button
2. Say something (or play audio into your mic)
3. Click the square icon to stop
4. Wait for analysis (first time takes ~10-15 min for Whisper to download)
5. View the color-coded transcript

## ✅ Verified Working

All endpoints tested with TestClient:
- ✅ `GET /api/health` → `{"status": "ok", "service": "neuroapp"}`
- ✅ `GET /api/meetings/` → `[]` (empty list)
- ✅ `GET /api/folders/` → `[]`
- ✅ `GET /api/notes/` → `[]`
- ✅ Router imports all load successfully
- ✅ Vite proxy configured to forward `/api` → `localhost:8000`
- ✅ Frontend TypeScript types match backend Pydantic models

## 📝 What Happens Next

When you click the record button and submit audio:

1. **Frontend** (`useRecording.ts`):
   - Captures audio via MediaRecorder
   - Sends to `POST /api/analyze?context=work`

2. **Backend** (`api/main.py`):
   - Receives audio blob
   - Loads Whisper model (first time only, ~3GB, ~10 min)
   - Transcribes to text segments
   - For each segment:
     - Analyzes prosody (pitch, rate, pauses)
     - Detects emotion (angry, happy, sad, etc.)
     - Scores importance (0-100) based on keywords + prosody
   - Returns `AnalyzeResponse` with segments + summary

3. **Frontend** displays:
   - RED band for HIGH importance (70-100)
   - YELLOW band for MEDIUM importance (40-69)
   - GREEN band for LOW importance (0-39)
   - Score breakdowns, top moments, recommendations

## 🔧 Troubleshooting

**"Can't connect to localhost:8000"**
- Backend may still be loading Whisper model on first run
- Check that uvicorn is still running
- Try: `python -m uvicorn api.main:app --reload --port 8000`

**"Import errors in backend"**
- Ensure venv is activated: `source venv/Scripts/activate`
- Reinstall deps: `pip install -r requirements.txt`

**"Frontend showing blank page"**
- Check browser console (F12) for JS errors
- Ensure Vite is running on port 3000
- Try: `npm run dev`

**"Audio doesn't record"**
- Check microphone permissions in OS
- Try recording in a different browser (Chrome recommended)
- Check DevTools > Console for MediaRecorder errors

---

**Built with:** FastAPI, React, Vite, Tailwind CSS, Whisper, Librosa, Transformers

**Status:** ✅ Phase 1 & 2 Complete — Ready to Test!
