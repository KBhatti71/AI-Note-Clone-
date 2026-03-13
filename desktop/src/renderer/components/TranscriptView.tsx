import React, { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { Segment, Summary, formatTime } from "../utils/api";

interface TranscriptViewProps {
  segments: Segment[];
  summary: Summary;
  mode: "school" | "work";
}

function importanceColor(level: Segment["importance_level"]): string {
  switch (level) {
    case "HIGH":   return "border-l-red-500 bg-red-500/10";
    case "MEDIUM": return "border-l-yellow-400 bg-yellow-400/10";
    default:       return "border-l-green-500 bg-green-500/10";
  }
}

function importanceBadge(level: Segment["importance_level"]): string {
  switch (level) {
    case "HIGH":   return "bg-red-500/20 text-red-300 border border-red-500/30";
    case "MEDIUM": return "bg-yellow-400/20 text-yellow-300 border border-yellow-400/30";
    default:       return "bg-green-500/20 text-green-300 border border-green-500/30";
  }
}

function ScoreMeter({ score }: { score: number }) {
  const color =
    score >= 70 ? "bg-red-500" : score >= 40 ? "bg-yellow-400" : "bg-green-500";
  return (
    <div className="flex items-center gap-2 mt-1">
      <div className="flex-1 h-1 rounded-full bg-slate-700">
        <div
          className={`h-1 rounded-full ${color} transition-all`}
          style={{ width: `${score}%` }}
        />
      </div>
      <span className="text-xs text-slate-400 w-12 text-right">{score}/100</span>
    </div>
  );
}

function SegmentCard({ seg }: { seg: Segment }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className={`border-l-4 rounded-r-lg p-4 space-y-2 ${importanceColor(seg.importance_level)}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <p className="text-white text-sm leading-relaxed">{seg.text}</p>
          <ScoreMeter score={seg.importance_score} />
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${importanceBadge(seg.importance_level)}`}>
            {seg.importance_level}
          </span>
          <span className="text-xs text-slate-500">{formatTime(seg.start_time)}</span>
        </div>
      </div>

      {/* Recommendations pills */}
      {seg.recommendations.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {seg.recommendations.map((rec, i) => (
            <span
              key={i}
              className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30"
            >
              {rec}
            </span>
          ))}
        </div>
      )}

      {/* Expand for details */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-300 transition-colors"
      >
        {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
        {expanded ? "Hide" : "Details"}
      </button>

      {expanded && (
        <div className="text-xs text-slate-400 space-y-1 pt-1 border-t border-slate-700">
          <div className="flex gap-4">
            <span>Emotion: <span className="text-slate-200">{seg.emotion}</span></span>
            <span>Confidence: <span className="text-slate-200">{Math.round(seg.emotion_confidence * 100)}%</span></span>
          </div>
          <div className="flex gap-4">
            <span>Pitch σ: <span className="text-slate-200">{seg.prosody.pitch_std.toFixed(1)} Hz</span></span>
            <span>Emphasis: <span className="text-slate-200">{seg.prosody.vocal_emphasis_score.toFixed(0)}/100</span></span>
            <span>Rate: <span className="text-slate-200">{seg.prosody.speaking_rate.toFixed(1)} syl/s</span></span>
          </div>
          {Object.keys(seg.score_breakdown).length > 0 && (
            <div>
              Breakdown:{" "}
              {Object.entries(seg.score_breakdown).map(([k, v]) => (
                <span key={k} className="mr-3">
                  {k}: <span className="text-slate-200">{v}</span>
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function TranscriptView({ segments, summary, mode }: TranscriptViewProps) {
  const [filter, setFilter] = useState<"ALL" | "HIGH" | "MEDIUM" | "LOW">("ALL");

  const filtered = filter === "ALL"
    ? segments
    : segments.filter((s) => s.importance_level === filter);

  return (
    <div className="space-y-4">
      {/* Summary bar */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "High", count: summary.high_importance_count, color: "text-red-400" },
          { label: "Medium", count: summary.medium_importance_count, color: "text-yellow-400" },
          { label: "Low", count: summary.low_importance_count, color: "text-green-400" },
          { label: "Avg Score", count: summary.average_importance, color: "text-indigo-400" },
        ].map(({ label, count, color }) => (
          <div key={label} className="rounded-lg bg-slate-800 border border-slate-700 p-3 text-center">
            <p className={`text-xl font-bold ${color}`}>{count}</p>
            <p className="text-xs text-slate-400 mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {/* Filter buttons */}
      <div className="flex gap-2">
        {(["ALL", "HIGH", "MEDIUM", "LOW"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={[
              "px-3 py-1 rounded-full text-xs font-medium transition-colors",
              filter === f
                ? "bg-indigo-600 text-white"
                : "bg-slate-800 text-slate-400 hover:text-white border border-slate-700",
            ].join(" ")}
          >
            {f}
          </button>
        ))}
        <span className="ml-auto text-xs text-slate-500 self-center">
          {filtered.length} segment{filtered.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Segment list */}
      <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
        {filtered.map((seg) => (
          <SegmentCard key={seg.id} seg={seg} />
        ))}
        {filtered.length === 0 && (
          <p className="text-center text-slate-500 py-8">No {filter.toLowerCase()} importance segments</p>
        )}
      </div>

      {/* Top moments */}
      {summary.top_moments.length > 0 && (
        <div className="rounded-lg bg-slate-800 border border-slate-700 p-4 space-y-2">
          <h3 className="text-sm font-semibold text-slate-300">
            🔥 Top Moments
          </h3>
          {summary.top_moments.map((m, i) => (
            <div key={i} className="flex items-start gap-3 text-sm">
              <span className="text-slate-500 shrink-0">{formatTime(m.start_time)}</span>
              <span className="text-slate-300 flex-1">{m.text}</span>
              <span className="text-indigo-400 shrink-0 font-medium">{m.score}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
