'use client'

import dynamic from 'next/dynamic'
import { LogIn } from 'lucide-react'

const hasClerk = !!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY

const ClerkButtons = dynamic(
  () => import('./ClerkButtons'),
  { ssr: false }
)

export default function Header() {
  return (
    <header className="sticky top-0 z-50 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
      <div className="max-w-lg mx-auto px-4 h-14 flex items-center justify-between">
        <h1 className="font-bold text-lg text-blue-600">Gen-Friend</h1>
        {hasClerk && <ClerkButtons />}
      </div>
    </header>
  )
}
