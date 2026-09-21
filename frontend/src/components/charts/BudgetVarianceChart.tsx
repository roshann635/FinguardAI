import {
  ResponsiveContainer,
  BarChart,
  Bar,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  Cell,
} from 'recharts'
import type { BudgetVarianceItem } from '../../types'
import { formatINR } from '../../utils/format'

interface BudgetVarianceChartProps {
  data: BudgetVarianceItem[]
  height?: number
}

function statusColor(status: BudgetVarianceItem['status']) {
  if (status === 'under') return '#16a34a'
  if (status === 'near') return '#d97706'
  return '#dc2626'
}

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ name: string; value: number }>; label?: string }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-slate-200 rounded-md shadow-md p-3 text-sm">
      <p className="text-slate-600 font-medium mb-2">{label}</p>
      {payload.map(p => (
        <div key={p.name} className="flex justify-between gap-4">
          <span className="text-slate-500">{p.name}</span>
          <span className="font-semibold text-slate-800">{formatINR(p.value)}</span>
        </div>
      ))}
    </div>
  )
}

export default function BudgetVarianceChart({ data, height = 320 }: BudgetVarianceChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 4, right: 16, left: 0, bottom: 60 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis
          dataKey="category"
          tick={{ fontSize: 11, fill: '#64748b' }}
          tickLine={false}
          axisLine={false}
          angle={-35}
          textAnchor="end"
          interval={0}
        />
        <YAxis tickFormatter={v => formatINR(v, true)} tick={{ fontSize: 11, fill: '#94a3b8' }} tickLine={false} axisLine={false} width={65} />
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="budget" name="Budget" fill="#cbd5e1" radius={[2, 2, 0, 0]} />
        <Bar dataKey="actual" name="Actual" radius={[2, 2, 0, 0]}>
          {data.map((row, idx) => (
            <Cell key={idx} fill={statusColor(row.status)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
