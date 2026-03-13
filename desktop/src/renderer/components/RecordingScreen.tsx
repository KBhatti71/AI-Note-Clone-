import React from "react";
import { Mic, Square, Loader2 } from "lucide-react";
import { formatTime } from "../utils/api";

interface RecordingScreenProps {
  state: "idle" | "recording" | "processing" | "done" | "error";
  duration: number;
  mode: "school" | "work";
  onStart: () => void;
  onStop: () => void;
}

export function RecordingScreen({
  state,
  duration,
  mode,
  onStart,
  onStop,
}: RecordingScreenProps) {
  const isRecording = state === "recording";
  const isProcessing = state === "processing";
  const modeEmoji = mode === "school" ? "📚" : "💼";
  const modeLabel = mode === "school" ? "School Mode" : "Work Mode";

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] gap-8">
      {/* Mode badge */}
      <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-slate-800 border border-slate-700 text-slate-300 text-sm font-medium">
        <span>{modeEmoji}</span>
        <span>{modeLabel}</span>
      </div>

      {/* Record button */}
      <button
        onClick={isRecording ? onStop : onStart}
        disabled={isProcessing}
        className={[
          "relative w-32 h-32 rounded-full flex items-center justify-center",
          "transition-all duration-300 focus:outline-none focus:ring-4",
          isRecording
            ? "bg-red-500 hover:bg-red-600 focus:ring-red-500/40 shadow-lg shadow-red-500/30 animate-pulse-slow"
            : isProcessing
            ? "bg-slate-700 cursor-not-allowed"
            : "bg-indigo-600 hover:bg-indigo-500 focus:ring-indigo-500/40 shadow-lg shadow-indigo-500/20",
        ].join(" ")}
        aria-label={isRecording ? "Stop recording" : "Start recording"}
      >
        {isProcessing ? (
          <Loader2 className="w-12 h-12 text-white animate-spin" />
        ) : isRecording ? (
          <Square className="w-12 h-12 text-white fill-white" />
        ) : (
          <Mic className="w-12 h-12 text-white" />
        )}

        {/* Pulsing ring when recording */}
        {isRecording && (
          <span className="absolute inset-0 rounded-full border-4 border-red-400 animate-ping opacity-30" />
        )}
      </button>

      {/* Status text */}
      <div className="text-center space-y-1">
        <p className="text-xl font-semibold text-white">
          {isProcessing
            ? "Analyzing…"
            : isRecording
            ? formatTime(duration)
            : "Ready to Record"}
        </p>
        <p className="text-sm text-slate-400">
          {isProcessing
            ? "Transcribing and scoring importance"
            : isRecording
            ? "Click to stop"
            : "Click to start"}
        </p>
      </div>
    </div>
  );
}
