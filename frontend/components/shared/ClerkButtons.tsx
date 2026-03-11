'use client'

import { SignedIn, SignedOut, UserButton, SignInButton } from '@clerk/nextjs'
import { LogIn } from 'lucide-react'

export default function ClerkButtons() {
  return (
    <>
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
    </>
  )
}
