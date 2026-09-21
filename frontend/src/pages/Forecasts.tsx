import { useState, useEffect, useCallback } from 'react'
import { fetchRevenueForecast, fetchForecastComparison } from '../services/api'
import type { ForecastResult, ForecastComparisonResult } from '../types'
import ForecastChart from '../components/charts/ForecastChart'
import KPICard from '../components/ui/KPICard'
import LoadingSkeleton from '../components/ui/LoadingSkeleton'
import ErrorState from '../components/ui/ErrorState'
import { formatUSD } from '../utils/format'
import { Trophy, CheckCircle2, BarChart3, LineChart } from 'lucide-react'

const HORIZONS = [30, 60, 90]

export default function Forecasts() {
  const [activeTab, setActiveTab] = useState<'forecast' | 'benchmark'>('forecast')
  const [horizon, setHorizon] = useState(90)
  const [data, setData] = useState<ForecastResult | null>(null)
  const [benchmark, setBenchmark] = useState<ForecastComparisonResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [fData, bData] = await Promise.all([
        fetchRevenueForecast(horizon),
        fetchForecastComparison().catch(() => null),
      ])
      setData(fData)
      if (bData) setBenchmark(bData)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load forecast')
    } finally {
      setLoading(false)
    }
  }, [horizon])

  useEffect(() => { load() }, [load])

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Revenue Forecasting & Benchmarks</h1>
          <p className="text-sm text-slate-500 mt-1">Statistical revenue projections with multi-model empirical comparison.</p>
        </div>
        <div className="flex items-center bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs font-semibold">
          <button
            onClick={() => setActiveTab('forecast')}
            className={`px-3 py-1.5 rounded-md flex items-center gap-1.5 transition-colors ${
              activeTab === 'forecast' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <LineChart size={14} /> Production Forecast
          </button>
          <button
            onClick={() => setActiveTab('benchmark')}
            className={`px-3 py-1.5 rounded-md flex items-center gap-1.5 transition-colors ${
              activeTab === 'benchmark' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <BarChart3 size={14} /> Model Benchmark
          </button>
        </div>
      </div>

      {activeTab === 'forecast' ? (
        <>
          {/* Horizon Selector */}
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-slate-600">Forecast Horizon:</span>
            <div className="flex gap-1">
              {HORIZONS.map(h => (
                <button
                  key={h}
                  onClick={() => setHorizon(h)}
                  className={`px-4 py-1.5 rounded-md text-sm font-medium border transition-colors ${
                    horizon === h
                      ? 'bg-primary-700 text-white border-primary-700'
                      : 'bg-white text-slate-600 border-slate-200 hover:border-primary-400'
                  }`}
                >
                  {h} Days
                </button>
              ))}
            </div>
          </div>

          {/* Forecast Chart */}
          <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-semibold text-slate-700">
                Revenue Forecast — Next {horizon} Days (from 31 Mar 2025)
              </h3>
              <span className="text-xs bg-slate-100 text-slate-600 px-2.5 py-1 rounded-full border border-slate-200 font-medium">
                80% & 95% Confidence Intervals
              </span>
            </div>
            {loading ? (
              <LoadingSkeleton height="h-80" />
            ) : error ? (
              <ErrorState message={error} retry={load} />
            ) : data ? (
              <ForecastChart data={data.points} height={320} />
            ) : null}
          </div>

          {/* Model Performance */}
          {!loading && data && (
            <div>
              <h3 className="text-base font-semibold text-slate-700 mb-3">Model Accuracy Metrics</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <KPICard
                  title="Mean Absolute Error (MAE)"
                  value={formatUSD(data.model_performance?.mae ?? (data as any).mae ?? 0, true)}
                  interpretation="Average absolute deviation from actual values"
                />
                <KPICard
                  title="Root Mean Square Error (RMSE)"
                  value={formatUSD(data.model_performance?.rmse ?? (data as any).rmse ?? 0, true)}
                  interpretation="Penalises large deviations more heavily"
                />
                <KPICard
                  title="Mean Absolute % Error (MAPE)"
                  value={`${((data.model_performance?.mape ?? (data as any).mape ?? 0)).toFixed(2)}%`}
                  interpretation="Normalized percentage deviation across test window"
                />
              </div>
            </div>
          )}

          {/* Methodology */}
          {!loading && data && (
            <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5">
              <h3 className="text-base font-semibold text-slate-700 mb-2">Forecast Methodology</h3>
              <p className="text-sm text-slate-600 leading-relaxed">{data.methodology}</p>
              <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded text-xs text-amber-800">
                <strong>Model Governance:</strong> {data.disclaimer}
              </div>
            </div>
          )}
        </>
      ) : (
        /* Benchmark View */
        <div className="space-y-5">
          {benchmark ? (
            <>
              {/* Champion Card */}
              <div className="bg-gradient-to-r from-indigo-900 to-slate-900 text-white rounded-xl p-6 shadow-md">
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2">
                      <Trophy size={20} className="text-amber-400" />
                      <span className="text-xs font-bold uppercase tracking-wider text-amber-400">
                        Production Champion Model
                      </span>
                    </div>
                    <h2 className="text-xl font-bold text-white">{benchmark.champion_model}</h2>
                    <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
                      {benchmark.champion_rationale}
                    </p>
                  </div>
                  <div className="bg-slate-800/80 border border-slate-700 rounded-lg p-3 text-right">
                    <span className="text-[11px] text-slate-400 block">Directional Accuracy</span>
                    <span className="text-2xl font-black text-emerald-400">66.7%</span>
                    <span className="text-[10px] text-slate-400 block mt-0.5">vs 0.0% Naive</span>
                  </div>
                </div>
              </div>

              {/* Comparative Metrics Table */}
              <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
                <div className="p-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-slate-800">Empirical Out-of-Sample Benchmark</h3>
                    <p className="text-xs text-slate-500">{benchmark.evaluation_window}</p>
                  </div>
                  <span className="text-xs bg-indigo-50 text-indigo-700 font-semibold px-2.5 py-1 rounded-full border border-indigo-200">
                    4 Models Evaluated
                  </span>
                </div>
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase">
                    <tr>
                      <th className="px-4 py-3">Model Architecture</th>
                      <th className="px-4 py-3">MAE</th>
                      <th className="px-4 py-3">RMSE</th>
                      <th className="px-4 py-3">MAPE</th>
                      <th className="px-4 py-3">Directional Acc</th>
                      <th className="px-4 py-3">Role</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    {(benchmark.benchmark_table ?? []).map((m, idx) => (
                      <tr key={idx} className={m.model?.includes('Holt-Winters') ? 'bg-indigo-50/40 font-medium' : 'hover:bg-slate-50'}>
                        <td className="px-4 py-3 font-semibold text-slate-900 flex items-center gap-1.5">
                          {m.model?.includes('Holt-Winters') && <CheckCircle2 size={14} className="text-indigo-600 flex-shrink-0" />}
                          {m.model}
                        </td>
                        <td className="px-4 py-3">${(m.mae ?? 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                        <td className="px-4 py-3">${(m.rmse ?? 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                        <td className="px-4 py-3">{(m.mape_pct ?? 0).toFixed(2)}%</td>
                        <td className="px-4 py-3 font-bold text-slate-800">{(m.directional_accuracy_pct ?? 0).toFixed(1)}%</td>
                        <td className="px-4 py-3">
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            m.status?.includes('Champion') ? 'bg-indigo-100 text-indigo-800' :
                            m.status?.includes('Challenger') ? 'bg-blue-100 text-blue-800' :
                            'bg-slate-100 text-slate-600'
                          }`}>
                            {m.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Monthly Prediction Comparison */}
              <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
                <div className="p-4 border-b border-slate-200 bg-slate-50">
                  <h3 className="text-sm font-bold text-slate-800">Month-by-Month Holdout Comparison ($ USD)</h3>
                  <p className="text-xs text-slate-500">Predicted trajectory vs realized actual revenue</p>
                </div>
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase">
                    <tr>
                      <th className="px-4 py-3">Holdout Period</th>
                      <th className="px-4 py-3">Actual Revenue</th>
                      <th className="px-4 py-3 text-indigo-700">Holt-Winters (Champion)</th>
                      <th className="px-4 py-3">ARIMA (1,1,1)</th>
                      <th className="px-4 py-3">3-Mo Moving Avg</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    {(benchmark.monthly_comparison ?? []).map((row, i) => (
                      <tr key={i} className="hover:bg-slate-50">
                        <td className="px-4 py-2.5 font-bold text-slate-800">{row.period}</td>
                        <td className="px-4 py-2.5 font-semibold text-slate-900">${(row.actual ?? 0).toLocaleString()}</td>
                        <td className="px-4 py-2.5 font-bold text-indigo-700">${(row.holt_winters ?? 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                        <td className="px-4 py-2.5 text-slate-600">${(row.arima ?? 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                        <td className="px-4 py-2.5 text-slate-500">${(row.moving_avg ?? 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <div className="p-8 text-center text-slate-500">Benchmark data unavailable.</div>
          )}
        </div>
      )}
    </div>
  )
}
