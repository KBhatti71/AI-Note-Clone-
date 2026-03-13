import { useState, useRef, useCallback } from "react";
import { analyzeAudio, AnalyzeResponse } from "../utils/api";

type RecordingState = "idle" | "recording" | "processing" | "done" | "error";

interface UseRecordingReturn {
  state: RecordingState;
  duration: number;
  result: AnalyzeResponse | null;
  error: string | null;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  reset: () => void;
}

export function useRecording(mode: "school" | "work"): UseRecordingReturn {
  const [state, setState] = useState<RecordingState>("idle");
  const [duration, setDuration] = useState(0);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number>(0);

  const startRecording = useCallback(async () => {
    try {
      setError(null);
      setResult(null);
      setDuration(0);
      chunksRef.current = [];

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        setState("processing");
        try {
          const data = await analyzeAudio(blob, mode, "recording.webm");
          setResult(data);
          setState("done");
        } catch (err) {
          setError(err instanceof Error ? err.message : "Analysis failed");
          setState("error");
        }
      };

      mediaRecorderRef.current = recorder;
      recorder.start(1000); // collect data every second
      startTimeRef.current = Date.now();
      setState("recording");

      timerRef.current = setInterval(() => {
        setDuration(Math.floor((Date.now() - startTimeRef.current) / 1000));
      }, 500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not access microphone");
      setState("error");
    }
  }, [mode]);

  const stopRecording = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (mediaRecorderRef.current && state === "recording") {
      mediaRecorderRef.current.stop();
    }
  }, [state]);

  const reset = useCallback(() => {
    setState("idle");
    setDuration(0);
    setResult(null);
    setError(null);
    chunksRef.current = [];
  }, []);

  return { state, duration, result, error, startRecording, stopRecording, reset };
}
