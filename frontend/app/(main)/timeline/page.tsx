'use client'

import { useState, useEffect } from 'react'
import { Plus, Calendar } from 'lucide-react'
import { entriesApi } from '@/lib/api-client'

interface Entry {
  id: string
  content: string
  mood?: string
  created_at: string
}

export default function TimelinePage() {
  const [entries, setEntries] = useState<Entry[]>([])
  const [newEntry, setNewEntry] = useState('')
  const [showInput, setShowInput] = useState(false)

  useEffect(() => {
    loadEntries()
  }, [])

  const loadEntries = async () => {
    try {
      const { data } = await entriesApi.list()
      setEntries(data.data || [])
    } catch {
      setEntries([])
    }
  }

  const addEntry = async () => {
    if (!newEntry.trim()) return
    try {
      await entriesApi.create({ content: newEntry })
      setNewEntry('')
      setShowInput(false)
      loadEntries()
    } catch {
      console.error('Failed to add entry')
    }
  }

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Timeline</h1>
          <p className="text-gray-500">Your journal entries</p>
        </div>
        <button
          onClick={() => setShowInput(!showInput)}
          className="w-10 h-10 bg-primary-600 text-white rounded-full flex items-center justify-center shadow-lg"
        >
          <Plus size={24} />
        </button>
      </header>

      {showInput && (
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-4 shadow-lg">
          <textarea
            value={newEntry}
            onChange={(e) => setNewEntry(e.target.value)}
            placeholder="What's on your mind?"
            className="w-full h-24 bg-transparent outline-none resize-none"
          />
          <div className="flex justify-end gap-2 mt-2">
            <button onClick={() => setShowInput(false)} className="px-4 py-2 text-gray-500">Cancel</button>
            <button onClick={addEntry} className="px-4 py-2 bg-primary-600 text-white rounded-lg">Save</button>
          </div>
        </div>
      )}

      {entries.length > 0 ? (
        <div className="space-y-4">
          {entries.map((entry) => (
            <div key={entry.id} className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
              <p className="text-gray-900 dark:text-white">{entry.content}</p>
              <div className="flex items-center gap-2 mt-3 text-sm text-gray-500">
                <Calendar size={14} />
                <span>{new Date(entry.created_at).toLocaleDateString()}</span>
                {entry.mood && <span className="ml-2 px-2 py-0.5 bg-primary-100 text-primary-700 rounded-full text-xs">{entry.mood}</span>}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-8 text-center">
          <Calendar className="mx-auto text-gray-300" size={48} />
          <p className="mt-4 text-gray-500">No entries yet. Start journaling!</p>
        </div>
      )}
    </div>
  )
}
