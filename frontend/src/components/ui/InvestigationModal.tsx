import { useState, useEffect } from 'react'
import { X, Search, CheckCircle2, TrendingUp, ShieldCheck, ArrowRight, Loader2 } from 'lucide-react'
import { fetchInvestigation } from '../../services/api'
import type { InvestigationResult } from '../../types'

interface InvestigationModalProps {
  kpi: string | null
  period?: string
  onClose: () => void
}

export default function InvestigationModal({ kpi, period = 'last_12_months', onClose }: InvestigationModalProps) {
  const [data, setData] = useState<InvestigationResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'why' | 'evidence' | 'actions'>('why')

  useEffect(() => {
    if (!kpi) return
    setLoading(true)
    setError(null)
    fetchInvestigation(kpi, period)
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : 'Investigation failed'))
      .finally(() => setLoading(false))
  }, [kpi, period])

  if (!kpi) return null

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-primary-100 text-primary-700 flex items-center justify-center font-bold">
              <Search size={18} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-slate-800">
                  {data?.kpi_label ?? `Investigating ${kpi.toUpperCase()}`}
                </h2>
                <span className="text-xs bg-indigo-50 text-indigo-700 font-medium px-2 py-0.5 rounded-full border border-indigo-200">
                  Investigation Mode
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Root-cause analytics grounded in verified data through 31 Mar 2025
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-md hover:bg-slate-200 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {loading ? (
            <div className="py-16 flex flex-col items-center justify-center gap-3 text-slate-500">
              <Loader2 size={28} className="animate-spin text-primary-600" />
              <p className="text-sm font-medium">Synthesizing root-cause drivers & audit evidence…</p>
            </div>
          ) : error ? (
            <div className="p-4 bg-red-50 text-red-700 rounded-lg text-sm border border-red-200">
              {error}
            </div>
          ) : data ? (
            <>
              {/* 1. What Changed? Box */}
              <div className="bg-slate-900 text-white rounded-lg p-5">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                  1. What Changed?
                </p>
                <h3 className="text-base font-bold text-white mb-3">
                  {data.what_changed.headline}
                </h3>
                <div className="grid grid-cols-3 gap-3 mb-3 text-xs">
                  <div className="bg-slate-800/80 rounded p-2.5">
                    <span className="text-slate-400 block">Current Period</span>
                    <span className="text-base font-bold text-white mt-0.5 block">{data.what_changed.current_metric}</span>
                  </div>
                  <div className="bg-slate-800/80 rounded p-2.5">
                    <span className="text-slate-400 block">Baseline / Target</span>
                    <span className="text-base font-bold text-slate-300 mt-0.5 block">{data.what_changed.baseline_metric}</span>
                  </div>
                  <div className="bg-slate-800/80 rounded p-2.5">
                    <span className="text-slate-400 block">Observed Variance</span>
                    <span className="text-base font-bold text-amber-400 mt-0.5 block">{data.what_changed.variance}</span>
                  </div>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {data.what_changed.summary}
                </p>
              </div>

              {/* Navigation Tabs */}
              <div className="flex border-b border-slate-200 text-sm gap-6">
                <button
                  onClick={() => setActiveTab('why')}
                  className={`pb-2.5 font-semibold transition-colors border-b-2 flex items-center gap-1.5 ${
                    activeTab === 'why'
                      ? 'border-primary-600 text-primary-700'
                      : 'border-transparent text-slate-500 hover:text-slate-700'
                  }`}
                >
                  <TrendingUp size={15} /> 2. Why Did It Change? ({data.why_it_changed.length})
                </button>
                <button
                  onClick={() => setActiveTab('evidence')}
                  className={`pb-2.5 font-semibold transition-colors border-b-2 flex items-center gap-1.5 ${
                    activeTab === 'evidence'
                      ? 'border-primary-600 text-primary-700'
                      : 'border-transparent text-slate-500 hover:text-slate-700'
                  }`}
                >
                  <ShieldCheck size={15} /> 3. Verified Evidence ({data.evidence.length})
                </button>
                <button
                  onClick={() => setActiveTab('actions')}
                  className={`pb-2.5 font-semibold transition-colors border-b-2 flex items-center gap-1.5 ${
                    activeTab === 'actions'
                      ? 'border-primary-600 text-primary-700'
                      : 'border-transparent text-slate-500 hover:text-slate-700'
                  }`}
                >
                  <CheckCircle2 size={15} /> 4. What Should Management Do? ({data.what_management_should_do.length})
                </button>
              </div>

              {/* Tab Content: Why Did It Change */}
              {activeTab === 'why' && (
                <div className="space-y-3">
                  {data.why_it_changed.map((item) => (
                    <div key={item.rank} className="border border-slate-200 rounded-lg p-4 bg-white hover:border-slate-300 transition-colors">
                      <div className="flex items-start justify-between gap-2 mb-1.5">
                        <div className="flex items-center gap-2">
                          <span className="w-5 h-5 rounded-full bg-slate-100 text-slate-700 font-bold text-xs flex items-center justify-center">
                            {item.rank}
                          </span>
                          <h4 className="text-sm font-bold text-slate-800">{item.title}</h4>
                        </div>
                        <span className="text-xs font-semibold px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200">
                          {item.impact}
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 leading-relaxed mb-2 pl-7">
                        {item.explanation}
                      </p>
                      <div className="pl-7 flex items-center gap-1.5 text-[11px] font-medium text-slate-500">
                        <span className="text-slate-400">Verified Driver:</span>
                        <code className="bg-slate-100 px-1.5 py-0.5 rounded text-slate-700">{item.verified_metric}</code>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Tab Content: Evidence */}
              {activeTab === 'evidence' && (
                <div className="space-y-3">
                  <div className="border border-slate-200 rounded-lg overflow-hidden">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase">
                        <tr>
                          <th className="px-4 py-2.5">Source</th>
                          <th className="px-4 py-2.5">Metric</th>
                          <th className="px-4 py-2.5">Observed Value</th>
                          <th className="px-4 py-2.5">Analytical Baseline</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 text-slate-700">
                        {data.evidence.map((ev, i) => (
                          <tr key={i} className="hover:bg-slate-50">
                            <td className="px-4 py-3 font-medium text-slate-800">{ev.source}</td>
                            <td className="px-4 py-3">{ev.metric}</td>
                            <td className="px-4 py-3 font-semibold text-primary-700">{ev.value}</td>
                            <td className="px-4 py-3 text-slate-500">{ev.benchmark}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className="text-[11px] text-slate-500 italic">
                    All metrics verified through analytical SQL queries against the local deterministic dataset. Zero extrapolation.
                  </p>
                </div>
              )}

              {/* Tab Content: Actions */}
              {activeTab === 'actions' && (
                <div className="space-y-3">
                  {data.what_management_should_do.map((act, i) => (
                    <div key={i} className="border border-slate-200 rounded-lg p-4 bg-white flex items-start gap-3">
                      <div className="w-7 h-7 rounded-md bg-emerald-50 text-emerald-600 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <ArrowRight size={15} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <h4 className="text-sm font-bold text-slate-800">{act.action}</h4>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            act.priority === 'HIGH' ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-slate-100 text-slate-700'
                          }`}>
                            {act.priority} PRIORITY
                          </span>
                        </div>
                        <p className="text-xs text-slate-600 mb-2">{act.rationale}</p>
                        <div className="flex flex-wrap items-center gap-4 text-[11px] text-slate-500">
                          <span>Owner: <strong className="text-slate-700">{act.owner}</strong></span>
                          <span>Benefit: <strong className="text-emerald-700">{act.expected_benefit}</strong></span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : null}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-200 bg-slate-50 flex items-center justify-between text-xs text-slate-500">
          <span>Data through: 31 Mar 2025</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-slate-800 hover:bg-slate-900 text-white rounded font-medium transition-colors"
          >
            Close Investigation
          </button>
        </div>

      </div>
    </div>
  )
}
