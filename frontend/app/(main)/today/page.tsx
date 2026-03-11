'use client'

import { useState, useEffect } from 'react'
import { Sun, CheckCircle2, Circle, Sparkles, Plus, Mic } from 'lucide-react'
import { planningApi, tasksApi } from '@/lib/api-client'
import { VoiceDictateButton } from '@/components/voice/VoiceDictateButton'

interface Task {
  id: string
  title: string
  priority: string
  time_block: string
  status: string
}

export default function TodayPage() {
  const [plan, setPlan] = useState<{ summary: string; tasks: Task[] } | null>(null)
  const [loading, setLoading] = useState(true)
  const [showAddTask, setShowAddTask] = useState(false)
  const [newTask, setNewTask] = useState('')
  const [addingTask, setAddingTask] = useState(false)

  const handleVoiceTranscript = (transcript: string) => {
    setNewTask((prev) => prev ? `${prev} ${transcript}` : transcript)
  }

  const addTask = async () => {
    if (!newTask.trim() || addingTask) return
    setAddingTask(true)
    try {
      const today = new Date().toISOString().split('T')[0]
      await tasksApi.create({ title: newTask, scheduled_date: today })
      setNewTask('')
      setShowAddTask(false)
      loadPlan() // Refresh the list
    } catch {
    } finally {
      setAddingTask(false)
    }
  }

  useEffect(() => {
    loadPlan()
  }, [])

  const loadPlan = async () => {
    try {
      const today = new Date().toISOString().split('T')[0]
      const [planRes, tasksRes] = await Promise.all([
        planningApi.getToday().catch(() => ({ data: { data: { summary: "Let's make today count!", tasks: [] } } })),
        tasksApi.list({ scheduled_date: today }).catch(() => ({ data: { data: [] } }))
      ])

      const planData = planRes.data.data || { summary: "Let's make today count!", tasks: [] }
      const userTasks = tasksRes.data.data || []

      // Merge AI-generated plan tasks with user-created tasks
      const allTasks = [
        ...userTasks.map((t: any) => ({
          id: t.id,
          title: t.title,
          priority: t.priority || 'medium',
          time_block: t.time_block || 'anytime',
          status: t.status || 'pending'
        })),
        ...(planData.tasks || [])
      ]

      setPlan({ summary: planData.summary, tasks: allTasks })
    } catch {
      setPlan({ summary: "Let's make today count!", tasks: [] })
    } finally {
      setLoading(false)
    }
  }

  const generatePlan = async () => {
    setLoading(true)
    try {
      const { data } = await planningApi.generateToday()
      setPlan(data.data)
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
          <p className="text-gray-500">{new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}</p>
        </div>
        <Sun className="text-yellow-500" size={32} />
      </header>

      {loading ? (
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      ) : (
        <>
          <div className="bg-gradient-to-r from-primary-500 to-accent-500 rounded-2xl p-6 text-white">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles size={20} />
              <span className="font-medium">Today&apos;s Focus</span>
            </div>
            <p className="text-lg">{plan?.summary || "Let's plan your day!"}</p>
            <button onClick={generatePlan} className="mt-4 bg-white/20 hover:bg-white/30 px-4 py-2 rounded-lg text-sm font-medium transition">
              Generate New Plan
            </button>
          </div>

          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Today&apos;s Tasks</h2>
              <button
                onClick={() => setShowAddTask(!showAddTask)}
                className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center shadow"
              >
                <Plus size={18} />
              </button>
            </div>

            {showAddTask && (
              <div className="bg-white dark:bg-gray-800 rounded-xl p-4 mb-4 shadow-sm">
                <div className="relative">
                  <input
                    type="text"
                    value={newTask}
                    onChange={(e) => setNewTask(e.target.value)}
                    placeholder="Quick task..."
                    className="w-full p-3 pr-12 bg-gray-50 dark:bg-gray-700 rounded-lg outline-none"
                    onKeyPress={(e) => e.key === 'Enter' && addTask()}
                  />
                  <div className="absolute right-2 top-1/2 -translate-y-1/2">
                    <VoiceDictateButton
                      onTranscript={handleVoiceTranscript}
                      size="sm"
                    />
                  </div>
                </div>
                <div className="flex gap-2 mt-2">
                  <button onClick={() => setShowAddTask(false)} className="flex-1 py-2 text-gray-500 text-sm">
                    Cancel
                  </button>
                  <button
                    onClick={addTask}
                    disabled={!newTask.trim() || addingTask}
                    className="flex-1 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium disabled:opacity-50"
                  >
                    {addingTask ? 'Adding...' : 'Add Task'}
                  </button>
                </div>
              </div>
            )}

            <div className="space-y-3">
              {plan?.tasks && plan.tasks.length > 0 ? (
                plan.tasks.map((task) => (
                  <div key={task.id} className="bg-white dark:bg-gray-800 rounded-xl p-4 flex items-center gap-4 shadow-sm">
                    {task.status === 'completed' ? (
                      <CheckCircle2 className="text-green-500" size={24} />
                    ) : (
                      <Circle className="text-gray-300" size={24} />
                    )}
                    <div className="flex-1">
                      <p className="font-medium">{task.title}</p>
                      <p className="text-sm text-gray-500">{task.time_block} • {task.priority} priority</p>
                    </div>
                  </div>
                ))
              ) : (
                <div className="bg-white dark:bg-gray-800 rounded-xl p-6 text-center text-gray-500">
                  <p>No tasks yet. Click &quot;Generate New Plan&quot; to get started!</p>
                </div>
              )}
            </div>
          </section>
        </>
      )}
    </div>
  )
}
