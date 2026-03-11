import type { Metadata, Viewport } from 'next'
import './globals.css'
import Providers from '@/components/providers/Providers'

export const dynamic = 'force-dynamic'

export const metadata: Metadata = {
  title: 'Gen-Friend - AI Productivity Companion',
  description: 'Your AI productivity companion - daily planning, career coaching, and skill development. The opposite of Instagram.',
  manifest: '/manifest.json',
  applicationName: 'Gen-Friend',
  keywords: ['productivity', 'AI coach', 'career planning', 'skill development', 'daily planner'],
  authors: [{ name: 'SriVSR' }],
  creator: 'SriVSR',
  publisher: 'SriVSR',
  formatDetection: {
    telephone: false,
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: 'Gen-Friend',
    startupImage: [
      {
        url: '/splash/apple-splash-2048-2732.png',
        media: '(device-width: 1024px) and (device-height: 1366px) and (-webkit-device-pixel-ratio: 2)',
      },
      {
        url: '/splash/apple-splash-1668-2388.png',
        media: '(device-width: 834px) and (device-height: 1194px) and (-webkit-device-pixel-ratio: 2)',
      },
      {
        url: '/splash/apple-splash-1290-2796.png',
        media: '(device-width: 430px) and (device-height: 932px) and (-webkit-device-pixel-ratio: 3)',
      },
      {
        url: '/splash/apple-splash-1179-2556.png',
        media: '(device-width: 393px) and (device-height: 852px) and (-webkit-device-pixel-ratio: 3)',
      },
      {
        url: '/splash/apple-splash-1170-2532.png',
        media: '(device-width: 390px) and (device-height: 844px) and (-webkit-device-pixel-ratio: 3)',
      },
    ],
  },
  openGraph: {
    type: 'website',
    siteName: 'Gen-Friend',
    title: 'Gen-Friend - AI Productivity Companion',
    description: 'Your AI productivity companion - daily planning, career coaching, and skill development.',
    images: [{ url: '/og-image.png', width: 1200, height: 630 }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Gen-Friend - AI Productivity Companion',
    description: 'Your AI productivity companion - daily planning, career coaching, and skill development.',
    images: ['/og-image.png'],
  },
  icons: {
    icon: [
      { url: '/icons/icon-32x32.png', sizes: '32x32', type: 'image/png' },
      { url: '/icons/icon-16x16.png', sizes: '16x16', type: 'image/png' },
    ],
    apple: [
      { url: '/icons/apple-touch-icon.png', sizes: '180x180', type: 'image/png' },
    ],
    other: [
      { rel: 'mask-icon', url: '/icons/safari-pinned-tab.svg', color: '#0ea5e9' },
    ],
  },
  other: {
    'mobile-web-app-capable': 'yes',
    'msapplication-TileColor': '#0f172a',
    'msapplication-TileImage': '/icons/icon-144x144.png',
    'msapplication-config': '/browserconfig.xml',
  },
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#0ea5e9' },
    { media: '(prefers-color-scheme: dark)', color: '#0f172a' },
  ],
  colorScheme: 'dark light',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  )
}
