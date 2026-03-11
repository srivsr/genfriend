'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { Send, Sparkles, Mic, MicOff, Volume2, Square, Loader2 } from 'lucide-react'
import { chatApi } from '@/lib/api-client'
import clsx from 'clsx'

interface Message {
  role: 'user' | 'assistant'
  content: string
  isVoice?: boolean
}

type VoiceStatus = 'idle' | 'recording' | 'processing' | 'playing' | 'error'

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: "Hey! I'm Gen-Friend, your AI companion. How can I help you today? Type or tap the mic to speak!" }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [voiceStatus, setVoiceStatus] = useState<VoiceStatus>('idle')
  const [voiceError, setVoiceError] = useState<string | null>(null)
  const [volume, setVolume] = useState(0)
  const [enableTTS, setEnableTTS] = useState(true)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const streamRef = useRef<MediaStream | null>(null)
  const currentAudioRef = useRef<HTMLAudioElement | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animationFrameRef = useRef<number | null>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRecording()
      if (currentAudioRef.current) {
        currentAudioRef.current.pause()
      }
    }
  }, [])

  const sendTextMessage = async (text?: string) => {
    const messageText = text || input.trim()
    if (!messageText || loading) return

    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: messageText }])
    setLoading(true)

    try {
      const { data } = await chatApi.send(messageText)
      const reply = data.data.message.content
      setMessages(prev => [...prev, { role: 'assistant', content: reply }])

      // Play TTS for text messages if enabled
      if (enableTTS) {
        playTTS(reply)
      }
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: "Sorry, I couldn't process that. Please try again." }])
    } finally {
      setLoading(false)
    }
  }

  const playTTS = async (text: string) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/audio/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text.slice(0, 500) }) // Limit for cost
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = URL.createObjectURL(blob)
        const audio = new Audio(url)
        currentAudioRef.current = audio
        setVoiceStatus('playing')

        audio.onended = () => {
          setVoiceStatus('idle')
          URL.revokeObjectURL(url)
        }
        audio.onerror = () => {
          setVoiceStatus('idle')
        }
        audio.play().catch(() => setVoiceStatus('idle'))
      }
    } catch (err) {
      console.error('TTS failed:', err)
    }
  }

  const stopPlayback = () => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause()
      currentAudioRef.current = null
    }
    setVoiceStatus('idle')
  }

  const startRecording = async () => {
    try {
      setVoiceError(null)
      audioChunksRef.current = []

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000,
        }
      })
      streamRef.current = stream

      // Set up volume meter
      const audioContext = new AudioContext()
      const source = audioContext.createMediaStreamSource(stream)
      const analyser = audioContext.createAnalyser()
      analyser.fftSize = 256
      source.connect(analyser)
      analyserRef.current = analyser

      const updateVolume = () => {
        if (analyserRef.current && voiceStatus === 'recording') {
          const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount)
          analyserRef.current.getByteFrequencyData(dataArray)
          const avg = dataArray.reduce((a, b) => a + b) / dataArray.length
          setVolume(Math.min(100, avg * 2))
          animationFrameRef.current = requestAnimationFrame(updateVolume)
        }
      }

      // Determine supported mime type
      const mimeTypes = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg']
      let mimeType = ''
      for (const type of mimeTypes) {
        if (MediaRecorder.isTypeSupported(type)) {
          mimeType = type
          break
        }
      }

      const mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)
      mediaRecorderRef.current = mediaRecorder

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.start(500)
      setVoiceStatus('recording')
      updateVolume()

    } catch (err) {
      const message = err instanceof Error ? err.message : 'Microphone access denied'
      setVoiceError(message)
      setVoiceStatus('error')
    }
  }

  const stopRecording = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current)
    }

    const mediaRecorder = mediaRecorderRef.current
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop()
    }

    streamRef.current?.getTracks().forEach(track => track.stop())
    setVolume(0)
  }, [])

  const sendVoiceMessage = async () => {
    stopRecording()

    // Wait for final data
    await new Promise(resolve => setTimeout(resolve, 300))

    if (audioChunksRef.current.length === 0) {
      setVoiceStatus('idle')
      return
    }

    const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })

    if (audioBlob.size < 1000) {
      setVoiceError('Recording too short. Please try again.')
      setVoiceStatus('idle')
      return
    }

    setVoiceStatus('processing')

    try {
      const formData = new FormData()
      formData.append('audio', audioBlob, 'recording.webm')
      formData.append('mode', 'chat')
      formData.append('include_tts', enableTTS ? 'true' : 'false')

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/audio/voice-chat-with-audio`,
        { method: 'POST', body: formData }
      )

      if (!response.ok) {
        throw new Error('Voice chat failed')
      }

      const result = await response.json()

      // Add user's transcript
      setMessages(prev => [...prev, { role: 'user', content: result.transcript, isVoice: true }])

      // Add AI reply
      setMessages(prev => [...prev, { role: 'assistant', content: result.reply_text }])

      // Play audio response if available
      if (result.audio && enableTTS) {
        setVoiceStatus('playing')
        const audio = new Audio(`data:audio/${result.audio_format || 'mp3'};base64,${result.audio}`)
        currentAudioRef.current = audio

        audio.onended = () => {
          setVoiceStatus('idle')
          currentAudioRef.current = null
        }
        audio.onerror = () => setVoiceStatus('idle')
        audio.play().catch(() => setVoiceStatus('idle'))
      } else {
        setVoiceStatus('idle')
      }

    } catch (err) {
      const message = err instanceof Error ? err.message : 'Voice chat failed'
      setVoiceError(message)
      setVoiceStatus('error')
      setTimeout(() => setVoiceStatus('idle'), 2000)
    }
  }

  const handleMicClick = () => {
    if (voiceStatus === 'recording') {
      sendVoiceMessage()
    } else if (voiceStatus === 'playing') {
      stopPlayback()
    } else if (voiceStatus === 'idle' || voiceStatus === 'error') {
      startRecording()
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendTextMessage()
    }
  }

  const getMicButtonStyle = () => {
    switch (voiceStatus) {
      case 'recording':
        return 'bg-red-500 hover:bg-red-600 animate-pulse'
      case 'processing':
        return 'bg-yellow-500 cursor-wait'
      case 'playing':
        return 'bg-green-500 hover:bg-green-600'
      case 'error':
        return 'bg-red-200 text-red-600'
      default:
        return 'bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300'
    }
  }

  const getMicIcon = () => {
    switch (voiceStatus) {
      case 'recording':
        return <Square size={18} className="text-white" />
      case 'processing':
        return <Loader2 size={18} className="text-white animate-spin" />
      case 'playing':
        return <Volume2 size={18} className="text-white" />
      default:
        return <Mic size={18} />
    }
  }

  const getStatusText = () => {
    switch (voiceStatus) {
      case 'recording':
        return 'Recording... Tap to send'
      case 'processing':
        return 'Processing...'
      case 'playing':
        return 'Playing... Tap to stop'
      case 'error':
        return voiceError || 'Error'
      default:
        return null
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <header className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-r from-primary-500 to-accent-500 flex items-center justify-center">
            <Sparkles className="text-white" size={20} />
          </div>
          <div>
            <h1 className="font-semibold">Gen-Friend</h1>
            <p className="text-xs text-gray-500">Your AI Companion</p>
          </div>
        </div>

        {/* TTS Toggle */}
        <button
          onClick={() => setEnableTTS(!enableTTS)}
          className={clsx(
            'flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium transition',
            enableTTS
              ? 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400'
              : 'bg-gray-100 text-gray-500 dark:bg-gray-800'
          )}
        >
          <Volume2 size={14} />
          Voice {enableTTS ? 'On' : 'Off'}
        </button>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {messages.map((msg, i) => (
          <div key={i} className={clsx('flex', msg.role === 'user' ? 'justify-end' : 'justify-start')}>
            <div className={clsx(
              'max-w-[85%] rounded-2xl px-4 py-3',
              msg.role === 'user'
                ? 'bg-primary-600 text-white rounded-br-md'
                : 'bg-white dark:bg-gray-800 shadow-sm rounded-bl-md'
            )}>
              {msg.isVoice && (
                <div className="flex items-center gap-1 text-xs opacity-70 mb-1">
                  <Mic size={10} />
                  <span>Voice</span>
                </div>
              )}
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white dark:bg-gray-800 rounded-2xl px-4 py-3 shadow-sm">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></span>
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Voice Status Bar */}
      {voiceStatus !== 'idle' && (
        <div className="mb-2">
          {voiceStatus === 'recording' && (
            <div className="flex items-center gap-2 px-4 py-2 bg-red-50 dark:bg-red-900/20 rounded-xl">
              <div className="flex-1 h-2 bg-red-200 dark:bg-red-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-red-500 transition-all duration-100"
                  style={{ width: `${volume}%` }}
                />
              </div>
              <span className="text-xs text-red-600 dark:text-red-400 font-medium">
                {getStatusText()}
              </span>
            </div>
          )}
          {voiceStatus === 'processing' && (
            <div className="flex items-center justify-center gap-2 px-4 py-2 bg-yellow-50 dark:bg-yellow-900/20 rounded-xl">
              <Loader2 size={16} className="animate-spin text-yellow-600" />
              <span className="text-xs text-yellow-600 dark:text-yellow-400 font-medium">
                {getStatusText()}
              </span>
            </div>
          )}
          {voiceStatus === 'playing' && (
            <div className="flex items-center justify-center gap-2 px-4 py-2 bg-green-50 dark:bg-green-900/20 rounded-xl">
              <Volume2 size={16} className="text-green-600" />
              <span className="text-xs text-green-600 dark:text-green-400 font-medium">
                {getStatusText()}
              </span>
            </div>
          )}
          {voiceStatus === 'error' && (
            <div className="flex items-center justify-center gap-2 px-4 py-2 bg-red-50 dark:bg-red-900/20 rounded-xl">
              <MicOff size={16} className="text-red-600" />
              <span className="text-xs text-red-600 dark:text-red-400 font-medium">
                {getStatusText()}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Input Bar */}
      <div className="flex gap-2 bg-white dark:bg-gray-800 rounded-2xl p-2 shadow-lg">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={voiceStatus === 'recording' ? 'Recording...' : 'Type or tap mic to speak...'}
          className="flex-1 px-4 py-2 bg-transparent outline-none"
          disabled={loading || voiceStatus === 'recording' || voiceStatus === 'processing'}
        />

        {/* Mic Button */}
        <button
          onClick={handleMicClick}
          disabled={loading || voiceStatus === 'processing'}
          className={clsx(
            'w-10 h-10 rounded-xl flex items-center justify-center transition-all',
            getMicButtonStyle()
          )}
          title={voiceStatus === 'recording' ? 'Tap to send' : voiceStatus === 'playing' ? 'Tap to stop' : 'Tap to speak'}
        >
          {getMicIcon()}
        </button>

        {/* Send Button */}
        <button
          onClick={() => sendTextMessage()}
          disabled={!input.trim() || loading || voiceStatus === 'recording'}
          className="w-10 h-10 bg-primary-600 hover:bg-primary-700 text-white rounded-xl flex items-center justify-center transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Send size={18} />
        </button>
      </div>

      {/* Helper Text */}
      <p className="text-center text-xs text-gray-400 mt-2">
        Type a message or tap the mic to speak
      </p>
    </div>
  )
}
