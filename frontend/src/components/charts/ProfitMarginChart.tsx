import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from 'recharts'
import type { TimeSeriesPoint } from '../../types'
import { formatINR, formatPct } from '../../utils/format'

interface ProfitMarginChartProps {
  profitData: TimeSeriesPoint[]
  marginData: TimeSeriesPoint[]
  height?: number
}

// Merge profit + margin arrays by date
function mergeData(
  profitData: TimeSeriesPoint[],
  marginData: TimeSeriesPoint[]
): Array<{ date: string; profit: number; margin: number }> {
  const map = new Map<string, { profit: number; margin: number }>()
  profitData.forEach(p => map.set(p.date, { profit: p.value, margin: 0 }))
  marginData.forEach(p => {
    const existing = map.get(p.date)
    if (existing) existing.margin = p.value
    else map.set(p.date, { profit: 0, margin: p.value })
  })
  return Array.from(map.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, vals]) => ({ date, ...vals }))
}

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ name: string; value: number }>; label?: string }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-slate-200 rounded-md shadow-md p-3 text-sm">
      <p className="text-slate-500 mb-1">{label}</p>
      {payload.map(p => (
        <p key={p.name} className="font-semibold text-slate-800">
          {p.name === 'Profit' ? formatINR(p.value) : formatPct(p.value)}
        </p>
      ))}
    </div>
  )
}

export default function ProfitMarginChart({ profitData, marginData, height = 280 }: ProfitMarginChartProps) {
  const merged = mergeData(profitData, marginData)

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={merged} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#94a3b8' }} tickLine={false} axisLine={false} />
        <YAxis
          yAxisId="profit"
          tickFormatter={v => formatINR(v, true)}
          tick={{ fontSize: 11, fill: '#94a3b8' }}
          tickLine={false}
          axisLine={false}
          width={60}
        />
        <YAxis
          yAxisId="margin"
          orientation="right"
          tickFormatter={v => `${v}%`}
          tick={{ fontSize: 11, fill: '#94a3b8' }}
          tickLine={false}
          axisLine={false}
          width={40}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Line yAxisId="profit" type="monotone" dataKey="profit" name="Profit" stroke="#2563eb" strokeWidth={2} dot={false} />
        <Line yAxisId="margin" type="monotone" dataKey="margin" name="Margin %" stroke="#16a34a" strokeWidth={2} dot={false} strokeDasharray="5 3" />
      </LineChart>
    </ResponsiveContainer>
  )
}
