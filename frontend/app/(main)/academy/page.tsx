'use client'

import { useState, useEffect } from 'react'
import { BookOpen, ChevronRight, Send } from 'lucide-react'
import { academyApi } from '@/lib/api-client'

interface Topic {
  slug: string
  title: string
  category: string
  difficulty: string
}

export default function AcademyPage() {
  const [topics, setTopics] = useState<Topic[]>([])
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadTopics()
  }, [])

  const loadTopics = async () => {
    try {
      const { data } = await academyApi.topics()
      setTopics(data.data || [])
    } catch {
      setTopics([])
    }
  }

  const askQuestion = async () => {
    if (!question.trim() || loading) return
    setLoading(true)
    try {
      const { data } = await academyApi.ask(question)
      setAnswer(data.data.answer)
    } catch {
      setAnswer('Sorry, I could not process that question.')
    } finally {
      setLoading(false)
    }
  }

  const difficultyColor = (d: string) => {
    switch (d) {
      case 'beginner': return 'bg-green-100 text-green-700'
      case 'intermediate': return 'bg-yellow-100 text-yellow-700'
      case 'advanced': return 'bg-red-100 text-red-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold">AI Academy</h1>
        <p className="text-gray-500">Learn how AI works</p>
      </header>

      <div className="bg-gradient-to-r from-accent-500 to-primary-500 rounded-2xl p-6 text-white">
        <h2 className="font-semibold mb-3">Ask about AI</h2>
        <div className="flex gap-2">
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && askQuestion()}
            placeholder="What is RAG? How do LLMs work?"
            className="flex-1 px-4 py-2 rounded-lg bg-white/20 placeholder-white/70 outline-none"
          />
          <button onClick={askQuestion} disabled={loading} className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
            <Send size={18} />
          </button>
        </div>
        {answer && (
          <div className="mt-4 p-4 bg-white/10 rounded-lg">
            <p className="text-sm whitespace-pre-wrap">{answer}</p>
          </div>
        )}
      </div>

      <section>
        <h2 className="font-semibold mb-4">Topics</h2>
        <div className="space-y-3">
          {topics.map((topic) => (
            <div key={topic.slug} className="bg-white dark:bg-gray-800 rounded-xl p-4 flex items-center justify-between shadow-sm">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                  <BookOpen className="text-primary-600" size={20} />
                </div>
                <div>
                  <p className="font-medium">{topic.title}</p>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${difficultyColor(topic.difficulty)}`}>
                    {topic.difficulty}
                  </span>
                </div>
              </div>
              <ChevronRight className="text-gray-400" size={20} />
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
