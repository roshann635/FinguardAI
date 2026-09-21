import {
  ResponsiveContainer,
  BarChart,
  Bar,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from 'recharts'
import type { CategoryBreakdown } from '../../types'
import { formatINR } from '../../utils/format'

const COLORS = [
  '#2563eb', '#7c3aed', '#0891b2', '#16a34a', '#d97706',
  '#dc2626', '#0d9488', '#9333ea', '#ea580c', '#1d4ed8',
]

interface CategoryBarChartProps {
  data: CategoryBreakdown[]
  valueLabel?: string
  colorScheme?: string
  height?: number
  horizontal?: boolean
}

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ value: number }>; label?: string }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-slate-200 rounded-md shadow-md p-3 text-sm">
      <p className="text-slate-500 mb-1">{label}</p>
      <p className="font-semibold text-slate-800">{formatINR(payload[0].value)}</p>
    </div>
  )
}

export default function CategoryBarChart({ data, valueLabel = 'Value', height = 280, horizontal = true }: CategoryBarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart
        data={data}
        layout={horizontal ? 'vertical' : 'horizontal'}
        margin={{ top: 4, right: 16, left: horizontal ? 80 : 0, bottom: 4 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={!horizontal} vertical={horizontal} />
        {horizontal ? (
          <>
            <XAxis type="number" tickFormatter={v => formatINR(v, true)} tick={{ fontSize: 11, fill: '#94a3b8' }} tickLine={false} axisLine={false} />
            <YAxis type="category" dataKey="category" tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} axisLine={false} width={80} />
          </>
        ) : (
          <>
            <XAxis dataKey="category" tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} axisLine={false} />
            <YAxis tickFormatter={v => formatINR(v, true)} tick={{ fontSize: 11, fill: '#94a3b8' }} tickLine={false} axisLine={false} />
          </>
        )}
        <Tooltip content={<CustomTooltip />} />
        <Bar dataKey="value" name={valueLabel} radius={[0, 3, 3, 0]}>
          {data.map((_, idx) => (
            <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
