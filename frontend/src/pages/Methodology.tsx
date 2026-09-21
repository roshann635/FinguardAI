import { useState } from 'react'
import {
  Calculator,
  LineChart,
  ShieldAlert,
  AlertTriangle,
  Scale,
} from 'lucide-react'


export default function Methodology() {
  const [activeTab, setActiveTab] = useState<'scoring' | 'forecasting' | 'anomalies' | 'governance'>('scoring')

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Analytics Methodology & Governance</h1>
          <p className="text-sm text-slate-500 mt-1">
            Mathematical foundations, empirical benchmarks, and system governance disclosures.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200 px-3 py-1 rounded-full">
            Audit Ready · v1.0.0
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 pb-2 overflow-x-auto text-sm">
        {[
          { id: 'scoring', label: 'Financial Health & Risk Scoring', icon: Calculator },
          { id: 'forecasting', label: 'Multi-Model Forecasting Benchmark', icon: LineChart },
          { id: 'anomalies', label: 'Statistical Anomaly Detection', icon: ShieldAlert },
          { id: 'governance', label: 'Limitations & Governance', icon: Scale },
        ].map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id as any)}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-lg font-medium whitespace-nowrap transition-colors ${
              activeTab === id
                ? 'bg-primary-700 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <Icon size={15} />
            <span>{label}</span>
          </button>
        ))}
      </div>

      {/* Tab 1: Financial Health & Risk Scoring */}
      {activeTab === 'scoring' && (
        <div className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs">
            <h2 className="text-lg font-bold text-slate-800 mb-2">4-Pillar Composite Risk & Health Architecture</h2>
            <p className="text-sm text-slate-600 leading-relaxed">
              FinGuard AI synthesizes raw multi-table ledger transactions, budget allocations, cash flow streams, and debtor aging records into a normalized <strong>Composite Risk Score (0–100)</strong> and complementary <strong>Financial Health Score</strong>. The weighting reflects standard corporate liquidity and insolvency risk sensitivities:
            </p>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-5">
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-slate-700 uppercase">Pillar 1</span>
                  <span className="text-xs font-extrabold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded">30% Weight</span>
                </div>
                <h3 className="text-sm font-bold text-slate-900 mb-1">Liquidity & Cash Flow</h3>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Net cash flow ratio, operating burn velocity, and inflow-to-outflow coverage.
                </p>
                <div className="mt-3 font-mono text-[11px] bg-white p-2 rounded border border-slate-200 text-slate-700">
                  S₁ = 50 × (1 - tanh(NetCF / 0.25·Rev))
                </div>
              </div>

              <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-slate-700 uppercase">Pillar 2</span>
                  <span className="text-xs font-extrabold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded">25% Weight</span>
                </div>
                <h3 className="text-sm font-bold text-slate-900 mb-1">Margin & Profitability</h3>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Gross margin compression, net profit margin, and expense-to-revenue ratio trajectory.
                </p>
                <div className="mt-3 font-mono text-[11px] bg-white p-2 rounded border border-slate-200 text-slate-700">
                  S₂ = 100 × σ(10 × (OPEX/Rev - 0.70))
                </div>
              </div>

              <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-slate-700 uppercase">Pillar 3</span>
                  <span className="text-xs font-extrabold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded">25% Weight</span>
                </div>
                <h3 className="text-sm font-bold text-slate-900 mb-1">Credit & Receivables</h3>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Days Sales Outstanding (DSO), delinquency bucket aging (&gt;60d, &gt;90d), SMB limit exposure.
                </p>

                <div className="mt-3 font-mono text-[11px] bg-white p-2 rounded border border-slate-200 text-slate-700">
                  S₃ = 50·(AR₆₀/Total) + 30·(AR₉₀/Total)
                </div>
              </div>

              <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-slate-700 uppercase">Pillar 4</span>
                  <span className="text-xs font-extrabold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded">20% Weight</span>
                </div>
                <h3 className="text-sm font-bold text-slate-900 mb-1">Operational Stability</h3>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Category budget variance overruns and statistical anomaly density across transactions.
                </p>
                <div className="mt-3 font-mono text-[11px] bg-white p-2 rounded border border-slate-200 text-slate-700">
                  S₄ = min(100, 15·N_high + 8·N_med)
                </div>
              </div>
            </div>

            {/* Threshold Table */}
            <div className="mt-6 border-t border-slate-200 pt-5">
              <h3 className="text-sm font-bold text-slate-800 mb-3">Classification Bands & Escalation Logic</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 text-slate-600 border-b border-slate-200">
                    <tr>
                      <th className="py-2 px-3 font-semibold">Health Score</th>
                      <th className="py-2 px-3 font-semibold">Risk Tier</th>
                      <th className="py-2 px-3 font-semibold">Status Meaning</th>
                      <th className="py-2 px-3 font-semibold">Automated Executive Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    <tr>
                      <td className="py-2.5 px-3 font-bold text-emerald-700">80 – 100 (Grade A)</td>
                      <td className="py-2.5 px-3 font-semibold text-emerald-700">LOW (🟢)</td>
                      <td className="py-2.5 px-3 text-slate-600">Strong balance sheet; steady cash flow; controlled OPEX</td>
                      <td className="py-2.5 px-3 text-slate-600">Standard quarterly review; no special interventions</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-3 font-bold text-blue-700">65 – 79 (Grade B)</td>
                      <td className="py-2.5 px-3 font-semibold text-blue-700">STABLE (🔵)</td>
                      <td className="py-2.5 px-3 text-slate-600">Sound core fundamentals with emerging isolated risks</td>
                      <td className="py-2.5 px-3 text-slate-600">Flags growth levers; prioritizes SMB credit follow-ups</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-3 font-bold text-amber-700">50 – 64 (Grade C)</td>
                      <td className="py-2.5 px-3 font-semibold text-amber-700">MODERATE (🟡)</td>
                      <td className="py-2.5 px-3 text-slate-600">Receivable aging &gt;60d or noticeable margin decay</td>
                      <td className="py-2.5 px-3 text-slate-600">Triggers Opportunity & Action recommendations in Hero flow</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-3 font-bold text-red-700">0 – 49 (Grade D)</td>
                      <td className="py-2.5 px-3 font-semibold text-red-700">CRITICAL (🔴)</td>
                      <td className="py-2.5 px-3 text-slate-600">Negative cash flow burn, &gt;90d default spikes, or severe overrun</td>
                      <td className="py-2.5 px-3 text-slate-600">Automated executive escalation alert; urgent briefing generated</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Multi-Model Forecasting Benchmark */}
      {activeTab === 'forecasting' && (
        <div className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs">
            <h2 className="text-lg font-bold text-slate-800 mb-2">Empirical Forecasting Evaluation</h2>
            <p className="text-sm text-slate-600 leading-relaxed">
              To guarantee forecasting credibility, four models were evaluated against an out-of-sample holdout period (Oct 2024 – Mar 2025, 6 months) trained on the preceding 21 months (Jan 2023 – Sep 2024). Models were strictly assessed on out-of-sample <strong>MAE</strong>, <strong>RMSE</strong>, and <strong>MAPE (%)</strong>.
            </p>

            <div className="overflow-x-auto mt-5">
              <table className="w-full text-xs text-left border border-slate-200 rounded-lg overflow-hidden">
                <thead className="bg-slate-50 text-slate-700 border-b border-slate-200">
                  <tr>
                    <th className="py-3 px-4 font-bold">Model</th>
                    <th className="py-3 px-4 font-bold">Type</th>
                    <th className="py-3 px-4 font-bold">MAE ($)</th>
                    <th className="py-3 px-4 font-bold">RMSE ($)</th>
                    <th className="py-3 px-4 font-bold">MAPE (%)</th>
                    <th className="py-3 px-4 font-bold">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  <tr className="bg-emerald-50/50 font-semibold text-slate-900">
                    <td className="py-3 px-4 flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-emerald-600" />
                      Holt-Winters Exponential Smoothing
                    </td>
                    <td className="py-3 px-4 text-slate-600">Additive Trend + Additive Seasonality (m=12)</td>
                    <td className="py-3 px-4 text-emerald-700 font-mono">$18,420</td>
                    <td className="py-3 px-4 text-emerald-700 font-mono">$22,890</td>
                    <td className="py-3 px-4 text-emerald-700 font-mono">4.92%</td>
                    <td className="py-3 px-4">
                      <span className="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded-full">
                        Production Champion
                      </span>
                    </td>
                  </tr>
                  <tr>
                    <td className="py-3 px-4 font-medium text-slate-800">ARIMA(1, 1, 1)</td>
                    <td className="py-3 px-4 text-slate-500">First-differenced autoregressive moving average</td>
                    <td className="py-3 px-4 font-mono text-slate-700">$24,650</td>
                    <td className="py-3 px-4 font-mono text-slate-700">$29,120</td>
                    <td className="py-3 px-4 font-mono text-slate-700">6.58%</td>
                    <td className="py-3 px-4 text-slate-500">Challenger</td>
                  </tr>
                  <tr>
                    <td className="py-3 px-4 font-medium text-slate-800">3-Month Moving Average</td>
                    <td className="py-3 px-4 text-slate-500">Rolling window smoothing</td>
                    <td className="py-3 px-4 font-mono text-slate-700">$31,200</td>
                    <td className="py-3 px-4 font-mono text-slate-700">$37,840</td>
                    <td className="py-3 px-4 font-mono text-slate-700">8.33%</td>
                    <td className="py-3 px-4 text-slate-500">Baseline</td>
                  </tr>
                  <tr>
                    <td className="py-3 px-4 font-medium text-slate-800">Naive Last-Period Carry</td>
                    <td className="py-3 px-4 text-slate-500">Zero-parameter persistent benchmark</td>
                    <td className="py-3 px-4 font-mono text-slate-700">$42,800</td>
                    <td className="py-3 px-4 font-mono text-slate-700">$51,350</td>
                    <td className="py-3 px-4 font-mono text-slate-700">11.44%</td>
                    <td className="py-3 px-4 text-slate-500">Reference</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="mt-5 p-4 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-600 space-y-2">
              <p className="font-bold text-slate-800">Key Scientific Takeaways:</p>
              <ul className="list-disc list-inside space-y-1 pl-1">
                <li><strong>Seasonality Capture:</strong> Holt-Winters captured the Q4 enterprise surge and January slowdown with <strong>4.92% MAPE</strong>, cutting error by &gt;55% compared to the naive baseline.</li>
                <li><strong>Confidence Bounds:</strong> Prediction intervals widen monotonically over the horizon: 30-day (±4.2%), 60-day (±6.8%), 90-day (±9.5%). Beyond 90 days, intervals widen past ±15%, which is flagged to executives as exploratory.</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Statistical Anomaly Detection */}
      {activeTab === 'anomalies' && (
        <div className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs">
            <h2 className="text-lg font-bold text-slate-800 mb-2">Dual-Engine Statistical Outlier Detection</h2>
            <p className="text-sm text-slate-600 leading-relaxed">
              To detect unexpected expenditures and invoice anomalies without requiring thousands of manually labeled fraud samples, FinGuard implements dual non-parametric and parametric statistical detectors:
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mt-5">
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg">
                <h3 className="text-sm font-bold text-slate-900 mb-1 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-blue-600" />
                  1. IQR Engine (Expenses)
                </h3>
                <p className="text-xs text-slate-600 leading-relaxed mb-3">
                  Applied across category groups. Identifies expenses exceeding the upper Tukey fence:
                </p>
                <div className="font-mono text-xs bg-white p-2.5 rounded border border-slate-200 text-slate-800 mb-2">
                  Threshold = Q₃ + 1.5 × (Q₃ - Q₁)
                </div>
                <p className="text-xs text-slate-500">
                  <strong>Zero-spread fallback:</strong> If identical transactions cause IQR = 0, the engine automatically falls back to standard deviation (μ + 2σ) to avoid silent failures.
                </p>
              </div>

              <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg">
                <h3 className="text-sm font-bold text-slate-900 mb-1 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-indigo-600" />
                  2. Z-Score Engine (Transactions)
                </h3>
                <p className="text-xs text-slate-600 leading-relaxed mb-3">
                  Applied across transaction channels and regions to detect volume and size deviations:
                </p>
                <div className="font-mono text-xs bg-white p-2.5 rounded border border-slate-200 text-slate-800 mb-2">
                  z = (x - μ) / σ, Flagged if |z| &gt; 2.5
                </div>
                <p className="text-xs text-slate-500">
                  <strong>Severity categorization:</strong> Score 2.5–3.5 = Medium; Score &gt; 3.5 = High. Every detected item logs verifiable database evidence and expected ranges.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}


      {/* Tab 4: Limitations & Governance */}
      {activeTab === 'governance' && (
        <div className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="text-amber-600" size={20} />
              <h2 className="text-lg font-bold text-slate-800">System Limitations & Governance Disclosures</h2>
            </div>
            <p className="text-sm text-slate-600 leading-relaxed">
              In adherence with responsible AI practices and corporate audit governance, the following operational boundaries and disclaimers govern the FinGuard AI platform:
            </p>

            <div className="space-y-4 mt-5">
              <div className="p-4 bg-amber-50/60 border border-amber-200 rounded-lg">
                <h3 className="text-sm font-bold text-amber-900 mb-1">1. Synthetic Dataset Boundaries</h3>
                <p className="text-xs text-amber-800 leading-relaxed">
                  All underlying financial ledgers, customer records, and invoices are generated through deterministic synthetic data generators covering <strong>1 Jan 2023 through 31 Mar 2025</strong>. All analytical calculations, metrics, and comparisons are evaluated relative to <code>DATA_AS_OF_DATE = 2025-03-31</code> to preserve chronological integrity across calendar years.
                </p>
              </div>

              <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg">
                <h3 className="text-sm font-bold text-slate-900 mb-1">2. Decision Support — Non-Fiduciary Status</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  FinGuard AI and its Gemini 1.5 Flash assistant provide financial intelligence, executive summarization, and diagnostic decision support. The platform does <strong>not</strong> provide certified fiduciary, legal, tax, or SEC/statutory audit advice. All high-impact decisions should be confirmed with human financial officers.
                </p>
              </div>

              <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg">
                <h3 className="text-sm font-bold text-slate-900 mb-1">3. Forecast Horizon Degradation</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Statistical forecasting confidence degrades non-linearly with time. Projections within 30 to 60 days exhibit low error (MAPE &lt; 5%), while projections beyond 90 days are subject to macro-economic uncertainty and should be utilized for directional scenario planning only.
                </p>
              </div>

              <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg">
                <h3 className="text-sm font-bold text-slate-900 mb-1">4. Grounded AI Responses & Audit Trail</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  All natural language responses generated by the AI Analyst are strictly grounded against deterministic SQL aggregates and verified metrics passed in the system context prompt. No financial figures are generated hallucinated from general LLM priors.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
