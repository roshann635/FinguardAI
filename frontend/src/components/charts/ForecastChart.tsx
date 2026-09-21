import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ReferenceLine,
} from 'recharts'
import type { ForecastPoint } from '../../types'
import { formatINR } from '../../utils/format'

interface ForecastChartProps {
  data: ForecastPoint[]
  height?: number
}

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ name: string; value: number; color: string }>; label?: string }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-slate-200 rounded-md shadow-md p-3 text-sm">
      <p className="text-slate-500 mb-2">{label}</p>
      {payload
        .filter(p => p.value !== undefined && p.name !== 'Uncertainty Range')
        .map(p => (
          <div key={p.name} className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
            <span className="text-slate-600">{p.name}:</span>
            <span className="font-semibold text-slate-800">{formatINR(p.value)}</span>
          </div>
        ))}
    </div>
  )
}

export default function ForecastChart({ data, height = 320 }: ForecastChartProps) {
  // Find where actuals end (first forecast point)
  const splitDate = data.find(d => d.is_forecast)?.date

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={data} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
        <defs>
          <linearGradient id="confidenceGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#93c5fd" stopOpacity={0.4} />
            <stop offset="95%" stopColor="#93c5fd" stopOpacity={0.05} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#94a3b8' }} tickLine={false} axisLine={false} />
        <YAxis tickFormatter={v => formatINR(v, true)} tick={{ fontSize: 11, fill: '#94a3b8' }} tickLine={false} axisLine={false} width={65} />
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ fontSize: 12 }} />

        {splitDate && (
          <ReferenceLine
            x={splitDate}
            stroke="#94a3b8"
            strokeDasharray="6 3"
            label={{ value: 'Forecast Start', position: 'top', fontSize: 10, fill: '#94a3b8' }}
          />
        )}

        {/* Confidence interval area */}
        <Area
          type="monotone"
          dataKey="upper_bound"
          name="Uncertainty Range"
          fill="url(#confidenceGrad)"
          stroke="none"
          legendType="none"
        />
        <Area
          type="monotone"
          dataKey="lower_bound"
          fill="white"
          stroke="none"
          legendType="none"
        />

        {/* Actual line */}
        <Line
          type="monotone"
          dataKey="actual"
          name="Actual"
          stroke="#2563eb"
          strokeWidth={2}
          dot={false}
          connectNulls={false}
        />

        {/* Forecast line */}
        <Line
          type="monotone"
          dataKey="forecast"
          name="Forecast"
          stroke="#2563eb"
          strokeWidth={2}
          strokeDasharray="6 3"
          dot={false}
          connectNulls={false}
        />
      </ComposedChart>
    </ResponsiveContainer>
  )
}
