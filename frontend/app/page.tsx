'use client'

import { useState, useEffect } from 'react'
import dynamic from 'next/dynamic'
import Navbar from '@/components/Navbar'
import MetricCard from '@/components/MetricCard'

const MapView = dynamic(() => import('@/components/MapView'), { ssr: false })
import { api, type GraphNode, type GraphEdge, type RouteResult } from '@/lib/api'

export default function Dashboard() {
  const [nodes, setNodes] = useState<GraphNode[]>([])
  const [edges, setEdges] = useState<GraphEdge[]>([])
  const [summary, setSummary] = useState<Record<string, unknown>>({})
  const [source, setSource] = useState(0)
  const [target, setTarget] = useState(3)
  const [timeIndex, setTimeIndex] = useState(0)
  const [mode, setMode] = useState('car')
  const [algorithm, setAlgorithm] = useState('dijkstra')
  const [routeResult, setRouteResult] = useState<RouteResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.graphNodes().then(setNodes).catch(console.error)
    api.graphEdges().then(setEdges).catch(console.error)
    api.graphSummary().then(setSummary).catch(console.error)
  }, [])

  const computeRoute = async () => {
    if (source === target) {
      setError('Source and target must be different')
      return
    }
    setLoading(true)
    setError('')
    try {
      let result: RouteResult
      switch (algorithm) {
        case 'astar':
          result = await api.routeAstar(source, target, timeIndex, mode)
          break
        case 'time-dependent':
          result = await api.routeTimeDep(source, target, timeIndex, mode)
          break
        case 'ml-aware':
          result = await api.routeMLAware(source, target, timeIndex, mode)
          break
        default:
          result = await api.routeDijkstra(source, target, timeIndex, mode)
      }
      setRouteResult(result)
      if (!result.found) setError('No route found between these nodes')
    } catch (err) {
      console.error(err)
      setError('Failed to compute route. Is the backend running?')
    }
    setLoading(false)
  }

  return (
    <>
      <Navbar />
      <main className="pt-16 px-4 max-w-7xl mx-auto">
        {/* Hero */}
        <div className="text-center py-8">
          <h1 className="text-4xl font-bold mb-2">
            <span className="bg-gradient-to-r from-[#e94560] via-[#f5c518] to-[#00b4d8] bg-clip-text text-transparent">
              Cairo Smart Transportation
            </span>
          </h1>
          <p className="text-gray-400 text-lg">Network Optimization System</p>
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <MetricCard label="Nodes" value={summary.nodes as number || '...'} icon="📍" color="#00b4d8" />
          <MetricCard label="Edges" value={summary.edges as number || '...'} icon="🛣️" color="#2ecc71" />
          <MetricCard label="Distance" value={summary.total_distance_km ? `${(summary.total_distance_km as number).toFixed(0)}` : '...'} unit="km" icon="📏" color="#f5c518" />
          <MetricCard label="Potential" value={summary.potential_roads as number || '...'} icon="🏗️" color="#e94560" />
        </div>

        {/* Route Controls */}
        <div className="bg-[#16213e] rounded-xl p-4 border border-gray-800 mb-4">
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
            <div>
              <label className="text-xs text-gray-400">From</label>
              <select value={source} onChange={e => setSource(Number(e.target.value))}
                className="w-full bg-[#1a1a2e] border border-gray-700 rounded-lg px-3 py-2 text-sm">
                {nodes.map(n => <option key={n.id} value={n.id}>{n.name}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400">To</label>
              <select value={target} onChange={e => setTarget(Number(e.target.value))}
                className="w-full bg-[#1a1a2e] border border-gray-700 rounded-lg px-3 py-2 text-sm">
                {nodes.map(n => <option key={n.id} value={n.id}>{n.name}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400">Algorithm</label>
              <select value={algorithm} onChange={e => setAlgorithm(e.target.value)}
                className="w-full bg-[#1a1a2e] border border-gray-700 rounded-lg px-3 py-2 text-sm">
                <option value="dijkstra">Dijkstra</option>
                <option value="astar">A* Search</option>
                <option value="time-dependent">Time-Dependent</option>
                <option value="ml-aware">🧠 ML-Aware</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400">Time</label>
              <select value={timeIndex} onChange={e => setTimeIndex(Number(e.target.value))}
                className="w-full bg-[#1a1a2e] border border-gray-700 rounded-lg px-3 py-2 text-sm">
                <option value={0}>Morning</option>
                <option value={1}>Afternoon</option>
                <option value={2}>Evening</option>
                <option value={3}>Night</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400">Mode</label>
              <select value={mode} onChange={e => setMode(e.target.value)}
                className="w-full bg-[#1a1a2e] border border-gray-700 rounded-lg px-3 py-2 text-sm">
                <option value="car">🚗 Car</option>
                <option value="emergency">🚑 Emergency</option>
                <option value="bus">🚌 Bus</option>
                <option value="metro">🚇 Metro</option>
              </select>
            </div>
            <div className="flex items-end">
              <button onClick={computeRoute} disabled={loading}
                className="w-full bg-[#e94560] hover:bg-[#c73e54] disabled:opacity-50 text-white font-bold py-2 px-4 rounded-lg transition-colors">
                {loading ? '⏳ Computing...' : '🗺️ Compute Route'}
              </button>
            </div>
          </div>
          {error && <p className="text-red-400 text-sm mt-2">⚠️ {error}</p>}
        </div>

        {/* Map */}
        <MapView
          nodes={nodes}
          edges={edges}
          routeNodes={routeResult?.found ? routeResult.nodes : []}
          routeColor={algorithm === 'astar' ? '#e63946' : algorithm === 'ml-aware' ? '#2ecc71' : '#1d3557'}
          height="500px"
        />

        {/* Route Results */}
        {routeResult?.found && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
            <MetricCard label="Travel Time" value={routeResult.time.toFixed(1)} unit="min" icon="⏱️" color="#e94560" />
            <MetricCard label="Distance" value={routeResult.distance.toFixed(1)} unit="km" icon="📏" color="#00b4d8" />
            <MetricCard label="Congestion" value={`${(routeResult.congestion * 100).toFixed(0)}%`} icon="🚦" color="#f5c518" />
            <MetricCard label="Algorithm" value={routeResult.algorithm} icon="⚙️" color="#2ecc71" />
          </div>
        )}

        <div className="h-8" />
      </main>
    </>
  )
}
