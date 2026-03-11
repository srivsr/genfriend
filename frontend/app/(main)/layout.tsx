'use client'

import Navigation from '@/components/shared/Navigation'
import Header from '@/components/shared/Header'

export default function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen pb-20">
      <Header />
      <main className="max-w-lg mx-auto px-4 py-6">
        {children}
      </main>
      <Navigation />
    </div>
  )
}
