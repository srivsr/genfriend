'use client'

import { useState, useEffect } from 'react'
import { usePWA } from './PWAProvider'

export default function InstallPrompt() {
  const { isInstallable, isInstalled, install } = usePWA()
  const [dismissed, setDismissed] = useState(false)
  const [showPrompt, setShowPrompt] = useState(false)

  useEffect(() => {
    const wasDismissed = localStorage.getItem('pwa-install-dismissed')
    if (wasDismissed) {
      const dismissedAt = new Date(wasDismissed)
      const daysSince = (Date.now() - dismissedAt.getTime()) / (1000 * 60 * 60 * 24)
      if (daysSince < 7) {
        setDismissed(true)
      }
    }

    const timer = setTimeout(() => {
      setShowPrompt(true)
    }, 30000)

    return () => clearTimeout(timer)
  }, [])

  const handleInstall = async () => {
    const success = await install()
    if (success) {
      setShowPrompt(false)
    }
  }

  const handleDismiss = () => {
    localStorage.setItem('pwa-install-dismissed', new Date().toISOString())
    setDismissed(true)
  }

  if (!isInstallable || isInstalled || dismissed || !showPrompt) {
    return null
  }

  return (
    <div className="fixed bottom-20 left-4 right-4 md:left-auto md:right-4 md:w-96 bg-gradient-to-r from-sky-600 to-blue-600 rounded-xl shadow-2xl p-4 z-50 animate-slide-up">
      <button
        onClick={handleDismiss}
        className="absolute top-2 right-2 text-white/60 hover:text-white p-1"
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      <div className="flex items-start gap-4">
        <div className="flex-shrink-0 w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
          <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-white">Install Gen-Friend</h3>
          <p className="text-sm text-white/80 mt-1">
            Add to your home screen for quick access and offline support.
          </p>
        </div>
      </div>

      <div className="flex gap-3 mt-4">
        <button
          onClick={handleDismiss}
          className="flex-1 text-sm text-white/80 hover:text-white py-2.5 transition-colors"
        >
          Not Now
        </button>
        <button
          onClick={handleInstall}
          className="flex-1 bg-white text-sky-600 font-medium text-sm py-2.5 rounded-lg hover:bg-white/90 transition-colors"
        >
          Install App
        </button>
      </div>
    </div>
  )
}
