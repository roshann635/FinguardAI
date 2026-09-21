import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from 'recharts'
import type { ReceivablesAging } from '../../types'
import { formatINR } from '../../utils/format'

interface AgingChartProps {
  data: ReceivablesAging
  height?: number
}

const BUCKETS = [
  { key: 'current' as const, label: 'Current', color: '#16a34a' },
  { key: 'days_1_30' as const, label: '1–30 Days', color: '#65a30d' },
  { key: 'days_31_60' as const, label: '31–60 Days', color: '#d97706' },
  { key: 'days_61_90' as const, label: '61–90 Days', color: '#ea580c' },
  { key: 'days_over_90' as const, label: '90+ Days', color: '#dc2626' },
]

function CustomTooltip({ active, payload }: { active?: boolean; payload?: Array<{ name: string; value: number }> }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-slate-200 rounded-md shadow-md p-3 text-sm">
      <p className="text-slate-500 mb-1">{payload[0].name}</p>
      <p className="font-semibold text-slate-800">{formatINR(payload[0].value)}</p>
    </div>
  )
}

export default function AgingChart({ data, height = 280 }: AgingChartProps) {
  const chartData = BUCKETS.map(b => ({ name: b.label, value: data[b.key], color: b.color }))

  return (
    <div>
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            paddingAngle={2}
            dataKey="value"
          >
            {chartData.map((entry, idx) => (
              <Cell key={idx} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
        </PieChart>
      </ResponsiveContainer>

      {/* Aging Summary Table */}
      <div className="mt-2 border border-slate-100 rounded-md overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 text-xs text-slate-500">
              <th className="text-left px-3 py-2 font-medium">Bucket</th>
              <th className="text-right px-3 py-2 font-medium">Amount</th>
              <th className="text-right px-3 py-2 font-medium">% of Total</th>
            </tr>
          </thead>
          <tbody>
            {BUCKETS.map(b => {
              const pct = data.total ? ((data[b.key] / data.total) * 100).toFixed(1) : '0.0'
              return (
                <tr key={b.key} className="border-t border-slate-100">
                  <td className="px-3 py-2 flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ background: b.color }} />
                    {b.label}
                  </td>
                  <td className="px-3 py-2 text-right font-medium">{formatINR(data[b.key])}</td>
                  <td className="px-3 py-2 text-right text-slate-500">{pct}%</td>
                </tr>
              )
            })}
            <tr className="border-t-2 border-slate-200 font-semibold bg-slate-50">
              <td className="px-3 py-2">Total</td>
              <td className="px-3 py-2 text-right">{formatINR(data.total)}</td>
              <td className="px-3 py-2 text-right">100%</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}
