-- NeuroApp PostgreSQL Schema
-- Run: psql -U postgres -d neuroapp -f schema.sql

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- -------------------------------------------------------
-- Meetings
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS meetings (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID,
  title       VARCHAR(255)  NOT NULL DEFAULT 'Untitled Meeting',
  context     VARCHAR(20)   NOT NULL DEFAULT 'work',  -- 'school' | 'work' | 'general'
  audio_url   VARCHAR(500),
  duration    INTEGER,                                 -- seconds
  created_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_meetings_user_id   ON meetings (user_id);
CREATE INDEX IF NOT EXISTS idx_meetings_context    ON meetings (context);
CREATE INDEX IF NOT EXISTS idx_meetings_created_at ON meetings (created_at DESC);

-- -------------------------------------------------------
-- Transcripts (one row per Whisper segment)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS transcripts (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  meeting_id       UUID         NOT NULL REFERENCES meetings (id) ON DELETE CASCADE,
  text             TEXT         NOT NULL,
  start_time       FLOAT        NOT NULL,
  end_time         FLOAT        NOT NULL,
  speaker          VARCHAR(100) DEFAULT 'speaker_0',
  importance_score INTEGER      CHECK (importance_score BETWEEN 0 AND 100),
  importance_level VARCHAR(20),                       -- HIGH | MEDIUM | LOW
  emotion          VARCHAR(50),
  emotion_confidence FLOAT,
  prosody_features JSONB,
  score_breakdown  JSONB,
  recommendations  JSONB,                             -- array of strings
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transcripts_meeting_id        ON transcripts (meeting_id);
CREATE INDEX IF NOT EXISTS idx_transcripts_importance_level  ON transcripts (importance_level);
CREATE INDEX IF NOT EXISTS idx_transcripts_importance_score  ON transcripts (importance_score DESC);

-- -------------------------------------------------------
-- Action Items  (Work Mode)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS action_items (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  meeting_id   UUID        NOT NULL REFERENCES meetings (id) ON DELETE CASCADE,
  task         TEXT        NOT NULL,
  owner        VARCHAR(255),
  deadline     DATE,
  priority     VARCHAR(20) DEFAULT 'MEDIUM',          -- HIGH | MEDIUM | LOW
  status       VARCHAR(50) DEFAULT 'open',            -- open | in-progress | done
  source_text  TEXT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_action_items_meeting_id ON action_items (meeting_id);
CREATE INDEX IF NOT EXISTS idx_action_items_priority   ON action_items (priority);

-- -------------------------------------------------------
-- Flashcards  (School Mode)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS flashcards (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  meeting_id       UUID         NOT NULL REFERENCES meetings (id) ON DELETE CASCADE,
  question         TEXT         NOT NULL,
  answer           TEXT         NOT NULL,
  importance_score INTEGER,
  tags             JSONB,                             -- array of strings
  next_review      DATE         DEFAULT CURRENT_DATE + INTERVAL '1 day',
  review_count     INTEGER      DEFAULT 0,
  created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_flashcards_meeting_id  ON flashcards (meeting_id);
CREATE INDEX IF NOT EXISTS idx_flashcards_next_review ON flashcards (next_review);
