'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, ArrowRight, Sparkles, Target, Eye, Mountain, Zap, Check, RotateCcw, X } from 'lucide-react'
import { goalsApi, identityApi } from '@/lib/api-client'

type WoopStep = 'future-you' | 'wish' | 'outcome' | 'obstacle' | 'plan' | 'review'

const OBSTACLES = [
  { id: 'procrastination', label: 'Procrastination', description: "I'll do it later... then never do" },
  { id: 'perfectionism', label: 'Perfectionism', description: "If I can't do it perfectly, why start?" },
  { id: 'fear_of_failure', label: 'Fear of Failure', description: "What if I try and fail?" },
  { id: 'lack_of_energy', label: 'Lack of Energy', description: "I'm too tired to work on this" },
  { id: 'distractions', label: 'Distractions', description: "Phone, social media, notifications..." },
  { id: 'self_doubt', label: 'Self-Doubt', description: "Maybe I'm not capable of this" },
  { id: 'overwhelm', label: 'Overwhelm', description: "There's too much to do, where do I start?" },
  { id: 'other', label: 'Something Else', description: "I'll describe my obstacle" },
]

const IF_THEN_TEMPLATES: Record<string, string[]> = {
  procrastination: [
    "When I feel like putting it off, I will just do 2 minutes to get started",
    "When I think 'later', I will immediately open my task and begin",
    "When I want to delay, I will remind myself why this matters to Future Me"
  ],
  perfectionism: [
    "When I feel it's not good enough, I will ship it at 80% and iterate",
    "When I want to keep tweaking, I will set a timer and stop when it rings",
    "When I think it must be perfect, I will remember done is better than perfect"
  ],
  fear_of_failure: [
    "When I feel afraid to try, I will ask 'What's the worst that could happen?'",
    "When I want to avoid risk, I will take the smallest possible step forward",
    "When fear shows up, I will thank it for trying to protect me, then act anyway"
  ],
  lack_of_energy: [
    "When I'm tired, I will do the 2-minute minimum viable version",
    "When energy is low, I will start with my easiest task first",
    "When I feel drained, I will do just one small action to maintain momentum"
  ],
  distractions: [
    "When I reach for my phone, I will put it in another room first",
    "When notifications tempt me, I will turn on Do Not Disturb for 25 minutes",
    "When I want to check social media, I will complete one task first"
  ],
  self_doubt: [
    "When I doubt myself, I will remember a time I succeeded at something hard",
    "When imposter syndrome hits, I will focus on the next tiny step only",
    "When I think I can't, I will say 'I'm learning and growing'"
  ],
  overwhelm: [
    "When I feel overwhelmed, I will write down just 3 things to focus on",
    "When everything feels too much, I will pick the smallest task and start",
    "When paralyzed by options, I will just do the next obvious thing"
  ],
}

const TIMEFRAMES = [
  { id: '1_month', label: '1 Month', description: 'Quick win, build momentum' },
  { id: '3_months', label: '3 Months', description: 'Quarterly goal, meaningful progress' },
  { id: '6_months', label: '6 Months', description: 'Half-year transformation' },
  { id: '1_year', label: '1 Year', description: 'Major life change' },
]

export default function WoopWizardPage() {
  const router = useRouter()
  const [step, setStep] = useState<WoopStep>('future-you')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Form data
  const [futureYou, setFutureYou] = useState('')
  const [wish, setWish] = useState('')
  const [outcome, setOutcome] = useState('')
  const [obstacle, setObstacle] = useState('')
  const [customObstacle, setCustomObstacle] = useState('')
  const [ifThenPlan, setIfThenPlan] = useState('')
  const [timeframe, setTimeframe] = useState('3_months')
  const [goalType, setGoalType] = useState<'performance' | 'learning'>('performance')

  const steps: WoopStep[] = ['future-you', 'wish', 'outcome', 'obstacle', 'plan', 'review']
  const currentStepIndex = steps.indexOf(step)
  const progress = ((currentStepIndex + 1) / steps.length) * 100

  const canProceed = () => {
    switch (step) {
      case 'future-you': return futureYou.length >= 20
      case 'wish': return wish.length >= 10
      case 'outcome': return outcome.length >= 20
      case 'obstacle': return obstacle !== '' && (obstacle !== 'other' || customObstacle.length >= 10)
      case 'plan': return ifThenPlan.length >= 10
      case 'review': return true
      default: return false
    }
  }

  const nextStep = () => {
    const idx = steps.indexOf(step)
    if (idx < steps.length - 1) {
      setStep(steps[idx + 1])
    }
  }

  const prevStep = () => {
    const idx = steps.indexOf(step)
    if (idx > 0) {
      setStep(steps[idx - 1])
    }
  }

  const handleSubmit = async () => {
    setLoading(true)
    setError('')
    try {
      // First, create/update the identity with the Future You vision
      const identityInput = `I want to become: ${futureYou}. My goal is ${wish}. This matters because ${outcome}.`
      await identityApi.create(identityInput)

      // Now create the goal
      const goalInput = `
Goal: ${wish}

Future Vision (2 years): ${futureYou}

Success looks like: ${outcome}

Main obstacle: ${obstacle === 'other' ? customObstacle : obstacle}

If-Then Plan: ${ifThenPlan}

Timeframe: ${timeframe}
Goal Type: ${goalType}
      `.trim()

      await goalsApi.create(goalInput)
      router.push('/goals')
    } catch (e: any) {
      setError(e.response?.data?.message || 'Failed to create goal')
    } finally {
      setLoading(false)
    }
  }

  const handleStartOver = () => {
    if (confirm('Start over? All entered data will be cleared.')) {
      setFutureYou('')
      setWish('')
      setOutcome('')
      setObstacle('')
      setCustomObstacle('')
      setIfThenPlan('')
      setStep('future-you')
    }
  }

  return (
    <div className="min-h-screen pb-24">
      {/* Header */}
      <div className="sticky top-0 bg-white dark:bg-gray-900 z-10 px-4 py-3 border-b border-gray-100 dark:border-gray-800">
        <div className="flex items-center justify-between mb-3">
          <button onClick={() => router.back()} className="p-2 -ml-2 text-gray-500">
            <X size={24} />
          </button>
          <h1 className="font-semibold">Create Goal (WOOP)</h1>
          <button onClick={handleStartOver} className="p-2 -mr-2 text-gray-500">
            <RotateCcw size={20} />
          </button>
        </div>
        {/* Progress bar */}
        <div className="h-1 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-primary-500 to-accent-500 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="flex justify-between mt-2 text-xs text-gray-400">
          <span>Step {currentStepIndex + 1} of {steps.length}</span>
          <span>{Math.round(progress)}%</span>
        </div>
      </div>

      {/* Content */}
      <div className="px-4 py-6">
        {/* Step: Future You */}
        {step === 'future-you' && (
          <div className="space-y-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 dark:bg-purple-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <Sparkles className="text-purple-600" size={32} />
              </div>
              <h2 className="text-2xl font-bold mb-2">Future You</h2>
              <p className="text-gray-500">Close your eyes. Imagine yourself 2 years from now, having achieved everything you want. What does that person look like?</p>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Describe Future You in detail:</label>
              <textarea
                value={futureYou}
                onChange={(e) => setFutureYou(e.target.value)}
                placeholder="In 2 years, I am someone who... I wake up feeling... My days look like... People see me as..."
                className="w-full h-40 px-4 py-3 border border-gray-200 dark:border-gray-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 resize-none"
              />
              <p className="text-xs text-gray-400 mt-1">{futureYou.length}/20 characters minimum</p>
            </div>
            <div className="bg-purple-50 dark:bg-purple-900/20 rounded-xl p-4">
              <p className="text-sm text-purple-700 dark:text-purple-300">
                <strong>Why this matters:</strong> Research shows that connecting with your "Future Self" makes you 3x more likely to take action today. Make it vivid!
              </p>
            </div>
          </div>
        )}

        {/* Step: Wish */}
        {step === 'wish' && (
          <div className="space-y-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-yellow-100 dark:bg-yellow-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <Target className="text-yellow-600" size={32} />
              </div>
              <h2 className="text-2xl font-bold mb-2">Your Wish</h2>
              <p className="text-gray-500">What's the ONE goal that would bring you closest to that Future You?</p>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">My goal is to:</label>
              <textarea
                value={wish}
                onChange={(e) => setWish(e.target.value)}
                placeholder="e.g., Learn Spanish to conversational level, Run a 5K in under 30 minutes, Launch my side business..."
                className="w-full h-24 px-4 py-3 border border-gray-200 dark:border-gray-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 resize-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Timeframe:</label>
              <div className="grid grid-cols-2 gap-2">
                {TIMEFRAMES.map((tf) => (
                  <button
                    key={tf.id}
                    onClick={() => setTimeframe(tf.id)}
                    className={`p-3 rounded-xl border-2 text-left transition ${
                      timeframe === tf.id
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                        : 'border-gray-200 dark:border-gray-700'
                    }`}
                  >
                    <p className="font-medium">{tf.label}</p>
                    <p className="text-xs text-gray-500">{tf.description}</p>
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Goal Type:</label>
              <div className="flex gap-2">
                <button
                  onClick={() => setGoalType('performance')}
                  className={`flex-1 p-3 rounded-xl border-2 transition ${
                    goalType === 'performance'
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                      : 'border-gray-200 dark:border-gray-700'
                  }`}
                >
                  <p className="font-medium">Performance</p>
                  <p className="text-xs text-gray-500">Achieve a specific outcome</p>
                </button>
                <button
                  onClick={() => setGoalType('learning')}
                  className={`flex-1 p-3 rounded-xl border-2 transition ${
                    goalType === 'learning'
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                      : 'border-gray-200 dark:border-gray-700'
                  }`}
                >
                  <p className="font-medium">Learning</p>
                  <p className="text-xs text-gray-500">Master a new skill</p>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step: Outcome */}
        {step === 'outcome' && (
          <div className="space-y-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <Eye className="text-green-600" size={32} />
              </div>
              <h2 className="text-2xl font-bold mb-2">Outcome Visualization</h2>
              <p className="text-gray-500">Imagine you've achieved this goal. What does success look, feel, and sound like?</p>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">When I achieve this goal...</label>
              <textarea
                value={outcome}
                onChange={(e) => setOutcome(e.target.value)}
                placeholder="I will feel... I will see... Others will notice... My life will be different because..."
                className="w-full h-40 px-4 py-3 border border-gray-200 dark:border-gray-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 resize-none"
              />
              <p className="text-xs text-gray-400 mt-1">{outcome.length}/20 characters minimum</p>
            </div>
            <div className="bg-green-50 dark:bg-green-900/20 rounded-xl p-4">
              <p className="text-sm text-green-700 dark:text-green-300">
                <strong>Tip:</strong> Use all your senses. The more vivid and emotional, the stronger your motivation. This is the "O" in WOOP - Outcome.
              </p>
            </div>
          </div>
        )}

        {/* Step: Obstacle */}
        {step === 'obstacle' && (
          <div className="space-y-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <Mountain className="text-red-600" size={32} />
              </div>
              <h2 className="text-2xl font-bold mb-2">Your Main Obstacle</h2>
              <p className="text-gray-500">What INNER obstacle is most likely to get in your way? (Not external circumstances)</p>
            </div>
            <div className="space-y-2">
              {OBSTACLES.map((obs) => (
                <button
                  key={obs.id}
                  onClick={() => setObstacle(obs.id)}
                  className={`w-full p-4 rounded-xl border-2 text-left transition ${
                    obstacle === obs.id
                      ? 'border-red-500 bg-red-50 dark:bg-red-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                  }`}
                >
                  <p className="font-medium">{obs.label}</p>
                  <p className="text-sm text-gray-500">{obs.description}</p>
                </button>
              ))}
            </div>
            {obstacle === 'other' && (
              <div>
                <label className="block text-sm font-medium mb-2">Describe your obstacle:</label>
                <textarea
                  value={customObstacle}
                  onChange={(e) => setCustomObstacle(e.target.value)}
                  placeholder="The inner obstacle that gets in my way is..."
                  className="w-full h-24 px-4 py-3 border border-gray-200 dark:border-gray-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 resize-none"
                />
              </div>
            )}
          </div>
        )}

        {/* Step: Plan (If-Then) */}
        {step === 'plan' && (
          <div className="space-y-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <Zap className="text-blue-600" size={32} />
              </div>
              <h2 className="text-2xl font-bold mb-2">Your If-Then Plan</h2>
              <p className="text-gray-500">When your obstacle shows up, what will you do? Create your implementation intention.</p>
            </div>

            {obstacle && obstacle !== 'other' && IF_THEN_TEMPLATES[obstacle] && (
              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-600">Suggested plans for "{OBSTACLES.find(o => o.id === obstacle)?.label}":</p>
                {IF_THEN_TEMPLATES[obstacle].map((template, i) => (
                  <button
                    key={i}
                    onClick={() => setIfThenPlan(template)}
                    className={`w-full p-3 rounded-xl border-2 text-left text-sm transition ${
                      ifThenPlan === template
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                    }`}
                  >
                    {template}
                  </button>
                ))}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium mb-2">Your If-Then Plan:</label>
              <textarea
                value={ifThenPlan}
                onChange={(e) => setIfThenPlan(e.target.value)}
                placeholder="When [obstacle happens], I will [specific action]..."
                className="w-full h-24 px-4 py-3 border border-gray-200 dark:border-gray-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 resize-none"
              />
            </div>

            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4">
              <p className="text-sm text-blue-700 dark:text-blue-300">
                <strong>Research says:</strong> Implementation intentions (If-Then plans) increase goal success by 2-3x. Be specific about the trigger and the action!
              </p>
            </div>
          </div>
        )}

        {/* Step: Review */}
        {step === 'review' && (
          <div className="space-y-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-r from-primary-500 to-accent-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <Check className="text-white" size={32} />
              </div>
              <h2 className="text-2xl font-bold mb-2">Review Your Goal</h2>
              <p className="text-gray-500">Here's your complete WOOP goal. Ready to commit?</p>
            </div>

            <div className="space-y-4">
              <div className="bg-purple-50 dark:bg-purple-900/20 rounded-xl p-4">
                <p className="text-xs font-medium text-purple-600 dark:text-purple-400 mb-1">FUTURE YOU</p>
                <p className="text-sm">{futureYou}</p>
              </div>

              <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-xl p-4">
                <p className="text-xs font-medium text-yellow-600 dark:text-yellow-400 mb-1">WISH (GOAL)</p>
                <p className="text-sm font-medium">{wish}</p>
                <p className="text-xs text-gray-500 mt-1">{TIMEFRAMES.find(t => t.id === timeframe)?.label} • {goalType === 'performance' ? 'Performance' : 'Learning'} goal</p>
              </div>

              <div className="bg-green-50 dark:bg-green-900/20 rounded-xl p-4">
                <p className="text-xs font-medium text-green-600 dark:text-green-400 mb-1">OUTCOME</p>
                <p className="text-sm">{outcome}</p>
              </div>

              <div className="bg-red-50 dark:bg-red-900/20 rounded-xl p-4">
                <p className="text-xs font-medium text-red-600 dark:text-red-400 mb-1">OBSTACLE</p>
                <p className="text-sm">{obstacle === 'other' ? customObstacle : OBSTACLES.find(o => o.id === obstacle)?.label}</p>
              </div>

              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4">
                <p className="text-xs font-medium text-blue-600 dark:text-blue-400 mb-1">IF-THEN PLAN</p>
                <p className="text-sm">{ifThenPlan}</p>
              </div>
            </div>

            {error && (
              <div className="bg-red-50 dark:bg-red-900/20 text-red-600 rounded-xl p-4 text-sm">
                {error}
              </div>
            )}

            <div className="bg-gradient-to-r from-primary-50 to-accent-50 dark:from-primary-900/20 dark:to-accent-900/20 rounded-xl p-4">
              <p className="text-sm text-gray-700 dark:text-gray-300">
                <strong>You're starting at 20% progress!</strong> Setting a clear goal with WOOP is the first step. You've already done the hard work of planning.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-900 border-t border-gray-100 dark:border-gray-800 p-4">
        <div className="flex gap-3 max-w-lg mx-auto">
          {currentStepIndex > 0 && (
            <button
              onClick={prevStep}
              className="flex items-center justify-center gap-2 px-6 py-3 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-xl font-medium"
            >
              <ArrowLeft size={20} />
              Back
            </button>
          )}
          {step !== 'review' ? (
            <button
              onClick={nextStep}
              disabled={!canProceed()}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-primary-500 to-accent-500 text-white rounded-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Continue
              <ArrowRight size={20} />
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-primary-500 to-accent-500 text-white rounded-xl font-medium disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create Goal'}
              <Check size={20} />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
