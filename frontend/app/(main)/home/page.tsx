'use client'

import { useState, useEffect } from 'react'
import { Sun, Target, Plus, Trophy, MessageCircle } from 'lucide-react'
import Link from 'next/link'
import { goalsApi, progressApi, tasksApi } from '@/lib/api-client'

export default function HomePage() {
  const [overview, setOverview] = useState<any>(null)
  const [topGoal, setTopGoal] = useState<any>(null)
  const [todayFocus, setTodayFocus] = useState<string>('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [overviewRes, goalsRes] = await Promise.all([
        progressApi.overview(),
        goalsApi.list('active')
      ])
      setOverview(overviewRes.data.data)
      if (goalsRes.data.data?.length > 0) {
        setTopGoal(goalsRes.data.data[0])
      }
    } catch {
    } finally {
      setLoading(false)
    }
  }

  const greeting = () => {
    const hour = new Date().getHours()
    if (hour < 12) return 'Good morning'
    if (hour < 17) return 'Good afternoon'
    return 'Good evening'
  }

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{greeting()}</h1>
          <p className="text-gray-500">Let&apos;s make progress today</p>
        </div>
        <Sun className="text-yellow-500" size={32} />
      </header>

      {loading ? (
        <div className="space-y-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 animate-pulse h-32" />
          <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 animate-pulse h-24" />
        </div>
      ) : (
        <>
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-2xl p-6 text-white">
            <div className="flex items-center gap-2 mb-2">
              <Target size={20} />
              <span className="font-medium">Your focus today</span>
            </div>
            {topGoal ? (
              <>
                <p className="text-lg font-semibold">{topGoal.title}</p>
                <div className="mt-3 bg-white/20 rounded-full h-2">
                  <div
                    className="bg-white rounded-full h-2 transition-all"
                    style={{ width: `${topGoal.progress_percent || 0}%` }}
                  />
                </div>
                <p className="text-sm mt-2 opacity-80">{topGoal.progress_percent || 0}% complete</p>
              </>
            ) : (
              <Link href="/identity" className="block mt-2">
                <p className="text-lg">Define who you want to become</p>
                <p className="text-sm opacity-80 mt-1">Start your journey &rarr;</p>
              </Link>
            )}
          </div>

          {overview && (
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
                <div className="flex items-center gap-2 text-green-600 mb-1">
                  <Target size={18} />
                  <span className="text-sm font-medium">On Track</span>
                </div>
                <p className="text-2xl font-bold">{overview.goals_on_track || 0}</p>
                <p className="text-xs text-gray-500">goals</p>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
                <div className="flex items-center gap-2 text-yellow-600 mb-1">
                  <Trophy size={18} />
                  <span className="text-sm font-medium">Wins</span>
                </div>
                <p className="text-2xl font-bold">{overview.wins_this_week || 0}</p>
                <p className="text-xs text-gray-500">this week</p>
              </div>
            </div>
          )}

          <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
            <h3 className="font-medium mb-3">Quick capture</h3>
            <div className="flex gap-2">
              <Link href="/journal?type=win" className="flex-1 flex items-center justify-center gap-2 py-3 bg-green-50 text-green-700 rounded-lg font-medium">
                <Trophy size={18} />
                Log Win
              </Link>
              <Link href="/today" className="flex-1 flex items-center justify-center gap-2 py-3 bg-blue-50 text-blue-700 rounded-lg font-medium">
                <Plus size={18} />
                Add Task
              </Link>
            </div>
          </div>

          <Link href="/chat" className="block bg-gray-900 dark:bg-gray-700 rounded-xl p-4 text-white">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
                <MessageCircle size={20} />
              </div>
              <div>
                <p className="font-medium">Talk to Future-You</p>
                <p className="text-sm opacity-70">Get advice from who you&apos;re becoming</p>
              </div>
            </div>
          </Link>
        </>
      )}
    </div>
  )
}
