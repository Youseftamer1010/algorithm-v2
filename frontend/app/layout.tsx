import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Cairo Smart Transportation Network',
  description: 'Optimization system for Cairo metropolitan transportation using graph algorithms, DP, greedy, and ML',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link
          rel="stylesheet"
          href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
          integrity="sha256-p4NxAoJBhIIN+hmNHrzRC2G3RQaQFn0r2FjE+1JYKs="
          crossOrigin=""
        />
      </head>
      <body className="min-h-screen bg-[#0f0f1a] text-gray-200">
        {children}
      </body>
    </html>
  )
}
