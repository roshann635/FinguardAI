import { useState, useEffect, useCallback, type ReactNode } from 'react'
import {
  fetchRiskOverview,
  fetchExpenseAnomalies,
  fetchTransactionAnomalies,
  fetchReceivablesAnalytics,
  fetchBudgetAnalytics,
} from '../services/api'
import type { RiskScore, AnomalyRecord, ReceivablesAging, BudgetAnalytics } from '../types'
import RiskBadge from '../components/ui/RiskBadge'
import AgingChart from '../components/charts/AgingChart'
import BudgetVarianceChart from '../components/charts/BudgetVarianceChart'
import LoadingSkeleton from '../components/ui/LoadingSkeleton'
import ErrorState from '../components/ui/ErrorState'
import EmptyState from '../components/ui/EmptyState'
import { formatINR } from '../utils/format'

function SectionCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5">
      <h3 className="text-base font-semibold text-slate-700 mb-4">{title}</h3>
      {children}
    </div>
  )
}

function AnomalyTable({ records, emptyMsg }: { records: AnomalyRecord[]; emptyMsg: string }) {
  if (records.length === 0) return <EmptyState message={emptyMsg} />
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm min-w-[700px]">
        <thead>
          <tr className="text-xs text-slate-500 border-b border-slate-100">
            <th className="text-left py-2 font-medium">Date</th>
            <th className="text-left py-2 font-medium">Category</th>
            <th className="text-right py-2 font-medium">Amount</th>
            <th className="text-left py-2 font-medium">Expected Range</th>
            <th className="text-left py-2 font-medium">Severity</th>
            <th className="text-left py-2 font-medium">Reason</th>
            <th className="text-center py-2 font-medium">Investigate</th>
          </tr>
        </thead>
        <tbody>
          {records.map((r, i) => (
            <tr key={i} className="border-b border-slate-50 hover:bg-slate-50">
              <td className="py-2 text-slate-600">{r.date}</td>
              <td className="py-2 text-slate-700">{r.category}</td>
              <td className="py-2 text-right font-medium text-slate-800">{formatINR(r.amount)}</td>
              <td className="py-2 text-slate-500 text-xs">
                {r.expected_min !== undefined && r.expected_max !== undefined
                  ? `${formatINR(r.expected_min)} – ${formatINR(r.expected_max)}`
                  : '—'}
              </td>
              <td className="py-2"><RiskBadge level={r.severity} /></td>
              <td className="py-2 text-slate-600 text-xs max-w-xs truncate">{r.reason}</td>
              <td className="py-2 text-center">
                {r.requires_investigation ? (
                  <span className="text-xs font-semibold text-red-600">⚠ Yes</span>
                ) : (
                  <span className="text-xs text-slate-400">—</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function RiskIntelligence() {
  const [riskScore, setRiskScore] = useState<RiskScore | null>(null)
  const [expenseAnomalies, setExpenseAnomalies] = useState<AnomalyRecord[]>([])
  const [txnAnomalies, setTxnAnomalies] = useState<AnomalyRecord[]>([])
  const [receivables, setReceivables] = useState<ReceivablesAging | null>(null)
  const [budget, setBudget] = useState<BudgetAnalytics | null>(null)

  const [loadingRisk, setLoadingRisk] = useState(true)
  const [loadingAnomalies, setLoadingAnomalies] = useState(true)
  const [loadingReceivables, setLoadingReceivables] = useState(true)
  const [loadingBudget, setLoadingBudget] = useState(true)

  const [errorRisk, setErrorRisk] = useState<string | null>(null)
  const [errorAnomalies, setErrorAnomalies] = useState<string | null>(null)
  const [errorReceivables, setErrorReceivables] = useState<string | null>(null)
  const [errorBudget, setErrorBudget] = useState<string | null>(null)

  const loadRisk = useCallback(async () => {
    setLoadingRisk(true); setErrorRisk(null)
    try { setRiskScore(await fetchRiskOverview()) }
    catch (e) { setErrorRisk(e instanceof Error ? e.message : 'Failed') }
    finally { setLoadingRisk(false) }
  }, [])

  const loadAnomalies = useCallback(async () => {
    setLoadingAnomalies(true); setErrorAnomalies(null)
    try {
      const [exp, txn] = await Promise.all([fetchExpenseAnomalies(), fetchTransactionAnomalies()])
      setExpenseAnomalies(exp)
      setTxnAnomalies(txn)
    }
    catch (e) { setErrorAnomalies(e instanceof Error ? e.message : 'Failed') }
    finally { setLoadingAnomalies(false) }
  }, [])

  const loadReceivables = useCallback(async () => {
    setLoadingReceivables(true); setErrorReceivables(null)
    try { setReceivables(await fetchReceivablesAnalytics()) }
    catch (e) { setErrorReceivables(e instanceof Error ? e.message : 'Failed') }
    finally { setLoadingReceivables(false) }
  }, [])

  const loadBudget = useCallback(async () => {
    setLoadingBudget(true); setErrorBudget(null)
    try { setBudget(await fetchBudgetAnalytics()) }
    catch (e) { setErrorBudget(e instanceof Error ? e.message : 'Failed') }
    finally { setLoadingBudget(false) }
  }, [])

  useEffect(() => {
    loadRisk()
    loadAnomalies()
    loadReceivables()
    loadBudget()
  }, [loadRisk, loadAnomalies, loadReceivables, loadBudget])

  const overBudget = budget?.variance?.filter(v => v.status === 'over') ?? []

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Risk Intelligence</h1>
        <p className="text-sm text-slate-500 mt-1">Anomaly detection, risk scoring, and predictive risk indicators.</p>
      </div>

      {/* Risk Score Card */}
      {loadingRisk ? (
        <div className="bg-white border border-slate-200 rounded-lg p-5 space-y-3">
          <LoadingSkeleton height="h-6" width="w-32" />
          <LoadingSkeleton height="h-12" width="w-48" />
          <LoadingSkeleton height="h-4" />
        </div>
      ) : errorRisk ? (
        <ErrorState message={errorRisk} retry={loadRisk} />
      ) : riskScore ? (
        <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5">
          <div className="flex items-start gap-8">
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">Overall Risk Level</p>
              <div className="flex items-center gap-3 mb-2">
                <span className="text-4xl font-bold text-slate-800">{riskScore.overall_score}</span>
                <div>
                  <RiskBadge level={riskScore.level} />
                  <p className="text-xs text-slate-500 mt-1">out of 100</p>
                </div>
              </div>
              <p className="text-sm text-slate-600 max-w-md leading-relaxed">{riskScore.summary}</p>
            </div>
            <div className="flex-1 border border-slate-100 rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-slate-50 text-xs text-slate-500">
                    <th className="text-left px-3 py-2 font-medium">Indicator</th>
                    <th className="text-left px-3 py-2 font-medium">Level</th>
                    <th className="text-right px-3 py-2 font-medium">Value</th>
                    <th className="text-right px-3 py-2 font-medium">Threshold</th>
                  </tr>
                </thead>
                <tbody>
                  {(riskScore.indicators ?? []).map((ind, i) => (
                    <tr key={i} className="border-t border-slate-100">
                      <td className="px-3 py-2 text-slate-700">{ind.name}</td>
                      <td className="px-3 py-2"><RiskBadge level={ind.level} /></td>
                      <td className="px-3 py-2 text-right font-medium">{String(ind.value)}</td>
                      <td className="px-3 py-2 text-right text-slate-500">{ind.threshold !== undefined ? String(ind.threshold) : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : null}

      {/* Risk Indicators Detail */}
      {riskScore && (riskScore.indicators?.length ?? 0) > 0 && (
        <SectionCard title="Risk Indicators Detail">
          <div className="space-y-3">
            {(riskScore.indicators ?? []).map((ind, i) => (
              <div key={i} className="border border-slate-100 rounded-lg p-4">
                <div className="flex items-center gap-3 mb-2">
                  <RiskBadge level={ind.level} />
                  <span className="text-sm font-semibold text-slate-700">{ind.name}</span>
                </div>
                <p className="text-sm text-slate-600">{ind.description}</p>
                {ind.evidence && <p className="text-xs text-slate-500 mt-1 italic">{ind.evidence}</p>}
              </div>
            ))}
          </div>
        </SectionCard>
      )}

      {/* Expense Anomalies */}
      <SectionCard title="Expense Anomalies">
        {loadingAnomalies ? (
          <LoadingSkeleton height="h-48" />
        ) : errorAnomalies ? (
          <ErrorState message={errorAnomalies} retry={loadAnomalies} />
        ) : (
          <AnomalyTable records={expenseAnomalies} emptyMsg="No expense anomalies detected" />
        )}
      </SectionCard>

      {/* Transaction Anomalies */}
      <SectionCard title="Transaction Anomalies">
        {loadingAnomalies ? (
          <LoadingSkeleton height="h-48" />
        ) : errorAnomalies ? (
          <ErrorState message={errorAnomalies} retry={loadAnomalies} />
        ) : (
          <AnomalyTable records={txnAnomalies} emptyMsg="No transaction anomalies detected" />
        )}
      </SectionCard>

      {/* Receivables Aging Risk */}
      <SectionCard title="Receivables Aging Risk">
        {loadingReceivables ? (
          <LoadingSkeleton height="h-64" />
        ) : errorReceivables ? (
          <ErrorState message={errorReceivables} retry={loadReceivables} />
        ) : receivables ? (
          <AgingChart data={receivables} height={260} />
        ) : (
          <EmptyState message="No receivables data" />
        )}
      </SectionCard>

      {/* Budget Overrun Risk */}
      {!loadingBudget && !errorBudget && overBudget.length > 0 && (
        <SectionCard title={`Budget Overrun Risk (${overBudget.length} categories over budget)`}>
          <BudgetVarianceChart data={overBudget} height={300} />
        </SectionCard>
      )}
      {!loadingBudget && errorBudget && (
        <ErrorState message={errorBudget} retry={loadBudget} />
      )}
    </div>
  )
}
