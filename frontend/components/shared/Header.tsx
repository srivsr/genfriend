'use client'

import { SignedIn, SignedOut, UserButton, SignInButton } from '@clerk/nextjs'
import { LogIn } from 'lucide-react'

export default function Header() {
  return (
    <header className="sticky top-0 z-50 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
      <div className="max-w-lg mx-auto px-4 h-14 flex items-center justify-between">
        <h1 className="font-bold text-lg text-blue-600">Gen-Friend</h1>
        
        <SignedIn>
          <UserButton afterSignOutUrl="/sign-in" />
        </SignedIn>
        
        <SignedOut>
          <SignInButton mode="modal">
            <button className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700">
              <LogIn size={16} />
              Sign In
            </button>
          </SignInButton>
        </SignedOut>
      </div>
    </header>
  )
}
