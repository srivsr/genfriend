'use client'

import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

export default function RootPage() {
  const router = useRouter()

  useEffect(() => {
    // Auth temporarily disabled - redirect directly to home
    router.push('/home')
  }, [router])

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="animate-pulse text-xl text-gray-600">Loading...</div>
    </div>
  )
}
