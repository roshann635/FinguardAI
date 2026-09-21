import { useState, useEffect, useCallback, type ReactNode } from 'react'
import {
  fetchRevenueAnalytics,
  fetchProfitAnalytics,
  fetchExpenseAnalytics,
  fetchCashFlowAnalytics,
} from '../services/api'
import type { RevenueAnalytics, ProfitAnalytics, ExpenseAnalytics, CashFlowAnalytics } from '../types'
import RevenueChart from '../components/charts/RevenueChart'
import ProfitMarginChart from '../components/charts/ProfitMarginChart'
import CategoryBarChart from '../components/charts/CategoryBarChart'
import CashFlowChart from '../components/charts/CashFlowChart'
import LoadingSkeleton from '../components/ui/LoadingSkeleton'
import ErrorState from '../components/ui/ErrorState'
import { useFilters } from '../components/layout/Layout'
import { formatINR, formatPct } from '../utils/format'

type Tab = 'revenue' | 'profitability' | 'expenses' | 'cashflow'

const TABS: { id: Tab; label: string }[] = [
  { id: 'revenue', label: 'Revenue Analytics' },
  { id: 'profitability', label: 'Profitability' },
  { id: 'expenses', label: 'Expenses' },
  { id: 'cashflow', label: 'Cash Flow' },
]

function SectionCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5">
      <h3 className="text-base font-semibold text-slate-700 mb-4">{title}</h3>
      {children}
    </div>
  )
}

function SkeletonSection() {
  return (
    <div className="space-y-4">
      <div className="bg-white border border-slate-200 rounded-lg p-5 space-y-3">
        <LoadingSkeleton height="h-4" width="w-40" />
        <LoadingSkeleton height="h-64" />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white border border-slate-200 rounded-lg p-5 space-y-3">
          <LoadingSkeleton height="h-4" width="w-32" />
          <LoadingSkeleton height="h-48" />
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-5 space-y-3">
          <LoadingSkeleton height="h-4" width="w-32" />
          <LoadingSkeleton height="h-48" />
        </div>
      </div>
    </div>
  )
}

// ─── Revenue Tab ──────────────────────────────────────────────────────────────

function RevenueTab({ period }: { period: string }) {
  const [data, setData] = useState<RevenueAnalytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true); setError(null)
    try { setData(await fetchRevenueAnalytics({ period })) }
    catch (e) { setError(e instanceof Error ? e.message : 'Failed') }
    finally { setLoading(false) }
  }, [period])

  useEffect(() => { load() }, [load])

  if (loading) return <SkeletonSection />
  if (error) return <ErrorState message={error} retry={load} />
  if (!data) return null

  return (
    <div className="space-y-4">
      <SectionCard title="Revenue Trend">
        <RevenueChart data={data.trend} height={260} />
      </SectionCard>

      <div className="grid grid-cols-2 gap-4">
        <SectionCard title="Revenue by Category">
          <CategoryBarChart data={data.by_category} valueLabel="Revenue" height={240} />
        </SectionCard>
        <SectionCard title="Revenue by Region">
          <CategoryBarChart data={data.by_region.map(r => ({ category: r.region, value: r.value, percentage: r.percentage }))} valueLabel="Revenue" height={240} />
        </SectionCard>
      </div>

      <SectionCard title="Revenue Growth Trend">
        <RevenueChart data={data.growth_trend} height={200} />
      </SectionCard>

      {data.top_contributors.length > 0 && (
        <SectionCard title="Top Revenue Contributors">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-slate-500 border-b border-slate-100">
                <th className="text-left py-2 font-medium">Contributor</th>
                <th className="text-right py-2 font-medium">Revenue</th>
                <th className="text-right py-2 font-medium">Share</th>
              </tr>
            </thead>
            <tbody>
              {data.top_contributors.map((c, i) => (
                <tr key={i} className="border-b border-slate-50">
                  <td className="py-2 text-slate-700">{c.name}</td>
                  <td className="py-2 text-right font-medium text-slate-800">{c.formatted ?? formatINR(c.value)}</td>
                  <td className="py-2 text-right text-slate-500">{formatPct(c.pct)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </SectionCard>
      )}
    </div>
  )
}

// ─── Profitability Tab ────────────────────────────────────────────────────────

function ProfitabilityTab({ period }: { period: string }) {
  const [data, setData] = useState<ProfitAnalytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true); setError(null)
    try { setData(await fetchProfitAnalytics({ period })) }
    catch (e) { setError(e instanceof Error ? e.message : 'Failed') }
    finally { setLoading(false) }
  }, [period])

  useEffect(() => { load() }, [load])

  if (loading) return <SkeletonSection />
  if (error) return <ErrorState message={error} retry={load} />
  if (!data) return null

  return (
    <div className="space-y-4">
      <SectionCard title="Profit & Margin Trend">
        <ProfitMarginChart profitData={data.profit_trend} marginData={data.margin_trend} height={260} />
      </SectionCard>
      <div className="grid grid-cols-2 gap-4">
        <SectionCard title="Profit by Category">
          <CategoryBarChart data={data.by_category} valueLabel="Profit" height={240} />
        </SectionCard>
        <SectionCard title="Profit by Region">
          <CategoryBarChart data={data.by_region.map(r => ({ category: r.region, value: r.value, percentage: r.percentage }))} valueLabel="Profit" height={240} />
        </SectionCard>
      </div>
    </div>
  )
}

// ─── Expenses Tab ─────────────────────────────────────────────────────────────

function ExpensesTab({ period }: { period: string }) {
  const [data, setData] = useState<ExpenseAnalytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true); setError(null)
    try { setData(await fetchExpenseAnalytics({ period })) }
    catch (e) { setError(e instanceof Error ? e.message : 'Failed') }
    finally { setLoading(false) }
  }, [period])

  useEffect(() => { load() }, [load])

  if (loading) return <SkeletonSection />
  if (error) return <ErrorState message={error} retry={load} />
  if (!data) return null

  return (
    <div className="space-y-4">
      <SectionCard title="Expense Trend">
        <RevenueChart data={data.trend} height={240} />
      </SectionCard>
      <div className="grid grid-cols-2 gap-4">
        <SectionCard title="Expenses by Category">
          <CategoryBarChart data={data.by_category} valueLabel="Expenses" height={260} />
        </SectionCard>
        <SectionCard title="Expenses by Department">
          <CategoryBarChart data={data.by_department} valueLabel="Expenses" height={260} />
        </SectionCard>
      </div>
      <SectionCard title="Expense-to-Revenue Ratio">
        <RevenueChart data={data.expense_to_revenue} height={200} />
      </SectionCard>
    </div>
  )
}

// ─── Cash Flow Tab ────────────────────────────────────────────────────────────

function CashFlowTab({ period }: { period: string }) {
  const [data, setData] = useState<CashFlowAnalytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true); setError(null)
    try { setData(await fetchCashFlowAnalytics({ period })) }
    catch (e) { setError(e instanceof Error ? e.message : 'Failed') }
    finally { setLoading(false) }
  }, [period])

  useEffect(() => { load() }, [load])

  if (loading) return <SkeletonSection />
  if (error) return <ErrorState message={error} retry={load} />
  if (!data) return null

  return (
    <div className="space-y-4">
      <SectionCard title="Cash Flow Trend (Inflow / Outflow / Net)">
        <CashFlowChart data={data.trend} height={280} />
      </SectionCard>
      <div className="grid grid-cols-2 gap-4">
        <SectionCard title="Cash Flow by Category">
          <CategoryBarChart data={data.by_category} valueLabel="Amount" height={240} />
        </SectionCard>
        <SectionCard title="Cumulative Cash Flow">
          <RevenueChart data={data.cumulative} height={240} />
        </SectionCard>
      </div>
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function FinancialPerformance() {
  const { period } = useFilters()
  const [activeTab, setActiveTab] = useState<Tab>('revenue')

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Financial Performance</h1>
        <p className="text-sm text-slate-500 mt-1">Detailed analytics across revenue, profitability, expenses and cash flow.</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-slate-100 rounded-lg p-1 w-fit">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-white text-slate-800 shadow-sm'
                : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'revenue' && <RevenueTab period={period} />}
      {activeTab === 'profitability' && <ProfitabilityTab period={period} />}
      {activeTab === 'expenses' && <ExpensesTab period={period} />}
      {activeTab === 'cashflow' && <CashFlowTab period={period} />}
    </div>
  )
}
