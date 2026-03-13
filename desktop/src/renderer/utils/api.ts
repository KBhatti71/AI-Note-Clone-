const API_BASE = "";

export interface ProsodyFeatures {
  pitch_mean: number;
  pitch_std: number;
  intensity_mean: number;
  speaking_rate: number;
  pause_count: number;
  vocal_emphasis_score: number;
  speaking_pattern_score: number;
}

export interface Segment {
  id: string;
  text: string;
  start_time: number;
  end_time: number;
  speaker: string;
  importance_score: number;
  importance_level: "HIGH" | "MEDIUM" | "LOW";
  emotion: string;
  emotion_confidence?: number;
  prosody: ProsodyFeatures;
  score_breakdown: Record<string, number>;
  recommendations: string[];
}

export interface Summary {
  total_segments: number;
  high_importance_count: number;
  medium_importance_count: number;
  low_importance_count: number;
  average_importance: number;
  dominant_emotion: string;
  top_moments: Array<{ text: string; score: number; start_time: number }>;
  recommendations: string[];
}

export interface AnalyzeResponse {
  meeting_id: string;
  context: string;
  duration: number;
  segments: Segment[];
  summary: Summary;
}

export async function analyzeAudio(
  audioBlob: Blob,
  mode: "school" | "work",
  fileName = "recording.wav"
): Promise<AnalyzeResponse> {
  const formData = new FormData();
  formData.append("file", audioBlob, fileName);
  formData.append("context", mode);

  const res = await fetch(`${API_BASE}/api/analyze`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Analysis failed");
  }

  return res.json();
}

export async function fetchMeetings() {
  const res = await fetch(`${API_BASE}/api/meetings/`);
  if (!res.ok) throw new Error("Failed to fetch meetings");
  return res.json();
}

export function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}
