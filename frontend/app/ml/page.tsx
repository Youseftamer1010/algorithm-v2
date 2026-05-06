'use client'

import { useState, useEffect } from 'react'
import Navbar from '@/components/Navbar'
import MetricCard from '@/components/MetricCard'
import { api, type MLPrediction } from '@/lib/api'

export default function MLPage() {
  const [hour, setHour] = useState(8)
  const [day, setDay] = useState(1)
  const [roadType, setRoadType] = useState(2)
  const [condition, setCondition] = useState(7)
  const [capacity, setCapacity] = useState(0.5)
  const [isHoliday, setIsHoliday] = useState(0)
  const [temperature, setTemperature] = useState(30)
  const [population, setPopulation] = useState(0.7)
  const [prediction, setPrediction] = useState<MLPrediction | null>(null)
  const [importance, setImportance] = useState<Record<string, number>>({})
  const [metrics, setMetrics] = useState<Record<string, unknown>>({})
  const [loading, setLoading] = useState(false)
  const [batchResults, setBatchResults] = useState<Array<{ label: string; congestion: number; level: string }>>([])

  useEffect(() => {
    api.mlFeatureImportance().then(setImportance).catch(console.error)
    api.mlMetrics().then(setMetrics).catch(console.error)
  }, [])

  const predict = async () => {
    setLoading(true)
    try {
      const p = await api.mlPredict({
        hour_of_day: hour, day_of_week: day, road_type: roadType,
        capacity_norm: capacity, road_condition: condition,
        is_holiday: isHoliday, temperature, population_norm: population,
      })
      setPrediction(p)
    } catch (err) { console.error(err) }
    setLoading(false)
  }

  const runBatch = async () => {
    setLoading(true)
    try {
      const scenarios = [
        { label: 'Mon 8am City', hour: 8, day: 1, rt: 2, cap: 0.5, cond: 7, hol: 0, temp: 30, pop: 0.7 },
        { label: 'Fri 20pm Highway', hour: 20, day: 5, rt: 0, cap: 0.8, cond: 8, hol: 0, temp: 28, pop: 0.3 },
        { label: 'Wed 13pm Main', hour: 13, day: 3, rt: 1, cap: 0.6, cond: 5, hol: 0, temp: 35, pop: 0.6 },
        { label: 'Sun 3am City', hour: 3, day: 6, rt: 2, cap: 0.4, cond: 6, hol: 1, temp: 22, pop: 0.8 },
        { label: 'Tue 18pm Metro', hour: 18, day: 2, rt: 3, cap: 0.9, cond: 9, hol: 0, temp: 32, pop: 0.5 },
        { label: 'Thu 9am Ring', hour: 9, day: 4, rt: 4, cap: 0.7, cond: 4, hol: 0, temp: 38, pop: 0.4 },
      ]
      const results = []
      for (const s of scenarios) {
        const p = await api.mlPredict({
          hour_of_day: s.hour, day_of_week: s.day, road_type: s.rt,
          capacity_norm: s.cap, road_condition: s.cond,
          is_holiday: s.hol, temperature: s.temp, population_norm: s.pop,
        })
        results.push({ label: s.label, congestion: p.congestion, level: p.level })
      }
      setBatchResults(results)
    } catch (err) { console.error(err) }
    setLoading(false)
  }

  const sortedImportance = Object.entries(importance).sort(([,a], [,b]) => b - a)
  const maxImp = sortedImportance.length > 0 ? sortedImportance[0][1] : 1

  return (
    <>
      <Navbar />
      <main className="pt-16 px-4 max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold mb-4">🧠 Rule-Based Traffic Model</h1>
        <p className="text-gray-400 mb-6">Congestion scoring based on time of day, road type, and day patterns</p>

        {/* Model Info */}
        <div className="bg-[#16213e] rounded-xl p-4 border border-gray-800 mb-4">
          <h3 className="font-bold mb-3">📈 Model Information</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <MetricCard label="Model Type" value="Rule-Based" color="#00b4d8" />
            <MetricCard label="Primary Factor" value="Time of Day" color="#e94560" />
            <MetricCard label="Secondary" value="Road Type" color="#f5c518" />
          </div>
          <p className="text-gray-400 text-sm mt-2">
            This model uses a rule-based formula: base score + time adjustment + road type adjustment + day type adjustment.
            Scores are clamped to 0.0-1.0 range.
          </p>
        </div>

        {/* Prediction Controls */}
        <div className="bg-[#16213e] rounded-xl p-4 border border-gray-800 mb-4">
          <h3 className="font-bold mb-3">🔮 Single Prediction</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div>
              <label className="text-xs text-gray-400">Hour (0-23)</label>
              <input type="number" min={0} max={23} value={hour}
                onChange={e => setHour(Number(e.target.value))}
                className="w-full bg-[#1a1a2e] border border-gray-700 rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="text-xs text-gray-400">Day (0=Mon)</label>
              <input type="number" min={0} max={6} value={day}
                onChange={e => setDay(Number(e.target.value))}
                className="w-full bg-[#1a1a2e] border border-gray-700 rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="text-xs text-gray-400">Road Type</label>
              <select value={roadType} onChange={e => setRoadType(Number(e.target.value))}
                className="w-full bg-[#1a1a2e] border border-gray-700 rounded-lg px-3 py-2 text-sm">
                <option value={0}>Highway</option>
                <option value={1}>Main Road</option>
                <option value={2}>City Road</option>
                <option value={3}>Metro Line</option>
                <option value={4}>Ring Road</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400">Condition (0-10)</label>
              <input type="number" min={0} max={10} step={0.5} value={condition}
                onChange={e => setCondition(Number(e.target.value))}
                className="w-full bg-[#1a1a2e] border border-gray-700 rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="text-xs text-gray-400">Capacity (0-1)</label>
              <input type="number" min={0} max={1} step={0.1} value={capacity}
                onChange={e => setCapacity(Number(e.target.value))}
                className="w-full bg-[#1a1a2e] border border-gray-700 rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="text-xs text-gray-400">Holiday?</label>
              <select value={isHoliday} onChange={e => setIsHoliday(Number(e.target.value))}
                className="w-full bg-[#1a1a2e] border border-gray-700 rounded-lg px-3 py-2 text-sm">
                <option value={0}>No</option>
                <option value={1}>Yes</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400">Temperature (°C)</label>
              <input type="number" min={15} max={45} value={temperature}
                onChange={e => setTemperature(Number(e.target.value))}
                className="w-full bg-[#1a1a2e] border border-gray-700 rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="text-xs text-gray-400">Population (0-1)</label>
              <input type="number" min={0} max={1} step={0.1} value={population}
                onChange={e => setPopulation(Number(e.target.value))}
                className="w-full bg-[#1a1a2e] border border-gray-700 rounded-lg px-3 py-2 text-sm" />
            </div>
            <div className="flex items-end col-span-2 md:col-span-1">
              <button onClick={predict} disabled={loading}
                className="w-full bg-[#e94560] hover:bg-[#c73e54] disabled:opacity-50 text-white font-bold py-2 px-4 rounded-lg">
                {loading ? '⏳ Predicting...' : '🔮 Predict'}
              </button>
            </div>
          </div>
        </div>

        {prediction && (
          <div className="bg-[#16213e] rounded-xl p-4 border border-gray-800 mb-4">
            <h3 className="font-bold mb-3">🔮 Prediction Result</h3>
            
            {/* Congestion Gauge */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">Congestion Score</span>
                <span className="text-2xl font-bold">{(prediction.congestion * 100).toFixed(1)}%</span>
              </div>
              <div className="w-full bg-[#1a1a2e] rounded-full h-6 overflow-hidden">
                <div 
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${prediction.congestion * 100}%`,
                    background: prediction.congestion < 0.3 
                      ? '#2ecc71' 
                      : prediction.congestion < 0.6 
                      ? '#f5c518' 
                      : prediction.congestion < 0.8 
                      ? '#e67e22' 
                      : '#e94560'
                  }} 
                />
              </div>
            </div>

            {/* Congestion Level */}
            <div className="grid grid-cols-3 gap-3">
              <div className="text-center">
                <div className={`text-3xl font-bold ${
                  prediction.level === 'Low' ? 'text-green-500' :
                  prediction.level === 'Moderate' ? 'text-yellow-500' :
                  prediction.level === 'High' ? 'text-orange-500' :
                  'text-red-500'
                }`}>
                  {prediction.level}
                </div>
                <div className="text-xs text-gray-400 mt-1">Congestion Level</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-400">
                  {prediction.congestion.toFixed(3)}
                </div>
                <div className="text-xs text-gray-400 mt-1">Raw Score</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-400">
                  {prediction.level === 'Low' ? '🟢' : prediction.level === 'Moderate' ? '🟡' : prediction.level === 'High' ? '🟠' : '🔴'}
                </div>
                <div className="text-xs text-gray-400 mt-1">Status</div>
              </div>
            </div>
          </div>
        )}

        {/* Batch Predictions */}
        <div className="bg-[#16213e] rounded-xl p-4 border border-gray-800 mb-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-bold">📊 Batch Scenario Comparison</h3>
            <button onClick={runBatch} disabled={loading}
              className="bg-[#00b4d8] hover:bg-[#0096b4] disabled:opacity-50 text-white font-bold py-1 px-4 rounded-lg text-sm">
              {loading ? '⏳ Running...' : '▶ Run All Scenarios'}
            </button>
          </div>
          {batchResults.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="text-left py-2 text-gray-400">Scenario</th>
                    <th className="text-right py-2 text-gray-400">Congestion</th>
                    <th className="text-right py-2 text-gray-400">Level</th>
                    <th className="text-right py-2 text-gray-400">Bar</th>
                  </tr>
                </thead>
                <tbody>
                  {batchResults.map((r, i) => (
                    <tr key={i} className="border-b border-gray-800">
                      <td className="py-2">{r.label}</td>
                      <td className="text-right py-2">{(r.congestion * 100).toFixed(1)}%</td>
                      <td className="text-right py-2">
                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                          r.level === 'Low' ? 'bg-green-900 text-green-300' :
                          r.level === 'Medium' ? 'bg-yellow-900 text-yellow-300' :
                          r.level === 'High' ? 'bg-orange-900 text-orange-300' :
                          'bg-red-900 text-red-300'}`}>{r.level}</span>
                      </td>
                      <td className="py-2">
                        <div className="w-full bg-[#1a1a2e] rounded-full h-3 overflow-hidden">
                          <div className="h-full rounded-full" style={{
                            width: `${r.congestion * 100}%`,
                            background: r.congestion < 0.3 ? '#2ecc71' : r.congestion < 0.6 ? '#f5c518' : r.congestion < 0.8 ? '#e67e22' : '#e94560'
                          }} />
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Feature Importance */}
        {sortedImportance.length > 0 && (
          <div className="bg-[#16213e] rounded-xl p-4 border border-gray-800">
            <h3 className="font-bold mb-3">📊 Feature Weights (Rule-Based)</h3>
            <div className="space-y-2">
              {sortedImportance.map(([feature, imp]) => (
                <div key={feature} className="flex items-center gap-3">
                  <span className="text-sm text-gray-400 w-36">{feature.replace(/_/g, ' ').replace(/day_type/g, 'day type')}</span>
                  <div className="flex-1 bg-[#1a1a2e] rounded-full h-4 overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-[#e94560] to-[#f5c518] rounded-full"
                      style={{ width: `${(imp / maxImp) * 100}%` }} />
                  </div>
                  <span className="text-xs text-gray-400 w-12 text-right">{imp > 0 ? (imp * 100).toFixed(1) : '0'}%</span>
                </div>
              ))}
            </div>
            <p className="text-gray-400 text-sm mt-3">
              Only features used in the rule-based formula have non-zero weights.
            </p>
          </div>
        )}
        <div className="h-8" />
      </main>
    </>
  )
}
