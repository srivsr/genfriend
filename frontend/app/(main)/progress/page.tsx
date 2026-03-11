'use client'

import { useState, useEffect } from 'react'
import { TrendingUp, AlertTriangle, Lightbulb, Trophy, Target } from 'lucide-react'
import { progressApi } from '@/lib/api-client'

interface Pattern {
  pattern_type: string
  description: string
  confidence: number
  suggested_action: string
}

export default function ProgressPage() {
  const [overview, setOverview] = useState<any>(null)
  const [patterns, setPatterns] = useState<Pattern[]>([])
  const [loading, setLoading] = useState(true)
  const [detecting, setDetecting] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [overviewRes, patternsRes] = await Promise.all([
        progressApi.overview(),
        progressApi.patterns()
      ])
      setOverview(overviewRes.data.data)
      setPatterns(patternsRes.data.data || [])
    } catch {
    } finally {
      setLoading(false)
    }
  }

  const detectPatterns = async () => {
    setDetecting(true)
    try {
      const { data } = await progressApi.detectPatterns()
      setPatterns(data.data || [])
    } catch {
    } finally {
      setDetecting(false)
    }
  }

  const getPatternIcon = (type: string) => {
    switch (type) {
      case 'recurring_failure': return <AlertTriangle className="text-red-500" size={20} />
      case 'avoidance': return <AlertTriangle className="text-yellow-500" size={20} />
      case 'success_pattern': return <TrendingUp className="text-green-500" size={20} />
      default: return <Lightbulb className="text-blue-500" size={20} />
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 animate-pulse h-40" />
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 animate-pulse h-32" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold">Your Progress</h1>
        <p className="text-gray-500">How far you&apos;ve come</p>
      </header>

      {overview && (
        <div className="bg-gradient-to-br from-green-600 to-teal-600 rounded-2xl p-6 text-white">
          <h2 className="text-lg font-semibold mb-4">Overview</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="flex items-center gap-2">
                <Target size={20} />
                <span className="text-2xl font-bold">{overview.total_goals}</span>
              </div>
              <p className="text-sm opacity-80">Active Goals</p>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <TrendingUp size={20} />
                <span className="text-2xl font-bold">{overview.goals_on_track}</span>
              </div>
              <p className="text-sm opacity-80">On Track</p>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <Trophy size={20} />
                <span className="text-2xl font-bold">{overview.wins_this_week}</span>
              </div>
              <p className="text-sm opacity-80">Wins This Week</p>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <AlertTriangle size={20} />
                <span className="text-2xl font-bold">{overview.goals_at_risk}</span>
              </div>
              <p className="text-sm opacity-80">Need Attention</p>
            </div>
          </div>
        </div>
      )}

      <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold">Patterns & Insights</h2>
          <button
            onClick={detectPatterns}
            disabled={detecting}
            className="text-sm text-blue-600 font-medium"
          >
            {detecting ? 'Analyzing...' : 'Analyze Now'}
          </button>
        </div>

        {patterns.length > 0 ? (
          <div className="space-y-4">
            {patterns.map((pattern, i) => (
              <div key={i} className="border-l-4 border-blue-500 pl-4 py-2">
                <div className="flex items-start gap-2">
                  {getPatternIcon(pattern.pattern_type)}
                  <div>
                    <p className="font-medium">{pattern.description}</p>
                    <p className="text-sm text-gray-500 mt-1">{pattern.suggested_action}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                        {Math.round(pattern.confidence * 100)}% confidence
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <Lightbulb className="mx-auto text-gray-300" size={40} />
            <p className="text-gray-500 mt-3">
              Keep using Gen-Friend to discover patterns in your behavior
            </p>
          </div>
        )}
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm">
        <h2 className="font-semibold mb-4">Growth Journey</h2>
        <div className="text-center py-8">
          <TrendingUp className="mx-auto text-gray-300" size={40} />
          <p className="text-gray-500 mt-3">
            Your growth timeline will appear here as you make progress
          </p>
        </div>
      </div>
    </div>
  )
}
