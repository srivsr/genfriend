'use client'

import { useState, useEffect } from 'react'
import { Bell, Clock, Target, Lightbulb, Check, X, Settings, RefreshCw } from 'lucide-react'
import { notificationsApi, preferencesApi } from '@/lib/api-client'

type NudgeType = 'reminder' | 'insight' | 'motivation' | 'milestone' | 'warning'

interface Nudge {
  id: string
  type: NudgeType
  title: string
  message: string
  action_url?: string
  action_label?: string
  created_at: string
  read: boolean
  goal_id?: string
}

interface NotificationPrefs {
  daily_reminders: boolean
  weekly_summary: boolean
  milestone_alerts: boolean
  insight_notifications: boolean
  quiet_hours_start: string
  quiet_hours_end: string
}

const nudgeIcons: Record<NudgeType, typeof Bell> = {
  reminder: Clock,
  insight: Lightbulb,
  motivation: Bell,
  milestone: Target,
  warning: Bell,
}

const nudgeColors: Record<NudgeType, string> = {
  reminder: 'bg-blue-100 text-blue-600',
  insight: 'bg-purple-100 text-purple-600',
  motivation: 'bg-green-100 text-green-600',
  milestone: 'bg-yellow-100 text-yellow-600',
  warning: 'bg-red-100 text-red-600',
}

export default function NotificationsPage() {
  const [nudges, setNudges] = useState<Nudge[]>([])
  const [loading, setLoading] = useState(true)
  const [showSettings, setShowSettings] = useState(false)
  const [prefs, setPrefs] = useState<NotificationPrefs>({
    daily_reminders: true,
    weekly_summary: true,
    milestone_alerts: true,
    insight_notifications: true,
    quiet_hours_start: '22:00',
    quiet_hours_end: '07:00',
  })
  const [savingPrefs, setSavingPrefs] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [nudgesRes, prefsRes] = await Promise.all([
        notificationsApi.getNudges().catch(() => ({ data: { data: [] } })),
        preferencesApi.get().catch(() => ({ data: { data: {} } })),
      ])

      const nudgesData = nudgesRes.data?.data || nudgesRes.data || []
      setNudges(Array.isArray(nudgesData) ? nudgesData : [])

      const prefsData = prefsRes.data?.data || prefsRes.data || {}
      if (prefsData.notification_settings) {
        setPrefs(prev => ({ ...prev, ...prefsData.notification_settings }))
      }
    } catch (error) {
      console.error('Failed to load notifications:', error)
    } finally {
      setLoading(false)
    }
  }

  const markAsRead = (id: string) => {
    setNudges(prev => prev.map(n => n.id === id ? { ...n, read: true } : n))
  }

  const dismissNudge = (id: string) => {
    setNudges(prev => prev.filter(n => n.id !== id))
  }

  const savePreferences = async () => {
    setSavingPrefs(true)
    try {
      await preferencesApi.update({ notification_settings: prefs })
      setShowSettings(false)
    } catch (error) {
      console.error('Failed to save preferences:', error)
    } finally {
      setSavingPrefs(false)
    }
  }

  const unreadCount = nudges.filter(n => !n.read).length

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)

    if (minutes < 60) return `${minutes}m ago`
    if (hours < 24) return `${hours}h ago`
    return `${days}d ago`
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-6">
        <div className="max-w-2xl mx-auto">
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-200 rounded w-1/3"></div>
            <div className="h-24 bg-gray-200 rounded"></div>
            <div className="h-24 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-6">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Notifications</h1>
            {unreadCount > 0 && (
              <p className="text-sm text-gray-600">{unreadCount} unread</p>
            )}
          </div>
          <div className="flex gap-2">
            <button
              onClick={loadData}
              className="p-2 rounded-lg bg-white border border-gray-200 hover:bg-gray-50 transition-colors"
              title="Refresh"
            >
              <RefreshCw className="w-5 h-5 text-gray-600" />
            </button>
            <button
              onClick={() => setShowSettings(true)}
              className="p-2 rounded-lg bg-white border border-gray-200 hover:bg-gray-50 transition-colors"
              title="Settings"
            >
              <Settings className="w-5 h-5 text-gray-600" />
            </button>
          </div>
        </div>

        {nudges.length === 0 ? (
          <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
            <Bell className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">All caught up!</h3>
            <p className="text-gray-600">
              No new notifications. Keep making progress on your goals!
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {nudges.map((nudge) => {
              const Icon = nudgeIcons[nudge.type] || Bell
              const colorClass = nudgeColors[nudge.type] || 'bg-gray-100 text-gray-600'

              return (
                <div
                  key={nudge.id}
                  className={`bg-white rounded-xl border p-4 transition-all ${
                    nudge.read ? 'border-gray-200 opacity-75' : 'border-blue-200 shadow-sm'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`p-2 rounded-lg ${colorClass}`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <h3 className="font-medium text-gray-900">{nudge.title}</h3>
                          <p className="text-sm text-gray-600 mt-1">{nudge.message}</p>
                        </div>
                        <button
                          onClick={() => dismissNudge(nudge.id)}
                          className="p-1 rounded hover:bg-gray-100 transition-colors"
                        >
                          <X className="w-4 h-4 text-gray-400" />
                        </button>
                      </div>
                      <div className="flex items-center gap-3 mt-3">
                        <span className="text-xs text-gray-500">
                          {formatTime(nudge.created_at)}
                        </span>
                        {nudge.action_url && (
                          <a
                            href={nudge.action_url}
                            className="text-xs text-blue-600 hover:text-blue-700 font-medium"
                          >
                            {nudge.action_label || 'View'}
                          </a>
                        )}
                        {!nudge.read && (
                          <button
                            onClick={() => markAsRead(nudge.id)}
                            className="text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1"
                          >
                            <Check className="w-3 h-3" />
                            Mark read
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {showSettings && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl max-w-md w-full p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold">Notification Settings</h2>
                <button
                  onClick={() => setShowSettings(false)}
                  className="p-1 rounded hover:bg-gray-100"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-4">
                <label className="flex items-center justify-between">
                  <span className="text-gray-700">Daily reminders</span>
                  <input
                    type="checkbox"
                    checked={prefs.daily_reminders}
                    onChange={(e) => setPrefs({ ...prefs, daily_reminders: e.target.checked })}
                    className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </label>

                <label className="flex items-center justify-between">
                  <span className="text-gray-700">Weekly summary</span>
                  <input
                    type="checkbox"
                    checked={prefs.weekly_summary}
                    onChange={(e) => setPrefs({ ...prefs, weekly_summary: e.target.checked })}
                    className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </label>

                <label className="flex items-center justify-between">
                  <span className="text-gray-700">Milestone alerts</span>
                  <input
                    type="checkbox"
                    checked={prefs.milestone_alerts}
                    onChange={(e) => setPrefs({ ...prefs, milestone_alerts: e.target.checked })}
                    className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </label>

                <label className="flex items-center justify-between">
                  <span className="text-gray-700">Insight notifications</span>
                  <input
                    type="checkbox"
                    checked={prefs.insight_notifications}
                    onChange={(e) => setPrefs({ ...prefs, insight_notifications: e.target.checked })}
                    className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </label>

                <div className="border-t pt-4 mt-4">
                  <h3 className="font-medium text-gray-900 mb-3">Quiet Hours</h3>
                  <p className="text-sm text-gray-600 mb-3">
                    No notifications during these hours
                  </p>
                  <div className="flex items-center gap-3">
                    <div>
                      <label className="text-xs text-gray-500 block mb-1">From</label>
                      <input
                        type="time"
                        value={prefs.quiet_hours_start}
                        onChange={(e) => setPrefs({ ...prefs, quiet_hours_start: e.target.value })}
                        className="border rounded-lg px-3 py-2 text-sm"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-gray-500 block mb-1">To</label>
                      <input
                        type="time"
                        value={prefs.quiet_hours_end}
                        onChange={(e) => setPrefs({ ...prefs, quiet_hours_end: e.target.value })}
                        className="border rounded-lg px-3 py-2 text-sm"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setShowSettings(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={savePreferences}
                  disabled={savingPrefs}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {savingPrefs ? 'Saving...' : 'Save'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
