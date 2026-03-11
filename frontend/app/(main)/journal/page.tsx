'use client'

import { useState, useEffect, Suspense } from 'react'
import { Trophy, Heart, BookOpen, Plus, Star, Mic } from 'lucide-react'
import { journalApi } from '@/lib/api-client'
import { useSearchParams } from 'next/navigation'
import { VoiceDictateButton } from '@/components/voice/VoiceDictateButton'

interface JournalEntry {
  id: string
  entry_type: string
  content: string
  enrichment?: string
  mood?: string
  created_at: string
  is_favorite?: boolean
}

function JournalContent() {
  const [entries, setEntries] = useState<JournalEntry[]>([])
  const [filter, setFilter] = useState<string>('all')
  const [showCreate, setShowCreate] = useState(false)
  const [entryType, setEntryType] = useState('win')
  const [content, setContent] = useState('')
  const [mood, setMood] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const searchParams = useSearchParams()

  useEffect(() => {
    const type = searchParams.get('type')
    if (type === 'win') {
      setShowCreate(true)
      setEntryType('win')
    }
    loadEntries()
  }, [searchParams])

  const loadEntries = async () => {
    try {
      const { data } = await journalApi.list(filter !== 'all' ? filter : undefined)
      setEntries(data.data || [])
    } catch {
    } finally {
      setLoading(false)
    }
  }

  const createEntry = async () => {
    if (!content.trim() || saving) return
    setSaving(true)

    try {
      await journalApi.create({
        entry_type: entryType,
        content,
        mood: mood || undefined
      })
      setContent('')
      setMood('')
      setShowCreate(false)
      loadEntries()
    } catch {
    } finally {
      setSaving(false)
    }
  }

  const handleVoiceTranscript = (transcript: string) => {
    setContent((prev) => prev ? `${prev} ${transcript}` : transcript)
  }

  const getIcon = (type: string) => {
    switch (type) {
      case 'win': return <Trophy className="text-yellow-500" size={18} />
      case 'moment': return <Heart className="text-pink-500" size={18} />
      default: return <BookOpen className="text-blue-500" size={18} />
    }
  }

  const filters = [
    { key: 'all', label: 'All' },
    { key: 'win', label: 'Wins' },
    { key: 'moment', label: 'Moments' },
    { key: 'reflection', label: 'Reflections' },
  ]

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Journal</h1>
          <p className="text-gray-500">Your wins & moments</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="w-10 h-10 bg-yellow-500 text-white rounded-full flex items-center justify-center shadow-lg"
        >
          <Plus size={24} />
        </button>
      </header>

      <div className="flex gap-2 overflow-x-auto pb-2">
        {filters.map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap ${
              filter === f.key
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {showCreate && (
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-lg">
          <div className="flex gap-2 mb-4">
            {[
              { key: 'win', label: 'Win', icon: Trophy, color: 'yellow' },
              { key: 'moment', label: 'Moment', icon: Heart, color: 'pink' },
              { key: 'reflection', label: 'Reflect', icon: BookOpen, color: 'blue' },
            ].map((t) => (
              <button
                key={t.key}
                onClick={() => setEntryType(t.key)}
                className={`flex-1 py-2 rounded-lg flex items-center justify-center gap-1 text-sm font-medium ${
                  entryType === t.key
                    ? `bg-${t.color}-100 text-${t.color}-700`
                    : 'bg-gray-100 text-gray-500'
                }`}
              >
                <t.icon size={16} />
                {t.label}
              </button>
            ))}
          </div>

          <div className="relative">
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder={
                entryType === 'win'
                  ? "What did you accomplish? What are you proud of?"
                  : entryType === 'moment'
                  ? "What made you happy today?"
                  : "What did you learn? What's on your mind?"
              }
              className="w-full h-24 p-3 pr-12 bg-gray-50 dark:bg-gray-700 rounded-lg outline-none resize-none"
            />
            <div className="absolute right-2 bottom-2">
              <VoiceDictateButton
                onTranscript={handleVoiceTranscript}
                size="sm"
              />
            </div>
          </div>

          <p className="text-xs text-gray-400 mt-1 flex items-center gap-1">
            <Mic size={12} /> Tap mic to dictate
          </p>

          <div className="flex gap-2 mt-3">
            <button onClick={() => setShowCreate(false)} className="flex-1 py-2 text-gray-500">
              Cancel
            </button>
            <button
              onClick={createEntry}
              disabled={!content.trim() || saving}
              className="flex-1 py-2 bg-yellow-500 text-white rounded-lg font-medium disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Entry'}
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white dark:bg-gray-800 rounded-xl p-4 animate-pulse h-24" />
          ))}
        </div>
      ) : entries.length > 0 ? (
        <div className="space-y-4">
          {entries.map((entry) => (
            <div key={entry.id} className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
              <div className="flex items-start gap-3">
                {getIcon(entry.entry_type)}
                <div className="flex-1">
                  <p className="text-gray-900 dark:text-white">{entry.content}</p>
                  {entry.enrichment && (
                    <p className="text-sm text-blue-600 mt-2 italic">{entry.enrichment}</p>
                  )}
                  <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
                    <span>{new Date(entry.created_at).toLocaleDateString()}</span>
                    {entry.mood && <span className="px-2 py-0.5 bg-gray-100 rounded-full">{entry.mood}</span>}
                    {entry.is_favorite && <Star className="text-yellow-500" size={12} />}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 text-center">
          <Trophy className="mx-auto text-gray-300" size={48} />
          <h3 className="text-lg font-semibold mt-4">No entries yet</h3>
          <p className="text-gray-500 mt-2">Capture your first win or moment!</p>
        </div>
      )}
    </div>
  )
}

export default function JournalPage() {
  return (
    <Suspense fallback={<div className="animate-pulse p-4">Loading...</div>}>
      <JournalContent />
    </Suspense>
  )
}
