import { useState, type ReactNode } from 'react'
import { Brain, Send, Loader2, Sparkles, CheckCircle2 } from 'lucide-react'
import { askAI, generateExecutiveBrief } from '../services/api'
import type { AIResponse, ExecutiveBriefResponse } from '../types'
import InsightCardComponent from '../components/ui/InsightCard'
import { useFilters } from '../components/layout/Layout'

const SUGGESTED_QUESTIONS = [
  'Why did profit change?',
  'What are the biggest financial risks?',
  "Summarize this quarter's performance",
  'Which expense categories need attention?',
  'What are the growth opportunities?',
  'How is cash flow trending?',
]

function SectionGroup({ title, color, children }: { title: string; color: string; children: ReactNode }) {
  return (
    <div>
      <h4 className={`text-xs font-bold uppercase tracking-wide mb-2 ${color}`}>{title}</h4>
      <div className="space-y-2">{children}</div>
    </div>
  )
}

export default function AIAnalyst() {
  const { period } = useFilters()
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [response, setResponse] = useState<AIResponse | null>(null)

  const [briefLoading, setBriefLoading] = useState(false)
  const [briefError, setBriefError] = useState<string | null>(null)
  const [brief, setBrief] = useState<ExecutiveBriefResponse | null>(null)

  const handleAsk = async (q?: string) => {
    const finalQ = (q ?? question).trim()
    if (!finalQ) return
    if (!q) setQuestion(finalQ)
    setLoading(true)
    setError(null)
    setResponse(null)
    try {
      const res = await askAI(finalQ, period)
      setResponse(res)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'AI analysis temporarily unavailable')
    } finally {
      setLoading(false)
    }
  }

  const handleBrief = async () => {
    setBriefLoading(true)
    setBriefError(null)
    setBrief(null)
    try {
      setBrief(await generateExecutiveBrief(period))
    } catch (e) {
      setBriefError(e instanceof Error ? e.message : 'Failed to generate executive brief')
    } finally {
      setBriefLoading(false)
    }
  }

  return (
    <div className="space-y-5 max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">AI Analyst</h1>
          <p className="text-sm text-slate-500 mt-1">Ask questions about your financial data.</p>
        </div>
        <div className="flex items-center gap-2">
          <Sparkles size={14} className="text-purple-500" />
          <span className="text-xs font-semibold text-purple-600 bg-purple-50 border border-purple-200 px-2 py-1 rounded-full">
            Powered by Google Gemini 1.5 Flash
          </span>
        </div>
      </div>

      {/* Suggested Questions */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5">
        <p className="text-sm font-medium text-slate-600 mb-3">Suggested questions:</p>
        <div className="flex flex-wrap gap-2">
          {SUGGESTED_QUESTIONS.map(q => (
            <button
              key={q}
              onClick={() => { setQuestion(q); handleAsk(q) }}
              className="text-sm px-3 py-1.5 bg-slate-100 hover:bg-primary-50 hover:text-primary-700 hover:border-primary-300 border border-slate-200 text-slate-600 rounded-full transition-colors"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Input */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5">
        <div className="flex gap-2">
          <Brain size={18} className="text-primary-600 flex-shrink-0 mt-2.5" />
          <textarea
            value={question}
            onChange={e => setQuestion(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleAsk() } }}
            placeholder="Ask FinGuard AI anything about your financial data…"
            rows={2}
            className="flex-1 border border-slate-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 text-slate-800 placeholder:text-slate-400 resize-none"
          />
          <button
            onClick={() => handleAsk()}
            disabled={loading || !question.trim()}
            className="self-end flex items-center gap-1.5 bg-primary-700 hover:bg-primary-800 disabled:opacity-60 text-white text-sm font-medium px-4 py-2 rounded-md transition-colors"
          >
            {loading ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
            {loading ? 'Thinking…' : 'Ask AI'}
          </button>
        </div>
      </div>

      {/* AI Response */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
          <strong>AI analysis temporarily unavailable.</strong> Dashboard metrics remain available.
          <br />
          <span className="text-xs text-red-500">{error}</span>
        </div>
      )}

      {response && (
        <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5 space-y-5">
          {/* Summary */}
          <div className="pb-4 border-b border-slate-100">
            <div className="flex items-center gap-2 mb-2">
              <Brain size={16} className="text-primary-600" />
              <span className="text-sm font-semibold text-slate-700">AI Summary</span>
              <span className="ml-auto text-xs bg-green-50 text-green-700 border border-green-200 px-2 py-0.5 rounded-full font-medium">
                Data Grounded · {response.context_period}
              </span>
            </div>
            <p className="text-sm text-slate-800 leading-relaxed font-medium">{response.summary}</p>
          </div>

          {/* Verified Evidence Drawer */}
          {response.evidence && response.evidence.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-lg p-4 space-y-3 shadow-2xs">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 size={16} className="text-emerald-600" />
                  <h4 className="text-xs font-bold uppercase tracking-wide text-slate-800">
                    Audit Evidence (Verified Financial Analytics)
                  </h4>
                </div>
                <span className="text-[11px] font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
                  As-Of: 31 Mar 2025
                </span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
                {response.evidence.map((ev, i) => (
                  <div key={i} className="bg-slate-50 border border-slate-100 rounded-md p-3">
                    <span className="text-[11px] text-slate-500 block truncate">{ev.metric}</span>
                    <span className="text-sm font-bold text-slate-800 block mt-0.5">{ev.value}</span>
                    <span className="text-[10px] text-primary-700 block truncate mt-1">{ev.source}</span>
                    {ev.context && (
                      <span className="text-[10px] text-slate-400 block mt-0.5">{ev.context}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Facts */}
          {response.facts.length > 0 && (
            <SectionGroup title="Facts" color="text-blue-700">
              {response.facts.map((c, i) => <InsightCardComponent key={i} card={c} />)}
            </SectionGroup>
          )}

          {/* Insights */}
          {response.insights.length > 0 && (
            <SectionGroup title="Insights" color="text-purple-700">
              {response.insights.map((c, i) => <InsightCardComponent key={i} card={c} />)}
            </SectionGroup>
          )}

          {/* Risks */}
          {response.risks.length > 0 && (
            <SectionGroup title="Risks" color="text-red-700">
              {response.risks.map((c, i) => <InsightCardComponent key={i} card={c} />)}
            </SectionGroup>
          )}

          {/* Opportunities */}
          {response.opportunities.length > 0 && (
            <SectionGroup title="Opportunities" color="text-green-700">
              {response.opportunities.map((c, i) => <InsightCardComponent key={i} card={c} />)}
            </SectionGroup>
          )}

          {/* Actions */}
          {response.actions.length > 0 && (
            <SectionGroup title="Recommended Actions" color="text-orange-700">
              {response.actions.map((c, i) => <InsightCardComponent key={i} card={c} />)}
            </SectionGroup>
          )}

          {/* Limitations */}
          {response.limitations && (
            <div className="bg-slate-50 border border-slate-200 rounded p-3 text-xs text-slate-500">
              <strong className="text-slate-600">Limitations:</strong> {response.limitations}
            </div>
          )}

          {response.model_used && (
            <p className="text-[11px] text-slate-400">Model: {response.model_used}</p>
          )}
        </div>
      )}

      {/* Executive Brief */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-base font-semibold text-slate-700">Executive Brief</h3>
            <p className="text-xs text-slate-500 mt-0.5">Generate a comprehensive executive summary for the selected period</p>
          </div>
          <button
            onClick={handleBrief}
            disabled={briefLoading}
            className="flex items-center gap-2 bg-slate-800 hover:bg-slate-900 disabled:opacity-60 text-white text-sm font-medium px-4 py-2 rounded-md transition-colors"
          >
            {briefLoading ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
            {briefLoading ? 'Generating…' : 'Generate Brief'}
          </button>
        </div>

        {briefError && <p className="text-xs text-red-600">{briefError}</p>}

        {brief && (
          <div className="space-y-4">
            <div className="flex flex-wrap gap-3">
              {Object.entries(brief.key_metrics).map(([k, v]) => (
                <div key={k} className="bg-slate-50 border border-slate-100 rounded px-3 py-2 text-xs">
                  <span className="text-slate-500">{k}: </span>
                  <span className="font-semibold text-slate-700">{v}</span>
                </div>
              ))}
            </div>
            <div className="prose prose-sm max-w-none">
              <div className="text-sm text-slate-700 whitespace-pre-line leading-relaxed border-t border-slate-100 pt-4">
                {brief.brief}
              </div>
            </div>
            <p className="text-[11px] text-slate-400">Generated: {new Date(brief.generated_at).toLocaleString()}</p>
          </div>
        )}
      </div>
    </div>
  )
}
