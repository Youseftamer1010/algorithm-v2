'use client'

import { useState, useEffect } from 'react'
import Navbar from '@/components/Navbar'
import MetricCard from '@/components/MetricCard'
import { api, type MetricData } from '@/lib/api'

const TIME_LABELS = ['Morning (7-9am)', 'Afternoon (12-2pm)', 'Evening (5-8pm)', 'Night (10pm-1am)']
const SCENARIOS = ['normal', 'morning_rush', 'road_closure', 'emergency', 'peak_chaos']

export default function SimulationPage() {
  const [scenario, setScenario] = useState('normal')
  const [metrics, setMetrics] = useState<Record<number, MetricData>>({})

  useEffect(() => {
    Promise.all(TIME_LABELS.map((_, i) => api.simMetrics(i, scenario)))
      .then(results => {
        const m: Record<number, MetricData> = {}
        results.forEach((r, i) => { m[i] = r })
        setMetrics(m)
      })
      .catch(console.error)
  }, [scenario])

  return (
    <>
      <Navbar />
      <main className="pt-16 px-4 max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold mb-4">📊 Traffic Simulation</h1>

        <div className="bg-[#16213e] rounded-xl p-4 border border-gray-800 mb-4">
          <label className="text-xs text-gray-400">Scenario</label>
          <select value={scenario} onChange={e => setScenario(e.target.value)}
            className="w-full bg-[#1a1a2e] border border-gray-700 rounded-lg px-3 py-2 text-sm mt-1">
            {SCENARIOS.map(s => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
          </select>
        </div>

        <div className="space-y-3">
          {TIME_LABELS.map((label, i) => {
            const m = metrics[i]
            if (!m) return <div key={i} className="text-gray-500">Loading {label}...</div>
            return (
              <div key={i} className="bg-[#16213e] rounded-xl p-4 border border-gray-800">
                <h3 className="font-semibold mb-2">{label}</h3>
                <div className="grid grid-cols-4 gap-2">
                  <MetricCard label="Avg Congestion" value={`${(m.avg_congestion * 100).toFixed(0)}%`} color="#e94560" />
                  <MetricCard label="Network Score" value={`${m.network_score}`} color="#00b4d8" />
                  <MetricCard label="Free Flow" value={m.free_flow} color="#2ecc71" />
                  <MetricCard label="Gridlock" value={m.gridlock} color="#f5c518" />
                </div>
              </div>
            )
          })}
        </div>

        {/* Greedy Analysis */}
        <div className="bg-[#16213e] rounded-xl p-4 border border-gray-800 mt-4">
          <h3 className="font-bold mb-2">⚖️ Greedy Optimality Analysis</h3>
          <p className="text-gray-400 text-sm">The traffic signal optimization uses a greedy approach. Run <code className="bg-[#1a1a2e] px-1 rounded">python main.py</code> to see the full greedy optimality analysis comparing greedy vs. optimal solutions at each intersection.</p>
        </div>

        {/* Road Maintenance */}
        <div className="bg-[#16213e] rounded-xl p-4 border border-gray-800 mt-4">
          <h3 className="font-bold mb-2">🛣️ Road Maintenance (DP)</h3>
          <p className="text-gray-400 text-sm">Visit the Transit page to adjust bus fleet DP scheduling, or use the API endpoint <code className="bg-[#1a1a2e] px-1 rounded">/api/optimization/maintenance</code> to test DP road maintenance with different budgets.</p>
        </div>
        <div className="h-8" />
      </main>
    </>
  )
}
