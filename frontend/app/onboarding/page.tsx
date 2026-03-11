'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowRight, User, Bot, Heart, MessageCircle, Bell, Clock, Check, Sparkles } from 'lucide-react'
import { preferencesApi } from '@/lib/api-client'

type OnboardingStep = 'welcome' | 'name' | 'coach-name' | 'coach-relationship' | 'coach-tone' | 'notification' | 'quiet-hours' | 'complete'

const COACH_TONES = [
  { id: 'warm', label: 'Warm & Supportive', description: 'Encouraging, empathetic, like a caring friend', emoji: '🤗' },
  { id: 'direct', label: 'Direct & Focused', description: 'Concise, action-oriented, no fluff', emoji: '🎯' },
  { id: 'playful', label: 'Playful & Energetic', description: 'Fun, motivating, uses humor', emoji: '⚡' },
]

const NOTIFICATION_LEVELS = [
  { id: 'off', label: 'Off', description: 'No proactive notifications' },
  { id: 'gentle', label: 'Gentle', description: '1-2 nudges per week' },
  { id: 'balanced', label: 'Balanced', description: 'Daily check-ins when needed' },
  { id: 'intense', label: 'Intense', description: 'Multiple daily reminders' },
]

const COACH_RELATIONSHIPS = [
  { id: 'friend', label: 'Best Friend', description: 'Someone who knows me well' },
  { id: 'mentor', label: 'Wise Mentor', description: 'Experienced guide and advisor' },
  { id: 'future_self', label: 'My Future Self', description: 'Who I want to become' },
  { id: 'coach', label: 'Professional Coach', description: 'Focused on results' },
  { id: 'pet', label: 'My Pet (Dog/Cat)', description: 'Unconditional support and love' },
]

export default function OnboardingPage() {
  const router = useRouter()
  const [step, setStep] = useState<OnboardingStep>('welcome')
  const [loading, setLoading] = useState(false)

  // Form data
  const [preferredName, setPreferredName] = useState('')
  const [coachName, setCoachName] = useState('Gen')
  const [coachRelationship, setCoachRelationship] = useState('')
  const [coachTone, setCoachTone] = useState('warm')
  const [notificationLevel, setNotificationLevel] = useState('balanced')
  const [quietHoursStart, setQuietHoursStart] = useState('22:00')
  const [quietHoursEnd, setQuietHoursEnd] = useState('07:00')

  const steps: OnboardingStep[] = ['welcome', 'name', 'coach-name', 'coach-relationship', 'coach-tone', 'notification', 'quiet-hours', 'complete']
  const currentStepIndex = steps.indexOf(step)
  const progress = ((currentStepIndex) / (steps.length - 1)) * 100

  const nextStep = () => {
    const idx = steps.indexOf(step)
    if (idx < steps.length - 1) {
      setStep(steps[idx + 1])
    }
  }

  const canProceed = () => {
    switch (step) {
      case 'welcome': return true
      case 'name': return preferredName.length >= 2
      case 'coach-name': return coachName.length >= 2
      case 'coach-relationship': return coachRelationship !== ''
      case 'coach-tone': return coachTone !== ''
      case 'notification': return notificationLevel !== ''
      case 'quiet-hours': return true
      default: return true
    }
  }

  const handleComplete = async () => {
    setLoading(true)
    try {
      await preferencesApi.update({
        preferred_name: preferredName,
        coach_name: coachName,
        coach_relationship: coachRelationship,
        coach_tone: coachTone,
        notification_level: notificationLevel,
        quiet_hours_start: quietHoursStart,
        quiet_hours_end: quietHoursEnd,
        onboarding_completed: true
      })
      router.push('/home')
    } catch (e) {
      console.error('Failed to save preferences', e)
      router.push('/home')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-50 to-white dark:from-gray-900 dark:to-gray-800">
      {/* Progress bar */}
      {step !== 'welcome' && step !== 'complete' && (
        <div className="fixed top-0 left-0 right-0 h-1 bg-gray-200 dark:bg-gray-700 z-10">
          <div
            className="h-full bg-gradient-to-r from-primary-500 to-accent-500 transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      <div className="max-w-md mx-auto px-6 py-12 min-h-screen flex flex-col">
        {/* Welcome */}
        {step === 'welcome' && (
          <div className="flex-1 flex flex-col items-center justify-center text-center">
            <div className="w-24 h-24 bg-gradient-to-r from-primary-500 to-accent-500 rounded-full flex items-center justify-center mb-6 animate-pulse">
              <Sparkles className="text-white" size={48} />
            </div>
            <h1 className="text-3xl font-bold mb-4">Welcome to Gen-Friend</h1>
            <p className="text-gray-600 dark:text-gray-300 mb-8">
              Your AI-powered productivity companion. Let's set things up so I can be the best partner for your journey.
            </p>
            <p className="text-sm text-gray-500 mb-8">This will take about 2 minutes</p>
            <button
              onClick={nextStep}
              className="w-full py-4 bg-gradient-to-r from-primary-500 to-accent-500 text-white rounded-2xl font-semibold text-lg flex items-center justify-center gap-2"
            >
              Let's Get Started
              <ArrowRight size={20} />
            </button>
          </div>
        )}

        {/* Step: Name */}
        {step === 'name' && (
          <div className="flex-1 flex flex-col">
            <div className="flex-1 flex flex-col justify-center">
              <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mb-6">
                <User className="text-blue-600" size={32} />
              </div>
              <h2 className="text-2xl font-bold mb-2">What should I call you?</h2>
              <p className="text-gray-500 mb-6">Pick a name you'd like me to use in our conversations.</p>
              <input
                type="text"
                value={preferredName}
                onChange={(e) => setPreferredName(e.target.value)}
                placeholder="e.g., Sri, Alex, Coach..."
                className="w-full px-4 py-4 text-lg border-2 border-gray-200 dark:border-gray-700 rounded-2xl focus:outline-none focus:border-primary-500 dark:bg-gray-800"
                autoFocus
              />
            </div>
            <button
              onClick={nextStep}
              disabled={!canProceed()}
              className="w-full py-4 bg-gradient-to-r from-primary-500 to-accent-500 text-white rounded-2xl font-semibold disabled:opacity-50 flex items-center justify-center gap-2"
            >
              Continue
              <ArrowRight size={20} />
            </button>
          </div>
        )}

        {/* Step: Coach Name */}
        {step === 'coach-name' && (
          <div className="flex-1 flex flex-col">
            <div className="flex-1 flex flex-col justify-center">
              <div className="w-16 h-16 bg-purple-100 dark:bg-purple-900/30 rounded-full flex items-center justify-center mb-6">
                <Bot className="text-purple-600" size={32} />
              </div>
              <h2 className="text-2xl font-bold mb-2">What's my name?</h2>
              <p className="text-gray-500 mb-6">Give me a name you'll enjoy calling me. I'll sign my messages with it!</p>
              <input
                type="text"
                value={coachName}
                onChange={(e) => setCoachName(e.target.value)}
                placeholder="e.g., Gen, Max, Coach, Buddy..."
                className="w-full px-4 py-4 text-lg border-2 border-gray-200 dark:border-gray-700 rounded-2xl focus:outline-none focus:border-primary-500 dark:bg-gray-800"
              />
              <p className="text-sm text-gray-400 mt-2">Default: Gen</p>
            </div>
            <button
              onClick={nextStep}
              disabled={!canProceed()}
              className="w-full py-4 bg-gradient-to-r from-primary-500 to-accent-500 text-white rounded-2xl font-semibold disabled:opacity-50 flex items-center justify-center gap-2"
            >
              Continue
              <ArrowRight size={20} />
            </button>
          </div>
        )}

        {/* Step: Coach Relationship */}
        {step === 'coach-relationship' && (
          <div className="flex-1 flex flex-col">
            <div className="flex-1 flex flex-col justify-center">
              <div className="w-16 h-16 bg-pink-100 dark:bg-pink-900/30 rounded-full flex items-center justify-center mb-6">
                <Heart className="text-pink-600" size={32} />
              </div>
              <h2 className="text-2xl font-bold mb-2">Who am I to you?</h2>
              <p className="text-gray-500 mb-6">This helps me understand how to support you best.</p>
              <div className="space-y-3">
                {COACH_RELATIONSHIPS.map((rel) => (
                  <button
                    key={rel.id}
                    onClick={() => setCoachRelationship(rel.id)}
                    className={`w-full p-4 rounded-xl border-2 text-left transition ${
                      coachRelationship === rel.id
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                        : 'border-gray-200 dark:border-gray-700'
                    }`}
                  >
                    <p className="font-medium">{rel.label}</p>
                    <p className="text-sm text-gray-500">{rel.description}</p>
                  </button>
                ))}
              </div>
            </div>
            <button
              onClick={nextStep}
              disabled={!canProceed()}
              className="w-full py-4 bg-gradient-to-r from-primary-500 to-accent-500 text-white rounded-2xl font-semibold disabled:opacity-50 flex items-center justify-center gap-2 mt-4"
            >
              Continue
              <ArrowRight size={20} />
            </button>
          </div>
        )}

        {/* Step: Coach Tone */}
        {step === 'coach-tone' && (
          <div className="flex-1 flex flex-col">
            <div className="flex-1 flex flex-col justify-center">
              <div className="w-16 h-16 bg-yellow-100 dark:bg-yellow-900/30 rounded-full flex items-center justify-center mb-6">
                <MessageCircle className="text-yellow-600" size={32} />
              </div>
              <h2 className="text-2xl font-bold mb-2">How should I talk to you?</h2>
              <p className="text-gray-500 mb-6">Pick a communication style that resonates with you.</p>
              <div className="space-y-3">
                {COACH_TONES.map((tone) => (
                  <button
                    key={tone.id}
                    onClick={() => setCoachTone(tone.id)}
                    className={`w-full p-4 rounded-xl border-2 text-left transition ${
                      coachTone === tone.id
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                        : 'border-gray-200 dark:border-gray-700'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{tone.emoji}</span>
                      <div>
                        <p className="font-medium">{tone.label}</p>
                        <p className="text-sm text-gray-500">{tone.description}</p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
            <button
              onClick={nextStep}
              disabled={!canProceed()}
              className="w-full py-4 bg-gradient-to-r from-primary-500 to-accent-500 text-white rounded-2xl font-semibold disabled:opacity-50 flex items-center justify-center gap-2 mt-4"
            >
              Continue
              <ArrowRight size={20} />
            </button>
          </div>
        )}

        {/* Step: Notification Level */}
        {step === 'notification' && (
          <div className="flex-1 flex flex-col">
            <div className="flex-1 flex flex-col justify-center">
              <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mb-6">
                <Bell className="text-green-600" size={32} />
              </div>
              <h2 className="text-2xl font-bold mb-2">How much should I check in?</h2>
              <p className="text-gray-500 mb-6">I can send proactive nudges to keep you on track.</p>
              <div className="space-y-3">
                {NOTIFICATION_LEVELS.map((level) => (
                  <button
                    key={level.id}
                    onClick={() => setNotificationLevel(level.id)}
                    className={`w-full p-4 rounded-xl border-2 text-left transition ${
                      notificationLevel === level.id
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                        : 'border-gray-200 dark:border-gray-700'
                    }`}
                  >
                    <p className="font-medium">{level.label}</p>
                    <p className="text-sm text-gray-500">{level.description}</p>
                  </button>
                ))}
              </div>
            </div>
            <button
              onClick={nextStep}
              disabled={!canProceed()}
              className="w-full py-4 bg-gradient-to-r from-primary-500 to-accent-500 text-white rounded-2xl font-semibold disabled:opacity-50 flex items-center justify-center gap-2 mt-4"
            >
              Continue
              <ArrowRight size={20} />
            </button>
          </div>
        )}

        {/* Step: Quiet Hours */}
        {step === 'quiet-hours' && (
          <div className="flex-1 flex flex-col">
            <div className="flex-1 flex flex-col justify-center">
              <div className="w-16 h-16 bg-indigo-100 dark:bg-indigo-900/30 rounded-full flex items-center justify-center mb-6">
                <Clock className="text-indigo-600" size={32} />
              </div>
              <h2 className="text-2xl font-bold mb-2">When should I stay quiet?</h2>
              <p className="text-gray-500 mb-6">Set your quiet hours - I won't send notifications during this time.</p>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">From</label>
                  <input
                    type="time"
                    value={quietHoursStart}
                    onChange={(e) => setQuietHoursStart(e.target.value)}
                    className="w-full px-4 py-3 border-2 border-gray-200 dark:border-gray-700 rounded-xl dark:bg-gray-800"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">To</label>
                  <input
                    type="time"
                    value={quietHoursEnd}
                    onChange={(e) => setQuietHoursEnd(e.target.value)}
                    className="w-full px-4 py-3 border-2 border-gray-200 dark:border-gray-700 rounded-xl dark:bg-gray-800"
                  />
                </div>
              </div>
              <p className="text-sm text-gray-400 mt-4 text-center">
                Default: 10:00 PM - 7:00 AM
              </p>
            </div>
            <button
              onClick={nextStep}
              className="w-full py-4 bg-gradient-to-r from-primary-500 to-accent-500 text-white rounded-2xl font-semibold flex items-center justify-center gap-2"
            >
              Continue
              <ArrowRight size={20} />
            </button>
          </div>
        )}

        {/* Complete */}
        {step === 'complete' && (
          <div className="flex-1 flex flex-col items-center justify-center text-center">
            <div className="w-24 h-24 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mb-6">
              <Check className="text-green-600" size={48} />
            </div>
            <h1 className="text-3xl font-bold mb-4">You're All Set!</h1>
            <p className="text-gray-600 dark:text-gray-300 mb-8">
              Nice to meet you, <strong>{preferredName}</strong>! I'm <strong>{coachName}</strong>, and I'm excited to be your {COACH_RELATIONSHIPS.find(r => r.id === coachRelationship)?.label.toLowerCase() || 'companion'}.
            </p>
            <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-4 mb-8 w-full text-left">
              <p className="text-sm text-gray-500 mb-2">Your preferences:</p>
              <ul className="text-sm space-y-1">
                <li>• Tone: {COACH_TONES.find(t => t.id === coachTone)?.label}</li>
                <li>• Notifications: {NOTIFICATION_LEVELS.find(n => n.id === notificationLevel)?.label}</li>
                <li>• Quiet hours: {quietHoursStart} - {quietHoursEnd}</li>
              </ul>
              <p className="text-xs text-gray-400 mt-2">You can change these anytime in Settings.</p>
            </div>
            <button
              onClick={handleComplete}
              disabled={loading}
              className="w-full py-4 bg-gradient-to-r from-primary-500 to-accent-500 text-white rounded-2xl font-semibold text-lg flex items-center justify-center gap-2"
            >
              {loading ? 'Setting up...' : "Let's Go!"}
              <Sparkles size={20} />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
