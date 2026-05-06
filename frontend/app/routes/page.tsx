'use client'

import { useState, useEffect } from 'react'
import dynamic from 'next/dynamic'
import Navbar from '@/components/Navbar'
import MetricCard from '@/components/MetricCard'
import { api, type GraphNode, type GraphEdge, type RouteResult } from '@/lib/api'

const MapView = dynamic(() => import('@/components/MapView'), { ssr: false })

export default function RoutesPage() {
  const [nodes, setNodes] = useState<GraphNode[]>([])
  const [edges, setEdges] = useState<GraphEdge[]>([])
  const [source, setSource] = useState(0)
  const [target, setTarget] = useState(3)
  const [timeIndex, setTimeIndex] = useState(0)
  const [mode, setMode] = useState('car')
  const [algorithm, setAlgorithm] = useState('dijkstra')
  const [results, setResults] = useState<RouteResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.graphNodes().then(setNodes).catch(console.error)
    api.graphEdges().then(setEdges).catch(console.error)
  }, [])

  const compute = async () => {
    if (source === target) {
      setError('Source and target must be different')
      return
    }
    setLoading(true)
    setError('')
    try {
      let res: RouteResult[]
      switch (algorithm) {
        case 'astar':
          res = [await api.routeAstar(source, target, timeIndex, mode)]
          break
        case 'time-dependent':
          res = [await api.routeTimeDep(source, target, timeIndex, mode)]
          break
        case 'k-shortest':
          res = await api.routeKShortest(source, target, 3, timeIndex, mode)
          break
        case 'ml-aware':
          const mlResult = await api.routeMLAware(source, target, timeIndex, mode)
          res = [mlResult]
          break
        default:
          res = [await api.routeDijkstra(source, target, timeIndex, mode)]
      }
      setResults(res)
      if (res.length === 0 || !res.some(r => r.found)) setError('No route found')
    } catch (err) {
      console.error(err)
      setError('Failed to compute route. Is the backend running?')
    }
    setLoading(false)
  }

  const bestRoute = results.find(r => r.found)
  const routeNodes = bestRoute?.nodes || []

  return (
    <>
      <Navbar />
      <main className="pt-16 px-4 max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold mb-4">🛣️ Route Finder</h1>

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
                <option value="k-shortest">K-Shortest (Yen)</option>
                <option value="ml-aware">🧠 ML-Aware Route</option>
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
              <button onClick={compute} disabled={loading}
                className="w-full bg-[#e94560] hover:bg-[#c73e54] disabled:opacity-50 text-white font-bold py-2 px-4 rounded-lg">
                {loading ? '⏳' : '🔍 Find Route'}
              </button>
            </div>
          </div>
        </div>

        <MapView nodes={nodes} edges={edges} routeNodes={routeNodes}
          routeColor={algorithm === 'astar' ? '#e63946' : algorithm === 'ml-aware' ? '#2ecc71' : '#1d3557'} height="450px" />

        {error && <p className="text-red-400 text-sm mt-2">⚠️ {error}</p>}

        {results.length > 0 && (
          <div className="space-y-3 mt-4">
            {results.map((r, i) => (
              <div key={i} className={`bg-[#16213e] rounded-xl p-4 border ${r.found ? 'border-gray-700' : 'border-red-800'}`}>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-bold">
                    {algorithm === 'k-shortest' ? `Path ${i + 1}` : 'Route'}
                    {!r.found && ' (Not Found)'}
                  </h3>
                  <span className="text-xs text-gray-400 bg-[#1a1a2e] px-2 py-1 rounded">{r.algorithm}</span>
                </div>
                {r.found && (
                  <>
                    <div className="grid grid-cols-4 gap-2 mb-2">
                      <MetricCard label="Time" value={`${r.time.toFixed(1) }`} unit="min" color="#e94560" />
                      <MetricCard label="Distance" value={`${r.distance.toFixed(1)}`} unit="km" color="#00b4d8" />
                      <MetricCard label="Congestion" value={`${(r.congestion * 100).toFixed(0)}%`} color="#f5c518" />
                      <MetricCard label="Stops" value={r.path.length} color="#2ecc71" />
                    </div>
                    <p className="text-xs text-gray-400">
                      {r.path.join(' → ')}
                    </p>
                  </>
                )}
              </div>
            ))}
          </div>
        )}
        <div className="h-8" />
      </main>
    </>
  )
}
