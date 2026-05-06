'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Map, Route, Network, Activity, Bus, Brain, Zap } from 'lucide-react'

const navItems = [
  { href: '/', label: 'Dashboard', icon: Activity },
  { href: '/map', label: 'Live Map', icon: Map },
  { href: '/routes', label: 'Routes', icon: Route },
  { href: '/race', label: 'Race Animation', icon: Zap },
  { href: '/mst', label: 'MST Network', icon: Network },
  { href: '/simulation', label: 'Simulation', icon: Activity },
  { href: '/transit', label: 'Transit', icon: Bus },
  { href: '/ml', label: 'ML Predict', icon: Brain },
]

export default function Navbar() {
  const pathname = usePathname()

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-[#1a1a2e]/95 backdrop-blur-sm border-b border-gray-800">
      <div className="flex items-center justify-between px-4 h-14">
        <Link href="/" className="flex items-center gap-2 text-lg font-bold">
          <span className="text-2xl">🏙️</span>
          <span className="bg-gradient-to-r from-[#e94560] to-[#f5c518] bg-clip-text text-transparent">
            Cairo Transport
          </span>
        </Link>
        <div className="flex items-center gap-1 overflow-x-auto">
          {navItems.map(({ href, label, icon: Icon }) => {
            const active = pathname === href
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-all whitespace-nowrap
                  ${active
                    ? 'bg-[#e94560]/20 text-[#e94560] font-semibold'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
                  }`}
              >
                <Icon size={14} />
                {label}
              </Link>
            )
          })}
        </div>
      </div>
    </nav>
  )
}
