"use client";

import { useRef, useCallback, useState } from "react";

interface VADOptions {
  silenceThreshold?: number;
  silenceDuration?: number;
  onSpeechStart?: () => void;
  onSpeechEnd?: () => void;
  onSilence?: () => void;
  onVolumeChange?: (volume: number) => void;
}

export function useVAD(options: VADOptions = {}) {
  const {
    silenceThreshold = -50,  // More sensitive threshold (was -45)
    silenceDuration = 1500,
    onSpeechStart,
    onSpeechEnd,
    onSilence,
    onVolumeChange,
  } = options;

  const [isSpeaking, setIsSpeaking] = useState(false);
  const [volume, setVolume] = useState(0);

  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const rafIdRef = useRef<number | null>(null);
  const wasSpeakingRef = useRef(false);
  const isActiveRef = useRef(false);

  const startVAD = useCallback(
    (stream: MediaStream) => {
      if (isActiveRef.current) return;
      isActiveRef.current = true;

      try {
        const audioContext = new AudioContext();
        audioContextRef.current = audioContext;

        const analyser = audioContext.createAnalyser();
        analyser.fftSize = 512;
        analyser.smoothingTimeConstant = 0.8;
        analyserRef.current = analyser;

        const source = audioContext.createMediaStreamSource(stream);
        source.connect(analyser);

        const dataArray = new Uint8Array(analyser.frequencyBinCount);

        const checkAudio = () => {
          if (!isActiveRef.current) return;

          analyser.getByteFrequencyData(dataArray);

          let sum = 0;
          for (let i = 0; i < dataArray.length; i++) {
            sum += dataArray[i] * dataArray[i];
          }
          const rms = Math.sqrt(sum / dataArray.length);
          const db = 20 * Math.log10(rms / 255);
          const normalizedVolume = Math.max(0, Math.min(100, (db + 60) * 2));

          setVolume(normalizedVolume);
          onVolumeChange?.(normalizedVolume);

          const isCurrentlySpeaking = db > silenceThreshold;

          if (isCurrentlySpeaking) {
            if (silenceTimerRef.current) {
              clearTimeout(silenceTimerRef.current);
              silenceTimerRef.current = null;
            }

            if (!wasSpeakingRef.current) {
              wasSpeakingRef.current = true;
              setIsSpeaking(true);
              onSpeechStart?.();
            }
          } else {
            if (wasSpeakingRef.current && !silenceTimerRef.current) {
              silenceTimerRef.current = setTimeout(() => {
                wasSpeakingRef.current = false;
                setIsSpeaking(false);
                onSpeechEnd?.();
                onSilence?.();
                silenceTimerRef.current = null;
              }, silenceDuration);
            }
          }

          rafIdRef.current = requestAnimationFrame(checkAudio);
        };

        checkAudio();
      } catch (error) {
        console.error("[VAD] Error starting VAD:", error);
        isActiveRef.current = false;
      }
    },
    [silenceThreshold, silenceDuration, onSpeechStart, onSpeechEnd, onSilence, onVolumeChange]
  );

  const stopVAD = useCallback(() => {
    isActiveRef.current = false;

    if (rafIdRef.current) {
      cancelAnimationFrame(rafIdRef.current);
      rafIdRef.current = null;
    }

    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    analyserRef.current = null;
    wasSpeakingRef.current = false;
    setIsSpeaking(false);
    setVolume(0);
  }, []);

  return {
    startVAD,
    stopVAD,
    isSpeaking,
    volume,
  };
}

export default useVAD;
