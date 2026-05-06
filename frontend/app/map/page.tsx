'use client'

import { useState, useEffect } from 'react'
import dynamic from 'next/dynamic'
import Navbar from '@/components/Navbar'
import { api, type GraphNode, type GraphEdge } from '@/lib/api'

const MapView = dynamic(() => import('@/components/MapView'), { ssr: false })

export default function MapPage() {
  const [nodes, setNodes] = useState<GraphNode[]>([])
  const [edges, setEdges] = useState<GraphEdge[]>([])
  const [showPotential, setShowPotential] = useState(false)

  useEffect(() => {
    api.graphNodes().then(setNodes).catch(console.error)
    api.graphEdges(true).then(setEdges).catch(console.error)
  }, [])

  const displayEdges = showPotential ? edges : edges.filter(e => !e.is_potential)

  return (
    <>
      <Navbar />
      <main className="pt-16 px-4 max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold">🗺️ Cairo Network Map</h1>
          <label className="flex items-center gap-2 text-sm bg-[#16213e] px-4 py-2 rounded-lg border border-gray-800 cursor-pointer">
            <input type="checkbox" checked={showPotential}
              onChange={e => setShowPotential(e.target.checked)}
              className="accent-[#e94560]" />
            Show potential roads
          </label>
        </div>

        <MapView
          nodes={nodes}
          edges={displayEdges}
          height="calc(100vh - 140px)"
        />

        {/* Node list */}
        <div className="mt-4 bg-[#16213e] rounded-xl p-4 border border-gray-800">
          <h3 className="font-bold mb-2">📍 Network Nodes ({nodes.length})</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {nodes.map(n => (
              <div key={n.id} className="flex items-center gap-2 text-sm bg-[#1a1a2e] rounded-lg px-3 py-2">
                <div className="w-3 h-3 rounded-full" style={{ background: n.color }} />
                <span>{n.name}</span>
                <span className="text-gray-500 text-xs ml-auto">{n.type}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="h-8" />
      </main>
    </>
  )
}
