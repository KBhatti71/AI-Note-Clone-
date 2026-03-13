import React, { useState } from "react";
import { RecordingScreen } from "./components/RecordingScreen";
import { TranscriptView } from "./components/TranscriptView";
import { useRecording } from "./hooks/useRecording";
import { Settings, ChevronLeft } from "lucide-react";

type Mode = "school" | "work";
type View = "record" | "transcript" | "settings";

function ModeToggle({ mode, onChange }: { mode: Mode; onChange: (m: Mode) => void }) {
  return (
    <div className="flex rounded-lg bg-slate-800 border border-slate-700 p-1 gap-1">
      {(["school", "work"] as Mode[]).map((m) => (
        <button
          key={m}
          onClick={() => onChange(m)}
          className={[
            "px-4 py-1.5 rounded-md text-sm font-medium transition-colors",
            mode === m
              ? "bg-indigo-600 text-white shadow"
              : "text-slate-400 hover:text-white",
          ].join(" ")}
        >
          {m === "school" ? "📚 School" : "💼 Work"}
        </button>
      ))}
    </div>
  );
}

function SettingsPanel() {
  const [key, setKey] = useState(() => localStorage.getItem("openai_key") ?? "");

  return (
    <div className="space-y-6 max-w-md mx-auto">
      <h2 className="text-lg font-semibold text-white">Settings</h2>

      <div className="space-y-2">
        <label className="block text-sm text-slate-400">OpenAI API Key</label>
        <input
          type="password"
          value={key}
          onChange={(e) => {
            setKey(e.target.value);
            localStorage.setItem("openai_key", e.target.value);
          }}
          placeholder="sk-…"
          className="w-full px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 placeholder-slate-600"
        />
        <p className="text-xs text-slate-500">
          Used for flashcard generation (school) and action item extraction (work).
        </p>
      </div>

      <div className="space-y-2">
        <label className="block text-sm text-slate-400">Backend URL</label>
        <input
          type="text"
          defaultValue="http://localhost:8000"
          className="w-full px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>
    </div>
  );
}

export default function App() {
  const [mode, setMode] = useState<Mode>("work");
  const [view, setView] = useState<View>("record");
  const { state, duration, result, error, startRecording, stopRecording, reset } =
    useRecording(mode);

  // Auto-navigate to transcript when analysis is done
  React.useEffect(() => {
    if (state === "done" && result) {
      setView("transcript");
    }
  }, [state, result]);

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          {view !== "record" && (
            <button
              onClick={() => { setView("record"); reset(); }}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <ChevronLeft size={18} />
            </button>
          )}
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-md bg-indigo-600 flex items-center justify-center text-sm font-bold">
              N
            </div>
            <span className="font-semibold text-lg tracking-tight">NeuroApp</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {view === "record" && (
            <ModeToggle mode={mode} onChange={setMode} />
          )}
          <button
            onClick={() => setView(view === "settings" ? "record" : "settings")}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <Settings size={18} />
          </button>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-6 py-8">
          {view === "settings" && <SettingsPanel />}

          {view === "record" && (
            <div className="space-y-6">
              <RecordingScreen
                state={state}
                duration={duration}
                mode={mode}
                onStart={startRecording}
                onStop={stopRecording}
              />
              {error && (
                <div className="rounded-lg bg-red-900/30 border border-red-700 px-4 py-3 text-red-300 text-sm">
                  {error}
                </div>
              )}
            </div>
          )}

          {view === "transcript" && result && (
            <TranscriptView
              segments={result.segments}
              summary={result.summary}
              mode={mode}
            />
          )}
        </div>
      </main>
    </div>
  );
}
