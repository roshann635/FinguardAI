// ─── KPI Types ───────────────────────────────────────────────────────────────

export interface KPIValue {
  value: number
  formatted: string
  previous_value?: number
  change_abs?: number
  change_pct?: number
  direction?: 'up' | 'down' | 'flat'
  interpretation?: string
}

export interface ExecutiveKPIs {
  total_revenue: KPIValue
  total_profit: KPIValue
  profit_margin: KPIValue
  total_expenses: KPIValue
  net_cash_flow: KPIValue
  accounts_receivable: KPIValue
  expense_to_revenue_ratio: KPIValue
  revenue_growth_rate: KPIValue
}

// ─── Analytics Types ──────────────────────────────────────────────────────────

export interface TimeSeriesPoint {
  date: string
  value: number
  label?: string
}

export interface CategoryBreakdown {
  category: string
  value: number
  percentage?: number
  formatted?: string
}

export interface RegionBreakdown {
  region: string
  value: number
  percentage?: number
  formatted?: string
}

export interface BudgetVarianceItem {
  category: string
  budget: number
  actual: number
  variance: number
  variance_pct: number
  status: 'under' | 'near' | 'over'
}

export interface ReceivablesAging {
  current: number
  days_1_30: number
  days_31_60: number
  days_61_90: number
  days_over_90: number
  total: number
  overdue_pct?: number
}

// ─── Risk Types ───────────────────────────────────────────────────────────────

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export interface RiskIndicator {
  name: string
  level: RiskLevel
  value: number | string
  threshold?: number | string
  description: string
  evidence?: string
}

export interface RiskScore {
  overall_score: number
  level: RiskLevel
  indicators: RiskIndicator[]
  summary: string
}

export interface AnomalyRecord {
  id?: string
  date: string
  category: string
  amount: number
  expected_min?: number
  expected_max?: number
  severity: RiskLevel
  reason: string
  requires_investigation: boolean
  transaction_id?: string
  description?: string
  z_score?: number
}

// ─── Forecast Types ───────────────────────────────────────────────────────────

export interface ForecastPoint {
  date: string
  actual?: number
  forecast?: number
  lower_bound?: number
  upper_bound?: number
  is_forecast: boolean
}

export interface ForecastResult {
  horizon_days: number
  points: ForecastPoint[]
  model_performance: {
    mae: number
    rmse: number
    mape: number
  }
  methodology: string
  disclaimer?: string
  generated_at: string
}

// ─── Insight / AI Types ───────────────────────────────────────────────────────

export type InsightType = 'FACT' | 'INSIGHT' | 'RISK' | 'OPPORTUNITY' | 'ACTION'

export interface InsightCard {
  type: InsightType
  title: string
  body: string
  evidence?: string
  metric_source?: string
  severity?: RiskLevel
  priority?: 'LOW' | 'MEDIUM' | 'HIGH'
}

export interface OpportunityItem {
  title: string
  description: string
  potential_impact?: string
  effort?: string
  category?: string
}

export interface ActionItem {
  title: string
  description: string
  priority: 'LOW' | 'MEDIUM' | 'HIGH'
  timeline?: string
  owner?: string
  category?: string
}

export interface EvidenceItem {
  metric: string
  value: string
  source: string
  context?: string
}

export interface AIResponse {
  question: string
  context_period: string
  summary: string
  facts: InsightCard[]
  insights: InsightCard[]
  risks: InsightCard[]
  opportunities: InsightCard[]
  actions: InsightCard[]
  limitations?: string
  evidence?: EvidenceItem[]
  generated_at: string
  model_used?: string
}

export interface InvestigationResult {
  kpi: string
  kpi_label: string
  period: string
  as_of_date: string
  as_of_display: string
  what_changed: {
    headline: string
    current_metric: string
    baseline_metric: string
    variance: string
    summary: string
  }
  why_it_changed: Array<{
    rank: number
    title: string
    impact: string
    driver_category: string
    explanation: string
    verified_metric: string
  }>
  evidence: Array<{
    source: string
    metric: string
    value: string
    benchmark: string
  }>
  what_management_should_do: Array<{
    priority: string
    action: string
    rationale: string
    owner: string
    expected_benefit: string
  }>
}

export interface ForecastComparisonResult {
  title: string
  as_of_date: string
  as_of_display: string
  evaluation_window: string
  champion_model: string
  champion_rationale: string
  benchmark_table: Array<{
    model: string
    mae: number
    rmse: number
    mape_pct: number
    directional_accuracy_pct: number
    status: string
    strengths: string
  }>
  monthly_comparison: Array<{
    period: string
    actual: number
    holt_winters: number
    arima: number
    moving_avg: number
  }>
}

export interface ExecutiveBriefResponse {
  period: string
  brief: string
  key_metrics: Record<string, string>
  generated_at: string
}

// ─── Data Quality Types ───────────────────────────────────────────────────────

export interface DataQualityDimension {
  name: string
  score: number
  description: string
  issues_found?: number
}

export interface DataQualityIssue {
  severity: RiskLevel
  description: string
  affected_records?: number
  table?: string
  column?: string
}

export interface DataQualityReport {
  overall_score: number
  completeness: DataQualityDimension
  consistency: DataQualityDimension
  validity: DataQualityDimension
  duplicate_rate: number
  missing_value_rate: number
  issues: DataQualityIssue[]
  last_checked: string
  total_records?: number
}

// ─── Dashboard Overview ───────────────────────────────────────────────────────

export interface DashboardOverview {
  period: string
  kpis: ExecutiveKPIs
  revenue_trend: TimeSeriesPoint[]
  profit_trend: TimeSeriesPoint[]
  expense_trend: TimeSeriesPoint[]
  cash_flow_summary: Array<{ date: string; inflow: number; outflow: number; net: number }>
  expense_by_category: CategoryBreakdown[]
  budget_variance: BudgetVarianceItem[]
  insights: InsightCard[]
  top_risks: RiskIndicator[]
  opportunities: OpportunityItem[]
  actions: ActionItem[]
  risk_score: RiskScore
  last_updated: string
}

// ─── Analytics Response Wrappers ──────────────────────────────────────────────

export interface RevenueAnalytics {
  period: string
  trend: TimeSeriesPoint[]
  by_category: CategoryBreakdown[]
  by_region: RegionBreakdown[]
  growth_trend: TimeSeriesPoint[]
  top_contributors: Array<{ name: string; value: number; formatted: string; pct: number }>
}

export interface ProfitAnalytics {
  period: string
  profit_trend: TimeSeriesPoint[]
  margin_trend: TimeSeriesPoint[]
  by_category: CategoryBreakdown[]
  by_region: RegionBreakdown[]
}

export interface ExpenseAnalytics {
  period: string
  trend: TimeSeriesPoint[]
  by_category: CategoryBreakdown[]
  by_department: CategoryBreakdown[]
  expense_to_revenue: TimeSeriesPoint[]
}

export interface CashFlowAnalytics {
  period: string
  trend: Array<{ date: string; inflow: number; outflow: number; net: number }>
  by_category: CategoryBreakdown[]
  cumulative: TimeSeriesPoint[]
}

export interface BudgetAnalytics {
  year: number
  variance: BudgetVarianceItem[]
  summary: {
    total_budget: number
    total_actual: number
    total_variance: number
    over_budget_count: number
  }
}

export interface AnomalySummary {
  total_anomalies: number
  expense_anomalies: number
  transaction_anomalies: number
  critical_count: number
  high_count: number
  requires_investigation_count: number
}

export interface SystemInfo {
  app_name: string
  version: string
  environment: string
  dataset_type: string
  dataset_period: {
    start: string
    end: string
    display: string
  }
  data_as_of_date: string
  data_as_of_display: string
  record_counts: Record<string, number>
  total_records: number
  currency: string
}

export interface HealthPillarMetric {

  label: string
  value: string
  benchmark: string
}

export interface HealthPillar {
  name: string
  weight_pct: number
  score: number
  status: 'Excellent' | 'Good' | 'Fair' | 'Critical'
  metrics: HealthPillarMetric[]
}

export interface FinancialHealthScore {
  composite_score: number
  grade: 'A' | 'B' | 'C' | 'D'
  status: string
  summary: string
  as_of_date: string
  pillars: {
    liquidity: HealthPillar
    profitability: HealthPillar
    credit: HealthPillar
    stability: HealthPillar
  }
}


