interface MetricCardProps {
  label: string
  value: string | number
  unit?: string
  color?: string
  icon?: string
}

export default function MetricCard({ label, value, unit = '', color = '#e94560', icon = '' }: MetricCardProps) {
  return (
    <div className="bg-[#16213e] rounded-xl p-4 border border-gray-800 hover:border-gray-600 transition-colors">
      <div className="flex items-center gap-2 mb-1">
        {icon && <span className="text-lg">{icon}</span>}
        <span className="text-xs text-gray-400 uppercase tracking-wider">{label}</span>
      </div>
      <div className="text-2xl font-bold" style={{ color }}>
        {value}
        {unit && <span className="text-sm text-gray-400 ml-1">{unit}</span>}
      </div>
    </div>
  )
}
