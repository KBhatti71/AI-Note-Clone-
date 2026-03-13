import React, { useState, useEffect, useRef } from "react";
import { useRecording } from "./hooks/useRecording";
import {
  Settings,
  ChevronLeft,
  Download,
  RotateCcw,
  Play,
  Square,
  AlertCircle,
} from "lucide-react";

type Mode = "school" | "work";

interface AnalysisMetrics {
  avgImportance: number;
  emotionDistribution: Record<string, number>;
  analysisTime: number;
}

interface RecordingPanelProps {
  mode: Mode;
  isRecording: boolean;
  duration: number;
  onStart: () => void;
  onStop: () => void;
}

interface AnalysisPanelProps {
  isAnalyzing: boolean;
  progress: number;
  metrics?: AnalysisMetrics;
  onRetry: () => void;
}

interface HistoryPanelProps {
  segments: any[];
  summary: any;
  onExport: () => void;
  onReanalyze: () => void;
}

// Color scheme
const COLORS = {
  bg: {
    primary: "#0f172a", // Dark slate
    secondary: "#1e293b",
    tertiary: "#334155",
  },
  accent: {
    blue: "#3b82f6",
    green: "#10b981",
    red: "#ef4444",
    amber: "#f59e0b",
  },
};

// RecordingPanel: Main recording interface
function RecordingPanel({
  mode,
  isRecording,
  duration,
  onStart,
  onStop,
}: RecordingPanelProps) {
  const [waveform, setWaveform] = useState<number[]>([]);

  // Simulate waveform visualization
  useEffect(() => {
    if (isRecording) {
      const interval = setInterval(() => {
        const newBars = Array.from({ length: 24 }, () =>
          Math.random() * 100
        );
        setWaveform(newBars);
      }, 100);
      return () => clearInterval(interval);
    }
  }, [isRecording]);

  const formatTime = (seconds: number) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${String(hrs).padStart(2, "0")}:${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  };

  return (
    <div className="space-y-8">
      <div className="text-center">
        <p className="text-sm text-slate-400 mb-2">Recording Mode</p>
        <div className="inline-block px-4 py-2 rounded-full bg-blue-500/20 border border-blue-500/40">
          <p className="text-blue-300 font-semibold capitalize">{mode}</p>
        </div>
      </div>

      {/* Waveform Visualization */}
      {isRecording && (
        <div className="flex items-end justify-center gap-1 h-32 px-8 py-6 bg-slate-900/50 rounded-lg border border-slate-800">
          {waveform.map((height, i) => (
            <div
              key={i}
              className="flex-1 rounded-t bg-gradient-to-t from-blue-500 to-blue-300 transition-all"
              style={{ height: `${(height / 100) * 120}px` }}
            />
          ))}
        </div>
      )}

      {/* Duration Display */}
      <div className="text-center">
        <p className="text-5xl font-mono font-bold text-blue-400 tracking-tight">
          {formatTime(duration)}
        </p>
        <p className="text-sm text-slate-500 mt-2">
          {isRecording ? "Recording in progress..." : "Ready to record"}
        </p>
      </div>

      {/* Recording Controls */}
      <div className="flex gap-4 justify-center">
        {!isRecording ? (
          <button
            onClick={onStart}
            className="flex items-center gap-2 px-6 py-3 rounded-lg bg-green-600 hover:bg-green-700 text-white font-semibold transition-all hover:shadow-lg hover:shadow-green-500/30 active:scale-95"
          >
            <Play size={20} />
            Start Recording
          </button>
        ) : (
          <button
            onClick={onStop}
            className="flex items-center gap-2 px-6 py-3 rounded-lg bg-red-600 hover:bg-red-700 text-white font-semibold transition-all hover:shadow-lg hover:shadow-red-500/30 active:scale-95"
          >
            <Square size={20} />
            Stop Recording
          </button>
        )}
      </div>

      {/* Keyboard Hint */}
      <p className="text-xs text-slate-600 text-center">
        💡 Tip: Press <kbd className="px-2 py-1 bg-slate-800 rounded">Space</kbd> to
        start/stop
      </p>
    </div>
  );
}

// AnalysisPanel: Shows progress and metrics during analysis
function AnalysisPanel({
  isAnalyzing,
  progress,
  metrics,
  onRetry,
}: AnalysisPanelProps) {
  return (
    <div className="space-y-6">
      {isAnalyzing && (
        <>
          <div className="text-center">
            <p className="text-lg font-semibold text-white mb-4">
              Analyzing your recording...
            </p>
            <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-blue-400 transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-sm text-slate-400 mt-2">{progress}% complete</p>
          </div>

          {/* Analysis Steps */}
          <div className="space-y-3">
            {[
              { step: "Loading audio", done: progress > 10 },
              { step: "Transcribing speech", done: progress > 30 },
              { step: "Detecting emotions", done: progress > 60 },
              { step: "Scoring importance", done: progress > 80 },
              { step: "Generating insights", done: progress === 100 },
            ].map((item, i) => (
              <div key={i} className="flex items-center gap-3">
                <div
                  className={`w-2 h-2 rounded-full transition-colors ${
                    item.done ? "bg-green-500" : "bg-slate-700"
                  }`}
                />
                <p className={item.done ? "text-green-400" : "text-slate-500"}>
                  {item.step}
                </p>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Metrics Display */}
      {metrics && (
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 rounded-lg bg-slate-900/50 border border-slate-800">
            <p className="text-sm text-slate-400">Avg Importance</p>
            <p className="text-2xl font-bold text-blue-400 mt-1">
              {metrics.avgImportance.toFixed(1)}/10
            </p>
          </div>
          <div className="p-4 rounded-lg bg-slate-900/50 border border-slate-800">
            <p className="text-sm text-slate-400">Analysis Time</p>
            <p className="text-2xl font-bold text-blue-400 mt-1">
              {metrics.analysisTime.toFixed(1)}s
            </p>
          </div>

          {/* Emotion Distribution */}
          <div className="col-span-2 p-4 rounded-lg bg-slate-900/50 border border-slate-800">
            <p className="text-sm text-slate-400 mb-3">Emotion Distribution</p>
            <div className="space-y-2">
              {Object.entries(metrics.emotionDistribution)
                .sort((a, b) => (b[1] as number) - (a[1] as number))
                .slice(0, 3)
                .map(([emotion, count]) => (
                  <div key={emotion} className="flex items-center gap-2">
                    <p className="text-sm text-slate-300 w-16 capitalize">
                      {emotion}
                    </p>
                    <div className="flex-1 bg-slate-800 rounded h-2 overflow-hidden">
                      <div
                        className="h-full bg-blue-500"
                        style={{ width: `${(count as number) * 10}%` }}
                      />
                    </div>
                    <p className="text-sm text-slate-400 w-8">
                      {count as number}
                    </p>
                  </div>
                ))}
            </div>
          </div>
        </div>
      )}

      {!isAnalyzing && (
        <button
          onClick={onRetry}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium transition-colors"
        >
          <RotateCcw size={16} />
          Retry Analysis
        </button>
      )}
    </div>
  );
}

// HistoryPanel: Shows transcript and analysis results
function HistoryPanel({
  segments,
  summary,
  onExport,
  onReanalyze,
}: HistoryPanelProps) {
  const textContent = segments.map((s: any) => s.text).join(" ");

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-3">
        <div className="p-4 rounded-lg bg-slate-900/50 border border-slate-800">
          <p className="text-xs text-slate-500 uppercase">Segments</p>
          <p className="text-2xl font-bold text-blue-400 mt-1">
            {summary.total_segments}
          </p>
        </div>
        <div className="p-4 rounded-lg bg-slate-900/50 border border-slate-800">
          <p className="text-xs text-slate-500 uppercase">Avg Importance</p>
          <p className="text-2xl font-bold text-amber-400 mt-1">
            {summary.average_importance.toFixed(1)}
          </p>
        </div>
        <div className="p-4 rounded-lg bg-slate-900/50 border border-slate-800">
          <p className="text-xs text-slate-500 uppercase">Emotion</p>
          <p className="text-lg font-bold text-green-400 mt-1 capitalize">
            {summary.dominant_emotion}
          </p>
        </div>
      </div>

      {/* Importance Distribution */}
      <div className="p-4 rounded-lg bg-slate-900/50 border border-slate-800 space-y-3">
        <p className="text-sm font-semibold text-white">Importance Breakdown</p>
        {[
          { level: "High", count: summary.high_importance_count, color: "text-red-400" },
          { level: "Medium", count: summary.medium_importance_count, color: "text-amber-400" },
          { level: "Low", count: summary.low_importance_count, color: "text-slate-400" },
        ].map((item) => (
          <div key={item.level} className="flex items-center justify-between">
            <span className="text-sm text-slate-300">{item.level}</span>
            <div className="flex items-center gap-2">
              <div className="flex-1 bg-slate-800 rounded h-2 w-20 overflow-hidden">
                <div
                  className={`h-full ${item.color}`}
                  style={{
                    width: `${(item.count / summary.total_segments) * 100}%`,
                    backgroundColor: item.color === "text-red-400" ? "#ef4444" : item.color === "text-amber-400" ? "#f59e0b" : "#64748b",
                  }}
                />
              </div>
              <span className={`text-sm font-semibold ${item.color}`}>{item.count}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Transcript */}
      <div className="p-4 rounded-lg bg-slate-900/50 border border-slate-800">
        <p className="text-sm font-semibold text-white mb-3">Transcript</p>
        <div className="space-y-3 max-h-64 overflow-y-auto">
          {segments.map((segment: any, i: number) => (
            <div
              key={i}
              className="p-3 rounded bg-slate-800/50 border border-slate-700/50"
            >
              <div className="flex items-start justify-between gap-2 mb-1">
                <p className="text-xs font-mono text-slate-500">
                  {segment.speaker} • {segment.start_time.toFixed(2)}s
                </p>
                <span
                  className="text-xs px-2 py-1 rounded font-semibold"
                  style={{
                    backgroundColor:
                      segment.importance_level === "high"
                        ? "rgba(239, 68, 68, 0.2)"
                        : segment.importance_level === "medium"
                        ? "rgba(245, 158, 11, 0.2)"
                        : "rgba(100, 116, 139, 0.2)",
                    color:
                      segment.importance_level === "high"
                        ? "#ef4444"
                        : segment.importance_level === "medium"
                        ? "#f59e0b"
                        : "#64748b",
                  }}
                >
                  {segment.importance_level}
                </span>
              </div>
              <p className="text-sm text-slate-300">{segment.text}</p>
              <div className="flex gap-2 mt-2 text-xs">
                <span className="text-blue-400">
                  💭 {segment.emotion}
                </span>
                <span className="text-slate-500">
                  ⭐ {segment.importance_score}/10
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Top Moments */}
      {summary.top_moments.length > 0 && (
        <div className="p-4 rounded-lg bg-slate-900/50 border border-slate-800">
          <p className="text-sm font-semibold text-white mb-3">Top Moments</p>
          <div className="space-y-2">
            {summary.top_moments.slice(0, 3).map((moment: any, i: number) => (
              <div key={i} className="p-2 rounded bg-slate-800/50">
                <p className="text-sm text-slate-300">{moment.text}</p>
                <p className="text-xs text-amber-400 mt-1">
                  Score: {moment.score}/10
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {summary.recommendations.length > 0 && (
        <div className="p-4 rounded-lg bg-slate-900/50 border border-slate-800">
          <p className="text-sm font-semibold text-white mb-3">Recommendations</p>
          <ul className="space-y-2">
            {summary.recommendations.slice(0, 3).map((rec: string, i: number) => (
              <li key={i} className="flex gap-2 text-sm text-slate-300">
                <span className="text-green-400 mt-0.5">✓</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Action Buttons */}
      <div className="grid grid-cols-2 gap-3">
        <button
          onClick={onExport}
          className="flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium transition-colors"
        >
          <Download size={16} />
          Export
        </button>
        <button
          onClick={onReanalyze}
          className="flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-300 font-medium transition-colors"
        >
          <RotateCcw size={16} />
          Re-analyze
        </button>
      </div>
    </div>
  );
}

// Main App component
export default function App() {
  const [mode, setMode] = useState<Mode>("work");
  const [currentView, setCurrentView] = useState<"recording" | "analysis" | "results">(
    "recording"
  );
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [analysisMetrics, setAnalysisMetrics] = useState<AnalysisMetrics>();
  const { state, duration, result, error, startRecording, stopRecording, reset } =
    useRecording(mode);

  const keyboardRef = useRef<HTMLDivElement>(null);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Space = toggle recording
      if (e.code === "Space" && currentView === "recording") {
        e.preventDefault();
        if (state === "recording") {
          stopRecording();
        } else if (state === "idle") {
          startRecording();
        }
      }
      // Escape = cancel/go back
      if (e.key === "Escape") {
        if (currentView === "results") {
          handleReset();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [state, currentView, startRecording, stopRecording]);

  // Auto-navigate when recording completes
  useEffect(() => {
    if (state === "done") {
      setCurrentView("analysis");
      startAnalysisSimulation();
    }
  }, [state]);

  // Auto-navigate when analysis completes
  useEffect(() => {
    if (isAnalyzing && analysisProgress === 100) {
      setTimeout(() => {
        setIsAnalyzing(false);
        setCurrentView("results");
      }, 500);
    }
  }, [analysisProgress, isAnalyzing]);

  const startAnalysisSimulation = () => {
    setIsAnalyzing(true);
    setAnalysisProgress(0);
    let progress = 0;

    const interval = setInterval(() => {
      progress += Math.random() * 25;
      if (progress > 100) progress = 100;

      setAnalysisProgress(progress);

      // Simulate metrics
      if (result) {
        const emotions: Record<string, number> = {};
        result.segments.forEach((seg: any) => {
          emotions[seg.emotion] = (emotions[seg.emotion] || 0) + 1;
        });

        setAnalysisMetrics({
          avgImportance: result.summary.average_importance,
          emotionDistribution: emotions,
          analysisTime: (progress / 100) * 8,
        });
      }

      if (progress >= 100) {
        clearInterval(interval);
      }
    }, 400);
  };

  const handleExport = () => {
    if (!result) return;
    const text = result.segments.map((s: any) => s.text).join("\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `transcript-${new Date().toISOString().split("T")[0]}.txt`;
    a.click();
  };

  const handleReset = () => {
    reset();
    setCurrentView("recording");
    setIsAnalyzing(false);
    setAnalysisProgress(0);
    setAnalysisMetrics(undefined);
  };

  return (
    <div
      ref={keyboardRef}
      className="min-h-screen text-white flex flex-col"
      style={{ backgroundColor: COLORS.bg.primary }}
    >
      {/* Header */}
      <header
        className="flex items-center justify-between px-6 py-4 border-b"
        style={{
          borderColor: COLORS.bg.secondary,
          backgroundColor: COLORS.bg.secondary,
        }}
      >
        <div className="flex items-center gap-3">
          {currentView !== "recording" && (
            <button
              onClick={handleReset}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white transition-colors"
              style={{ backgroundColor: "rgba(51, 65, 85, 0.5)" }}
            >
              <ChevronLeft size={18} />
            </button>
          )}
          <div className="flex items-center gap-2">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold text-white"
              style={{ backgroundColor: COLORS.accent.blue }}
            >
              N
            </div>
            <span className="font-semibold text-lg tracking-tight">
              NeuroApp
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {currentView === "recording" && (
            <div
              className="flex rounded-lg border p-1 gap-1"
              style={{
                backgroundColor: COLORS.bg.tertiary,
                borderColor: COLORS.bg.tertiary,
              }}
            >
              {(["school", "work"] as Mode[]).map((m) => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    mode === m
                      ? "text-white"
                      : "text-slate-400 hover:text-slate-300"
                  }`}
                  style={
                    mode === m ? { backgroundColor: COLORS.accent.blue } : {}
                  }
                >
                  {m === "school" ? "📚 School" : "💼 Work"}
                </button>
              ))}
            </div>
          )}
          <button
            className="p-2 rounded-lg text-slate-400 hover:text-white transition-colors"
            style={{ backgroundColor: "rgba(51, 65, 85, 0.5)" }}
          >
            <Settings size={18} />
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-2xl mx-auto px-6 py-8">
          {/* Error Message */}
          {error && (
            <div
              className="mb-6 p-4 rounded-lg border flex gap-3"
              style={{
                backgroundColor: "rgba(239, 68, 68, 0.1)",
                borderColor: "rgba(239, 68, 68, 0.5)",
              }}
            >
              <AlertCircle size={20} style={{ color: COLORS.accent.red }} />
              <div>
                <p className="font-semibold" style={{ color: COLORS.accent.red }}>
                  Error
                </p>
                <p className="text-sm text-slate-400 mt-1">{error}</p>
                <button
                  onClick={handleReset}
                  className="text-sm mt-2 underline hover:no-underline"
                  style={{ color: COLORS.accent.red }}
                >
                  Try again
                </button>
              </div>
            </div>
          )}

          {/* Recording View */}
          {currentView === "recording" && (
            <RecordingPanel
              mode={mode}
              isRecording={state === "recording"}
              duration={duration}
              onStart={startRecording}
              onStop={stopRecording}
            />
          )}

          {/* Analysis View */}
          {currentView === "analysis" && (
            <AnalysisPanel
              isAnalyzing={isAnalyzing}
              progress={analysisProgress}
              metrics={analysisMetrics}
              onRetry={startAnalysisSimulation}
            />
          )}

          {/* Results View */}
          {currentView === "results" && result && (
            <HistoryPanel
              segments={result.segments}
              summary={result.summary}
              onExport={handleExport}
              onReanalyze={handleReset}
            />
          )}
        </div>
      </main>
    </div>
  );
}
