'use client'

import { useState, useEffect } from 'react'
import { Users, Trash2, RefreshCw, Search, ChevronDown, AlertTriangle, BarChart3, Target, CheckSquare } from 'lucide-react'
import { adminApi } from '@/lib/api-client'

interface User {
  id: string
  email: string
  name: string | null
  preferred_name: string | null
  timezone: string
  onboarding_completed: boolean
  is_active: boolean
  created_at: string | null
  goals_count: number
}

interface UserDetails {
  user: User & { coach_name: string; coach_tone: string; onboarding_step: string | null }
  stats: { goals_count: number; tasks_count: number; conversations_count: number }
  goals: Array<{ id: string; title: string; status: string; progress_percent: number; current_streak: number; created_at: string | null }>
}

interface Stats {
  users: { total: number; active: number }
  goals: { total: number; active: number }
  tasks: { total: number }
}

export default function AdminPage() {
  const [adminKey, setAdminKey] = useState('')
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [users, setUsers] = useState<User[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(false)
  const [selectedUser, setSelectedUser] = useState<UserDetails | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null)
  const [showResetModal, setShowResetModal] = useState<string | null>(null)
  const [error, setError] = useState('')

  const authenticate = async () => {
    if (!adminKey) {
      setError('Please enter admin key')
      return
    }
    setLoading(true)
    setError('')
    try {
      const res = await adminApi.stats(adminKey)
      setStats(res.data.data)
      setIsAuthenticated(true)
      loadUsers()
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Invalid admin key')
    } finally {
      setLoading(false)
    }
  }

  const loadUsers = async () => {
    setLoading(true)
    try {
      const res = await adminApi.listUsers({ search: search || undefined }, adminKey)
      setUsers(res.data.data.users)
    } catch (e) {
      console.error('Failed to load users', e)
    } finally {
      setLoading(false)
    }
  }

  const loadUserDetails = async (userId: string) => {
    setLoading(true)
    try {
      const res = await adminApi.getUser(userId, adminKey)
      setSelectedUser(res.data.data)
    } catch (e) {
      console.error('Failed to load user details', e)
    } finally {
      setLoading(false)
    }
  }

  const deleteUser = async (userId: string) => {
    setLoading(true)
    try {
      await adminApi.deleteUser(userId, adminKey)
      setShowDeleteConfirm(null)
      setSelectedUser(null)
      loadUsers()
    } catch (e) {
      console.error('Failed to delete user', e)
    } finally {
      setLoading(false)
    }
  }

  const resetUser = async (userId: string, resetType: string) => {
    setLoading(true)
    try {
      await adminApi.resetUser(userId, resetType, adminKey)
      setShowResetModal(null)
      loadUserDetails(userId)
    } catch (e) {
      console.error('Failed to reset user', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isAuthenticated && search !== undefined) {
      const timer = setTimeout(() => loadUsers(), 300)
      return () => clearTimeout(timer)
    }
  }, [search, isAuthenticated])

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-md">
          <div className="text-center mb-6">
            <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Users className="text-primary-600" size={32} />
            </div>
            <h1 className="text-2xl font-bold">Gen-Friend Admin</h1>
            <p className="text-gray-500 mt-2">Enter admin key to continue</p>
          </div>
          <div className="space-y-4">
            <input
              type="password"
              value={adminKey}
              onChange={(e) => setAdminKey(e.target.value)}
              placeholder="Admin Secret Key"
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500"
              onKeyDown={(e) => e.key === 'Enter' && authenticate()}
            />
            {error && <p className="text-red-500 text-sm">{error}</p>}
            <button
              onClick={authenticate}
              disabled={loading}
              className="w-full bg-primary-600 text-white py-3 rounded-xl font-medium hover:bg-primary-700 transition disabled:opacity-50"
            >
              {loading ? 'Authenticating...' : 'Access Admin Panel'}
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow-sm">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold flex items-center gap-2">
            <Users className="text-primary-600" size={24} />
            Gen-Friend Admin
          </h1>
          <button
            onClick={() => setIsAuthenticated(false)}
            className="text-gray-500 hover:text-gray-700"
          >
            Logout
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-6 space-y-6">
        {stats && (
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white rounded-xl p-4 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Users className="text-blue-600" size={20} />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats.users.total}</p>
                  <p className="text-gray-500 text-sm">Users ({stats.users.active} active)</p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl p-4 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                  <Target className="text-green-600" size={20} />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats.goals.total}</p>
                  <p className="text-gray-500 text-sm">Goals ({stats.goals.active} active)</p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl p-4 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                  <CheckSquare className="text-purple-600" size={20} />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats.tasks.total}</p>
                  <p className="text-gray-500 text-sm">Tasks</p>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="bg-white rounded-xl shadow-sm">
          <div className="p-4 border-b border-gray-100 flex items-center gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by email or name..."
                className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <button
              onClick={loadUsers}
              className="p-2 text-gray-500 hover:text-gray-700"
            >
              <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
            </button>
          </div>

          <div className="divide-y divide-gray-100">
            {users.map((user) => (
              <div
                key={user.id}
                className="p-4 hover:bg-gray-50 cursor-pointer flex items-center justify-between"
                onClick={() => loadUserDetails(user.id)}
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gradient-to-r from-primary-500 to-accent-500 rounded-full flex items-center justify-center text-white font-bold">
                    {(user.preferred_name || user.name || user.email)[0].toUpperCase()}
                  </div>
                  <div>
                    <p className="font-medium">{user.preferred_name || user.name || 'No name'}</p>
                    <p className="text-sm text-gray-500">{user.email}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-sm text-gray-500">{user.goals_count} goals</span>
                  <span className={`px-2 py-1 rounded-full text-xs ${user.onboarding_completed ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                    {user.onboarding_completed ? 'Active' : 'Onboarding'}
                  </span>
                  <ChevronDown size={16} className="text-gray-400" />
                </div>
              </div>
            ))}
            {users.length === 0 && !loading && (
              <div className="p-8 text-center text-gray-500">
                No users found
              </div>
            )}
          </div>
        </div>
      </main>

      {selectedUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[80vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-100 flex items-center justify-between">
              <h2 className="text-xl font-bold">User Details</h2>
              <button onClick={() => setSelectedUser(null)} className="text-gray-400 hover:text-gray-600">✕</button>
            </div>

            <div className="p-6 space-y-6">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 bg-gradient-to-r from-primary-500 to-accent-500 rounded-full flex items-center justify-center text-white text-2xl font-bold">
                  {(selectedUser.user.preferred_name || selectedUser.user.name || selectedUser.user.email)[0].toUpperCase()}
                </div>
                <div>
                  <h3 className="text-lg font-semibold">{selectedUser.user.preferred_name || selectedUser.user.name || 'No name'}</h3>
                  <p className="text-gray-500">{selectedUser.user.email}</p>
                  <p className="text-sm text-gray-400">ID: {selectedUser.user.id}</p>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-2xl font-bold">{selectedUser.stats.goals_count}</p>
                  <p className="text-sm text-gray-500">Goals</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-2xl font-bold">{selectedUser.stats.tasks_count}</p>
                  <p className="text-sm text-gray-500">Tasks</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-2xl font-bold">{selectedUser.stats.conversations_count}</p>
                  <p className="text-sm text-gray-500">Conversations</p>
                </div>
              </div>

              <div className="space-y-2">
                <h4 className="font-medium">Settings</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="bg-gray-50 rounded-lg p-2">
                    <span className="text-gray-500">Coach Name:</span> {selectedUser.user.coach_name || 'Gen'}
                  </div>
                  <div className="bg-gray-50 rounded-lg p-2">
                    <span className="text-gray-500">Coach Tone:</span> {selectedUser.user.coach_tone || 'warm'}
                  </div>
                  <div className="bg-gray-50 rounded-lg p-2">
                    <span className="text-gray-500">Timezone:</span> {selectedUser.user.timezone}
                  </div>
                  <div className="bg-gray-50 rounded-lg p-2">
                    <span className="text-gray-500">Onboarding:</span> {selectedUser.user.onboarding_completed ? 'Complete' : selectedUser.user.onboarding_step || 'Not started'}
                  </div>
                </div>
              </div>

              {selectedUser.goals.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-medium">Goals</h4>
                  <div className="space-y-2">
                    {selectedUser.goals.map((goal) => (
                      <div key={goal.id} className="bg-gray-50 rounded-lg p-3 flex items-center justify-between">
                        <div>
                          <p className="font-medium">{goal.title}</p>
                          <p className="text-sm text-gray-500">Streak: {goal.current_streak} days</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm">{goal.progress_percent}%</span>
                          <span className={`px-2 py-1 rounded-full text-xs ${goal.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                            {goal.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex gap-2 pt-4 border-t border-gray-100">
                <button
                  onClick={() => setShowResetModal(selectedUser.user.id)}
                  className="flex-1 flex items-center justify-center gap-2 py-2 bg-yellow-50 text-yellow-700 rounded-lg hover:bg-yellow-100 transition"
                >
                  <RefreshCw size={16} />
                  Reset Data
                </button>
                <button
                  onClick={() => setShowDeleteConfirm(selectedUser.user.id)}
                  className="flex-1 flex items-center justify-center gap-2 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition"
                >
                  <Trash2 size={16} />
                  Delete User
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                <AlertTriangle className="text-red-600" size={24} />
              </div>
              <div>
                <h3 className="text-lg font-bold">Delete User?</h3>
                <p className="text-gray-500 text-sm">This action cannot be undone</p>
              </div>
            </div>
            <p className="text-gray-600 mb-6">
              All user data including goals, tasks, conversations, and journal entries will be permanently deleted.
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setShowDeleteConfirm(null)}
                className="flex-1 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition"
              >
                Cancel
              </button>
              <button
                onClick={() => deleteUser(showDeleteConfirm)}
                disabled={loading}
                className="flex-1 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition disabled:opacity-50"
              >
                {loading ? 'Deleting...' : 'Delete User'}
              </button>
            </div>
          </div>
        </div>
      )}

      {showResetModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
            <h3 className="text-lg font-bold mb-4">Reset User Data</h3>
            <p className="text-gray-600 mb-4">Choose what to reset for this user:</p>
            <div className="space-y-2 mb-6">
              <button
                onClick={() => resetUser(showResetModal, 'onboarding')}
                className="w-full text-left p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition"
              >
                <p className="font-medium">Reset Onboarding</p>
                <p className="text-sm text-gray-500">User will go through onboarding again</p>
              </button>
              <button
                onClick={() => resetUser(showResetModal, 'goals')}
                className="w-full text-left p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition"
              >
                <p className="font-medium">Reset Goals & Tasks</p>
                <p className="text-sm text-gray-500">Delete all goals, tasks, and if-then plans</p>
              </button>
              <button
                onClick={() => resetUser(showResetModal, 'streaks')}
                className="w-full text-left p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition"
              >
                <p className="font-medium">Reset Streaks</p>
                <p className="text-sm text-gray-500">Set all streak counters to 0</p>
              </button>
              <button
                onClick={() => resetUser(showResetModal, 'all')}
                className="w-full text-left p-3 bg-red-50 rounded-lg hover:bg-red-100 transition border border-red-200"
              >
                <p className="font-medium text-red-700">Reset Everything</p>
                <p className="text-sm text-red-500">Clear all data except account credentials</p>
              </button>
            </div>
            <button
              onClick={() => setShowResetModal(null)}
              className="w-full py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
