"use client";

import { useVoiceChat, VoiceChatStatus } from "@/hooks/useVoiceChat";

interface VoiceChatButtonProps {
  onTranscript?: (transcript: string) => void;
  onReply?: (reply: string) => void;
  onError?: (error: string) => void;
  includeTts?: boolean;
  className?: string;
}

export function VoiceChatButton({
  onTranscript,
  onReply,
  onError,
  includeTts = true,
  className = "",
}: VoiceChatButtonProps) {
  const {
    status,
    isRecording,
    isProcessing,
    startRecording,
    stopRecording,
    cancelRecording,
    error,
  } = useVoiceChat({
    onTranscript,
    onReply,
    onError,
    includeTts,
  });

  const handleClick = async () => {
    if (isRecording) {
      await new Promise(resolve => setTimeout(resolve, 300));
      await stopRecording();
    } else if (!isProcessing) {
      await startRecording();
    }
  };

  const getStatusText = (status: VoiceChatStatus): string => {
    switch (status) {
      case "listening":
        return "Listening...";
      case "thinking":
        return "Thinking...";
      case "speaking":
        return "Speaking...";
      case "error":
        return "Error";
      default:
        return "Tap to speak";
    }
  };

  const getButtonStyle = () => {
    const base =
      "relative flex items-center justify-center w-16 h-16 rounded-full transition-all duration-200 focus:outline-none focus:ring-4 focus:ring-purple-300";

    if (isRecording) {
      return `${base} bg-red-500 hover:bg-red-600 animate-pulse`;
    }
    if (isProcessing) {
      return `${base} bg-yellow-500 cursor-wait`;
    }
    if (status === "error") {
      return `${base} bg-red-100 border-2 border-red-500`;
    }
    return `${base} bg-gradient-to-br from-purple-500 to-indigo-500 hover:from-purple-600 hover:to-indigo-600 shadow-lg hover:shadow-xl`;
  };

  return (
    <div className={`flex flex-col items-center gap-2 ${className}`}>
      <button
        onClick={handleClick}
        disabled={isProcessing}
        className={getButtonStyle()}
        aria-label={getStatusText(status)}
      >
        {isRecording && (
          <span className="absolute inset-0 rounded-full animate-ping bg-red-400 opacity-75" />
        )}
        {isProcessing && (
          <span className="absolute inset-0 rounded-full animate-spin border-4 border-transparent border-t-white opacity-50" />
        )}
        <MicIcon status={status} />
      </button>
      <span className="text-sm text-gray-500 dark:text-gray-400">
        {getStatusText(status)}
      </span>
      {error && (
        <span className="text-xs text-red-500 max-w-[200px] text-center">
          {error}
        </span>
      )}
      {isRecording && (
        <button
          onClick={cancelRecording}
          className="text-xs text-gray-400 hover:text-red-500 underline"
        >
          Cancel
        </button>
      )}
    </div>
  );
}

function MicIcon({ status }: { status: VoiceChatStatus }) {
  if (status === "thinking") {
    return (
      <svg
        className="w-8 h-8 text-white animate-pulse"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <circle cx="12" cy="12" r="3" fill="currentColor" />
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 2v4m0 12v4m10-10h-4M6 12H2m15.07-5.07l-2.83 2.83M8.76 15.24l-2.83 2.83m11.31 0l-2.83-2.83M8.76 8.76L5.93 5.93"
        />
      </svg>
    );
  }

  if (status === "speaking") {
    return (
      <svg
        className="w-8 h-8 text-white"
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
      className="w-8 h-8 text-white"
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

export default VoiceChatButton;
