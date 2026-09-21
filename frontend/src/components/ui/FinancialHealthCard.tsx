import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Activity, ArrowUpRight, ChevronRight } from 'lucide-react'
import { fetchFinancialHealthScore } from '../../services/api'
import type { FinancialHealthScore, HealthPillar } from '../../types'


function getGradeColor(grade: string) {
  switch (grade) {
    case 'A':
      return {
        bg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
        ring: 'text-emerald-600',
        bar: 'bg-emerald-500',
      }
    case 'B':
      return {
        bg: 'bg-blue-50 text-blue-700 border-blue-200',
        ring: 'text-blue-600',
        bar: 'bg-blue-500',
      }
    case 'C':
      return {
        bg: 'bg-amber-50 text-amber-700 border-amber-200',
        ring: 'text-amber-600',
        bar: 'bg-amber-500',
      }
    default:
      return {
        bg: 'bg-red-50 text-red-700 border-red-200',
        ring: 'text-red-600',
        bar: 'bg-red-500',
      }
  }
}

function getStatusBadge(status: string) {
  switch (status) {
    case 'Excellent':
      return 'bg-emerald-100 text-emerald-800'
    case 'Good':
      return 'bg-blue-100 text-blue-800'
    case 'Fair':
      return 'bg-amber-100 text-amber-800'
    default:
      return 'bg-red-100 text-red-800'
  }
}

export default function FinancialHealthCard() {
  const [data, setData] = useState<FinancialHealthScore | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activePillar, setActivePillar] = useState<string | null>(null)

  useEffect(() => {
    fetchFinancialHealthScore()
      .then(setData)
      .catch(e => setError(e instanceof Error ? e.message : 'Unable to load health score'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs animate-pulse">
        <div className="h-4 bg-slate-200 rounded w-1/3 mb-4" />
        <div className="h-16 bg-slate-100 rounded mb-4" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-12 bg-slate-100 rounded" />
          ))}
        </div>
      </div>
    )
  }

  if (error || !data) {
    return null
  }

  const colors = getGradeColor(data.grade)
  const pillarList: Array<{ key: string; pillar: HealthPillar }> = [
    { key: 'liquidity', pillar: data.pillars.liquidity },
    { key: 'profitability', pillar: data.pillars.profitability },
    { key: 'credit', pillar: data.pillars.credit },
    { key: 'stability', pillar: data.pillars.stability },
  ]

  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 bg-gradient-to-r from-slate-900 to-slate-800 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-indigo-500/20 border border-indigo-400/30 flex items-center justify-center">
            <Activity className="text-indigo-400" size={18} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold tracking-wide uppercase">Financial Health Index</h2>
              <span className="text-[10px] bg-indigo-500/30 text-indigo-200 border border-indigo-400/30 px-2 py-0.5 rounded-full font-semibold">
                Composite Score
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-0.5">
              Multi-pillar solvency, margin defense, and credit quality evaluation
            </p>
          </div>
        </div>

        <Link
          to="/methodology"
          className="inline-flex items-center gap-1.5 text-xs text-slate-300 hover:text-white font-medium transition-colors"
        >
          <span>Methodology & Weights</span>
          <ChevronRight size={14} />
        </Link>
      </div>

      {/* Main Score & Pillars */}
      <div className="p-5">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
          {/* Left: Big Score & Grade */}
          <div className="lg:col-span-4 flex items-center gap-5 border-b lg:border-b-0 lg:border-r border-slate-200 pb-5 lg:pb-0 lg:pr-5">
            <div className="flex-shrink-0 w-20 h-20 rounded-2xl bg-slate-50 border-2 border-slate-200 flex flex-col items-center justify-center shadow-inner">
              <span className="text-2xl font-black text-slate-900 leading-none tracking-tight">
                {data.composite_score}
              </span>
              <span className="text-[10px] font-bold text-slate-500 uppercase mt-0.5">/ 100</span>
            </div>

            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className={`text-xs font-extrabold px-2.5 py-0.5 rounded-full border ${colors.bg}`}>
                  Grade {data.grade}
                </span>
                <span className="text-xs font-semibold text-slate-700">{data.status}</span>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed pr-2">
                {data.summary}
              </p>
            </div>
          </div>

          {/* Right: 4 Pillar Breakdown */}
          <div className="lg:col-span-8 grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            {pillarList.map(({ key, pillar }) => {
              const isSelected = activePillar === key
              return (
                <div
                  key={key}
                  onClick={() => setActivePillar(isSelected ? null : key)}
                  className={`p-3 rounded-lg border transition-all cursor-pointer ${
                    isSelected
                      ? 'border-indigo-300 bg-indigo-50/40 shadow-xs'
                      : 'border-slate-200 hover:border-slate-300 bg-slate-50/50 hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-bold text-slate-800">{pillar.name}</span>
                      <span className="text-[10px] text-slate-400 font-medium">({pillar.weight_pct}%)</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-extrabold text-slate-900">{pillar.score}</span>
                      <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded ${getStatusBadge(pillar.status)}`}>
                        {pillar.status}
                      </span>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="w-full h-1.5 bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        pillar.score >= 80 ? 'bg-emerald-500' : pillar.score >= 65 ? 'bg-blue-500' : pillar.score >= 50 ? 'bg-amber-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${Math.min(100, Math.max(0, pillar.score))}%` }}
                    />
                  </div>

                  {/* Metrics preview */}
                  <div className="mt-2 pt-2 border-t border-slate-200/60 flex items-center justify-between text-[11px] text-slate-500">
                    <span>{pillar.metrics[0]?.label}: <strong className="text-slate-700">{pillar.metrics[0]?.value}</strong></span>
                    <span className="text-[10px] text-indigo-600 font-medium hover:underline flex items-center gap-0.5">
                      {isSelected ? 'Hide' : 'Details'} <ArrowUpRight size={10} />
                    </span>
                  </div>

                  {/* Expanded Pillar Metrics Drawer */}
                  {isSelected && (
                    <div className="mt-2.5 pt-2 border-t border-indigo-100 space-y-1.5">
                      {pillar.metrics.map((m, idx) => (
                        <div key={idx} className="flex items-center justify-between text-[11px] bg-white px-2 py-1 rounded border border-indigo-100">
                          <span className="text-slate-600">{m.label}</span>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-slate-900">{m.value}</span>
                            <span className="text-[10px] text-slate-400">Target: {m.benchmark}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
