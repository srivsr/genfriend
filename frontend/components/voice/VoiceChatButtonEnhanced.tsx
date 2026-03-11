"use client";

import { useState } from "react";
import { useVoiceChatEnhanced, VoiceMode, VoiceChatStatus } from "@/hooks/useVoiceChatEnhanced";

interface VoiceChatButtonEnhancedProps {
  onTranscript?: (transcript: string) => void;
  onReply?: (reply: string) => void;
  onError?: (error: string) => void;
  includeTts?: boolean;
  className?: string;
  showModeToggle?: boolean;
  defaultMode?: VoiceMode;
}

export function VoiceChatButtonEnhanced({
  onTranscript,
  onReply,
  onError,
  includeTts = true,
  className = "",
  showModeToggle = true,
  defaultMode = "push-to-talk",
}: VoiceChatButtonEnhancedProps) {
  const {
    mode,
    status,
    error,
    volume,
    conversationHistory,
    isRecording,
    isProcessing,
    changeMode,
    handleMicClick,
    endSession,
    interruptPlayback,
    clearHistory,
  } = useVoiceChatEnhanced({
    mode: defaultMode,
    onTranscript,
    onReply,
    onError,
    includeTts,
    silenceDuration: 1500,
    sessionTimeout: 8000,
  });

  const handleModeChange = (newMode: VoiceMode) => {
    changeMode(newMode);
  };

  const getStatusText = (): string => {
    switch (status) {
      case "listening":
        return mode === "continuous" ? "Listening... (speak now)" : "Recording...";
      case "thinking":
        return "Processing...";
      case "speaking":
        return "Speaking... (tap to interrupt)";
      case "session-active":
        return "Session active";
      case "error":
        return "Error - tap to retry";
      default:
        return mode === "continuous" ? "Tap to start session" : "Tap to speak";
    }
  };

  const getModeLabel = (): string => {
    return mode === "continuous" ? "Continuous" : "Push-to-Talk";
  };

  const getButtonStyle = () => {
    const base =
      "relative flex items-center justify-center w-20 h-20 rounded-full transition-all duration-200 focus:outline-none focus:ring-4 focus:ring-purple-300";

    if (status === "listening") {
      return `${base} bg-red-500 hover:bg-red-600`;
    }
    if (status === "thinking") {
      return `${base} bg-yellow-500 cursor-wait`;
    }
    if (status === "speaking") {
      return `${base} bg-green-500 hover:bg-green-600`;
    }
    if (status === "error") {
      return `${base} bg-red-100 border-2 border-red-500`;
    }
    return `${base} bg-gradient-to-br from-purple-500 to-indigo-500 hover:from-purple-600 hover:to-indigo-600 shadow-lg hover:shadow-xl`;
  };

  const handleClick = () => {
    if (status === "speaking") {
      interruptPlayback();
    } else {
      handleMicClick();
    }
  };

  return (
    <div className={`flex flex-col items-center gap-3 ${className}`}>
      {showModeToggle && (
        <div className="flex items-center gap-2 bg-gray-100 dark:bg-gray-800 rounded-full p-1">
          <button
            onClick={() => handleModeChange("push-to-talk")}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
              mode === "push-to-talk"
                ? "bg-white dark:bg-gray-700 shadow text-purple-600 dark:text-purple-400"
                : "text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            }`}
          >
            Push-to-Talk
          </button>
          <button
            onClick={() => handleModeChange("continuous")}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
              mode === "continuous"
                ? "bg-white dark:bg-gray-700 shadow text-purple-600 dark:text-purple-400"
                : "text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            }`}
          >
            Continuous
          </button>
        </div>
      )}

      {status === "listening" && (
        <div className="w-32 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-green-400 to-green-600 transition-all duration-100"
            style={{ width: `${Math.min(100, volume)}%` }}
          />
        </div>
      )}

      <button
        onClick={handleClick}
        disabled={isProcessing && status !== "speaking"}
        className={getButtonStyle()}
        aria-label={getStatusText()}
      >
        {status === "listening" && (
          <span className="absolute inset-0 rounded-full animate-ping bg-red-400 opacity-50" />
        )}
        {status === "thinking" && (
          <span className="absolute inset-0 rounded-full animate-spin border-4 border-transparent border-t-white opacity-50" />
        )}
        <VoiceIcon status={status} mode={mode} />
      </button>

      <span className="text-sm text-gray-600 dark:text-gray-400 text-center">
        {getStatusText()}
      </span>

      <span className="text-xs text-gray-400 dark:text-gray-500">
        Mode: {getModeLabel()}
      </span>

      {error && (
        <span className="text-xs text-red-500 max-w-[200px] text-center">
          {error}
        </span>
      )}

      {mode === "continuous" && status === "listening" && (
        <button
          onClick={endSession}
          className="text-xs text-gray-400 hover:text-red-500 underline"
        >
          End Session
        </button>
      )}

      {conversationHistory.length > 0 && (
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <span>{conversationHistory.length / 2} exchanges</span>
          <button
            onClick={clearHistory}
            className="text-red-400 hover:text-red-600"
            title="Clear conversation history"
          >
            Clear
          </button>
        </div>
      )}

      <div className="text-xs text-gray-400 dark:text-gray-500 text-center max-w-[200px]">
        {mode === "continuous" ? (
          <>Tap mic to start. Speak naturally. Auto-stops after silence.</>
        ) : (
          <>Tap to start recording. Tap again to send.</>
        )}
      </div>
    </div>
  );
}

function VoiceIcon({ status, mode }: { status: VoiceChatStatus; mode: VoiceMode }) {
  if (status === "thinking") {
    return (
      <svg
        className="w-10 h-10 text-white animate-pulse"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <circle cx="12" cy="12" r="3" fill="currentColor" />
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 2v4m0 12v4m10-10h-4M6 12H2"
        />
      </svg>
    );
  }

  if (status === "speaking") {
    return (
      <svg
        className="w-10 h-10 text-white"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"
        />
      </svg>
    );
  }

  return (
    <svg
      className="w-10 h-10 text-white"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
      />
    </svg>
  );
}

export default VoiceChatButtonEnhanced;
