'use client'

import { useState, useEffect } from 'react'
import Navbar from '@/components/Navbar'
import RaceAnimation from '@/components/RaceAnimation'
import { api, type GraphNode, type GraphEdge } from '@/lib/api'

export default function RacePage() {
  const [nodes, setNodes] = useState<GraphNode[]>([])
  const [edges, setEdges] = useState<GraphEdge[]>([])

  useEffect(() => {
    api.graphNodes().then(setNodes).catch(console.error)
    api.graphEdges().then(setEdges).catch(console.error)
  }, [])

  return (
    <>
      <Navbar />
      <main className="pt-16 px-4 max-w-7xl mx-auto">
        <RaceAnimation nodes={nodes} edges={edges} />
        <div className="h-8" />
      </main>
    </>
  )
}
