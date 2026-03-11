'use client'

import { useState, useEffect } from 'react'
import { Sparkles, Check, ChevronRight, RefreshCw, Pencil } from 'lucide-react'
import { identityApi } from '@/lib/api-client'
import { useRouter } from 'next/navigation'

export default function IdentityPage() {
  const [identity, setIdentity] = useState<any>(null)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [followUp, setFollowUp] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const router = useRouter()

  useEffect(() => {
    loadIdentity()
  }, [])

  const loadIdentity = async () => {
    try {
      const { data } = await identityApi.get()
      if (data.data) {
        setIdentity(data.data)
      }
    } catch {
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async () => {
    if (!input.trim() || saving) return
    setSaving(true)
    setSuccessMessage(null)

    try {
      const { data } = identity?.ideal_self
        ? await identityApi.refine(input)
        : await identityApi.create(input)

      if (data.data?.follow_up_question) {
        setFollowUp(data.data.follow_up_question)
        setIdentity(data.data)
        setInput('')
      } else {
        setIdentity(data.data)
        setFollowUp(null)
        setInput('')
        setSuccessMessage(identity?.ideal_self ? 'Identity updated!' : 'Identity created!')
        setIsEditing(false)
        setTimeout(() => setSuccessMessage(null), 3000)
      }
    } catch {
      setSuccessMessage('Failed to save. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 animate-pulse h-48" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold">Your Identity</h1>
        <p className="text-gray-500">Who do you want to become?</p>
      </header>

      {/* Success Message */}
      {successMessage && (
        <div className={`rounded-xl p-4 text-center font-medium ${
          successMessage.includes('Failed')
            ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
            : 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
        }`}>
          {successMessage}
        </div>
      )}

      {identity?.ideal_self ? (
        <div className="bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl p-6 text-white relative">
          <button
            onClick={() => setIsEditing(!isEditing)}
            className="absolute top-4 right-4 p-2 bg-white/20 rounded-lg hover:bg-white/30 transition"
            title="Edit identity"
          >
            <Pencil size={16} />
          </button>
          <div className="flex items-center gap-2 mb-3">
            <Sparkles size={20} />
            <span className="text-sm font-medium opacity-80">Your Future Self</span>
          </div>
          <h2 className="text-2xl font-bold mb-2">{identity.ideal_self}</h2>
          {identity.description && (
            <p className="opacity-90 mb-4">{identity.description}</p>
          )}
          {identity.why && (
            <div className="bg-white/10 rounded-lg p-3 mt-4">
              <p className="text-sm font-medium opacity-80">Why this matters</p>
              <p className="mt-1">{identity.why}</p>
            </div>
          )}
          {identity.attributes?.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-4">
              {identity.attributes.map((attr: string, i: number) => (
                <span key={i} className="px-3 py-1 bg-white/20 rounded-full text-sm">{attr}</span>
              ))}
            </div>
          )}
          {identity.target_timeline && (
            <p className="text-sm opacity-70 mt-4">Timeline: {identity.target_timeline}</p>
          )}
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 text-center">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Sparkles className="text-blue-600" size={32} />
          </div>
          <h2 className="text-xl font-semibold mb-2">Define Your Future Self</h2>
          <p className="text-gray-500 mb-4">
            Who do you want to become? A CEO? A musician? An entrepreneur?
          </p>
        </div>
      )}

      {/* Show form when: no identity, followUp question, or editing */}
      {(!identity?.ideal_self || followUp || isEditing) && (
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm">
          <h3 className="font-medium mb-3">
            {followUp || (identity?.ideal_self ? "Update your identity" : "Tell me who you want to become")}
          </h3>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={identity?.ideal_self
              ? "Describe changes to your ideal self, add more details, or refine your vision..."
              : "I want to become a successful CEO who..."
            }
            className="w-full h-24 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg outline-none resize-none"
          />
          <div className="flex gap-2 mt-3">
            {isEditing && (
              <button
                onClick={() => { setIsEditing(false); setInput(''); }}
                className="px-4 py-3 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg font-medium"
              >
                Cancel
              </button>
            )}
            <button
              onClick={handleSubmit}
              disabled={!input.trim() || saving}
              className="flex-1 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {saving ? 'Saving...' : (
                <>
                  {identity?.ideal_self ? 'Update Identity' : 'Define My Future Self'}
                  <ChevronRight size={18} />
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {identity?.ideal_self && (
        <button
          onClick={() => router.push('/goals')}
          className="w-full py-4 bg-green-600 hover:bg-green-700 text-white rounded-xl font-medium flex items-center justify-center gap-2"
        >
          <Check size={20} />
          Set Goals for {identity.ideal_self}-You
        </button>
      )}
    </div>
  )
}
