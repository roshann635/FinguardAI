import { useState } from 'react'
import { FileText } from 'lucide-react'
import { generateExecutiveBrief } from '../../services/api'

interface TopBarProps {
  title: string
  onPeriodChange?: (period: string) => void
  onRegionChange?: (region: string) => void
  period?: string
  region?: string
}

const PERIOD_OPTIONS = [
  { value: 'last_30_days', label: 'Last 30 Days' },
  { value: 'last_90_days', label: 'Last 90 Days' },
  { value: 'last_12_months', label: 'Last 12 Months' },
  { value: 'year_to_date', label: 'Year to Date' },
]

const REGION_OPTIONS = [
  { value: 'all', label: 'All Regions' },
  { value: 'north', label: 'North' },
  { value: 'south', label: 'South' },
  { value: 'east', label: 'East' },
  { value: 'west', label: 'West' },
  { value: 'central', label: 'Central' },
]

export default function TopBar({ title, onPeriodChange, onRegionChange, period = 'last_12_months', region = 'all' }: TopBarProps) {
  const [briefLoading, setBriefLoading] = useState(false)
  const [briefError, setBriefError] = useState<string | null>(null)

  const handleGenerateBrief = async () => {
    setBriefLoading(true)
    setBriefError(null)
    try {
      const result = await generateExecutiveBrief(period)
      // Open brief in a new browser tab as plain text
      const blob = new Blob([result.brief], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      window.open(url, '_blank')
    } catch (e) {
      setBriefError(e instanceof Error ? e.message : 'Failed to generate brief')
    } finally {
      setBriefLoading(false)
    }
  }

  return (
    <header className="sticky top-0 z-10 bg-white border-b border-slate-200 h-14 flex items-center px-6 gap-4">
      <h1 className="text-base font-semibold text-slate-800 flex-1 truncate">{title}</h1>

      {/* Filters */}
      <div className="flex items-center gap-2">
        <select
          value={period}
          onChange={e => onPeriodChange?.(e.target.value)}
          className="text-sm border border-slate-200 rounded-md px-2 py-1.5 text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          {PERIOD_OPTIONS.map(o => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>

        <select
          value={region}
          onChange={e => onRegionChange?.(e.target.value)}
          className="text-sm border border-slate-200 rounded-md px-2 py-1.5 text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          {REGION_OPTIONS.map(o => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>

      {/* Generate Brief */}
      <button
        onClick={handleGenerateBrief}
        disabled={briefLoading}
        className="flex items-center gap-1.5 bg-primary-700 hover:bg-primary-800 disabled:opacity-60 text-white text-sm font-medium px-3 py-1.5 rounded-md transition-colors"
      >
        <FileText size={14} />
        {briefLoading ? 'Generating…' : 'Executive Brief'}
      </button>

      {briefError && (
        <span className="text-xs text-red-600 max-w-xs truncate" title={briefError}>
          {briefError}
        </span>
      )}

      {/* Dataset As-Of Date Badge */}
      <span className="hidden md:inline-flex items-center text-xs text-slate-600 bg-slate-100 border border-slate-200 px-2.5 py-1 rounded-full font-medium">
        Data through: 31 Mar 2025
      </span>

      {/* Dynamic indicator */}
      <div className="flex items-center gap-1.5 text-xs text-emerald-600 font-medium whitespace-nowrap">
        <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block animate-pulse" />
        Dynamic Analytics
      </div>
    </header>
  )
}
