# NeuroApp — Quick Start Guide

**Latest Version:** 2.0 Optimized
**Status:** ✅ Ready to use

---

## 📥 One-Time Setup

### 1. Clone & Install

```bash
git clone https://github.com/KBhatti71/AI-Note-Clone-.git
cd AI-Note-Clone--main
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment (one time)
python3 -m venv venv
source venv/Scripts/activate  # or: venv\Scripts\activate.bat (Windows)

# Install dependencies (one time)
pip install -r requirements.txt

# Create .env file (one time)
cp .env.example .env
# Edit .env if needed (WHISPER_MODEL, OpenAI key, etc.)
```

### 3. Frontend Setup

```bash
cd ../desktop

# Install dependencies (one time)
npm install
```

---

## 🚀 Running the App

### Terminal 1 — Backend Server

```bash
cd backend
source venv/Scripts/activate  # Activate venv (every session)
uvicorn api.main:app --reload --port 8000
```

**Output should show:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Terminal 2 — Frontend Dev Server

```bash
cd desktop
npm run dev
```

**Output should show:**
```
➜  Local:   http://localhost:3000/
```

### Open in Browser

```
http://localhost:3000
```

> **Note:** First time only, Whisper will download ~140 MB model (5-10 min)

---

## 🎯 Basic Usage

### 1. Select Mode
- **Work Mode** (💼) — For meetings, presentations, work notes
- **School Mode** (📚) — For lectures, studying, learning

### 2. Record Audio
1. Click the big **microphone button**
2. Start speaking (or play audio from speakers)
3. Click the **square button** to stop
4. Wait for analysis...

### 3. View Results
Once analysis completes, you'll see:
- **RED segments** = High importance (70-100)
- **YELLOW segments** = Medium importance (40-69)
- **GREEN segments** = Low importance (0-39)

Click any segment to expand and see:
- Emotion detected
- Prosody details (pitch, rate, pauses)
- Score breakdown (why important?)
- Recommendations (flashcard, study note, etc.)

### 4. Export & Share
Click **"Export Transcript"** to download analysis as text file.

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Space` | Start/stop recording |
| `Escape` | Cancel recording/analysis |
| `Cmd/Ctrl + E` | Export transcript |
| `Cmd/Ctrl + R` | Retry last analysis |

---

## 🐛 Troubleshooting

### "Microphone not working"
- Check OS permissions (Settings → Privacy → Microphone)
- Try using Chrome instead of Safari
- Check browser console (F12) for errors

### "Analysis takes forever"
- First run downloads model (~10 min) — normal
- If using "tiny" model: ~1 min per 5 min audio
- Try smaller file (30 sec audio) to test
- Check CPU usage (should be ~100% during analysis)

### "Backend won't start"
```bash
# Make sure FFmpeg is installed
ffmpeg -version

# If not installed:
# macOS: brew install ffmpeg
# Windows: winget install ffmpeg
# Linux: apt-get install ffmpeg
```

### "Port already in use"
```bash
# Kill existing process on port 8000
lsof -i :8000  # Shows PID
kill -9 <PID>

# Or use different port:
uvicorn api.main:app --port 8001
```

### "CORS error in console"
- Make sure backend is on `http://localhost:8000`
- Frontend should be on `http://localhost:3000` (or 3001/3002/3003)
- Vite proxy automatically forwards `/api` to backend

---

## 📊 Understanding Results

### Importance Score (0-100)
Based on:
- **Keywords** — "important", "remember", "critical", etc.
- **Prosody** — Slower speaking = important, emphasized
- **Emotion** — Angry/fearful = important signal
- **Context** — School vs Work affects scoring

### Emotions Detected
- 😠 **Angry** — High arousal, important
- 😊 **Happy** — Positive, lighter mood
- 😢 **Sad** — Emotional, pay attention
- 😨 **Fearful** — Urgent, important
- 😐 **Neutral** — Default/baseline
- 😲 **Surprised** — Unexpected, notable

### Recommendations

**Work Mode:**
- 📝 Add to meeting notes
- ✅ Create action item
- 📅 Schedule follow-up
- 📢 Share with team

**School Mode:**
- 📚 Include in study guide
- 📝 Create flashcard
- ⭐ Mark for exam review
- 🎯 Create practice question

---

## 🔧 Configuration

### Whisper Model Quality/Speed Tradeoff

In `backend/.env`, set `WHISPER_MODEL`:

```env
WHISPER_MODEL=tiny      # Fastest (~1 min per 5 min audio) - 75M params
WHISPER_MODEL=base      # Balanced (~2-5 min per 5 min audio) - 140M params
WHISPER_MODEL=small     # Better (~5-10 min per 5 min audio) - 244M params
WHISPER_MODEL=medium    # Very good (~10+ min per 5 min audio) - 769M params
WHISPER_MODEL=large     # Best (~15+ min per 5 min audio) - 1.5B params
```

> Restart backend after changing model.

### GPU Acceleration

If you have NVIDIA GPU:

```bash
# Install CUDA-enabled PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Restart backend
```

Audio analysis will be **10x faster** with GPU.

---

## 📈 Performance Expectations

### Hardware
- **CPU Only (laptop):** 3-5 min per 5 min audio
- **GPU (NVIDIA):** 30 sec - 1 min per 5 min audio
- **M1/M2 Mac:** 1-2 min per 5 min audio

### First Run
- **Model download:** 5-10 min (one time)
- **Subsequent runs:** 2-5 min

### Best Practice
1. Use smaller files first (~30 sec) to test setup
2. Upgrade model quality once confident
3. Use GPU if available
4. Run during off-peak times if processing many files

---

## 🌐 What Happens Next (Phases)

### Current (Phase 2 ✅)
- ✅ Record audio → transcribe → score importance
- ✅ Color-coded transcript view
- ✅ Emotion detection

### Future (Phase 3)
- 🔜 Database persistence (save analyses)
- 🔜 Folder organization & search
- 🔜 Flashcard generation (with OpenAI)
- 🔜 Action item extraction
- 🔜 Multi-speaker separation

### Future (Phase 4)
- 🔜 Web version (cloud deployment)
- 🔜 Mobile app
- 🔜 Real-time collaboration
- 🔜 Export to Notion/Obsidian
- 🔜 API for third-party apps

---

## 💡 Tips & Tricks

### Get Better Importance Scores
- **Be specific in speech** — Clear keywords get better scores
- **Use emphasis** — Slow down for important points
- **Set mood** — Consistent tone helps emotion detection
- **Choose correct mode** — Work vs School affects recommendations

### Speed Up Analysis
- Use "tiny" Whisper model for quick feedback
- Use GPU if available (10x faster)
- Process shorter segments (< 5 min each)

### Improve Quality
- Use "base" or "small" Whisper model for accuracy
- Use good microphone (reduces noise)
- Speak clearly (reduces transcription errors)
- Avoid background noise

---

## 📞 Need Help?

1. **Check logs** — Backend console shows detailed errors
2. **Check browser console** — F12 → Console tab shows JS errors
3. **Read OPTIMIZATION.md** — Technical details and architecture
4. **Check GitHub issues** — Common problems already solved

---

## 🎓 Project Structure

```
AI-Note-Clone--main/
├── backend/
│   ├── api/
│   │   ├── main.py (FastAPI server)
│   │   └── routes/ (CRUD endpoints)
│   ├── audio_processing/ (Whisper, emotion, scoring)
│   ├── venv/ (dependencies)
│   ├── .env (config - don't share!)
│   └── requirements.txt
├── desktop/
│   ├── src/
│   │   └── renderer/ (React components)
│   ├── vite.config.ts
│   ├── package.json
│   └── node_modules/
├── TEST.md (testing guide)
├── OPTIMIZATION.md (technical details)
└── README.md (overview)
```

---

## ✨ You're All Set!

**Everything is ready to use.** Just run the two commands above and start recording! 🎤

If you run into issues, check the Troubleshooting section or open a GitHub issue with:
- Your OS & hardware
- Error message from console
- Steps to reproduce

Happy note-taking! 📝✨
