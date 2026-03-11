# 🧠 NeuroApp Prototype - Audio Intelligence Pipeline

> **The secret sauce: Detect what's ACTUALLY important in meetings and lectures**

## What This Is

This is a **working prototype** of NeuroApp's core innovation: **automatic importance detection** using audio prosody, emotion analysis, and context-aware scoring.

**What makes it different from Granola/Otter/Fireflies:**
- ✅ Detects **emotional emphasis** in speech
- ✅ Scores **every segment** 0-100 for importance
- ✅ **Context-aware** (School mode vs. Work mode)
- ✅ Auto-generates **study materials** and **action items**
- ✅ Understands **what you need to remember**, not just what was said

---

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.8+
python --version

# Install dependencies
pip install -r requirements.txt
```

### Run the Demos

```bash
# 1. Prosody Analysis Demo
python audio_processing/prosody_analyzer.py

# 2. Emotion Detection Demo
python audio_processing/emotion_detector.py

# 3. Importance Scoring Demo
python audio_processing/importance_scorer.py

# 4. Complete Pipeline Demo
python audio_processing/pipeline.py
```

---

## 📊 How It Works

### The Pipeline

```
Audio Input
    ↓
┌─────────────────────────────────────┐
│  1. Prosody Analysis                │
│     - Pitch variation               │
│     - Volume changes                │
│     - Speaking rate                 │
│     - Pauses                        │
│     → Vocal emphasis score (0-100)  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  2. Emotion Detection (Optional)    │
│     - 6 emotions: angry, happy,     │
│       sad, neutral, fearful,        │
│       surprised                     │
│     → Importance boost (0-15)       │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  3. Importance Scoring              │
│     Combines:                       │
│     • Vocal emphasis (30%)          │
│     • Keywords (20%)                │
│     • Repetition (20%)              │
│     • Emotion (15%)                 │
│     • Context signals (15%)         │
│     → Final score (0-100)           │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  4. Recommendations                 │
│     School: Flashcards, quizzes     │
│     Work: Action items, follow-ups  │
└─────────────────────────────────────┘
```

---

## 💡 Key Features

### 1. Prosody Analysis

Extracts vocal features that humans use to emphasize important information:

```python
from audio_processing import ProsodyAnalyzer

analyzer = ProsodyAnalyzer(sample_rate=16000)
features = analyzer.analyze_segment(audio)

# Returns:
# {
#   'pitch_variation': 45.2,        # Hz
#   'intensity_peaks': 3,           # Loud moments
#   'speaking_rate': 2.8,           # Syllables/sec
#   'pause_count': 2,               # Thinking pauses
#   'vocal_emphasis_score': 75/100  # Overall emphasis
# }
```

**What this detects:**
- Professor slowing down → Important concept
- Voice getting louder → Emphasis
- Long pauses → Critical thinking moment
- Pitch changes → Emotional importance

### 2. Emotion Detection

Uses Wav2Vec2 to detect emotional state:

```python
from audio_processing import EmotionDetector

detector = EmotionDetector()
result = detector.detect_emotion(audio)

# Returns:
# {
#   'emotion': 'surprised',      # Or angry, happy, sad, neutral, fearful
#   'confidence': 0.87,
#   'importance_boost': 12       # Added to importance score
# }
```

**Why emotion matters:**
- Angry → Critical issue needs attention
- Surprised → Important revelation
- Fearful → Risk/concern flagged
- Happy → Excitement about key win

### 3. Context-Aware Scoring

Different contexts = different importance signals:

**School Mode:**
```python
from audio_processing import Context, ImportanceScorer

scorer = ImportanceScorer(context=Context.SCHOOL)

# Detects:
# - Keywords: "exam", "test", "remember", "important"
# - Slow speaking = explaining complex concept
# - Questions = confusion/clarification needed
# - Repetition = key concept repeated

# Auto-generates:
# ✅ Flashcards from high-importance segments
# ✅ Practice quizzes
# ✅ Study guides
```

**Work Mode:**
```python
scorer = ImportanceScorer(context=Context.WORK)

# Detects:
# - Keywords: "deadline", "action item", "decision"
# - Disagreement patterns = important discussion
# - Commitment language = "I'll" / "I will"
# - Stakeholder concerns

# Auto-generates:
# ✅ Action items with owners
# ✅ Follow-up reminders
# ✅ Decision tracking
```

### 4. Complete Pipeline

Ties everything together:

```python
from audio_processing import AudioIntelligencePipeline, Context

# Initialize for school mode
pipeline = AudioIntelligencePipeline(
    context=Context.SCHOOL,
    sample_rate=16000,
    enable_emotion=True
)

# Analyze a segment
result = pipeline.analyze_segment(
    audio=audio_samples,
    transcript="This will be on the midterm exam.",
    start_time=120.0,
    end_time=123.0,
    speaker="Professor"
)

# Result:
# {
#   'importance_score': 85,
#   'importance_level': 'HIGH',
#   'recommendations': [
#     '📝 Add to flashcards',
#     '⭐ Mark for exam review',
#     '🎯 Create practice question'
#   ]
# }
```

---

## 🎯 Usage Examples

### Example 1: Analyze a Lecture

```python
from audio_processing import AudioIntelligencePipeline, Context

# Set up for school
pipeline = AudioIntelligencePipeline(context=Context.SCHOOL)

# Your lecture segments (from Whisper transcription)
segments = [
    {
        'audio': audio_chunk_1,
        'transcript': "Recursion is fundamental to CS.",
        'start_time': 0.0,
        'end_time': 3.0,
        'speaker': 'Professor'
    },
    # ... more segments
]

# Analyze entire lecture
results = pipeline.analyze_conversation(segments)

# Generate summary
summary = pipeline.generate_summary(results)

print(f"High importance: {summary['high_importance_count']} segments")
print(f"Top moments: {summary['top_moments']}")
print(f"Recommendations: {summary['recommendations']}")
```

### Example 2: Analyze a Work Meeting

```python
pipeline = AudioIntelligencePipeline(context=Context.WORK)

# Process meeting
results = pipeline.analyze_conversation(meeting_segments)

# Filter high-importance moments
critical = [r for r in results if r.importance_score >= 70]

for moment in critical:
    print(f"⚠️  CRITICAL at {moment.start_time}s:")
    print(f"   {moment.text}")
    print(f"   Recommendations: {moment.recommendations}")
```

---

## 📁 Project Structure

```
neuroapp-prototype/
├── audio_processing/
│   ├── __init__.py
│   ├── prosody_analyzer.py      # Vocal feature extraction
│   ├── emotion_detector.py      # Emotion recognition
│   ├── importance_scorer.py     # Combines all signals
│   └── pipeline.py              # Complete pipeline
├── tests/                       # Unit tests (TODO)
├── config/                      # Configuration files
├── data/                        # Sample audio files
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

---

## 🧪 Testing with Real Audio

To test with real meeting/lecture audio:

1. **Record audio** (use any tool, save as .wav)

2. **Transcribe with Whisper:**
```python
import whisper

model = whisper.load_model("base")
result = model.transcribe("lecture.wav")

# result['segments'] contains timestamps + text
```

3. **Analyze with NeuroApp:**
```python
from audio_processing import AudioIntelligencePipeline, Context
import librosa

# Load audio
audio, sr = librosa.load("lecture.wav", sr=16000)

# Split into segments (matching Whisper)
pipeline = AudioIntelligencePipeline(context=Context.SCHOOL)

for segment in result['segments']:
    start = segment['start']
    end = segment['end']
    text = segment['text']
    
    # Extract audio chunk
    start_sample = int(start * sr)
    end_sample = int(end * sr)
    audio_chunk = audio[start_sample:end_sample]
    
    # Analyze
    analysis = pipeline.analyze_segment(
        audio=audio_chunk,
        transcript=text,
        start_time=start,
        end_time=end
    )
    
    print(f"[{start:.1f}s] {analysis.importance_level}: {text}")
```

---

## 🚀 Next Steps

### Phase 1: MVP (Current)
- ✅ Prosody analysis
- ✅ Emotion detection
- ✅ Importance scoring
- ✅ Context modes (School/Work)
- ⏳ Real audio testing

### Phase 2: Integration (Week 2-3)
- [ ] Integrate Whisper for transcription
- [ ] Real-time processing
- [ ] Web interface (React)
- [ ] Desktop app (Electron)

### Phase 3: Features (Week 4-6)
- [ ] Auto-generate flashcards
- [ ] Auto-generate action items
- [ ] Stakeholder sentiment tracking
- [ ] Multi-meeting search

### Phase 4: Launch (Week 7-12)
- [ ] Mobile app (React Native)
- [ ] Integrations (Slack, Notion, etc.)
- [ ] Team features
- [ ] Beta launch

---

## 🎯 The Competitive Advantage

**What competitors do:**
- Transcribe audio ✓
- Summarize with AI ✓

**What NeuroApp does differently:**
- **Understands WHAT MATTERS** ✨
- **Context-aware** (School vs. Work)
- **Emotional intelligence**
- **Auto-generates study materials**
- **Tracks stakeholder sentiment**

**The result:**
- Students: Never miss what's important, auto study materials
- Professionals: Never drop commitments, auto follow-ups

---

## 💰 Business Model

### Student Plan: $8/month
- Target: 50M students
- TAM: $400M/month

### Professional Plan: $15/month
- Target: 30M professionals
- TAM: $450M/month

**Total: $10.2B/year TAM** (2x bigger than Granola's market)

---

## 🤝 Contributing

This is a prototype. To contribute:

1. Test with real audio
2. Report bugs/issues
3. Suggest improvements
4. Add features

---

## 📄 License

MIT License - See LICENSE file

---

## 🙏 Acknowledgments

Built on top of:
- **Praat/Parselmouth** - Prosody analysis
- **Wav2Vec2** - Emotion recognition
- **Whisper** - Transcription (future)
- **GPT-4o/Claude** - Enhancement (future)

---

**This is the foundation of something special. Let's build it.** 🚀
