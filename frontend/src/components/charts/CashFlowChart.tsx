import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from 'recharts'
import { formatINR } from '../../utils/format'

interface CashFlowPoint {
  date: string
  inflow: number
  outflow: number
  net: number
}

interface CashFlowChartProps {
  data: CashFlowPoint[]
  height?: number
}

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ name: string; value: number; color: string }>; label?: string }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-slate-200 rounded-md shadow-md p-3 text-sm">
      <p className="text-slate-500 mb-2">{label}</p>
      {payload.map(p => (
        <div key={p.name} className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="text-slate-600">{p.name}:</span>
          <span className="font-semibold text-slate-800">{formatINR(p.value)}</span>
        </div>
      ))}
    </div>
  )
}

export default function CashFlowChart({ data, height = 280 }: CashFlowChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={data} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#94a3b8' }} tickLine={false} axisLine={false} />
        <YAxis tickFormatter={v => formatINR(v, true)} tick={{ fontSize: 11, fill: '#94a3b8' }} tickLine={false} axisLine={false} width={65} />
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="inflow" name="Inflow" fill="#16a34a" opacity={0.8} radius={[2, 2, 0, 0]} />
        <Bar dataKey="outflow" name="Outflow" fill="#dc2626" opacity={0.8} radius={[2, 2, 0, 0]} />
        <Line type="monotone" dataKey="net" name="Net" stroke="#2563eb" strokeWidth={2} dot={false} />
      </ComposedChart>
    </ResponsiveContainer>
  )
}
