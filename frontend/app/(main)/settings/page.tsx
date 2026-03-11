'use client'

import { useState, useEffect } from 'react'
import { LogOut, User, Bell, Moon, Shield, Trash2, Download, AlertTriangle, ChevronRight, X, Save, Check } from 'lucide-react'
import { useAuth } from '@/stores/auth'
import { usersApi, preferencesApi, identityApi } from '@/lib/api-client'

type ModalType = 'profile' | 'coach' | 'notifications' | 'appearance' | 'privacy' | null

interface Preferences {
  coach_name: string
  coach_tone: string
  coach_relationship: string
  daily_reminders: boolean
  weekly_summary: boolean
  milestone_alerts: boolean
  insight_notifications: boolean
  quiet_hours_start: string
  quiet_hours_end: string
  dark_mode: boolean
  compact_view: boolean
  data_collection: boolean
  share_anonymized_data: boolean
}

export default function SettingsPage() {
  const { logout, user } = useAuth()
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [deleteConfirmation, setDeleteConfirmation] = useState('')
  const [deleting, setDeleting] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [error, setError] = useState('')
  const [activeModal, setActiveModal] = useState<ModalType>(null)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  const [profile, setProfile] = useState({
    name: '',
    email: '',
  })

  const [prefs, setPrefs] = useState<Preferences>({
    coach_name: 'Gen',
    coach_tone: 'supportive',
    coach_relationship: 'mentor',
    daily_reminders: true,
    weekly_summary: true,
    milestone_alerts: true,
    insight_notifications: true,
    quiet_hours_start: '22:00',
    quiet_hours_end: '07:00',
    dark_mode: false,
    compact_view: false,
    data_collection: true,
    share_anonymized_data: false,
  })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [userRes, prefsRes] = await Promise.all([
        usersApi.me().catch(() => ({ data: { data: {} } })),
        preferencesApi.get().catch(() => ({ data: { data: {} } })),
      ])

      const userData = userRes.data?.data || userRes.data || {}
      setProfile({
        name: userData.name || user?.name || '',
        email: userData.email || user?.email || '',
      })

      const prefsData = prefsRes.data?.data || prefsRes.data || {}
      setPrefs(prev => ({
        ...prev,
        ...prefsData,
        ...(prefsData.notification_settings || {}),
        ...(prefsData.appearance_settings || {}),
        ...(prefsData.privacy_settings || {}),
      }))
    } catch (e) {
      console.error('Failed to load settings', e)
    }
  }

  const handleExportData = async () => {
    setExporting(true)
    try {
      const response = await usersApi.exportData()
      const data = response.data.data
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `gen-friend-export-${new Date().toISOString().split('T')[0]}.json`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      console.error('Export failed', e)
    } finally {
      setExporting(false)
    }
  }

  const handleDeleteAccount = async () => {
    if (deleteConfirmation !== 'DELETE') {
      setError('Please type DELETE to confirm')
      return
    }
    setDeleting(true)
    setError('')
    try {
      await usersApi.deleteAccount('DELETE')
      logout()
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to delete account')
      setDeleting(false)
    }
  }

  const savePreferences = async () => {
    setSaving(true)
    try {
      await preferencesApi.update({
        coach_name: prefs.coach_name,
        coach_tone: prefs.coach_tone,
        coach_relationship: prefs.coach_relationship,
        notification_settings: {
          daily_reminders: prefs.daily_reminders,
          weekly_summary: prefs.weekly_summary,
          milestone_alerts: prefs.milestone_alerts,
          insight_notifications: prefs.insight_notifications,
          quiet_hours_start: prefs.quiet_hours_start,
          quiet_hours_end: prefs.quiet_hours_end,
        },
        appearance_settings: {
          dark_mode: prefs.dark_mode,
          compact_view: prefs.compact_view,
        },
        privacy_settings: {
          data_collection: prefs.data_collection,
          share_anonymized_data: prefs.share_anonymized_data,
        },
      })
      setSaved(true)
      setTimeout(() => {
        setSaved(false)
        setActiveModal(null)
      }, 1500)
    } catch (e) {
      console.error('Failed to save preferences', e)
    } finally {
      setSaving(false)
    }
  }

  const menuItems = [
    { id: 'profile' as const, icon: User, label: 'Profile', description: 'Name and account info' },
    { id: 'coach' as const, icon: User, label: 'Coach Settings', description: 'Personalize your AI coach' },
    { id: 'notifications' as const, icon: Bell, label: 'Notifications', description: 'Reminders and alerts' },
    { id: 'appearance' as const, icon: Moon, label: 'Appearance', description: 'Dark mode & display' },
    { id: 'privacy' as const, icon: Shield, label: 'Privacy', description: 'Data & security' },
  ]

  const toneOptions = [
    { value: 'supportive', label: 'Supportive', desc: 'Encouraging and warm' },
    { value: 'direct', label: 'Direct', desc: 'Straightforward and clear' },
    { value: 'challenging', label: 'Challenging', desc: 'Pushes you to grow' },
    { value: 'analytical', label: 'Analytical', desc: 'Data-driven insights' },
  ]

  const relationshipOptions = [
    { value: 'mentor', label: 'Mentor', desc: 'Wise guide with experience' },
    { value: 'coach', label: 'Coach', desc: 'Performance-focused partner' },
    { value: 'friend', label: 'Friend', desc: 'Casual and relatable' },
    { value: 'accountability_partner', label: 'Accountability Partner', desc: 'Keeps you on track' },
  ]

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-gray-500">Manage your preferences</p>
      </header>

      <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 bg-gradient-to-r from-primary-500 to-accent-500 rounded-full flex items-center justify-center text-white text-2xl font-bold">
            {profile.name?.[0]?.toUpperCase() || 'G'}
          </div>
          <div>
            <h2 className="text-lg font-semibold">{profile.name || 'Gen-Friend User'}</h2>
            <p className="text-gray-500 text-sm">{profile.email || 'Member since 2024'}</p>
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-2xl overflow-hidden shadow-sm">
        {menuItems.map((item, i) => (
          <button
            key={item.label}
            onClick={() => setActiveModal(item.id)}
            className={`w-full flex items-center gap-4 p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition ${i > 0 ? 'border-t border-gray-100 dark:border-gray-700' : ''}`}
          >
            <div className="w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center">
              <item.icon className="text-gray-600 dark:text-gray-300" size={20} />
            </div>
            <div className="text-left flex-1">
              <p className="font-medium">{item.label}</p>
              <p className="text-sm text-gray-500">{item.description}</p>
            </div>
            <ChevronRight className="text-gray-400" size={20} />
          </button>
        ))}
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-2xl overflow-hidden shadow-sm">
        <button
          onClick={handleExportData}
          disabled={exporting}
          className="w-full flex items-center gap-4 p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition"
        >
          <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
            <Download className="text-blue-600" size={20} />
          </div>
          <div className="text-left">
            <p className="font-medium">{exporting ? 'Exporting...' : 'Export My Data'}</p>
            <p className="text-sm text-gray-500">Download all your data (GDPR)</p>
          </div>
        </button>
        <button
          onClick={() => setShowDeleteModal(true)}
          className="w-full flex items-center gap-4 p-4 hover:bg-red-50 dark:hover:bg-red-900/20 transition border-t border-gray-100 dark:border-gray-700"
        >
          <div className="w-10 h-10 bg-red-100 dark:bg-red-900/30 rounded-lg flex items-center justify-center">
            <Trash2 className="text-red-600" size={20} />
          </div>
          <div className="text-left">
            <p className="font-medium text-red-600">Delete Account</p>
            <p className="text-sm text-gray-500">Permanently remove your account</p>
          </div>
        </button>
      </div>

      <button
        onClick={logout}
        className="w-full flex items-center justify-center gap-2 p-4 bg-red-50 dark:bg-red-900/20 text-red-600 rounded-xl font-medium hover:bg-red-100 transition"
      >
        <LogOut size={20} />
        Sign Out
      </button>

      {activeModal === 'profile' && (
        <SettingsModal title="Profile" onClose={() => setActiveModal(null)}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input
                type="text"
                value={profile.name}
                onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                value={profile.email}
                disabled
                className="w-full border border-gray-300 rounded-lg px-4 py-2 bg-gray-50 text-gray-500"
              />
              <p className="text-xs text-gray-500 mt-1">Email cannot be changed</p>
            </div>
          </div>
          <SaveButton saving={saving} saved={saved} onClick={savePreferences} />
        </SettingsModal>
      )}

      {activeModal === 'coach' && (
        <SettingsModal title="Coach Settings" onClose={() => setActiveModal(null)}>
          <div className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Coach Name</label>
              <input
                type="text"
                value={prefs.coach_name}
                onChange={(e) => setPrefs({ ...prefs, coach_name: e.target.value })}
                placeholder="e.g., Gen, Alex, Coach"
                className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Communication Tone</label>
              <div className="grid grid-cols-2 gap-2">
                {toneOptions.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setPrefs({ ...prefs, coach_tone: option.value })}
                    className={`p-3 rounded-lg border text-left transition-colors ${
                      prefs.coach_tone === option.value
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <p className="font-medium text-sm">{option.label}</p>
                    <p className="text-xs text-gray-500">{option.desc}</p>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Relationship Style</label>
              <div className="grid grid-cols-2 gap-2">
                {relationshipOptions.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setPrefs({ ...prefs, coach_relationship: option.value })}
                    className={`p-3 rounded-lg border text-left transition-colors ${
                      prefs.coach_relationship === option.value
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <p className="font-medium text-sm">{option.label}</p>
                    <p className="text-xs text-gray-500">{option.desc}</p>
                  </button>
                ))}
              </div>
            </div>
          </div>
          <SaveButton saving={saving} saved={saved} onClick={savePreferences} />
        </SettingsModal>
      )}

      {activeModal === 'notifications' && (
        <SettingsModal title="Notifications" onClose={() => setActiveModal(null)}>
          <div className="space-y-4">
            <Toggle
              label="Daily Reminders"
              description="Get reminded about your daily tasks"
              checked={prefs.daily_reminders}
              onChange={(v) => setPrefs({ ...prefs, daily_reminders: v })}
            />
            <Toggle
              label="Weekly Summary"
              description="Receive weekly progress summaries"
              checked={prefs.weekly_summary}
              onChange={(v) => setPrefs({ ...prefs, weekly_summary: v })}
            />
            <Toggle
              label="Milestone Alerts"
              description="Celebrate when you hit milestones"
              checked={prefs.milestone_alerts}
              onChange={(v) => setPrefs({ ...prefs, milestone_alerts: v })}
            />
            <Toggle
              label="Insight Notifications"
              description="Get AI-powered insights about your progress"
              checked={prefs.insight_notifications}
              onChange={(v) => setPrefs({ ...prefs, insight_notifications: v })}
            />

            <div className="border-t pt-4 mt-4">
              <h3 className="font-medium text-gray-900 mb-3">Quiet Hours</h3>
              <p className="text-sm text-gray-600 mb-3">No notifications during these hours</p>
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
          <SaveButton saving={saving} saved={saved} onClick={savePreferences} />
        </SettingsModal>
      )}

      {activeModal === 'appearance' && (
        <SettingsModal title="Appearance" onClose={() => setActiveModal(null)}>
          <div className="space-y-4">
            <Toggle
              label="Dark Mode"
              description="Switch to dark theme"
              checked={prefs.dark_mode}
              onChange={(v) => setPrefs({ ...prefs, dark_mode: v })}
            />
            <Toggle
              label="Compact View"
              description="Show more content with less spacing"
              checked={prefs.compact_view}
              onChange={(v) => setPrefs({ ...prefs, compact_view: v })}
            />
          </div>
          <SaveButton saving={saving} saved={saved} onClick={savePreferences} />
        </SettingsModal>
      )}

      {activeModal === 'privacy' && (
        <SettingsModal title="Privacy" onClose={() => setActiveModal(null)}>
          <div className="space-y-4">
            <Toggle
              label="Data Collection"
              description="Allow collection of usage data to improve the app"
              checked={prefs.data_collection}
              onChange={(v) => setPrefs({ ...prefs, data_collection: v })}
            />
            <Toggle
              label="Share Anonymized Data"
              description="Help improve AI coaching with anonymized patterns"
              checked={prefs.share_anonymized_data}
              onChange={(v) => setPrefs({ ...prefs, share_anonymized_data: v })}
            />

            <div className="border-t pt-4 mt-4">
              <h3 className="font-medium text-gray-900 mb-2">Your Data Rights</h3>
              <ul className="text-sm text-gray-600 space-y-2">
                <li>You can export all your data at any time</li>
                <li>You can delete your account and all data</li>
                <li>Your data is encrypted at rest and in transit</li>
                <li>We never sell your personal data</li>
              </ul>
            </div>
          </div>
          <SaveButton saving={saving} saved={saved} onClick={savePreferences} />
        </SettingsModal>
      )}

      {showDeleteModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-md p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                <AlertTriangle className="text-red-600" size={24} />
              </div>
              <div>
                <h3 className="text-lg font-bold">Delete Account?</h3>
                <p className="text-gray-500 text-sm">This cannot be undone</p>
              </div>
            </div>
            <div className="space-y-4 mb-6">
              <p className="text-gray-600 dark:text-gray-300">
                This will permanently delete:
              </p>
              <ul className="text-sm text-gray-500 space-y-1 ml-4">
                <li>Your profile and settings</li>
                <li>All goals and progress</li>
                <li>All tasks and streaks</li>
                <li>All journal entries</li>
                <li>All chat conversations</li>
              </ul>
              <div>
                <label className="block text-sm font-medium mb-2">
                  Type <span className="font-bold text-red-600">DELETE</span> to confirm:
                </label>
                <input
                  type="text"
                  value={deleteConfirmation}
                  onChange={(e) => setDeleteConfirmation(e.target.value)}
                  placeholder="DELETE"
                  className="w-full px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 dark:bg-gray-900"
                />
              </div>
              {error && <p className="text-red-500 text-sm">{error}</p>}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setShowDeleteModal(false)
                  setDeleteConfirmation('')
                  setError('')
                }}
                className="flex-1 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteAccount}
                disabled={deleting || deleteConfirmation !== 'DELETE'}
                className="flex-1 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {deleting ? 'Deleting...' : 'Delete Account'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function SettingsModal({ title, children, onClose }: { title: string; children: React.ReactNode; onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button onClick={onClose} className="p-1 rounded hover:bg-gray-100">
            <X size={20} />
          </button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  )
}

function Toggle({ label, description, checked, onChange }: { label: string; description: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="flex items-start gap-3 cursor-pointer">
      <div className="relative mt-0.5">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          className="sr-only"
        />
        <div className={`w-10 h-6 rounded-full transition-colors ${checked ? 'bg-blue-600' : 'bg-gray-200'}`}>
          <div className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform ${checked ? 'translate-x-4' : ''}`} />
        </div>
      </div>
      <div>
        <p className="font-medium text-gray-900">{label}</p>
        <p className="text-sm text-gray-500">{description}</p>
      </div>
    </label>
  )
}

function SaveButton({ saving, saved, onClick }: { saving: boolean; saved: boolean; onClick: () => void }) {
  return (
    <div className="mt-6 pt-4 border-t">
      <button
        onClick={onClick}
        disabled={saving}
        className={`w-full py-3 rounded-lg font-medium flex items-center justify-center gap-2 transition-colors ${
          saved ? 'bg-green-600 text-white' : 'bg-blue-600 text-white hover:bg-blue-700'
        } disabled:opacity-50`}
      >
        {saved ? (
          <>
            <Check size={20} />
            Saved!
          </>
        ) : saving ? (
          'Saving...'
        ) : (
          <>
            <Save size={20} />
            Save Changes
          </>
        )}
      </button>
    </div>
  )
}
