import { useState, useEffect, useCallback } from 'react'
import { Brain, Search, ShieldAlert, TrendingUp, CheckCircle2, ArrowRight, Sparkles } from 'lucide-react'
import { fetchDashboardOverview, askAI } from '../services/api'
import type { DashboardOverview, AIResponse } from '../types'
import KPICard from '../components/ui/KPICard'
import InsightCardComponent from '../components/ui/InsightCard'
import LoadingSkeleton from '../components/ui/LoadingSkeleton'
import ErrorState from '../components/ui/ErrorState'
import RiskBadge from '../components/ui/RiskBadge'
import RevenueChart from '../components/charts/RevenueChart'
import CashFlowChart from '../components/charts/CashFlowChart'
import BudgetVarianceChart from '../components/charts/BudgetVarianceChart'
import InvestigationModal from '../components/ui/InvestigationModal'
import FinancialHealthCard from '../components/ui/FinancialHealthCard'
import { useFilters } from '../components/layout/Layout'

import { formatUSD } from '../utils/format'

export default function Overview() {
  const { period } = useFilters()
  const [data, setData] = useState<DashboardOverview | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Investigation Mode
  const [investigatingKPI, setInvestigatingKPI] = useState<string | null>(null)

  // AI quick-ask
  const [aiQuestion, setAiQuestion] = useState('')
  const [aiLoading, setAiLoading] = useState(false)
  const [aiResponse, setAiResponse] = useState<AIResponse | null>(null)
  const [aiError, setAiError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await fetchDashboardOverview(period)
      setData(result)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }, [period])

  useEffect(() => { load() }, [load])

  const handleAsk = async (presetQuestion?: string) => {
    const q = presetQuestion ?? aiQuestion
    if (!q.trim()) return
    setAiLoading(true)
    setAiError(null)
    try {
      const res = await askAI(q, period)
      setAiResponse(res)
      if (presetQuestion) setAiQuestion(presetQuestion)
    } catch (e) {
      setAiError(e instanceof Error ? e.message : 'AI analysis failed')
    } finally {
      setAiLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Executive Financial Overview</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Dynamic financial intelligence & decision support · Data through: 31 Mar 2025
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setInvestigatingKPI('profit')}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 text-xs font-semibold rounded-md transition-colors"
          >
            <Search size={13} />
            Investigation Mode
          </button>
          <span className="bg-slate-100 text-slate-600 text-xs font-semibold px-2.5 py-1 rounded-full border border-slate-200">
            Jan 2023 – Mar 2025
          </span>
        </div>
      </div>

      {/* KPI Grid with "Why?" Drilldowns */}
      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="bg-white border border-slate-200 rounded-lg p-5 space-y-3">
              <LoadingSkeleton height="h-3" width="w-24" />
              <LoadingSkeleton height="h-8" width="w-32" />
              <LoadingSkeleton height="h-3" width="w-20" />
            </div>
          ))}
        </div>
      ) : error ? (
        <ErrorState message={error} retry={load} />
      ) : data ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { title: 'Total Revenue', kpi: data.kpis.total_revenue, key: 'revenue' },
            { title: 'Total Profit', kpi: data.kpis.total_profit ?? (data.kpis as any).net_profit, key: 'profit' },
            { title: 'Profit Margin', kpi: data.kpis.profit_margin, key: 'profit' },
            { title: 'Total Expenses', kpi: data.kpis.total_expenses, scheme: 'risk' as const, key: 'expenses' },
            { title: 'Net Cash Flow', kpi: data.kpis.net_cash_flow, scheme: 'opportunity' as const, key: 'cash_flow' },
            { title: 'Accounts Receivable', kpi: data.kpis.accounts_receivable ?? (data.kpis as any).outstanding_receivables, key: 'receivables' },
            { title: 'Expense / Revenue', kpi: data.kpis.expense_to_revenue_ratio ?? (data.kpis as any).budget_variance_pct, scheme: 'risk' as const, key: 'expenses' },
            { title: 'Revenue Growth', kpi: data.kpis.revenue_growth_rate ?? (data.kpis as any).revenue_growth_pct, scheme: 'opportunity' as const, key: 'revenue' },
          ].map(({ title, kpi, scheme, key }) => (
            <KPICard
              key={title}
              title={title}
              value={kpi?.formatted ?? '—'}
              changeAbs={kpi?.change_abs !== undefined ? formatUSD(kpi.change_abs, true) : undefined}
              changePct={kpi?.change_pct}
              direction={kpi?.direction}
              interpretation={kpi?.interpretation}
              colorScheme={scheme}
              onInvestigate={() => setInvestigatingKPI(key)}
            />
          ))}
        </div>
      ) : null}

      {/* Corporate Financial Health Index */}
      {!loading && !error && <FinancialHealthCard />}

      {/* Hero: Risk → Opportunity → Action Intelligence Center */}
      {!loading && data && (

        <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
          <div className="bg-slate-50 px-5 py-3 border-b border-slate-200 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-indigo-600" />
              <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wide">
                Executive Action Flow: Risk ➔ Opportunity ➔ Action
              </h2>
            </div>
            <span className="text-xs text-slate-500 font-medium">Integrated Decision Support</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-slate-200">
            {/* 1. What is the Risk? */}
            <div className="p-5 space-y-3 bg-red-50/20">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ShieldAlert size={16} className="text-red-600" />
                  <h3 className="text-sm font-bold text-red-900">1. What is the Risk?</h3>
                </div>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-red-100 text-red-700">
                  {(data.top_risks ?? (data as any).risks ?? []).length} Detected
                </span>
              </div>
              <p className="text-xs text-slate-600">Emerging operational & credit headwinds flagged by the Risk Engine:</p>
              <div className="space-y-2.5">
                {(data.top_risks ?? (data as any).risks ?? []).slice(0, 3).map((r: any, i: number) => (
                  <div key={i} className="bg-white border border-red-100 rounded-lg p-3 shadow-2xs">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-slate-800 truncate">{r.name ?? r.title}</span>
                      <RiskBadge level={r.level ?? r.severity ?? 'MEDIUM'} />
                    </div>
                    {(r.evidence ?? r.description) && <p className="text-[11px] text-slate-500 leading-snug">{r.evidence ?? r.description}</p>}
                  </div>
                ))}
              </div>
              <button
                onClick={() => setInvestigatingKPI('receivables')}
                className="w-full text-center text-xs font-semibold text-red-700 hover:text-red-900 pt-1 flex items-center justify-center gap-1"
              >
                Investigate credit risk drivers <ArrowRight size={12} />
              </button>
            </div>

            {/* 2. What is the Opportunity? */}
            <div className="p-5 space-y-3 bg-emerald-50/20">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <TrendingUp size={16} className="text-emerald-600" />
                  <h3 className="text-sm font-bold text-emerald-900">2. What is Opportunity?</h3>
                </div>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700">
                  {(data.opportunities ?? []).length} Levers
                </span>
              </div>
              <p className="text-xs text-slate-600">High-margin growth levers identified across business segments:</p>
              <div className="space-y-2.5">
                {(data.opportunities ?? []).slice(0, 3).map((o: any, i: number) => (
                  <div key={i} className="bg-white border border-emerald-100 rounded-lg p-3 shadow-2xs">
                    <span className="text-xs font-bold text-slate-800 block mb-0.5">{o.title}</span>
                    <p className="text-[11px] text-slate-500 leading-snug mb-1">{o.description}</p>
                    {o.potential_impact && (
                      <span className="text-[11px] font-bold text-emerald-700 block">{o.potential_impact}</span>
                    )}
                  </div>
                ))}
              </div>
              <button
                onClick={() => setInvestigatingKPI('revenue')}
                className="w-full text-center text-xs font-semibold text-emerald-700 hover:text-emerald-900 pt-1 flex items-center justify-center gap-1"
              >
                Investigate SaaS expansion levers <ArrowRight size={12} />
              </button>
            </div>

            {/* 3. Action Center */}
            <div className="p-5 space-y-3 bg-amber-50/20">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 size={16} className="text-amber-600" />
                  <h3 className="text-sm font-bold text-amber-900">3. Action Center</h3>
                </div>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800">
                  Prioritized
                </span>
              </div>
              <p className="text-xs text-slate-600">Actionable executive decisions mapped to risk mitigation:</p>
              <div className="space-y-2.5">
                {(data.actions ?? []).slice(0, 3).map((a: any, i: number) => (
                  <div key={i} className="bg-white border border-amber-100 rounded-lg p-3 shadow-2xs">
                    <div className="flex items-center justify-between gap-1 mb-1">
                      <span className="text-xs font-bold text-slate-800 truncate">{a.title}</span>
                      <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                        a.priority === 'HIGH' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-800'
                      }`}>{a.priority}</span>
                    </div>
                    <p className="text-[11px] text-slate-500 leading-snug">{a.description}</p>
                  </div>
                ))}
              </div>
              <button
                onClick={() => setInvestigatingKPI('profit')}
                className="w-full text-center text-xs font-semibold text-amber-800 hover:text-amber-950 pt-1 flex items-center justify-center gap-1"
              >
                Launch full executive audit <ArrowRight size={12} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Revenue Trend + Financial Health */}
      {/* Revenue Trend + Financial Health */}
      {!loading && data && ((data.revenue_trend && data.revenue_trend.length > 0) || data.risk_score) && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {data.revenue_trend && data.revenue_trend.length > 0 && (
            <div className={`${data.risk_score ? 'lg:col-span-2' : 'lg:col-span-3'} bg-white border border-slate-200 rounded-lg shadow-sm p-5`}>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-base font-semibold text-slate-700">Revenue Trend (Jan 2023 – Mar 2025)</h2>
                <button
                  onClick={() => setInvestigatingKPI('revenue')}
                  className="text-xs text-primary-600 hover:text-primary-800 font-medium"
                >
                  Investigate Trend →
                </button>
              </div>
              <RevenueChart data={data.revenue_trend} height={260} />
            </div>
          )}
          {data.risk_score && (
            <div className={`${data.revenue_trend && data.revenue_trend.length > 0 ? '' : 'lg:col-span-3'} bg-white border border-slate-200 rounded-lg shadow-sm p-5`}>
              <h2 className="text-base font-semibold text-slate-700 mb-4">Financial Health Assessment</h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-600">Overall Risk Level</span>
                  <RiskBadge level={data.risk_score.level} />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-600">Composite Risk Score</span>
                  <span className="text-sm font-bold text-slate-800">{data.risk_score.overall_score} / 100</span>
                </div>
                <div className="h-px bg-slate-100" />
                <p className="text-xs text-slate-600 leading-relaxed">{data.risk_score.summary}</p>
                <div className="h-px bg-slate-100" />
                {data.risk_score.indicators?.slice(0, 4).map(ind => (
                  <div key={ind.name} className="flex items-center justify-between">
                    <span className="text-xs text-slate-600 truncate pr-2">{ind.name}</span>
                    <RiskBadge level={ind.level} />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Expense Trend + Cash Flow */}
      {!loading && data && ((data.expense_trend && data.expense_trend.length > 0) || (data.cash_flow_summary && data.cash_flow_summary.length > 0)) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {data.expense_trend && data.expense_trend.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-base font-semibold text-slate-700">Expense Trend & Outlier Detection</h2>
                <button
                  onClick={() => setInvestigatingKPI('expenses')}
                  className="text-xs text-primary-600 hover:text-primary-800 font-medium"
                >
                  Investigate Outliers →
                </button>
              </div>
              <RevenueChart data={data.expense_trend} height={220} />
            </div>
          )}
          {data.cash_flow_summary && data.cash_flow_summary.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-base font-semibold text-slate-700">Operating Cash Flow Trajectory</h2>
                <button
                  onClick={() => setInvestigatingKPI('cash_flow')}
                  className="text-xs text-primary-600 hover:text-primary-800 font-medium"
                >
                  Cash Flow Drilldown →
                </button>
              </div>
              <CashFlowChart data={data.cash_flow_summary} height={220} />
            </div>
          )}
        </div>
      )}

      {/* Budget vs Actual */}
      {!loading && data && data.budget_variance && data.budget_variance.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5">
          <h2 className="text-base font-semibold text-slate-700 mb-4">Budget vs Actual Variance by Category</h2>
          <BudgetVarianceChart data={data.budget_variance} height={320} />
        </div>
      )}

      {/* Ask FinGuard AI with Verified Evidence */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-xs p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-purple-100 text-purple-700 flex items-center justify-center">
              <Brain size={18} />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-800">Ask FinGuard AI Analyst</h2>
              <p className="text-xs text-slate-500">Natural language analytical querying backed by verified data evidence</p>
            </div>
          </div>
          <span className="text-xs bg-purple-50 text-purple-700 font-semibold px-2.5 py-1 rounded-full border border-purple-200 flex items-center gap-1">
            <Sparkles size={12} /> Grounded Gemini 1.5
          </span>
        </div>

        {/* Quick Question Chips */}
        <div className="flex flex-wrap gap-2 pt-1">
          {[
            'Why did profit decline in H2 2024?',
            'What are the biggest financial risks right now?',
            'How is accounts receivable aging affecting liquidity?',
            'Were there any unusual expense spikes in October 2024?',
          ].map((prompt) => (
            <button
              key={prompt}
              onClick={() => handleAsk(prompt)}
              className="text-xs bg-slate-50 hover:bg-purple-50 text-slate-700 hover:text-purple-800 border border-slate-200 hover:border-purple-200 px-3 py-1.5 rounded-full transition-colors font-medium text-left"
            >
              {prompt}
            </button>
          ))}
        </div>

        <div className="flex gap-2">
          <input
            type="text"
            value={aiQuestion}
            onChange={e => setAiQuestion(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleAsk()}
            placeholder="e.g. Why did profit margins compress in Q3 2024?"
            className="flex-1 border border-slate-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 text-slate-800 placeholder:text-slate-400"
          />
          <button
            onClick={() => handleAsk()}
            disabled={aiLoading || !aiQuestion.trim()}
            className="bg-purple-700 hover:bg-purple-800 disabled:opacity-60 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition-colors flex items-center gap-2"
          >
            {aiLoading ? 'Analyzing…' : 'Ask AI'}
          </button>
        </div>

        {aiError && <p className="text-xs text-red-600">{aiError}</p>}

        {aiResponse && (
          <div className="mt-4 p-5 bg-slate-50 rounded-xl border border-slate-200 space-y-4">
            <div>
              <span className="text-[11px] uppercase tracking-wider font-bold text-slate-500 block mb-1">
                Executive Synthesis
              </span>
              <p className="text-sm font-semibold text-slate-900 leading-relaxed">{aiResponse.summary}</p>
            </div>

            {/* Evidence Drawer */}
            {aiResponse.evidence && aiResponse.evidence.length > 0 && (
              <div className="bg-white rounded-lg border border-slate-200 p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-800 uppercase tracking-wide flex items-center gap-1.5">
                    <CheckCircle2 size={14} className="text-emerald-600" /> Verified Audit Evidence
                  </span>
                  <span className="text-[11px] text-slate-500">As-Of: 31 Mar 2025</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 pt-1">
                  {aiResponse.evidence.map((ev, idx) => (
                    <div key={idx} className="bg-slate-50 border border-slate-100 rounded-md p-2.5">
                      <span className="text-[11px] text-slate-500 block truncate">{ev.metric}</span>
                      <span className="text-sm font-bold text-slate-800 block mt-0.5">{ev.value}</span>
                      <span className="text-[10px] text-primary-700 block truncate mt-1">{ev.source}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {aiResponse.insights && aiResponse.insights.length > 0 && (
              <div className="space-y-1.5">
                <span className="text-[11px] uppercase tracking-wider font-bold text-slate-500 block">
                  Actionable Insights
                </span>
                {aiResponse.insights.slice(0, 2).map((c, i) => (
                  <InsightCardComponent key={i} card={c} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Investigation Modal */}
      <InvestigationModal
        kpi={investigatingKPI}
        period={period}
        onClose={() => setInvestigatingKPI(null)}
      />
    </div>
  )
}
