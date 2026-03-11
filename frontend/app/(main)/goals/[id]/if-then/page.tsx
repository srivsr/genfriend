'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, Plus, Star, Edit2, Trash2, BarChart3, Zap, CheckCircle, XCircle, TrendingUp } from 'lucide-react'
import { goalsApi, ifThenApi } from '@/lib/api-client'

interface IfThenPlan {
  id: string
  goal_id: string
  when_trigger: string
  then_action: string
  obstacle_type: string | null
  is_primary: boolean
  is_active: boolean
  times_triggered: number
  times_used: number
  times_effective: number
  effectiveness_rate: number
  created_at: string | null
}

interface Goal {
  id: string
  title: string
  woop_primary_obstacle: string | null
}

export default function IfThenPlansPage() {
  const params = useParams()
  const router = useRouter()
  const goalId = params.id as string

  const [goal, setGoal] = useState<Goal | null>(null)
  const [plans, setPlans] = useState<IfThenPlan[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState<IfThenPlan | null>(null)
  const [showStatsModal, setShowStatsModal] = useState<IfThenPlan | null>(null)
  const [showLogModal, setShowLogModal] = useState<IfThenPlan | null>(null)

  // Form state
  const [whenTrigger, setWhenTrigger] = useState('')
  const [thenAction, setThenAction] = useState('')
  const [isPrimary, setIsPrimary] = useState(false)

  useEffect(() => {
    loadData()
  }, [goalId])

  const loadData = async () => {
    setLoading(true)
    try {
      const [goalRes, plansRes] = await Promise.all([
        goalsApi.get(goalId),
        ifThenApi.getPlans(goalId)
      ])
      setGoal(goalRes.data.data)
      setPlans(plansRes.data.data || [])
    } catch (e) {
      console.error('Failed to load data', e)
    } finally {
      setLoading(false)
    }
  }

  const handleAddPlan = async () => {
    if (!whenTrigger || !thenAction) return
    try {
      await ifThenApi.createPlan(goalId, {
        when_trigger: whenTrigger,
        then_action: thenAction,
        obstacle_type: goal?.woop_primary_obstacle || undefined,
        is_primary: isPrimary
      })
      setShowAddModal(false)
      setWhenTrigger('')
      setThenAction('')
      setIsPrimary(false)
      loadData()
    } catch (e) {
      console.error('Failed to create plan', e)
    }
  }

  const handleUpdatePlan = async () => {
    if (!showEditModal) return
    try {
      await ifThenApi.updatePlan(showEditModal.id, {
        when_trigger: whenTrigger,
        then_action: thenAction
      })
      setShowEditModal(null)
      loadData()
    } catch (e) {
      console.error('Failed to update plan', e)
    }
  }

  const handleDeletePlan = async (planId: string) => {
    if (!confirm('Delete this If-Then plan?')) return
    try {
      await ifThenApi.deletePlan(planId)
      loadData()
    } catch (e) {
      console.error('Failed to delete plan', e)
    }
  }

  const handleSetPrimary = async (plan: IfThenPlan) => {
    try {
      // Create a new plan with is_primary true (API will unset others)
      await ifThenApi.createPlan(goalId, {
        when_trigger: plan.when_trigger,
        then_action: plan.then_action,
        obstacle_type: plan.obstacle_type || undefined,
        is_primary: true
      })
      await ifThenApi.deletePlan(plan.id)
      loadData()
    } catch (e) {
      console.error('Failed to set primary', e)
    }
  }

  const handleLogUse = async (plan: IfThenPlan, wasUsed: boolean, wasEffective: boolean) => {
    try {
      await ifThenApi.logUse(plan.id, {
        was_triggered: true,
        was_used: wasUsed,
        was_effective: wasEffective
      })
      setShowLogModal(null)
      loadData()
    } catch (e) {
      console.error('Failed to log use', e)
    }
  }

  const openEditModal = (plan: IfThenPlan) => {
    setWhenTrigger(plan.when_trigger)
    setThenAction(plan.then_action)
    setShowEditModal(plan)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  const primaryPlan = plans.find(p => p.is_primary)
  const otherPlans = plans.filter(p => !p.is_primary)

  return (
    <div className="space-y-6 pb-24">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button onClick={() => router.back()} className="p-2 -ml-2 text-gray-500">
          <ArrowLeft size={24} />
        </button>
        <div>
          <h1 className="text-xl font-bold">If-Then Plans</h1>
          <p className="text-sm text-gray-500">{goal?.title}</p>
        </div>
      </div>

      {/* Info Card */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-xl p-4">
        <div className="flex items-start gap-3">
          <Zap className="text-blue-600 mt-1" size={20} />
          <div>
            <p className="font-medium text-blue-900 dark:text-blue-100">Implementation Intentions</p>
            <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
              If-Then plans increase goal success by 2-3x. When your obstacle shows up, your brain automatically knows what to do.
            </p>
          </div>
        </div>
      </div>

      {/* Primary Plan */}
      {primaryPlan && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Star className="text-yellow-500" size={16} fill="currentColor" />
            <span className="text-sm font-medium">Primary Plan</span>
          </div>
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border-2 border-yellow-200 dark:border-yellow-800 rounded-xl p-4">
            <p className="text-sm text-gray-500 mb-1">WHEN</p>
            <p className="font-medium mb-3">{primaryPlan.when_trigger}</p>
            <p className="text-sm text-gray-500 mb-1">THEN</p>
            <p className="font-medium mb-4">{primaryPlan.then_action}</p>

            <div className="flex items-center justify-between pt-3 border-t border-yellow-200 dark:border-yellow-800">
              <div className="flex items-center gap-4 text-sm">
                <span className="text-gray-500">
                  Triggered: <strong>{primaryPlan.times_triggered}</strong>
                </span>
                <span className="text-gray-500">
                  Effective: <strong>{primaryPlan.effectiveness_rate.toFixed(0)}%</strong>
                </span>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setShowLogModal(primaryPlan)}
                  className="p-2 bg-green-100 text-green-600 rounded-lg hover:bg-green-200"
                  title="Log use"
                >
                  <CheckCircle size={16} />
                </button>
                <button
                  onClick={() => openEditModal(primaryPlan)}
                  className="p-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200"
                  title="Edit"
                >
                  <Edit2 size={16} />
                </button>
                <button
                  onClick={() => setShowStatsModal(primaryPlan)}
                  className="p-2 bg-blue-100 text-blue-600 rounded-lg hover:bg-blue-200"
                  title="Stats"
                >
                  <BarChart3 size={16} />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Other Plans */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-600">Alternative Plans ({otherPlans.length})</span>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-1 text-sm text-primary-600 font-medium"
          >
            <Plus size={16} />
            Add Plan
          </button>
        </div>

        {otherPlans.length === 0 && !primaryPlan && (
          <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-6 text-center">
            <Zap className="mx-auto text-gray-400 mb-2" size={32} />
            <p className="text-gray-500">No If-Then plans yet</p>
            <button
              onClick={() => setShowAddModal(true)}
              className="mt-3 px-4 py-2 bg-primary-500 text-white rounded-lg text-sm"
            >
              Create Your First Plan
            </button>
          </div>
        )}

        {otherPlans.map((plan) => (
          <div key={plan.id} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4">
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <p className="text-xs text-gray-500 mb-1">WHEN</p>
                <p className="text-sm font-medium mb-2">{plan.when_trigger}</p>
                <p className="text-xs text-gray-500 mb-1">THEN</p>
                <p className="text-sm font-medium">{plan.then_action}</p>
              </div>
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-gray-100 dark:border-gray-700">
              <div className="flex items-center gap-3 text-xs text-gray-500">
                <span>Triggered: {plan.times_triggered}</span>
                <span>Effective: {plan.effectiveness_rate.toFixed(0)}%</span>
              </div>
              <div className="flex gap-1">
                <button
                  onClick={() => handleSetPrimary(plan)}
                  className="p-1.5 text-gray-400 hover:text-yellow-500"
                  title="Set as primary"
                >
                  <Star size={14} />
                </button>
                <button
                  onClick={() => setShowLogModal(plan)}
                  className="p-1.5 text-gray-400 hover:text-green-500"
                  title="Log use"
                >
                  <CheckCircle size={14} />
                </button>
                <button
                  onClick={() => openEditModal(plan)}
                  className="p-1.5 text-gray-400 hover:text-blue-500"
                  title="Edit"
                >
                  <Edit2 size={14} />
                </button>
                <button
                  onClick={() => handleDeletePlan(plan.id)}
                  className="p-1.5 text-gray-400 hover:text-red-500"
                  title="Delete"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Add Plan Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-md p-6">
            <h3 className="text-lg font-bold mb-4">Add If-Then Plan</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">When (trigger):</label>
                <textarea
                  value={whenTrigger}
                  onChange={(e) => setWhenTrigger(e.target.value)}
                  placeholder="When I feel like procrastinating..."
                  className="w-full h-20 px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg resize-none dark:bg-gray-900"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Then (action):</label>
                <textarea
                  value={thenAction}
                  onChange={(e) => setThenAction(e.target.value)}
                  placeholder="I will just do 2 minutes to get started"
                  className="w-full h-20 px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg resize-none dark:bg-gray-900"
                />
              </div>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={isPrimary}
                  onChange={(e) => setIsPrimary(e.target.checked)}
                  className="rounded"
                />
                <span className="text-sm">Set as primary plan</span>
              </label>
            </div>
            <div className="flex gap-2 mt-6">
              <button
                onClick={() => {
                  setShowAddModal(false)
                  setWhenTrigger('')
                  setThenAction('')
                  setIsPrimary(false)
                }}
                className="flex-1 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleAddPlan}
                disabled={!whenTrigger || !thenAction}
                className="flex-1 py-2 bg-primary-500 text-white rounded-lg disabled:opacity-50"
              >
                Add Plan
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Plan Modal */}
      {showEditModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-md p-6">
            <h3 className="text-lg font-bold mb-4">Edit If-Then Plan</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">When (trigger):</label>
                <textarea
                  value={whenTrigger}
                  onChange={(e) => setWhenTrigger(e.target.value)}
                  className="w-full h-20 px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg resize-none dark:bg-gray-900"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Then (action):</label>
                <textarea
                  value={thenAction}
                  onChange={(e) => setThenAction(e.target.value)}
                  className="w-full h-20 px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg resize-none dark:bg-gray-900"
                />
              </div>
            </div>
            <div className="flex gap-2 mt-6">
              <button
                onClick={() => setShowEditModal(null)}
                className="flex-1 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleUpdatePlan}
                className="flex-1 py-2 bg-primary-500 text-white rounded-lg"
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Log Use Modal */}
      {showLogModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-md p-6">
            <h3 className="text-lg font-bold mb-2">Log If-Then Use</h3>
            <p className="text-sm text-gray-500 mb-4">Did your obstacle show up? How did your plan work?</p>

            <div className="space-y-3">
              <button
                onClick={() => handleLogUse(showLogModal, true, true)}
                className="w-full p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl text-left hover:bg-green-100"
              >
                <div className="flex items-center gap-3">
                  <CheckCircle className="text-green-600" size={24} />
                  <div>
                    <p className="font-medium text-green-900 dark:text-green-100">Used & Effective</p>
                    <p className="text-sm text-green-600">I used my plan and it helped!</p>
                  </div>
                </div>
              </button>

              <button
                onClick={() => handleLogUse(showLogModal, true, false)}
                className="w-full p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl text-left hover:bg-yellow-100"
              >
                <div className="flex items-center gap-3">
                  <TrendingUp className="text-yellow-600" size={24} />
                  <div>
                    <p className="font-medium text-yellow-900 dark:text-yellow-100">Used but Struggled</p>
                    <p className="text-sm text-yellow-600">I used it but still had trouble</p>
                  </div>
                </div>
              </button>

              <button
                onClick={() => handleLogUse(showLogModal, false, false)}
                className="w-full p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-left hover:bg-red-100"
              >
                <div className="flex items-center gap-3">
                  <XCircle className="text-red-600" size={24} />
                  <div>
                    <p className="font-medium text-red-900 dark:text-red-100">Didn't Use</p>
                    <p className="text-sm text-red-600">I forgot or didn't use my plan</p>
                  </div>
                </div>
              </button>
            </div>

            <button
              onClick={() => setShowLogModal(null)}
              className="w-full mt-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Stats Modal */}
      {showStatsModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-md p-6">
            <h3 className="text-lg font-bold mb-4">Plan Effectiveness</h3>

            <div className="grid grid-cols-3 gap-3 mb-4">
              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3 text-center">
                <p className="text-2xl font-bold">{showStatsModal.times_triggered}</p>
                <p className="text-xs text-gray-500">Triggered</p>
              </div>
              <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-green-600">{showStatsModal.times_used}</p>
                <p className="text-xs text-gray-500">Used</p>
              </div>
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-blue-600">{showStatsModal.times_effective}</p>
                <p className="text-xs text-gray-500">Effective</p>
              </div>
            </div>

            <div className="bg-gradient-to-r from-primary-50 to-accent-50 dark:from-primary-900/20 dark:to-accent-900/20 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Effectiveness Rate</span>
                <span className="text-2xl font-bold text-primary-600">{showStatsModal.effectiveness_rate.toFixed(0)}%</span>
              </div>
              <div className="mt-2 h-2 bg-white dark:bg-gray-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-primary-500 to-accent-500"
                  style={{ width: `${showStatsModal.effectiveness_rate}%` }}
                />
              </div>
            </div>

            <button
              onClick={() => setShowStatsModal(null)}
              className="w-full mt-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
