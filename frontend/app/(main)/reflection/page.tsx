'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  Calendar, Trophy, TrendingUp, Target, Lightbulb,
  ChevronRight, Star, ArrowRight, Check, Sparkles,
  PenLine, Clock, Flame
} from 'lucide-react'
import { planningApi, goalsApi, journalApi, progressApi } from '@/lib/api-client'

interface WeeklyReview {
  week_start: string
  week_end: string
  goals_summary: {
    total: number
    completed: number
    in_progress: number
    at_risk: number
  }
  tasks_completed: number
  wins: Array<{ id: string; content: string; created_at: string }>
  patterns: Array<{ type: string; description: string; suggestion?: string }>
  streak_days: number
  total_time_invested: number
  top_achievements: string[]
  areas_for_improvement: string[]
  ai_insights: string
}

interface ReflectionEntry {
  wins: string
  challenges: string
  learned: string
  next_week_focus: string
  energy_level: number
  satisfaction_level: number
}

export default function WeeklyReflectionPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [review, setReview] = useState<WeeklyReview | null>(null)
  const [showReflectionForm, setShowReflectionForm] = useState(false)
  const [reflection, setReflection] = useState<ReflectionEntry>({
    wins: '',
    challenges: '',
    learned: '',
    next_week_focus: '',
    energy_level: 3,
    satisfaction_level: 3,
  })
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  useEffect(() => {
    loadWeeklyReview()
  }, [])

  const loadWeeklyReview = async () => {
    setLoading(true)
    try {
      const res = await planningApi.weeklyReview()
      setReview(res.data?.data || res.data)
    } catch (error) {
      console.error('Failed to load weekly review:', error)
      setReview({
        week_start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        week_end: new Date().toISOString().split('T')[0],
        goals_summary: { total: 0, completed: 0, in_progress: 0, at_risk: 0 },
        tasks_completed: 0,
        wins: [],
        patterns: [],
        streak_days: 0,
        total_time_invested: 0,
        top_achievements: [],
        areas_for_improvement: [],
        ai_insights: '',
      })
    } finally {
      setLoading(false)
    }
  }

  const submitReflection = async () => {
    setSubmitting(true)
    try {
      const content = `
## Weekly Reflection

### What went well this week
${reflection.wins}

### Challenges faced
${reflection.challenges}

### What I learned
${reflection.learned}

### Focus for next week
${reflection.next_week_focus}

### Energy Level: ${reflection.energy_level}/5
### Satisfaction Level: ${reflection.satisfaction_level}/5
      `.trim()

      await journalApi.create({
        entry_type: 'weekly_reflection',
        content,
        mood: reflection.satisfaction_level >= 4 ? 'positive' : reflection.satisfaction_level >= 3 ? 'neutral' : 'challenging',
      })

      setSubmitted(true)
      setTimeout(() => {
        setShowReflectionForm(false)
        setSubmitted(false)
      }, 2000)
    } catch (error) {
      console.error('Failed to submit reflection:', error)
    } finally {
      setSubmitting(false)
    }
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    })
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-purple-50 p-6">
        <div className="max-w-3xl mx-auto">
          <div className="animate-pulse space-y-6">
            <div className="h-8 bg-gray-200 rounded w-1/2"></div>
            <div className="h-32 bg-gray-200 rounded"></div>
            <div className="grid grid-cols-3 gap-4">
              <div className="h-24 bg-gray-200 rounded"></div>
              <div className="h-24 bg-gray-200 rounded"></div>
              <div className="h-24 bg-gray-200 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-purple-50 p-6">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Weekly Reflection</h1>
            {review && (
              <p className="text-gray-600">
                {formatDate(review.week_start)} - {formatDate(review.week_end)}
              </p>
            )}
          </div>
          <button
            onClick={() => setShowReflectionForm(true)}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            <PenLine className="w-4 h-4" />
            Write Reflection
          </button>
        </div>

        {review && (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex items-center gap-2 text-blue-600 mb-2">
                  <Target className="w-5 h-5" />
                  <span className="text-sm font-medium">Goals</span>
                </div>
                <div className="text-2xl font-bold text-gray-900">
                  {review.goals_summary.completed}/{review.goals_summary.total}
                </div>
                <p className="text-xs text-gray-500">completed</p>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex items-center gap-2 text-green-600 mb-2">
                  <Check className="w-5 h-5" />
                  <span className="text-sm font-medium">Tasks</span>
                </div>
                <div className="text-2xl font-bold text-gray-900">
                  {review.tasks_completed}
                </div>
                <p className="text-xs text-gray-500">completed</p>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex items-center gap-2 text-orange-600 mb-2">
                  <Flame className="w-5 h-5" />
                  <span className="text-sm font-medium">Streak</span>
                </div>
                <div className="text-2xl font-bold text-gray-900">
                  {review.streak_days}
                </div>
                <p className="text-xs text-gray-500">days</p>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex items-center gap-2 text-purple-600 mb-2">
                  <Clock className="w-5 h-5" />
                  <span className="text-sm font-medium">Time</span>
                </div>
                <div className="text-2xl font-bold text-gray-900">
                  {Math.round(review.total_time_invested / 60) || 0}h
                </div>
                <p className="text-xs text-gray-500">invested</p>
              </div>
            </div>

            {review.wins.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
                <div className="flex items-center gap-2 mb-4">
                  <Trophy className="w-5 h-5 text-yellow-500" />
                  <h2 className="text-lg font-semibold text-gray-900">This Week's Wins</h2>
                </div>
                <div className="space-y-3">
                  {review.wins.map((win) => (
                    <div
                      key={win.id}
                      className="flex items-start gap-3 p-3 bg-yellow-50 rounded-lg"
                    >
                      <Star className="w-4 h-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                      <p className="text-gray-700">{win.content}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {review.top_achievements.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
                <div className="flex items-center gap-2 mb-4">
                  <TrendingUp className="w-5 h-5 text-green-500" />
                  <h2 className="text-lg font-semibold text-gray-900">Top Achievements</h2>
                </div>
                <ul className="space-y-2">
                  {review.top_achievements.map((achievement, idx) => (
                    <li key={idx} className="flex items-center gap-2 text-gray-700">
                      <Check className="w-4 h-4 text-green-500" />
                      {achievement}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {review.patterns.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
                <div className="flex items-center gap-2 mb-4">
                  <Lightbulb className="w-5 h-5 text-purple-500" />
                  <h2 className="text-lg font-semibold text-gray-900">Patterns Detected</h2>
                </div>
                <div className="space-y-3">
                  {review.patterns.map((pattern, idx) => (
                    <div key={idx} className="p-4 bg-purple-50 rounded-lg">
                      <p className="font-medium text-gray-900">{pattern.description}</p>
                      {pattern.suggestion && (
                        <p className="text-sm text-purple-700 mt-1">
                          💡 {pattern.suggestion}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {review.areas_for_improvement.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
                <div className="flex items-center gap-2 mb-4">
                  <Target className="w-5 h-5 text-blue-500" />
                  <h2 className="text-lg font-semibold text-gray-900">Areas for Growth</h2>
                </div>
                <ul className="space-y-2">
                  {review.areas_for_improvement.map((area, idx) => (
                    <li key={idx} className="flex items-center gap-2 text-gray-700">
                      <ArrowRight className="w-4 h-4 text-blue-500" />
                      {area}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {review.ai_insights && (
              <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-xl p-6 text-white">
                <div className="flex items-center gap-2 mb-3">
                  <Sparkles className="w-5 h-5" />
                  <h2 className="text-lg font-semibold">AI Insights</h2>
                </div>
                <p className="text-white/90 leading-relaxed">{review.ai_insights}</p>
              </div>
            )}
          </>
        )}

        {showReflectionForm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
            <div className="bg-white rounded-2xl max-w-2xl w-full p-6 my-8">
              {submitted ? (
                <div className="text-center py-12">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Check className="w-8 h-8 text-green-600" />
                  </div>
                  <h2 className="text-xl font-semibold text-gray-900 mb-2">
                    Reflection Saved!
                  </h2>
                  <p className="text-gray-600">
                    Great job taking time to reflect on your week.
                  </p>
                </div>
              ) : (
                <>
                  <h2 className="text-xl font-semibold text-gray-900 mb-6">
                    Weekly Reflection
                  </h2>

                  <div className="space-y-5">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        🎉 What went well this week?
                      </label>
                      <textarea
                        value={reflection.wins}
                        onChange={(e) => setReflection({ ...reflection, wins: e.target.value })}
                        placeholder="List your wins, big or small..."
                        className="w-full border border-gray-300 rounded-lg px-4 py-3 text-sm resize-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        rows={3}
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        🚧 What challenges did you face?
                      </label>
                      <textarea
                        value={reflection.challenges}
                        onChange={(e) => setReflection({ ...reflection, challenges: e.target.value })}
                        placeholder="What obstacles came up?"
                        className="w-full border border-gray-300 rounded-lg px-4 py-3 text-sm resize-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        rows={3}
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        💡 What did you learn?
                      </label>
                      <textarea
                        value={reflection.learned}
                        onChange={(e) => setReflection({ ...reflection, learned: e.target.value })}
                        placeholder="Any insights or lessons?"
                        className="w-full border border-gray-300 rounded-lg px-4 py-3 text-sm resize-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        rows={3}
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        🎯 What will you focus on next week?
                      </label>
                      <textarea
                        value={reflection.next_week_focus}
                        onChange={(e) => setReflection({ ...reflection, next_week_focus: e.target.value })}
                        placeholder="Your top priorities..."
                        className="w-full border border-gray-300 rounded-lg px-4 py-3 text-sm resize-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        rows={3}
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          ⚡ Energy Level
                        </label>
                        <div className="flex gap-2">
                          {[1, 2, 3, 4, 5].map((level) => (
                            <button
                              key={level}
                              onClick={() => setReflection({ ...reflection, energy_level: level })}
                              className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                                reflection.energy_level === level
                                  ? 'bg-purple-600 text-white'
                                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                              }`}
                            >
                              {level}
                            </button>
                          ))}
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          😊 Satisfaction Level
                        </label>
                        <div className="flex gap-2">
                          {[1, 2, 3, 4, 5].map((level) => (
                            <button
                              key={level}
                              onClick={() => setReflection({ ...reflection, satisfaction_level: level })}
                              className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                                reflection.satisfaction_level === level
                                  ? 'bg-purple-600 text-white'
                                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                              }`}
                            >
                              {level}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-3 mt-6">
                    <button
                      onClick={() => setShowReflectionForm(false)}
                      className="flex-1 px-4 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={submitReflection}
                      disabled={submitting || !reflection.wins.trim()}
                      className="flex-1 px-4 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                    >
                      {submitting ? 'Saving...' : 'Save Reflection'}
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
