import { useEffect, useState, type ReactNode } from 'react'
import { Settings as SettingsIcon, Info, Database, CheckCircle2 } from 'lucide-react'
import { fetchSystemInfo } from '../services/api'
import type { SystemInfo } from '../types'

function SettingRow({ label, description, children }: { label: string; description?: string; children: ReactNode }) {
  return (
    <div className="flex items-start justify-between py-4 border-b border-slate-100 last:border-b-0">
      <div className="flex-1 pr-8">
        <p className="text-sm font-medium text-slate-800">{label}</p>
        {description && <p className="text-xs text-slate-500 mt-0.5">{description}</p>}
      </div>
      {children}
    </div>
  )
}

function SectionCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5">
      <h3 className="text-sm font-semibold text-slate-600 uppercase tracking-wide mb-1">{title}</h3>
      <div>{children}</div>
    </div>
  )
}

export default function Settings() {
  const [sysInfo, setSysInfo] = useState<SystemInfo | null>(null)

  useEffect(() => {
    fetchSystemInfo()
      .then(setSysInfo)
      .catch(() => {
        // Fallback default info if backend unavailable
        setSysInfo({
          app_name: 'FinGuard AI',
          version: '1.0.0',
          environment: 'development',
          dataset_type: 'Synthetic demonstration dataset · Jan 2023 – Mar 2025',
          dataset_period: {
            start: '2023-01-01',
            end: '2025-03-31',
            display: 'Jan 2023 – Mar 2025',
          },
          data_as_of_date: '2025-03-31',
          data_as_of_display: '31 Mar 2025',
          record_counts: {
            transactions: 5000,
            expenses: 1200,
            invoices: 850,
            customers: 120,
            vendors: 45,
            products: 60,
            cash_flows: 1500,
            budgets: 48,
          },
          total_records: 8823,
          currency: 'USD',
        })
      })
  }, [])

  return (
    <div className="space-y-5 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Settings & Dataset Metadata</h1>
        <p className="text-sm text-slate-500 mt-1">Configure display preferences and view analytical boundary information.</p>
      </div>

      {/* Dataset Attribution Notice */}
      <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 flex gap-3">
        <Info size={18} className="text-indigo-600 flex-shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="text-sm font-semibold text-indigo-900">
            Analytical Boundary: {sysInfo?.data_as_of_display ?? '31 Mar 2025'}
          </p>
          <p className="text-xs text-indigo-700 leading-relaxed">
            This platform operates on a verified synthetic demonstration dataset covering Jan 2023 – Mar 2025.
            All analytics, risk engines, anomalies, and AI reasoning compute metrics relative to this fixed
            analytical boundary rather than current clock time to ensure 100% reproducible evaluations.
          </p>
        </div>
      </div>

      {/* Dataset Statistics Card */}
      <SectionCard title="Dataset Inventory & Health">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 py-3">
          <div className="bg-slate-50 border border-slate-100 rounded-lg p-3">
            <p className="text-xs text-slate-500 font-medium">As-Of Date</p>
            <p className="text-base font-bold text-slate-800 mt-0.5">{sysInfo?.data_as_of_display ?? '31 Mar 2025'}</p>
            <p className="text-[10px] text-emerald-600 mt-1 flex items-center gap-1">
              <CheckCircle2 size={10} /> Active Boundary
            </p>
          </div>
          <div className="bg-slate-50 border border-slate-100 rounded-lg p-3">
            <p className="text-xs text-slate-500 font-medium">Total Records</p>
            <p className="text-base font-bold text-slate-800 mt-0.5">{sysInfo?.total_records?.toLocaleString() ?? '8,800+'}</p>
            <p className="text-[10px] text-slate-500 mt-1">Across 8 tables</p>
          </div>
          <div className="bg-slate-50 border border-slate-100 rounded-lg p-3">
            <p className="text-xs text-slate-500 font-medium">Dataset Coverage</p>
            <p className="text-base font-bold text-slate-800 mt-0.5">27 Months</p>
            <p className="text-[10px] text-slate-500 mt-1">Jan 2023 – Mar 2025</p>
          </div>
          <div className="bg-slate-50 border border-slate-100 rounded-lg p-3">
            <p className="text-xs text-slate-500 font-medium">Dataset Type</p>
            <p className="text-base font-bold text-slate-800 mt-0.5">Synthetic</p>
            <p className="text-[10px] text-slate-500 mt-1">Deterministic Seed</p>
          </div>
        </div>

        {sysInfo?.record_counts && (
          <div className="border-t border-slate-100 pt-3 mt-1">
            <p className="text-xs font-semibold text-slate-600 mb-2 flex items-center gap-1.5">
              <Database size={13} className="text-slate-500" /> Record Counts by Entity
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs text-slate-600">
              <div className="flex justify-between py-1 px-2 rounded bg-slate-50">
                <span>Transactions:</span>
                <span className="font-semibold text-slate-800">{sysInfo.record_counts.transactions?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between py-1 px-2 rounded bg-slate-50">
                <span>Expenses:</span>
                <span className="font-semibold text-slate-800">{sysInfo.record_counts.expenses?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between py-1 px-2 rounded bg-slate-50">
                <span>Invoices:</span>
                <span className="font-semibold text-slate-800">{sysInfo.record_counts.invoices?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between py-1 px-2 rounded bg-slate-50">
                <span>Cash Flows:</span>
                <span className="font-semibold text-slate-800">{sysInfo.record_counts.cash_flows?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between py-1 px-2 rounded bg-slate-50">
                <span>Customers:</span>
                <span className="font-semibold text-slate-800">{sysInfo.record_counts.customers?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between py-1 px-2 rounded bg-slate-50">
                <span>Vendors:</span>
                <span className="font-semibold text-slate-800">{sysInfo.record_counts.vendors?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between py-1 px-2 rounded bg-slate-50">
                <span>Products:</span>
                <span className="font-semibold text-slate-800">{sysInfo.record_counts.products?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between py-1 px-2 rounded bg-slate-50">
                <span>Budgets:</span>
                <span className="font-semibold text-slate-800">{sysInfo.record_counts.budgets?.toLocaleString()}</span>
              </div>
            </div>
          </div>
        )}
      </SectionCard>

      {/* Display Settings */}
      <SectionCard title="Display & Formatting">
        <SettingRow label="Base Currency" description="Currency unit used for revenue, expenses, and cash flow">
          <select
            defaultValue="USD"
            className="text-sm border border-slate-200 rounded-md px-2 py-1.5 text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="USD">$ USD (US Dollar — Primary)</option>
          </select>
        </SettingRow>
        <SettingRow label="Default Analysis Period" description="Default date range shown when opening dashboard pages">
          <select
            defaultValue="last_12_months"
            className="text-sm border border-slate-200 rounded-md px-2 py-1.5 text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="last_30_days">Last 30 Days (relative to 31 Mar 2025)</option>
            <option value="last_90_days">Last 90 Days</option>
            <option value="last_12_months">Last 12 Months (Apr 2024 – Mar 2025)</option>
            <option value="year_to_date">Year to Date (Jan 2025 – Mar 2025)</option>
          </select>
        </SettingRow>
        <SettingRow label="Number Formatting" description="Display style for high-value metrics">
          <select
            defaultValue="abbreviated"
            className="text-sm border border-slate-200 rounded-md px-2 py-1.5 text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="abbreviated">Abbreviated ($84.6M / $450K)</option>
            <option value="full">Full Value ($84,600,000.00)</option>
          </select>
        </SettingRow>
      </SectionCard>

      {/* Risk Thresholds */}
      <SectionCard title="Risk Thresholds">
        <SettingRow label="High Risk Score Threshold" description="Composite risk scores above this value trigger HIGH alerts">
          <input
            type="number"
            defaultValue={70}
            min={0}
            max={100}
            className="w-20 text-sm border border-slate-200 rounded-md px-2 py-1.5 text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </SettingRow>
        <SettingRow label="Anomaly Z-Score Threshold" description="Statistical sensitivity for transaction outlier detection">
          <input
            type="number"
            defaultValue={2.5}
            step={0.1}
            min={1}
            max={5}
            className="w-20 text-sm border border-slate-200 rounded-md px-2 py-1.5 text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </SettingRow>
        <SettingRow label="Budget Overrun Warning %" description="Budget utilisation above this percentage triggers a variance flag">
          <input
            type="number"
            defaultValue={90}
            min={50}
            max={100}
            className="w-20 text-sm border border-slate-200 rounded-md px-2 py-1.5 text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </SettingRow>
      </SectionCard>

      {/* AI Settings */}
      <SectionCard title="AI Intelligence Engine">
        <SettingRow label="Foundation Model" description="Large language model backing the Executive Financial Analyst">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-slate-700">Google Gemini 1.5 Flash</span>
            <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-medium">Grounded Prompting</span>
          </div>
        </SettingRow>
        <SettingRow label="Context Lookback" description="Verified analytical payload injected into AI prompts">
          <select
            defaultValue="last_12_months"
            className="text-sm border border-slate-200 rounded-md px-2 py-1.5 text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="last_3_months">Last 3 Months (Focus on Q1 2025)</option>
            <option value="last_12_months">Last 12 Months (Apr 2024 – Mar 2025)</option>
            <option value="all">Full Dataset (Jan 2023 – Mar 2025)</option>
          </select>
        </SettingRow>
        <div className="py-3">
          <div className="flex items-start gap-2 text-xs text-slate-500">
            <SettingsIcon size={12} className="mt-0.5 flex-shrink-0" />
            <span>
              AI responses are grounded strictly in the verified metrics provided in the system context.
              FinGuard adheres to a zero-fabrication contract: if a metric is unavailable, it is explicitly
              omitted rather than hallucinated.
            </span>
          </div>
        </div>
      </SectionCard>

      {/* About */}
      <SectionCard title="About FinGuard AI">
        <div className="py-2 space-y-1.5 text-sm text-slate-600">
          <p><span className="font-medium text-slate-700">Application:</span> FinGuard AI — Financial Analytics Platform</p>
          <p><span className="font-medium text-slate-700">Version:</span> {sysInfo?.version ?? '1.0.0'}</p>
          <p><span className="font-medium text-slate-700">Dataset:</span> Synthetic demonstration dataset · Jan 2023 – Mar 2025</p>
          <p><span className="font-medium text-slate-700">Analytical Boundary:</span> 31 March 2025</p>
          <p><span className="font-medium text-slate-700">Backend:</span> FastAPI + SQLAlchemy + PostgreSQL</p>
          <p><span className="font-medium text-slate-700">ML Engine:</span> Scikit-Learn + Statsmodels (Holt-Winters / ARIMA)</p>
          <p><span className="font-medium text-slate-700">Frontend:</span> React 18 + Vite + TypeScript + Tailwind CSS</p>
        </div>
      </SectionCard>
    </div>
  )
}
