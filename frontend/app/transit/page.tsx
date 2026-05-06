'use client'

import { useState, useEffect } from 'react'
import Navbar from '@/components/Navbar'
import MetricCard from '@/components/MetricCard'
import { api } from '@/lib/api'

interface TransitRoute {
  route_id: string
  route_name: string
  mode: 'bus' | 'metro'
  stops: string[]
  total_distance_km: number
  estimated_time_minutes: number
  frequency_minutes: number
  status: string
}

export default function TransitPage() {
  const [routes, setRoutes] = useState<TransitRoute[]>([])
  const [filter, setFilter] = useState<'all' | 'bus' | 'metro'>('all')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchRoutes = async () => {
      try {
        const data = await api.transitRoutes()
        setRoutes(data.routes || [])
      } catch (err) {
        console.error('Failed to fetch transit routes:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchRoutes()
  }, [])

  const filteredRoutes = routes.filter(r => 
    filter === 'all' || r.mode === filter
  )

  const busRoutes = routes.filter(r => r.mode === 'bus')
  const metroRoutes = routes.filter(r => r.mode === 'metro')
  const avgFrequency = routes.length > 0 
    ? (routes.reduce((sum, r) => sum + r.frequency_minutes, 0) / routes.length).toFixed(1)
    : 0

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'On Time': return 'bg-green-500'
      case 'Running': return 'bg-yellow-500'
      default: return 'bg-gray-500'
    }
  }

  const getModeIcon = (mode: string) => {
    return mode === 'metro' ? '🚇' : '🚌'
  }

  if (loading) {
    return (
      <>
        <Navbar />
        <main className="pt-16 px-4 max-w-7xl mx-auto">
          <div className="text-center py-12">
            <div className="text-gray-400">Loading transit routes...</div>
          </div>
        </main>
      </>
    )
  }

  return (
    <>
      <Navbar />
      <main className="pt-16 px-4 max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">🚇 Cairo Transit System</h1>

        {/* Filter Buttons */}
        <div className="flex gap-3 mb-6">
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'all' 
                ? 'bg-[#e94560] text-white' 
                : 'bg-[#16213e] text-gray-400 hover:bg-[#1a1a2e]'
            }`}
          >
            All Routes
          </button>
          <button
            onClick={() => setFilter('metro')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'metro' 
                ? 'bg-[#e94560] text-white' 
                : 'bg-[#16213e] text-gray-400 hover:bg-[#1a1a2e]'
            }`}
          >
            🚇 Metro
          </button>
          <button
            onClick={() => setFilter('bus')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'bus' 
                ? 'bg-[#e94560] text-white' 
                : 'bg-[#16213e] text-gray-400 hover:bg-[#1a1a2e]'
            }`}
          >
            🚌 Bus
          </button>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-4 gap-3 mb-6">
          <MetricCard label="Total Routes" value={routes.length} color="#00b4d8" />
          <MetricCard label="Metro Lines" value={metroRoutes.length} color="#2ecc71" />
          <MetricCard label="Bus Routes" value={busRoutes.length} color="#f5c518" />
          <MetricCard label="Avg Frequency" value={`${avgFrequency}`} unit="min" color="#e94560" />
        </div>

        {/* Route Cards */}
        <div className="grid gap-4">
          {filteredRoutes.map((route) => (
            <div key={route.route_id} className="bg-[#16213e] rounded-xl p-4 border border-gray-800 hover:border-[#3498db] transition-colors">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{getModeIcon(route.mode)}</span>
                  <div>
                    <h3 className="font-bold text-lg">{route.route_name}</h3>
                    <p className="text-sm text-gray-400">{route.route_id}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-1 rounded-full text-xs text-white ${getStatusColor(route.status)}`}>
                    {route.status}
                  </span>
                </div>
              </div>

              {/* Stops Visualization */}
              <div className="mb-3">
                <div className="flex items-center gap-2 overflow-x-auto pb-2">
                  {route.stops.map((stop, index) => (
                    <div key={index} className="flex items-center">
                      <div className="flex flex-col items-center">
                        <div className="w-3 h-3 bg-[#3498db] rounded-full"></div>
                        <span className="text-xs text-gray-400 mt-1 whitespace-nowrap max-w-20 truncate">
                          {stop}
                        </span>
                      </div>
                      {index < route.stops.length - 1 && (
                        <div className="w-8 h-0.5 bg-gray-600 mx-1"></div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Route Details */}
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">Distance:</span>
                  <span className="ml-2 font-medium">{route.total_distance_km} km</span>
                </div>
                <div>
                  <span className="text-gray-400">Journey Time:</span>
                  <span className="ml-2 font-medium">{route.estimated_time_minutes} min</span>
                </div>
                <div>
                  <span className="text-gray-400">Frequency:</span>
                  <span className="ml-2 font-medium">Every {route.frequency_minutes} min</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {filteredRoutes.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-400">
              {filter === 'all' ? 'No transit routes available.' : `No ${filter} routes found.`}
            </div>
          </div>
        )}

        <div className="h-8" />
      </main>
    </>
  )
}
