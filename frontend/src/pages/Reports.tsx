import { useState } from 'react'
import { generateExecutiveBrief } from '../services/api'
import type { ExecutiveBriefResponse } from '../types'
import { FileText, Loader2, Printer, Download, ShieldCheck, Building2 } from 'lucide-react'
import { useFilters } from '../components/layout/Layout'



export default function Reports() {
  const { period } = useFilters()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [brief, setBrief] = useState<ExecutiveBriefResponse | null>(null)

  const handleGenerate = async () => {
    setLoading(true)
    setError(null)
    try {
      setBrief(await generateExecutiveBrief(period))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to generate report')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-5">
      {/* Non-print controls header */}
      <div className="print:hidden">
        <h1 className="text-2xl font-bold text-slate-800">Executive Reports & PDF Dossier</h1>
        <p className="text-sm text-slate-500 mt-1">
          Generate formal audit-grade financial briefings and export as PDF or Markdown.
        </p>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-6 print:hidden">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 bg-primary-50 rounded-lg flex items-center justify-center">
            <FileText size={22} className="text-primary-700" />
          </div>
          <div className="flex-1">
            <h3 className="text-base font-semibold text-slate-800">Corporate Executive Financial Dossier</h3>
            <p className="text-sm text-slate-500 mt-0.5">
              Grounded AI synthesis of corporate performance, solvency indicators, emerging risks, and prioritized management decisions for the selected reporting window.
            </p>
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <button
                onClick={handleGenerate}
                disabled={loading}
                className="flex items-center gap-2 bg-primary-700 hover:bg-primary-800 disabled:opacity-60 text-white text-sm font-medium px-4 py-2 rounded-md transition-colors shadow-xs"
              >
                {loading ? <Loader2 size={14} className="animate-spin" /> : <FileText size={14} />}
                {loading ? 'Compiling Dossier…' : 'Generate Executive Report'}
              </button>
              {brief && (
                <>
                  <button
                    onClick={() => window.print()}
                    className="flex items-center gap-2 bg-slate-900 hover:bg-black text-white text-sm font-medium px-4 py-2 rounded-md transition-colors shadow-xs"
                  >
                    <Printer size={14} />
                    Export / Print as PDF
                  </button>
                  <button
                    onClick={() => {
                      const content = `# FinGuard AI — Corporate Financial Dossier\nPeriod: ${brief.period}\nGenerated: ${new Date(brief.generated_at).toLocaleString()}\nData through: 31 Mar 2025\nDataset: Synthetic demonstration dataset (Jan 2023 - Mar 2025)\n\n## Key Financial Metrics\n${Object.entries(brief.key_metrics).map(([k, v]) => `- **${k}**: ${v}`).join('\n')}\n\n## Executive Narrative & Strategic Analysis\n${brief.brief}\n\n---\n*Audit Statement: All metrics verified through deterministic ledger aggregation. Non-fiduciary decision support.*`
                      const blob = new Blob([content], { type: 'text/markdown' })
                      const url = URL.createObjectURL(blob)
                      const a = document.createElement('a')
                      a.href = url
                      a.download = `finguard-executive-report-${brief.period}.md`
                      a.click()
                    }}
                    className="flex items-center gap-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-sm font-medium px-4 py-2 rounded-md transition-colors"
                  >
                    <Download size={14} />
                    Download Markdown (.md)
                  </button>
                </>
              )}
            </div>
            {error && <p className="text-xs text-red-600 mt-2 font-medium">{error}</p>}
          </div>
        </div>
      </div>

      {brief && (
        <div
          id="printable-report"
          className="bg-white border border-slate-200 rounded-xl shadow-sm p-8 print:p-0 print:border-none print:shadow-none space-y-6"
        >
          {/* Official Document Header */}
          <div className="border-b-2 border-slate-800 pb-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Building2 size={20} className="text-primary-700 print:text-black" />
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                  FinGuard AI · Financial Intelligence
                </span>
              </div>
              <h2 className="text-2xl font-black text-slate-900 tracking-tight">
                Executive Financial Audit & Strategic Brief
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Reporting Window: <strong>{brief.period}</strong> · Data Boundary: <strong>31 Mar 2025</strong> · Generated: {new Date(brief.generated_at).toLocaleString()}
              </p>
            </div>

            <div className="flex flex-col sm:items-end gap-1">
              <span className="inline-flex items-center gap-1.5 text-[11px] font-bold px-2.5 py-1 rounded bg-slate-100 text-slate-800 border border-slate-200 uppercase">
                <ShieldCheck size={13} className="text-emerald-600" />
                Grounded Ledger Audit
              </span>
              <span className="text-[10px] text-slate-400">Classification: Corporate Confidential</span>
            </div>
          </div>

          {/* Key Metrics Snapshot */}
          {Object.keys(brief.key_metrics).length > 0 && (
            <div className="space-y-2.5">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600">
                1. Executive Financial Snapshot
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {Object.entries(brief.key_metrics).map(([k, v]) => (
                  <div key={k} className="bg-slate-50 border border-slate-200 rounded-lg p-3">
                    <p className="text-[11px] font-medium text-slate-500">{k}</p>
                    <p className="text-base font-extrabold text-slate-900 mt-0.5">{v}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Executive Narrative */}
          <div className="space-y-2.5 pt-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600">
              2. Strategic Performance & Risk Assessment
            </h3>
            <div className="bg-slate-50/50 border border-slate-200 rounded-lg p-5">
              <div className="text-sm text-slate-800 whitespace-pre-line leading-relaxed">
                {brief.brief}
              </div>
            </div>
          </div>

          {/* Audit Verification Block */}
          <div className="border-t border-slate-200 pt-6 mt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-500">
              <div>
                <p className="font-semibold text-slate-700 mb-0.5">Integrity & Governance Notice:</p>
                <p className="leading-relaxed">
                  Calculations derived from ledger transactions, invoice payment cycles, and OPEX classifications covering 1 Jan 2023 – 31 Mar 2025. Prepared for executive decision support; non-fiduciary status.
                </p>
              </div>
              <div className="flex flex-col justify-end sm:items-end text-[11px]">
                <p className="font-mono text-slate-400">FIN-GUARD-VERIFIED-{new Date(brief.generated_at).getTime().toString().slice(-8)}</p>
                <div className="mt-2 pt-2 border-t border-slate-300 w-48 text-center text-slate-600 font-medium">
                  Authorised Signatory
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
