'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Home, MessageCircle, Target, BookOpen, User } from 'lucide-react'
import clsx from 'clsx'

const navItems = [
  { href: '/home', icon: Home, label: 'Home' },
  { href: '/goals', icon: Target, label: 'Goals' },
  { href: '/chat', icon: MessageCircle, label: 'Chat' },
  { href: '/journal', icon: BookOpen, label: 'Journal' },
  { href: '/identity', icon: User, label: 'Profile' },
]

export default function Navigation() {
  const pathname = usePathname()

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 safe-bottom">
      <div className="flex justify-around items-center h-16 max-w-lg mx-auto">
        {navItems.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                'flex flex-col items-center justify-center w-16 h-full',
                isActive ? 'text-blue-600' : 'text-gray-500'
              )}
            >
              <item.icon size={24} strokeWidth={isActive ? 2.5 : 2} />
              <span className="text-xs mt-1">{item.label}</span>
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
