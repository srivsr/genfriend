"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { useVAD } from "./useVAD";

export type VoiceMode = "push-to-talk" | "continuous";
export type VoiceChatStatus = "idle" | "listening" | "thinking" | "speaking" | "error" | "session-active";

interface VoiceChatResult {
  transcript: string;
  reply_text: string;
  audio?: string | null;
  audio_format?: string | null;
}

interface UseVoiceChatEnhancedOptions {
  mode?: VoiceMode;
  onTranscript?: (transcript: string) => void;
  onReply?: (reply: string) => void;
  onError?: (error: string) => void;
  onModeChange?: (mode: VoiceMode) => void;
  includeTts?: boolean;
  silenceDuration?: number;
  sessionTimeout?: number;
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

export function useVoiceChatEnhanced(options: UseVoiceChatEnhancedOptions = {}) {
  const {
    mode: initialMode = "push-to-talk",
    onTranscript,
    onReply,
    onError,
    onModeChange,
    includeTts = true,
    silenceDuration = 1500,
    sessionTimeout = 8000,
  } = options;

  const [mode, setMode] = useState<VoiceMode>(initialMode);
  const [status, setStatus] = useState<VoiceChatStatus>("idle");
  const [transcript, setTranscript] = useState<string>("");
  const [replyText, setReplyText] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [volume, setVolume] = useState(0);
  const [conversationHistory, setConversationHistory] = useState<Array<{role: string, content: string}>>([]);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const mimeTypeRef = useRef<{ mimeType: string; extension: string }>({ mimeType: "", extension: "webm" });
  const sessionTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const maxRecordingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const isInSessionRef = useRef(false);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  const statusRef = useRef<VoiceChatStatus>("idle");
  const modeRef = useRef<VoiceMode>(initialMode);
  const lastSendTimeRef = useRef<number>(0);

  // Keep refs in sync with state
  useEffect(() => {
    statusRef.current = status;
  }, [status]);

  useEffect(() => {
    modeRef.current = mode;
  }, [mode]);

  const playAudio = useCallback(async (base64Audio: string, format: string) => {
    return new Promise<void>((resolve) => {
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current = null;
      }

      const audio = new Audio(`data:audio/${format};base64,${base64Audio}`);
      currentAudioRef.current = audio;

      audio.onended = () => {
        currentAudioRef.current = null;
        resolve();
      };
      audio.onerror = () => {
        currentAudioRef.current = null;
        resolve();
      };
      audio.play().catch(() => resolve());
    });
  }, []);

  const sendAudio = useCallback(async (audioBlob: Blob): Promise<VoiceChatResult | null> => {
    try {
      setStatus("thinking");

      const filename = `recording.${mimeTypeRef.current.extension}`;
      const formData = new FormData();
      formData.append("audio", audioBlob, filename);
      formData.append("mode", "chat");
      if (includeTts) {
        formData.append("include_tts", "true");
      }

      if (conversationHistory.length > 0) {
        formData.append("history", JSON.stringify(conversationHistory.slice(-10)));
      }

      const endpoint = includeTts
        ? "/audio/voice-chat-with-audio"
        : "/audio/voice-chat";

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
      onTranscript?.(result.transcript);
      onReply?.(result.reply_text);

      setConversationHistory(prev => [
        ...prev,
        { role: "user", content: result.transcript },
        { role: "assistant", content: result.reply_text }
      ]);

      if (result.audio && includeTts) {
        setStatus("speaking");
        await playAudio(result.audio, result.audio_format || "mp3");
      }

      // After response, check if we should continue listening (continuous mode)
      if (modeRef.current === "continuous" && isInSessionRef.current) {
        setStatus("listening");
        lastSendTimeRef.current = Date.now();
        // Reset session timeout
        if (sessionTimeoutRef.current) {
          clearTimeout(sessionTimeoutRef.current);
        }
        sessionTimeoutRef.current = setTimeout(() => {
          if (isInSessionRef.current && statusRef.current !== "thinking" && statusRef.current !== "speaking") {
            endSession();
          }
        }, sessionTimeout);
      } else {
        setStatus("idle");
      }

      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Voice chat failed";
      setError(message);
      setStatus("error");
      onError?.(message);
      return null;
    }
  }, [includeTts, conversationHistory, onTranscript, onReply, onError, playAudio, sessionTimeout]);

  const finishAndSendRecording = useCallback(async () => {
    const mediaRecorder = mediaRecorderRef.current;

    if (!mediaRecorder || mediaRecorder.state === "inactive") {
      return null;
    }

    return new Promise<VoiceChatResult | null>((resolve) => {
      // Request any pending data
      try {
        mediaRecorder.requestData();
      } catch (e) {}

      setTimeout(async () => {
        if (audioChunksRef.current.length === 0) {
          resolve(null);
          return;
        }

        const audioBlob = new Blob(audioChunksRef.current, {
          type: mimeTypeRef.current.mimeType || "audio/webm",
        });

        // Clear chunks for next recording
        audioChunksRef.current = [];

        if (audioBlob.size < 1000) {
          // Too small, probably no speech
          if (modeRef.current === "continuous" && isInSessionRef.current) {
            setStatus("listening");
          }
          resolve(null);
          return;
        }

        const result = await sendAudio(audioBlob);
        resolve(result);
      }, 200);
    });
  }, [sendAudio]);

  // Use ref for the silence handler to avoid stale closure
  const finishAndSendRef = useRef(finishAndSendRecording);
  useEffect(() => {
    finishAndSendRef.current = finishAndSendRecording;
  }, [finishAndSendRecording]);

  const handleSilenceDetected = useCallback(async () => {
    if (audioChunksRef.current.length > 0 && statusRef.current === "listening") {
      await finishAndSendRef.current();
    }
  }, []);

  const { startVAD, stopVAD, isSpeaking } = useVAD({
    silenceDuration,
    silenceThreshold: -55, // More sensitive for better speech detection
    onSilence: () => {
      if (modeRef.current === "continuous" && isInSessionRef.current && statusRef.current === "listening") {
        handleSilenceDetected();
      }
    },
    onVolumeChange: setVolume,
  });

  // Fallback: Auto-send after 5 seconds of recording if VAD doesn't trigger
  const startMaxRecordingTimer = useCallback(() => {
    if (maxRecordingTimerRef.current) {
      clearTimeout(maxRecordingTimerRef.current);
    }
    maxRecordingTimerRef.current = setTimeout(async () => {
      if (
        modeRef.current === "continuous" &&
        isInSessionRef.current &&
        statusRef.current === "listening" &&
        audioChunksRef.current.length > 0
      ) {
        const now = Date.now();
        // Only send if we haven't sent recently (avoid duplicate sends)
        if (now - lastSendTimeRef.current > 3000) {
          lastSendTimeRef.current = now;
          await finishAndSendRef.current();
          // Restart timer for next recording cycle
          if (isInSessionRef.current && statusRef.current === "listening") {
            startMaxRecordingTimer();
          }
        }
      }
    }, 5000); // 5 seconds max recording before auto-send
  }, []);

  const stopMaxRecordingTimer = useCallback(() => {
    if (maxRecordingTimerRef.current) {
      clearTimeout(maxRecordingTimerRef.current);
      maxRecordingTimerRef.current = null;
    }
  }, []);

  const endSession = useCallback(() => {
    isInSessionRef.current = false;

    if (sessionTimeoutRef.current) {
      clearTimeout(sessionTimeoutRef.current);
      sessionTimeoutRef.current = null;
    }

    stopMaxRecordingTimer();
    stopVAD();

    const mediaRecorder = mediaRecorderRef.current;
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
    }

    streamRef.current?.getTracks().forEach((track) => track.stop());

    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }

    audioChunksRef.current = [];
    setStatus("idle");
  }, [stopVAD, stopMaxRecordingTimer]);

  const changeMode = useCallback((newMode: VoiceMode) => {
    if (isInSessionRef.current) {
      endSession();
    }
    setMode(newMode);
    onModeChange?.(newMode);
  }, [endSession, onModeChange]);

  const startSession = useCallback(async () => {
    try {
      setError(null);
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
        onError?.("Recording failed");
      };

      mediaRecorder.start(500);

      if (mode === "continuous") {
        startVAD(stream);
        // Start fallback timer for auto-send
        startMaxRecordingTimer();
      }

      isInSessionRef.current = true;
      setStatus("listening");
      lastSendTimeRef.current = Date.now();

      // Set session timeout for continuous mode
      if (mode === "continuous") {
        sessionTimeoutRef.current = setTimeout(() => {
          if (isInSessionRef.current && statusRef.current !== "thinking" && statusRef.current !== "speaking") {
            endSession();
          }
        }, sessionTimeout);
      }

    } catch (err) {
      const message = err instanceof Error ? err.message : "Microphone access denied";
      setError(message);
      setStatus("error");
      onError?.(message);
    }
  }, [mode, startVAD, onError, sessionTimeout, endSession, startMaxRecordingTimer]);

  const handleMicClick = useCallback(async () => {
    if (mode === "push-to-talk") {
      if (status === "listening") {
        await finishAndSendRecording();
        endSession();
      } else if (status === "idle" || status === "error") {
        await startSession();
      }
    } else {
      // Continuous mode
      if (isInSessionRef.current) {
        endSession();
      } else {
        await startSession();
      }
    }
  }, [mode, status, startSession, finishAndSendRecording, endSession]);

  const interruptPlayback = useCallback(() => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
      if (isInSessionRef.current) {
        setStatus("listening");
      }
    }
  }, []);

  const clearHistory = useCallback(() => {
    setConversationHistory([]);
  }, []);

  useEffect(() => {
    return () => {
      endSession();
    };
  }, [endSession]);

  return {
    mode,
    status,
    transcript,
    replyText,
    error,
    volume,
    conversationHistory,
    isRecording: status === "listening",
    isProcessing: status === "thinking" || status === "speaking",
    isInSession: isInSessionRef.current,
    isSpeaking,
    changeMode,
    handleMicClick,
    startSession,
    endSession,
    interruptPlayback,
    clearHistory,
  };
}

export default useVoiceChatEnhanced;
