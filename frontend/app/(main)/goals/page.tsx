'use client'

import { useState, useEffect } from 'react'
import { Target, Plus, TrendingUp, Mic, Edit2, Trash2, X, MoreVertical, Pause, Play, CheckCircle, Archive, RotateCcw } from 'lucide-react'
import { goalsApi, identityApi } from '@/lib/api-client'
import { VoiceDictateButton } from '@/components/voice/VoiceDictateButton'

interface Goal {
  id: string
  title: string
  description?: string
  why?: string
  progress_percent: number
  status: string
  timeframe: string
  current_streak?: number
  longest_streak?: number
  suggested_key_results?: any[]
}

type ModalType = 'edit' | 'pause' | 'complete' | 'archive' | 'menu' | null

export default function GoalsPage() {
  const [goals, setGoals] = useState<Goal[]>([])
  const [identity, setIdentity] = useState<any>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [newGoal, setNewGoal] = useState('')
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [selectedGoal, setSelectedGoal] = useState<Goal | null>(null)
  const [modalType, setModalType] = useState<ModalType>(null)
  const [editTitle, setEditTitle] = useState('')
  const [editProgress, setEditProgress] = useState(0)
  const [pauseReason, setPauseReason] = useState('')
  const [archiveReason, setArchiveReason] = useState('')
  const [archiveLearning, setArchiveLearning] = useState('')
  const [completeProudOf, setCompleteProudOf] = useState('')
  const [completeLearned, setCompleteLearned] = useState('')
  const [processing, setProcessing] = useState(false)

  const handleVoiceTranscript = (transcript: string) => {
    setNewGoal((prev) => prev ? `${prev} ${transcript}` : transcript)
  }

  const openModal = (goal: Goal, type: ModalType) => {
    setSelectedGoal(goal)
    setModalType(type)
    if (type === 'edit') {
      setEditTitle(goal.title)
      setEditProgress(goal.progress_percent)
    }
  }

  const closeModal = () => {
    setSelectedGoal(null)
    setModalType(null)
    setEditTitle('')
    setEditProgress(0)
    setPauseReason('')
    setArchiveReason('')
    setArchiveLearning('')
    setCompleteProudOf('')
    setCompleteLearned('')
  }

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [goalsRes, identityRes] = await Promise.all([
        goalsApi.list('active'),
        identityApi.get()
      ])
      setGoals(goalsRes.data.data || [])
      setIdentity(identityRes.data.data)
    } catch {
    } finally {
      setLoading(false)
    }
  }

  const createGoal = async () => {
    if (!newGoal.trim() || creating) return
    setCreating(true)
    try {
      const { data } = await goalsApi.create(newGoal)
      if (data.success === false) {
        alert(data.message || 'Failed to create goal')
        return
      }
      if (data.data) {
        setGoals([...goals, data.data])
        setNewGoal('')
        setShowCreate(false)
      }
    } catch (err: any) {
      alert(err?.response?.data?.message || 'Failed to create goal')
    } finally {
      setCreating(false)
    }
  }

  const updateGoal = async () => {
    if (!selectedGoal || processing) return
    setProcessing(true)
    try {
      const { data } = await goalsApi.update(selectedGoal.id, {
        title: editTitle,
        progress_percent: editProgress
      })
      if (data.success !== false && data.data) {
        setGoals(goals.map(g => g.id === selectedGoal.id ? { ...g, ...data.data } : g))
        closeModal()
      }
    } catch (err: any) {
      alert(err?.response?.data?.message || 'Failed to update goal')
    } finally {
      setProcessing(false)
    }
  }

  const pauseGoal = async () => {
    if (!selectedGoal || processing) return
    setProcessing(true)
    try {
      await goalsApi.pause(selectedGoal.id, { reason: pauseReason })
      setGoals(goals.map(g => g.id === selectedGoal.id ? { ...g, status: 'paused' } : g))
      closeModal()
    } catch (err: any) {
      alert(err?.response?.data?.message || 'Failed to pause goal')
    } finally {
      setProcessing(false)
    }
  }

  const resumeGoal = async (goal: Goal) => {
    setProcessing(true)
    try {
      await goalsApi.resume(goal.id, { adjust_timeline: true })
      setGoals(goals.map(g => g.id === goal.id ? { ...g, status: 'active' } : g))
    } catch (err: any) {
      alert(err?.response?.data?.message || 'Failed to resume goal')
    } finally {
      setProcessing(false)
    }
  }

  const completeGoal = async () => {
    if (!selectedGoal || processing) return
    setProcessing(true)
    try {
      const { data } = await goalsApi.complete(selectedGoal.id, {
        proud_of: completeProudOf,
        learned: completeLearned
      })
      if (data.data?.celebration) {
        alert(data.data.celebration)
      }
      setGoals(goals.filter(g => g.id !== selectedGoal.id))
      closeModal()
    } catch (err: any) {
      alert(err?.response?.data?.message || 'Failed to complete goal')
    } finally {
      setProcessing(false)
    }
  }

  const archiveGoal = async () => {
    if (!selectedGoal || !archiveReason || processing) return
    setProcessing(true)
    try {
      await goalsApi.archive(selectedGoal.id, {
        reason: archiveReason,
        learning: archiveLearning
      })
      setGoals(goals.filter(g => g.id !== selectedGoal.id))
      closeModal()
    } catch (err: any) {
      alert(err?.response?.data?.message || 'Failed to archive goal')
    } finally {
      setProcessing(false)
    }
  }

  const deleteGoal = async (goal: Goal) => {
    if (!confirm('Are you sure? This will permanently delete the goal and all its data.')) return
    if (!confirm('This action CANNOT be undone. Type OK to confirm.')) return
    try {
      await goalsApi.deletePermanent(goal.id)
      setGoals(goals.filter(g => g.id !== goal.id))
    } catch (err: any) {
      alert(err?.response?.data?.message || 'Failed to delete goal')
    }
  }

  const getProgressColor = (percent: number) => {
    if (percent >= 70) return 'bg-green-500'
    if (percent >= 40) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'paused': return <span className="px-2 py-0.5 text-xs bg-yellow-100 text-yellow-700 rounded-full">Paused</span>
      case 'completed': return <span className="px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded-full">Completed</span>
      default: return null
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 animate-pulse h-32" />
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 animate-pulse h-24" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Goals</h1>
          <p className="text-gray-500">
            {identity?.ideal_self ? `Goals for ${identity.ideal_self}-You` : 'Your OKRs'}
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center shadow-lg"
        >
          <Plus size={24} />
        </button>
      </header>

      {showCreate && (
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-lg">
          <h3 className="font-semibold mb-3">New Goal</h3>
          <div className="relative">
            <textarea
              value={newGoal}
              onChange={(e) => setNewGoal(e.target.value)}
              placeholder="What do you want to achieve? e.g., 'Launch my first product'"
              className="w-full h-24 p-3 pr-12 bg-gray-50 dark:bg-gray-700 rounded-lg outline-none resize-none"
            />
            <div className="absolute right-2 bottom-2">
              <VoiceDictateButton onTranscript={handleVoiceTranscript} size="sm" />
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-1 flex items-center gap-1">
            <Mic size={12} /> Tap mic to dictate
          </p>
          <div className="flex gap-2 mt-3">
            <button onClick={() => setShowCreate(false)} className="flex-1 py-2 text-gray-500">Cancel</button>
            <button
              onClick={createGoal}
              disabled={!newGoal.trim() || creating}
              className="flex-1 py-2 bg-blue-600 text-white rounded-lg font-medium disabled:opacity-50"
            >
              {creating ? 'Creating...' : 'Create Goal'}
            </button>
          </div>
        </div>
      )}

      {/* Goal Options Menu Modal */}
      {modalType === 'menu' && selectedGoal && (
        <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-50" onClick={closeModal}>
          <div className="bg-white dark:bg-gray-800 rounded-t-2xl w-full max-w-md p-4 pb-8" onClick={e => e.stopPropagation()}>
            <div className="w-12 h-1 bg-gray-300 rounded-full mx-auto mb-4" />
            <h3 className="font-semibold text-lg mb-4">{selectedGoal.title}</h3>
            <div className="space-y-2">
              <button onClick={() => setModalType('edit')} className="w-full flex items-center gap-3 p-3 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg">
                <Edit2 size={20} className="text-blue-600" />
                <div className="text-left"><div className="font-medium">Edit Goal</div><div className="text-sm text-gray-500">Change title, progress</div></div>
              </button>
              {selectedGoal.status === 'active' && (
                <button onClick={() => setModalType('pause')} className="w-full flex items-center gap-3 p-3 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg">
                  <Pause size={20} className="text-yellow-600" />
                  <div className="text-left"><div className="font-medium">Pause Goal</div><div className="text-sm text-gray-500">Take a break, keep progress</div></div>
                </button>
              )}
              {selectedGoal.status === 'paused' && (
                <button onClick={() => { resumeGoal(selectedGoal); closeModal(); }} className="w-full flex items-center gap-3 p-3 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg">
                  <Play size={20} className="text-green-600" />
                  <div className="text-left"><div className="font-medium">Resume Goal</div><div className="text-sm text-gray-500">Continue where you left off</div></div>
                </button>
              )}
              <button onClick={() => setModalType('complete')} className="w-full flex items-center gap-3 p-3 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg">
                <CheckCircle size={20} className="text-green-600" />
                <div className="text-left"><div className="font-medium">Mark Complete</div><div className="text-sm text-gray-500">Celebrate your achievement</div></div>
              </button>
              <div className="border-t dark:border-gray-700 my-2" />
              <button onClick={() => setModalType('archive')} className="w-full flex items-center gap-3 p-3 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg">
                <Archive size={20} className="text-gray-500" />
                <div className="text-left"><div className="font-medium">Archive Goal</div><div className="text-sm text-gray-500">Remove from active, can restore</div></div>
              </button>
              <button onClick={() => { deleteGoal(selectedGoal); closeModal(); }} className="w-full flex items-center gap-3 p-3 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg text-red-600">
                <Trash2 size={20} />
                <div className="text-left"><div className="font-medium">Delete Permanently</div><div className="text-sm opacity-70">Cannot be undone</div></div>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {modalType === 'edit' && selectedGoal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-lg">Edit Goal</h3>
              <button onClick={closeModal} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-500 mb-1">Title</label>
                <input type="text" value={editTitle} onChange={(e) => setEditTitle(e.target.value)} className="w-full p-3 bg-gray-50 dark:bg-gray-700 rounded-lg outline-none" />
              </div>
              <div>
                <label className="block text-sm text-gray-500 mb-1">Progress: {editProgress}%</label>
                <input type="range" min="0" max="100" value={editProgress} onChange={(e) => setEditProgress(Number(e.target.value))} className="w-full" />
              </div>
              <div className="flex gap-2 pt-2">
                <button onClick={closeModal} className="flex-1 py-2 text-gray-500 border border-gray-200 dark:border-gray-600 rounded-lg">Cancel</button>
                <button onClick={updateGoal} disabled={processing} className="flex-1 py-2 bg-blue-600 text-white rounded-lg font-medium disabled:opacity-50">
                  {processing ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Pause Modal */}
      {modalType === 'pause' && selectedGoal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-lg">Pause Goal</h3>
              <button onClick={closeModal} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
            </div>
            <p className="text-gray-500 mb-4">Taking a break? Your {selectedGoal.current_streak || 0}-day streak will be preserved.</p>
            <div className="space-y-2 mb-4">
              {['Health / personal issue', 'Work got crazy', 'Priorities shifted', 'Need to recharge', 'Other'].map(reason => (
                <button key={reason} onClick={() => setPauseReason(reason)} className={`w-full p-3 text-left rounded-lg border ${pauseReason === reason ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-200 dark:border-gray-700'}`}>
                  {reason}
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <button onClick={closeModal} className="flex-1 py-2 text-gray-500 border border-gray-200 dark:border-gray-600 rounded-lg">Cancel</button>
              <button onClick={pauseGoal} disabled={processing} className="flex-1 py-2 bg-yellow-500 text-white rounded-lg font-medium disabled:opacity-50">
                {processing ? 'Pausing...' : 'Pause Goal'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Complete Modal */}
      {modalType === 'complete' && selectedGoal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-lg">Complete Goal</h3>
              <button onClick={closeModal} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
            </div>
            <p className="text-gray-500 mb-4">Congratulations on completing "{selectedGoal.title}"!</p>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-500 mb-1">What are you most proud of?</label>
                <textarea value={completeProudOf} onChange={(e) => setCompleteProudOf(e.target.value)} className="w-full p-3 bg-gray-50 dark:bg-gray-700 rounded-lg outline-none h-20 resize-none" placeholder="The journey, not just the destination..." />
              </div>
              <div>
                <label className="block text-sm text-gray-500 mb-1">What did you learn?</label>
                <textarea value={completeLearned} onChange={(e) => setCompleteLearned(e.target.value)} className="w-full p-3 bg-gray-50 dark:bg-gray-700 rounded-lg outline-none h-20 resize-none" placeholder="Key insights from this experience..." />
              </div>
            </div>
            <div className="flex gap-2 mt-4">
              <button onClick={closeModal} className="flex-1 py-2 text-gray-500 border border-gray-200 dark:border-gray-600 rounded-lg">Cancel</button>
              <button onClick={completeGoal} disabled={processing} className="flex-1 py-2 bg-green-600 text-white rounded-lg font-medium disabled:opacity-50">
                {processing ? 'Completing...' : 'Complete Goal'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Archive Modal */}
      {modalType === 'archive' && selectedGoal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-lg">Archive Goal</h3>
              <button onClick={closeModal} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
            </div>
            <p className="text-gray-500 mb-4">Your data stays safe — you can restore this anytime.</p>
            <div className="space-y-2 mb-4">
              {['Abandoned', 'Not relevant anymore', 'Duplicate of another goal', 'Replaced by different goal', 'Other'].map(reason => (
                <button key={reason} onClick={() => setArchiveReason(reason.toLowerCase().replace(/ /g, '_'))} className={`w-full p-3 text-left rounded-lg border ${archiveReason === reason.toLowerCase().replace(/ /g, '_') ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-200 dark:border-gray-700'}`}>
                  {reason}
                </button>
              ))}
            </div>
            {archiveReason === 'abandoned' && (
              <div className="mb-4">
                <label className="block text-sm text-gray-500 mb-1">What got in the way? (optional)</label>
                <textarea value={archiveLearning} onChange={(e) => setArchiveLearning(e.target.value)} className="w-full p-3 bg-gray-50 dark:bg-gray-700 rounded-lg outline-none h-20 resize-none" placeholder="This will help us set better goals next time..." />
              </div>
            )}
            <div className="flex gap-2">
              <button onClick={closeModal} className="flex-1 py-2 text-gray-500 border border-gray-200 dark:border-gray-600 rounded-lg">Cancel</button>
              <button onClick={archiveGoal} disabled={!archiveReason || processing} className="flex-1 py-2 bg-gray-600 text-white rounded-lg font-medium disabled:opacity-50">
                {processing ? 'Archiving...' : 'Archive Goal'}
              </button>
            </div>
          </div>
        </div>
      )}

      {goals.length > 0 ? (
        <div className="space-y-4">
          {goals.map((goal) => (
            <div key={goal.id} className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <Target className="text-blue-600" size={18} />
                    <h3 className="font-semibold">{goal.title}</h3>
                    {getStatusBadge(goal.status)}
                  </div>
                  {goal.why && <p className="text-sm text-gray-500 mt-1">{goal.why}</p>}
                </div>
                <button onClick={() => openModal(goal, 'menu')} className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
                  <MoreVertical size={18} />
                </button>
              </div>
              <div className="mt-4">
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-gray-500">{goal.timeframe || 'Quarterly'}</span>
                  <span className="font-medium">{goal.progress_percent}%</span>
                </div>
                <div className="bg-gray-100 dark:bg-gray-700 rounded-full h-2">
                  <div className={`${getProgressColor(goal.progress_percent)} rounded-full h-2 transition-all`} style={{ width: `${goal.progress_percent}%` }} />
                </div>
              </div>
              {goal.current_streak && goal.current_streak > 0 && (
                <div className="mt-2 text-sm text-orange-500">
                  🔥 {goal.current_streak} day streak
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 text-center">
          <Target className="mx-auto text-gray-300" size={48} />
          <h3 className="text-lg font-semibold mt-4">No goals yet</h3>
          <p className="text-gray-500 mt-2">
            {identity?.ideal_self ? `What would ${identity.ideal_self}-you have achieved?` : 'Set your first goal to start your journey'}
          </p>
          <button onClick={() => setShowCreate(true)} className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg font-medium">
            Create First Goal
          </button>
        </div>
      )}
    </div>
  )
}
