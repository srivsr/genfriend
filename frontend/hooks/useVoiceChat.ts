"use client";

import { useState, useRef, useCallback } from "react";

export type VoiceChatStatus = "idle" | "listening" | "thinking" | "speaking" | "error";

interface VoiceChatResult {
  transcript: string;
  reply_text: string;
  audio?: string | null;
  audio_format?: string | null;
}

interface UseVoiceChatOptions {
  onTranscript?: (transcript: string) => void;
  onReply?: (reply: string) => void;
  onError?: (error: string) => void;
  includeTts?: boolean;
}

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

export function useVoiceChat(options: UseVoiceChatOptions = {}) {
  const [status, setStatus] = useState<VoiceChatStatus>("idle");
  const [transcript, setTranscript] = useState<string>("");
  const [replyText, setReplyText] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const mimeTypeRef = useRef<{ mimeType: string; extension: string }>({ mimeType: "", extension: "webm" });

  const startRecording = useCallback(async () => {
    try {
      setError(null);
      setStatus("listening");
      audioChunksRef.current = [];

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000,
        }
      });
      streamRef.current = stream;

      const { mimeType, extension } = getSupportedMimeType();
      mimeTypeRef.current = { mimeType, extension };

      const mediaRecorderOptions: MediaRecorderOptions = {};
      if (mimeType) {
        mediaRecorderOptions.mimeType = mimeType;
      }

      const mediaRecorder = new MediaRecorder(stream, mediaRecorderOptions);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onerror = () => {
        setError("Recording failed");
        setStatus("error");
        options.onError?.("Recording failed");
      };

      mediaRecorder.start(1000);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Microphone access denied";
      setError(message);
      setStatus("error");
      options.onError?.(message);
    }
  }, [options]);

  const stopRecording = useCallback(async () => {
    return new Promise<Blob | null>((resolve) => {
      const mediaRecorder = mediaRecorderRef.current;

      if (!mediaRecorder) {
        resolve(null);
        return;
      }

      if (mediaRecorder.state === "inactive") {
        if (audioChunksRef.current.length > 0) {
          const audioBlob = new Blob(audioChunksRef.current, {
            type: mimeTypeRef.current.mimeType || "audio/webm",
          });
          resolve(audioBlob);
        } else {
          resolve(null);
        }
        return;
      }

      mediaRecorder.onstop = () => {
        setTimeout(() => {
          const totalSize = audioChunksRef.current.reduce((acc, chunk) => acc + chunk.size, 0);

          if (audioChunksRef.current.length === 0 || totalSize === 0) {
            resolve(null);
            return;
          }

          const audioBlob = new Blob(audioChunksRef.current, {
            type: mimeTypeRef.current.mimeType || "audio/webm",
          });

          streamRef.current?.getTracks().forEach((track) => track.stop());
          resolve(audioBlob);
        }, 100);
      };

      try {
        mediaRecorder.requestData();
      } catch (e) {}

      setTimeout(() => {
        if (mediaRecorder.state !== "inactive") {
          try {
            mediaRecorder.stop();
          } catch (e) {
            if (audioChunksRef.current.length > 0) {
              const audioBlob = new Blob(audioChunksRef.current, {
                type: mimeTypeRef.current.mimeType || "audio/webm",
              });
              resolve(audioBlob);
            } else {
              resolve(null);
            }
          }
        }
      }, 200);
    });
  }, []);

  const sendAudio = useCallback(
    async (audioBlob: Blob) => {
      try {
        setStatus("thinking");

        const filename = `recording.${mimeTypeRef.current.extension}`;
        const formData = new FormData();
        formData.append("audio", audioBlob, filename);
        formData.append("mode", "chat");
        if (options.includeTts !== false) {
          formData.append("include_tts", "true");
        }

        const endpoint = options.includeTts !== false
          ? "/api/v1/audio/voice-chat-with-audio"
          : "/api/v1/audio/voice-chat";

        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}${endpoint}`,
          {
            method: "POST",
            body: formData,
          }
        );

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.detail || "Voice chat failed");
        }

        const result: VoiceChatResult = await response.json();

        setTranscript(result.transcript);
        setReplyText(result.reply_text);
        options.onTranscript?.(result.transcript);
        options.onReply?.(result.reply_text);

        if (result.audio && options.includeTts !== false) {
          setStatus("speaking");
          await playAudio(result.audio, result.audio_format || "mp3");
        }

        setStatus("idle");
        return result;
      } catch (err) {
        const message = err instanceof Error ? err.message : "Voice chat failed";
        setError(message);
        setStatus("error");
        options.onError?.(message);
        return null;
      }
    },
    [options]
  );

  const playAudio = useCallback(async (base64Audio: string, format: string) => {
    return new Promise<void>((resolve) => {
      const audio = new Audio(`data:audio/${format};base64,${base64Audio}`);
      audio.onended = () => resolve();
      audio.onerror = () => resolve();
      audio.play().catch(() => resolve());
    });
  }, []);

  const finishRecording = useCallback(async () => {
    const audioBlob = await stopRecording();
    if (audioBlob && audioBlob.size > 0) {
      return sendAudio(audioBlob);
    }
    setError("No audio captured. Please try again.");
    setStatus("error");
    return null;
  }, [stopRecording, sendAudio]);

  const cancelRecording = useCallback(() => {
    const mediaRecorder = mediaRecorderRef.current;
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
    }
    streamRef.current?.getTracks().forEach((track) => track.stop());
    audioChunksRef.current = [];
    setStatus("idle");
  }, []);

  const reset = useCallback(() => {
    setStatus("idle");
    setTranscript("");
    setReplyText("");
    setError(null);
  }, []);

  return {
    status,
    transcript,
    replyText,
    error,
    isRecording: status === "listening",
    isProcessing: status === "thinking" || status === "speaking",
    startRecording,
    stopRecording: finishRecording,
    cancelRecording,
    reset,
  };
}
