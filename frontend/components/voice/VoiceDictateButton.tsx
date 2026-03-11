"use client";

import { useState, useRef, useCallback } from "react";
import { Mic, Square, Loader2 } from "lucide-react";

interface VoiceDictateButtonProps {
  onTranscript: (transcript: string) => void;
  onError?: (error: string) => void;
  className?: string;
  size?: "sm" | "md" | "lg";
}

type DictateStatus = "idle" | "recording" | "processing" | "error";

function getSupportedMimeType(): { mimeType: string; extension: string } {
  const types = [
    { mimeType: "audio/webm;codecs=opus", extension: "webm" },
    { mimeType: "audio/webm", extension: "webm" },
    { mimeType: "audio/mp4", extension: "m4a" },
    { mimeType: "audio/ogg;codecs=opus", extension: "ogg" },
    { mimeType: "audio/wav", extension: "wav" },
  ];

  for (const type of types) {
    if (typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported(type.mimeType)) {
      return type;
    }
  }
  return { mimeType: "", extension: "webm" };
}

export function VoiceDictateButton({
  onTranscript,
  onError,
  className = "",
  size = "md",
}: VoiceDictateButtonProps) {
  const [status, setStatus] = useState<DictateStatus>("idle");
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const mimeTypeRef = useRef<{ mimeType: string; extension: string }>({ mimeType: "", extension: "webm" });

  const startRecording = useCallback(async () => {
    try {
      setStatus("recording");
      audioChunksRef.current = [];

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, sampleRate: 16000 }
      });
      streamRef.current = stream;

      const { mimeType, extension } = getSupportedMimeType();
      mimeTypeRef.current = { mimeType, extension };

      const mediaRecorderOptions: MediaRecorderOptions = {};
      if (mimeType) mediaRecorderOptions.mimeType = mimeType;

      const mediaRecorder = new MediaRecorder(stream, mediaRecorderOptions);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onerror = () => {
        setStatus("error");
        onError?.("Recording failed");
      };

      mediaRecorder.start(1000);
    } catch (err) {
      setStatus("error");
      onError?.(err instanceof Error ? err.message : "Microphone access denied");
    }
  }, [onError]);

  const stopAndTranscribe = useCallback(async () => {
    const mediaRecorder = mediaRecorderRef.current;
    if (!mediaRecorder) return;

    setStatus("processing");

    return new Promise<void>((resolve) => {
      mediaRecorder.onstop = async () => {
        streamRef.current?.getTracks().forEach((track) => track.stop());

        const audioBlob = new Blob(audioChunksRef.current, {
          type: mimeTypeRef.current.mimeType || "audio/webm",
        });

        if (audioBlob.size < 1000) {
          setStatus("idle");
          resolve();
          return;
        }

        try {
          const formData = new FormData();
          formData.append("audio", audioBlob, `recording.${mimeTypeRef.current.extension}`);

          const response = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/audio/transcribe`,
            { method: "POST", body: formData }
          );

          if (!response.ok) {
            throw new Error("Transcription failed");
          }

          const result = await response.json();
          if (result.transcript) {
            onTranscript(result.transcript);
          }
          setStatus("idle");
        } catch (err) {
          setStatus("error");
          onError?.(err instanceof Error ? err.message : "Transcription failed");
          setTimeout(() => setStatus("idle"), 2000);
        }
        resolve();
      };

      try {
        mediaRecorder.requestData();
      } catch (e) {}

      setTimeout(() => {
        if (mediaRecorder.state !== "inactive") {
          mediaRecorder.stop();
        }
      }, 200);
    });
  }, [onTranscript, onError]);

  const handleClick = async () => {
    if (status === "recording") {
      await stopAndTranscribe();
    } else if (status === "idle" || status === "error") {
      await startRecording();
    }
  };

  const sizeClasses = {
    sm: "w-8 h-8",
    md: "w-10 h-10",
    lg: "w-12 h-12",
  };

  const iconSize = { sm: 14, md: 18, lg: 22 };

  return (
    <button
      onClick={handleClick}
      disabled={status === "processing"}
      className={`${sizeClasses[size]} rounded-full flex items-center justify-center transition-all ${
        status === "recording"
          ? "bg-red-500 hover:bg-red-600 text-white animate-pulse"
          : status === "processing"
          ? "bg-yellow-500 text-white cursor-wait"
          : status === "error"
          ? "bg-red-100 text-red-600 border-2 border-red-300"
          : "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-purple-100 hover:text-purple-600"
      } ${className}`}
      title={
        status === "recording"
          ? "Tap to stop"
          : status === "processing"
          ? "Processing..."
          : "Tap to dictate"
      }
    >
      {status === "recording" ? (
        <Square size={iconSize[size]} />
      ) : status === "processing" ? (
        <Loader2 size={iconSize[size]} className="animate-spin" />
      ) : (
        <Mic size={iconSize[size]} />
      )}
    </button>
  );
}

export default VoiceDictateButton;
