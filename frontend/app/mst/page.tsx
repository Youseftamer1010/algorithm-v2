'use client'

import { useState, useEffect } from 'react'
import dynamic from 'next/dynamic'
import Navbar from '@/components/Navbar'
import MetricCard from '@/components/MetricCard'
import { api, type GraphNode, type GraphEdge, type MSTResult } from '@/lib/api'

const MapView = dynamic(() => import('@/components/MapView'), { ssr: false })

export default function MSTPage() {
  const [nodes, setNodes] = useState<GraphNode[]>([])
  const [edges, setEdges] = useState<GraphEdge[]>([])
  const [kruskal, setKruskal] = useState<MSTResult | null>(null)
  const [prim, setPrim] = useState<MSTResult | null>(null)
  const [showMST, setShowMST] = useState(false)
  const [includePotential, setIncludePotential] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api.graphNodes().then(setNodes).catch(console.error)
    api.graphEdges(true).then(setEdges).catch(console.error)
  }, [])

  const computeMST = async () => {
    setLoading(true)
    try {
      const [k, p] = await Promise.all([
        api.mstKruskal(includePotential, true),
        api.mstPrim(includePotential, true),
      ])
      setKruskal(k)
      setPrim(p)
      setShowMST(true)
    } catch (err) { console.error(err) }
    setLoading(false)
  }

  return (
    <>
      <Navbar />
      <main className="pt-16 px-4 max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold mb-4">🌳 MST Network Design</h1>

        <div className="bg-[#16213e] rounded-xl p-4 border border-gray-800 mb-4">
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={includePotential}
                onChange={e => setIncludePotential(e.target.checked)}
                className="accent-[#e94560]" />
              Include potential roads
            </label>
            <button onClick={computeMST} disabled={loading}
              className="bg-[#e94560] hover:bg-[#c73e54] disabled:opacity-50 text-white font-bold py-2 px-6 rounded-lg">
              {loading ? '⏳ Computing...' : '🌳 Compute MST'}
            </button>
          </div>
        </div>

        <MapView
          nodes={nodes}
          edges={edges.filter(e => !e.is_potential)}
          mstEdges={showMST && kruskal ? kruskal.mst_edges : []}
          mstColor="#e63946"
          mstEdges2={showMST && prim ? prim.mst_edges : []}
          mstColor2="#457b9d"
          height="500px"
        />

        {kruskal && prim && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            <div className="bg-[#16213e] rounded-xl p-4 border border-[#e63946]">
              <h3 className="font-bold text-[#e63946] mb-2">Kruskal&apos;s Algorithm</h3>
              <div className="grid grid-cols-2 gap-2">
                <MetricCard label="Edges" value={kruskal.edge_count} color="#e63946" />
                <MetricCard label="Distance" value={`${kruskal.total_distance.toFixed(1)} km`} color="#e63946" />
                <MetricCard label="Cost" value={`${kruskal.total_cost.toFixed(0)} M EGP`} color="#e63946" />
                <MetricCard label="Connected" value={kruskal.connected ? '✅ Yes' : '❌ No'} color={kruskal.connected ? '#2ecc71' : '#e94560'} />
              </div>
            </div>
            <div className="bg-[#16213e] rounded-xl p-4 border border-[#457b9d]">
              <h3 className="font-bold text-[#457b9d] mb-2">Prim&apos;s Algorithm</h3>
              <div className="grid grid-cols-2 gap-2">
                <MetricCard label="Edges" value={prim.edge_count} color="#457b9d" />
                <MetricCard label="Distance" value={`${prim.total_distance.toFixed(1)} km`} color="#457b9d" />
                <MetricCard label="Cost" value={`${prim.total_cost.toFixed(0)} M EGP`} color="#457b9d" />
                <MetricCard label="Connected" value={prim.connected ? '✅ Yes' : '❌ No'} color={prim.connected ? '#2ecc71' : '#e94560'} />
              </div>
            </div>
          </div>
        )}
        <div className="h-8" />
      </main>
    </>
  )
}
