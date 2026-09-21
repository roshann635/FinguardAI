import axios, { AxiosError } from 'axios'
import type {
  DashboardOverview,
  RevenueAnalytics,
  ProfitAnalytics,
  ExpenseAnalytics,
  CashFlowAnalytics,
  BudgetAnalytics,
  ReceivablesAging,
  RiskScore,
  AnomalyRecord,
  AnomalySummary,
  OpportunityItem,
  ActionItem,
  ForecastResult,
  DataQualityReport,
  AIResponse,
  ExecutiveBriefResponse,
} from '../types'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  timeout: 60000,
})

function handleError(err: unknown, context: string): never {
  if (err instanceof AxiosError) {
    const msg = err.response?.data?.detail ?? err.response?.data?.message ?? err.message
    throw new Error(`${context}: ${msg}`)
  }
  throw new Error(`${context}: Unknown error`)
}

// ─── Dashboard ────────────────────────────────────────────────────────────────

export async function fetchDashboardOverview(period = 'last_12_months'): Promise<DashboardOverview> {
  try {
    const { data } = await api.get<DashboardOverview>('/dashboard/overview', { params: { period } })
    return data
  } catch (err) {
    return handleError(err, 'fetchDashboardOverview')
  }
}

// ─── Revenue ──────────────────────────────────────────────────────────────────

export async function fetchRevenueAnalytics(params?: {
  period?: string
  group_by?: string
}): Promise<RevenueAnalytics> {
  try {
    const { data } = await api.get<RevenueAnalytics>('/analytics/revenue', { params })
    return data
  } catch (err) {
    return handleError(err, 'fetchRevenueAnalytics')
  }
}

// ─── Profit ───────────────────────────────────────────────────────────────────

export async function fetchProfitAnalytics(params?: {
  period?: string
}): Promise<ProfitAnalytics> {
  try {
    const { data } = await api.get<ProfitAnalytics>('/analytics/profit', { params })
    return data
  } catch (err) {
    return handleError(err, 'fetchProfitAnalytics')
  }
}

// ─── Expenses ─────────────────────────────────────────────────────────────────

export async function fetchExpenseAnalytics(params?: {
  period?: string
  group_by?: string
}): Promise<ExpenseAnalytics> {
  try {
    const { data } = await api.get<ExpenseAnalytics>('/analytics/expenses', { params })
    return data
  } catch (err) {
    return handleError(err, 'fetchExpenseAnalytics')
  }
}

// ─── Cash Flow ────────────────────────────────────────────────────────────────

export async function fetchCashFlowAnalytics(params?: {
  period?: string
}): Promise<CashFlowAnalytics> {
  try {
    const { data } = await api.get<CashFlowAnalytics>('/analytics/cashflow', { params })
    return data
  } catch (err) {
    return handleError(err, 'fetchCashFlowAnalytics')
  }
}

// ─── Budget ───────────────────────────────────────────────────────────────────

export async function fetchBudgetAnalytics(year?: number): Promise<BudgetAnalytics> {
  try {
    const { data } = await api.get<BudgetAnalytics>('/analytics/budget', { params: { year } })
    return data
  } catch (err) {
    return handleError(err, 'fetchBudgetAnalytics')
  }
}

// ─── Receivables ──────────────────────────────────────────────────────────────

export async function fetchReceivablesAnalytics(): Promise<ReceivablesAging> {
  try {
    const { data } = await api.get<ReceivablesAging>('/analytics/receivables')
    return data
  } catch (err) {
    return handleError(err, 'fetchReceivablesAnalytics')
  }
}

// ─── Risk ─────────────────────────────────────────────────────────────────────

export async function fetchRiskOverview(): Promise<RiskScore> {
  try {
    const { data } = await api.get<RiskScore>('/risk/overview')
    return data
  } catch (err) {
    return handleError(err, 'fetchRiskOverview')
  }
}

export async function fetchExpenseAnomalies(params?: {
  severity?: string
  limit?: number
}): Promise<AnomalyRecord[]> {
  try {
    const { data } = await api.get<AnomalyRecord[]>('/risk/anomalies/expenses', { params })
    return data
  } catch (err) {
    return handleError(err, 'fetchExpenseAnomalies')
  }
}

export async function fetchTransactionAnomalies(params?: {
  severity?: string
  limit?: number
}): Promise<AnomalyRecord[]> {
  try {
    const { data } = await api.get<AnomalyRecord[]>('/risk/anomalies/transactions', { params })
    return data
  } catch (err) {
    return handleError(err, 'fetchTransactionAnomalies')
  }
}

export async function fetchAnomalySummary(): Promise<AnomalySummary> {
  try {
    const { data } = await api.get<AnomalySummary>('/risk/anomalies/summary')
    return data
  } catch (err) {
    return handleError(err, 'fetchAnomalySummary')
  }
}

// ─── Opportunities & Actions ──────────────────────────────────────────────────

export async function fetchOpportunities(): Promise<OpportunityItem[]> {
  try {
    const { data } = await api.get<OpportunityItem[]>('/insights/opportunities')
    return data
  } catch (err) {
    return handleError(err, 'fetchOpportunities')
  }
}

export async function fetchActions(): Promise<ActionItem[]> {
  try {
    const { data } = await api.get<ActionItem[]>('/insights/actions')
    return data
  } catch (err) {
    return handleError(err, 'fetchActions')
  }
}

// ─── Forecasts ────────────────────────────────────────────────────────────────

export async function fetchRevenueForecast(horizonDays = 90): Promise<ForecastResult> {
  try {
    const { data } = await api.get<ForecastResult>('/forecast/revenue', {
      params: { horizon_days: horizonDays },
    })
    return data
  } catch (err) {
    return handleError(err, 'fetchRevenueForecast')
  }
}

// ─── Data Quality ─────────────────────────────────────────────────────────────

export async function fetchDataQuality(): Promise<DataQualityReport> {
  try {
    const { data } = await api.get<DataQualityReport>('/data-quality')
    return data
  } catch (err) {
    return handleError(err, 'fetchDataQuality')
  }
}

// ─── AI ───────────────────────────────────────────────────────────────────────

export async function askAI(question: string, contextPeriod = 'last_12_months'): Promise<AIResponse> {
  try {
    const { data } = await api.post<AIResponse>('/ai/ask', {
      question,
      context_period: contextPeriod,
    })
    return data
  } catch (err) {
    return handleError(err, 'askAI')
  }
}

export async function generateExecutiveBrief(period = 'last_12_months'): Promise<ExecutiveBriefResponse> {
  try {
    const { data } = await api.post<ExecutiveBriefResponse>('/ai/executive-brief', { period })
    return data
  } catch (err) {
    return handleError(err, 'generateExecutiveBrief')
  }
}

// ─── System / Metadata ────────────────────────────────────────────────────────

export async function fetchSystemInfo(): Promise<import('../types').SystemInfo> {
  try {
    const { data } = await api.get<import('../types').SystemInfo>('/system/info')
    return data
  } catch (err) {
    return handleError(err, 'fetchSystemInfo')
  }
}

// ─── Investigation Mode ───────────────────────────────────────────────────────

export async function fetchInvestigation(kpi = 'profit', period = 'last_12_months'): Promise<import('../types').InvestigationResult> {
  try {
    const { data } = await api.get<import('../types').InvestigationResult>('/dashboard/investigation', {
      params: { kpi, period },
    })
    return data
  } catch (err) {
    return handleError(err, 'fetchInvestigation')
  }
}

// ─── Forecast Multi-Model Comparison ──────────────────────────────────────────

export async function fetchForecastComparison(): Promise<import('../types').ForecastComparisonResult> {
  try {
    const { data } = await api.get<import('../types').ForecastComparisonResult>('/forecast/comparison')
    return data
  } catch (err) {
    return handleError(err, 'fetchForecastComparison')
  }
}

// ─── Financial Health Score ───────────────────────────────────────────────────

export async function fetchFinancialHealthScore(): Promise<import('../types').FinancialHealthScore> {
  try {
    const { data } = await api.get<import('../types').FinancialHealthScore>('/dashboard/health-score')
    return data
  } catch (err) {
    return handleError(err, 'fetchFinancialHealthScore')
  }
}




