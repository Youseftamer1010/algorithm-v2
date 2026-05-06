'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import dynamic from 'next/dynamic'
import { Play, Pause, SkipForward, RotateCcw, Zap } from 'lucide-react'
import { api, type RaceResult, type GraphNode, type GraphEdge } from '@/lib/api'
import MetricCard from './MetricCard'

const MapView = dynamic(() => import('./MapView'), { ssr: false })

interface RaceAnimationProps {
  nodes: GraphNode[]
  edges?: GraphEdge[]
}

export default function RaceAnimation({ nodes, edges: edgesProp }: RaceAnimationProps) {
  const [edgesState, setEdgesState] = useState<GraphEdge[]>([])
  const edges = edgesProp && edgesProp.length > 0 ? edgesProp : edgesState
  const [source, setSource] = useState(0)
  const [target, setTarget] = useState(3)
  const [timeIndex, setTimeIndex] = useState(0)
  const [mode, setMode] = useState('car')
  const [raceData, setRaceData] = useState<RaceResult | null>(null)
  const [step, setStep] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [speed, setSpeed] = useState(500) // ms per step
  const timerRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    if (!edgesProp || edgesProp.length === 0) {
      api.graphEdges().then(setEdgesState).catch(console.error)
    }
  }, [edgesProp])

  const startRace = useCallback(async () => {
    try {
      const data = await api.routeRace(source, target, timeIndex, mode)
      setRaceData(data)
      setStep(0)
      setPlaying(false)
    } catch (err) {
      console.error('Race API error:', err)
    }
  }, [source, target, timeIndex, mode])

  // Auto-play

  useEffect(() => {
    if (!playing || !raceData) return
    const maxSteps = Math.max(raceData.dijkstra.steps.length, raceData.astar.steps.length)
    timerRef.current = setInterval(() => {
      setStep(s => {
        if (s >= maxSteps - 1) {
          setPlaying(false)
          return maxSteps - 1
        }
        return s + 1
      })
    }, speed)
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [playing, raceData, speed])

  const dijkstraVisited = raceData ? raceData.dijkstra.steps[Math.min(step, raceData.dijkstra.steps.length - 1)]?.visited || [] : []
  const astarVisited = raceData ? raceData.astar.steps[Math.min(step, raceData.astar.steps.length - 1)]?.visited || [] : []
  const currentD = raceData && step < raceData.dijkstra.steps.length ? raceData.dijkstra.steps[step].current : undefined
  const currentA = raceData && step < raceData.astar.steps.length ? raceData.astar.steps[step].current : undefined

  const dijkstraDone = raceData ? step >= raceData.dijkstra.steps.length - 1 : false
  const astarDone = raceData ? step >= raceData.astar.steps.length - 1 : false

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="bg-[#16213e] rounded-xl p-4 border border-gray-800">
        <h2 className="text-lg font-bold mb-3 flex items-center gap-2">
          <Zap size={20} className="text-[#f5c518]" />
          Dijkstra vs A* Race Animation
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
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
              <option value="car">Car</option>
              <option value="emergency">Emergency</option>
              <option value="bus">Bus</option>
              <option value="metro">Metro</option>
            </select>
          </div>
          <div className="flex items-end">
            <button onClick={startRace}
              className="w-full bg-[#e94560] hover:bg-[#c73e54] text-white font-bold py-2 px-4 rounded-lg transition-colors">
              🏁 Start Race
            </button>
          </div>
        </div>
      </div>

      {/* Map with race visualization */}
      {raceData && (
        <>
          <MapView
            nodes={nodes}
            edges={edges}
            routeNodes={dijkstraDone ? raceData.dijkstra.path : []}
            routeColor="#1d3557"
            mstEdges={astarDone ? raceData.astar.path.map((id, i) => {
              const nextId = raceData.astar.path[i + 1]
              if (nextId === undefined) return null
              const edge = edges.find(e => (e.u === id && e.v === nextId) || (e.u === nextId && e.v === id))
              return edge
            }).filter(Boolean) as GraphEdge[] : []}
            mstColor="#e63946"
            visitedNodesDijkstra={[...new Set(dijkstraVisited)]}
            visitedNodesAstar={[...new Set(astarVisited)]}
            currentNodeDijkstra={currentD}
            currentNodeAstar={currentA}
            raceMode={mode}
            height="500px"
          />

          {/* Playback controls */}
          <div className="bg-[#16213e] rounded-xl p-4 border border-gray-800 flex items-center gap-4">
            <button onClick={() => setPlaying(!playing)}
              className="p-2 rounded-lg bg-[#1a1a2e] hover:bg-gray-700 transition-colors">
              {playing ? <Pause size={20} /> : <Play size={20} />}
            </button>
            <button onClick={() => setStep(s => Math.min(s + 1, Math.max(raceData.dijkstra.steps.length, raceData.astar.steps.length) - 1))}
              className="p-2 rounded-lg bg-[#1a1a2e] hover:bg-gray-700 transition-colors">
              <SkipForward size={20} />
            </button>
            <button onClick={() => { setStep(0); setPlaying(false) }}
              className="p-2 rounded-lg bg-[#1a1a2e] hover:bg-gray-700 transition-colors">
              <RotateCcw size={20} />
            </button>
            <div className="flex-1">
              <input type="range" min={0} max={Math.max(raceData.dijkstra.steps.length, raceData.astar.steps.length) - 1}
                value={step} onChange={e => setStep(Number(e.target.value))}
                className="w-full accent-[#e94560]" />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-400">Speed:</span>
              <select value={speed} onChange={e => setSpeed(Number(e.target.value))}
                className="bg-[#1a1a2e] border border-gray-700 rounded px-2 py-1 text-xs">
                <option value={1000}>0.5x</option>
                <option value={500}>1x</option>
                <option value={250}>2x</option>
                <option value={100}>5x</option>
              </select>
            </div>
            <span className="text-sm text-gray-400">Step {step + 1}</span>
          </div>

          {/* Side-by-side comparison */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-[#16213e] rounded-xl p-4 border-2 border-[#1d3557]">
              <h3 className="font-bold text-[#1d3557] mb-2">{mode === 'car' ? '�' : mode === 'bus' ? '🚌' : mode === 'metro' ? '🚇' : '🚑'} Dijkstra</h3>
              <div className="grid grid-cols-2 gap-2">
                <MetricCard label="Explored" value={dijkstraVisited.length} color="#1d3557" />
                <MetricCard label="Time" value={dijkstraDone && raceData.dijkstra.total_time ? `${raceData.dijkstra.total_time} min` : '...'} color="#1d3557" />
              </div>
              {dijkstraDone && raceData.dijkstra.path.length > 0 && (
                <p className="text-xs text-gray-400 mt-2">
                  Path: {raceData.dijkstra.path.map(id => nodes.find(n => n.id === id)?.name || id).join(' → ')}
                </p>
              )}
            </div>
            <div className="bg-[#16213e] rounded-xl p-4 border-2 border-[#e63946]">
              <h3 className="font-bold text-[#e63946] mb-2">{mode === 'car' ? '🚗' : mode === 'bus' ? '🚌' : mode === 'metro' ? '🚇' : '🚑'} A* Search</h3>
              <div className="grid grid-cols-2 gap-2">
                <MetricCard label="Explored" value={astarVisited.length} color="#e63946" />
                <MetricCard label="Time" value={astarDone && raceData.astar.total_time ? `${raceData.astar.total_time} min` : '...'} color="#e63946" />
              </div>
              {astarDone && raceData.astar.path.length > 0 && (
                <p className="text-xs text-gray-400 mt-2">
                  Path: {raceData.astar.path.map(id => nodes.find(n => n.id === id)?.name || id).join(' → ')}
                </p>
              )}
            </div>
          </div>

          {/* Winner banner */}
          {dijkstraDone && astarDone && (
            <div className="bg-gradient-to-r from-[#16213e] to-[#1a1a2e] rounded-xl p-4 border border-[#f5c518] text-center">
              {raceData.astar.nodes_explored < raceData.dijkstra.nodes_explored ? (
                <p className="text-xl font-bold text-[#f5c518]">
                  🏆 A* wins! Explored {raceData.dijkstra.nodes_explored - raceData.astar.nodes_explored} fewer nodes
                  ({((1 - raceData.astar.nodes_explored / raceData.dijkstra.nodes_explored) * 100).toFixed(0)}% less exploration)
                </p>
              ) : (
                <p className="text-xl font-bold text-[#3498db]">
                  🏆 Dijkstra wins on this route! Both explored similar nodes.
                </p>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
