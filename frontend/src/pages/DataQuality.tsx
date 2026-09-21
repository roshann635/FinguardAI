import { useState, useEffect, useCallback } from 'react'
import { fetchDataQuality } from '../services/api'
import type { DataQualityReport } from '../types'
import RiskBadge from '../components/ui/RiskBadge'
import LoadingSkeleton from '../components/ui/LoadingSkeleton'
import ErrorState from '../components/ui/ErrorState'
import { CheckCircle, Database } from 'lucide-react'

function ScoreGauge({ score }: { score: number }) {
  const color = score >= 80 ? '#16a34a' : score >= 60 ? '#d97706' : '#dc2626'
  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative w-32 h-32">
        <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
          <path
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            fill="none"
            stroke="#e2e8f0"
            strokeWidth="3"
          />
          <path
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            fill="none"
            stroke={color}
            strokeWidth="3"
            strokeDasharray={`${score}, 100`}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-2xl font-bold text-slate-800">{score}%</span>
        </div>
      </div>
      <span className="text-sm font-medium text-slate-600">Overall Quality Score</span>
    </div>
  )
}

function DimensionCard({ name, score, description, issuesFound }: {
  name: string; score: number; description: string; issuesFound?: number
}) {
  const color = score >= 80 ? 'text-green-600' : score >= 60 ? 'text-amber-600' : 'text-red-600'
  const bg = score >= 80 ? 'bg-green-50 border-green-200' : score >= 60 ? 'bg-amber-50 border-amber-200' : 'bg-red-50 border-red-200'
  return (
    <div className={`border rounded-lg p-4 ${bg}`}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm font-semibold text-slate-700">{name}</span>
        <span className={`text-lg font-bold ${color}`}>{score.toFixed(1)}%</span>
      </div>
      <div className="w-full bg-white rounded-full h-1.5 mb-2">
        <div className="h-1.5 rounded-full" style={{ width: `${score}%`, background: score >= 80 ? '#16a34a' : score >= 60 ? '#d97706' : '#dc2626' }} />
      </div>
      <p className="text-xs text-slate-600">{description}</p>
      {issuesFound !== undefined && issuesFound > 0 && (
        <p className="text-xs text-amber-700 mt-1">{issuesFound} issue{issuesFound > 1 ? 's' : ''} detected</p>
      )}
    </div>
  )
}

export default function DataQuality() {
  const [data, setData] = useState<DataQualityReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true); setError(null)
    try { setData(await fetchDataQuality()) }
    catch (e) { setError(e instanceof Error ? e.message : 'Failed') }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Data Quality</h1>
        <p className="text-sm text-slate-500 mt-1">Monitoring completeness, consistency, and validity of financial data.</p>
      </div>

      {loading ? (
        <div className="space-y-4">
          <div className="bg-white border border-slate-200 rounded-lg p-5 space-y-3">
            <LoadingSkeleton height="h-32" width="w-32" className="rounded-full mx-auto" />
            <LoadingSkeleton height="h-4" width="w-48" className="mx-auto" />
          </div>
        </div>
      ) : error ? (
        <ErrorState message={error} retry={load} />
      ) : data ? (
        <>
          {/* Overall Score */}
          <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-6 flex items-center gap-8">
            <ScoreGauge score={data.overall_score} />
            <div className="flex-1 grid grid-cols-2 gap-3 text-sm">
              <div className="flex justify-between border-b border-slate-100 pb-2">
                <span className="text-slate-500">Total Records</span>
                <span className="font-semibold text-slate-800">{data.total_records?.toLocaleString() ?? '—'}</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-2">
                <span className="text-slate-500">Duplicate Rate</span>
                <span className={`font-semibold ${data.duplicate_rate > 2 ? 'text-amber-600' : 'text-green-600'}`}>
                  {data.duplicate_rate.toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-2">
                <span className="text-slate-500">Missing Value Rate</span>
                <span className={`font-semibold ${data.missing_value_rate > 5 ? 'text-amber-600' : 'text-green-600'}`}>
                  {data.missing_value_rate.toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-2">
                <span className="text-slate-500">Last Checked</span>
                <span className="font-semibold text-slate-800">{new Date(data.last_checked).toLocaleDateString()}</span>
              </div>
            </div>
          </div>

          {/* Dimension Cards */}
          <div className="grid grid-cols-3 gap-4">
            <DimensionCard
              name="Completeness"
              score={data.completeness.score}
              description={data.completeness.description}
              issuesFound={data.completeness.issues_found}
            />
            <DimensionCard
              name="Consistency"
              score={data.consistency.score}
              description={data.consistency.description}
              issuesFound={data.consistency.issues_found}
            />
            <DimensionCard
              name="Validity"
              score={data.validity.score}
              description={data.validity.description}
              issuesFound={data.validity.issues_found}
            />
          </div>

          {/* Issues Table */}
          {data.issues.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5">
              <h3 className="text-base font-semibold text-slate-700 mb-4">Detected Issues</h3>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs text-slate-500 border-b border-slate-100">
                    <th className="text-left py-2 font-medium">Severity</th>
                    <th className="text-left py-2 font-medium">Description</th>
                    <th className="text-left py-2 font-medium">Table</th>
                    <th className="text-left py-2 font-medium">Column</th>
                    <th className="text-right py-2 font-medium">Affected Records</th>
                  </tr>
                </thead>
                <tbody>
                  {data.issues.map((issue, i) => (
                    <tr key={i} className="border-b border-slate-50">
                      <td className="py-2"><RiskBadge level={issue.severity} /></td>
                      <td className="py-2 text-slate-700">{issue.description}</td>
                      <td className="py-2 text-slate-500">{issue.table ?? '—'}</td>
                      <td className="py-2 text-slate-500">{issue.column ?? '—'}</td>
                      <td className="py-2 text-right text-slate-600">{issue.affected_records?.toLocaleString() ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Data Pipeline */}
          <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5">
            <div className="flex items-center gap-2 mb-3">
              <Database size={16} className="text-primary-600" />
              <h3 className="text-base font-semibold text-slate-700">Data Pipeline</h3>
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-600 flex-wrap">
              {['Raw Transaction Data', 'Ingestion & Parsing', 'Validation & Cleansing', 'Aggregation Layer', 'Analytics Engine', 'Dashboard'].map((step, i, arr) => (
                <div key={i} className="flex items-center gap-2">
                  <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-200 rounded px-2 py-1">
                    <CheckCircle size={12} className="text-green-500" />
                    <span className="text-xs">{step}</span>
                  </div>
                  {i < arr.length - 1 && <span className="text-slate-300">→</span>}
                </div>
              ))}
            </div>
          </div>
        </>
      ) : null}
    </div>
  )
}
