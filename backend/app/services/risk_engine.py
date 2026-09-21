"""Risk / Opportunity / Action Engine for FinGuard AI."""

import logging
from datetime import date, timedelta
from typing import List

from sqlalchemy.orm import Session

from app.analytics import (
    BudgetAnalyticsService,
    ExpenseAnalyticsService,
    KPIService,
    ReceivablesService,
    RevenueAnalyticsService,
)
from app.ml import AnomalyDetectionService
from app.schemas import ActionItem, InsightCard, OpportunityItem
from app.utils.formatters import format_currency, format_percentage, safe_divide
from app.utils.date_utils import get_as_of_date

logger = logging.getLogger(__name__)

_SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


class RiskOpportunityActionEngine:
    """
    Derives risks, opportunities, and recommended actions from verified analytics.
    All outputs are evidence-based — no hardcoded strings.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.kpi_svc = KPIService(db)
        self.revenue_svc = RevenueAnalyticsService(db)
        self.expense_svc = ExpenseAnalyticsService(db)
        self.budget_svc = BudgetAnalyticsService(db)
        self.receivables_svc = ReceivablesService(db)
        self.anomaly_svc = AnomalyDetectionService(db)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _period_bounds() -> tuple[date, date, date, date]:
        """Return (curr_start, curr_end, prev_start, prev_end) for last 12 months."""
        today = get_as_of_date()
        curr_end = today
        curr_start = today - timedelta(days=364)
        prev_end = curr_start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=364)
        return curr_start, curr_end, prev_start, prev_end

    def _get_risk_indicators(self) -> List[dict]:
        """
        Returns list of risk signals with evidence. Each item:
        {
            'category': str,  # 'revenue' | 'margin' | 'expense' | 'cashflow' | 'receivables' | 'budget' | 'anomaly'
            'level': str,     # 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
            'title': str,
            'evidence': str,
            'metric_value': float,
            'threshold': float
        }
        """
        cs, ce, ps, pe = self._period_bounds()
        indicators: List[dict] = []

        # --- Revenue growth ---
        try:
            rev_growth = self.kpi_svc.calculate_revenue_growth(cs, ce, ps, pe)
            curr_rev = self.kpi_svc.calculate_revenue(cs, ce)
            if rev_growth < -5.0:
                indicators.append({
                    "category": "revenue",
                    "level": "HIGH",
                    "title": "Significant revenue decline",
                    "evidence": f"Revenue growth is {rev_growth:.1f}% (threshold: -5%)",
                    "metric_value": rev_growth,
                    "threshold": -5.0,
                })
            elif rev_growth < 0.0:
                indicators.append({
                    "category": "revenue",
                    "level": "MEDIUM",
                    "title": "Revenue growth negative",
                    "evidence": f"Revenue growth is {rev_growth:.1f}% — below zero",
                    "metric_value": rev_growth,
                    "threshold": 0.0,
                })
        except Exception:
            logger.exception("Revenue growth risk check failed")

        # --- Gross margin ---
        try:
            gross_margin = self.kpi_svc.calculate_gross_margin(cs, ce)
            if gross_margin < 10.0:
                indicators.append({
                    "category": "margin",
                    "level": "HIGH",
                    "title": "Critical gross margin compression",
                    "evidence": f"Gross margin is {gross_margin:.1f}% (threshold: 10%)",
                    "metric_value": gross_margin,
                    "threshold": 10.0,
                })
            elif gross_margin < 20.0:
                indicators.append({
                    "category": "margin",
                    "level": "MEDIUM",
                    "title": "Low gross margin",
                    "evidence": f"Gross margin is {gross_margin:.1f}% (threshold: 20%)",
                    "metric_value": gross_margin,
                    "threshold": 20.0,
                })
        except Exception:
            logger.exception("Gross margin risk check failed")

        # --- Expense growth ---
        try:
            curr_exp = self.kpi_svc.calculate_total_expenses(cs, ce)
            prev_exp = self.kpi_svc.calculate_total_expenses(ps, pe)
            exp_growth = safe_divide(curr_exp - prev_exp, prev_exp) * 100 if prev_exp else 0.0
            if exp_growth > 20.0:
                indicators.append({
                    "category": "expense",
                    "level": "HIGH",
                    "title": "Rapid expense growth",
                    "evidence": f"Expenses grew {exp_growth:.1f}% year-over-year (threshold: 20%)",
                    "metric_value": exp_growth,
                    "threshold": 20.0,
                })
            elif exp_growth > 10.0:
                indicators.append({
                    "category": "expense",
                    "level": "MEDIUM",
                    "title": "Elevated expense growth",
                    "evidence": f"Expenses grew {exp_growth:.1f}% year-over-year (threshold: 10%)",
                    "metric_value": exp_growth,
                    "threshold": 10.0,
                })
        except Exception:
            logger.exception("Expense growth risk check failed")

        # --- Net cash flow ---
        try:
            curr_rev = self.kpi_svc.calculate_revenue(cs, ce)
            net_cf = self.kpi_svc.calculate_net_cash_flow(cs, ce)
            cf_pct_of_revenue = safe_divide(net_cf, curr_rev) * 100 if curr_rev else 0.0
            if net_cf < 0:
                indicators.append({
                    "category": "cashflow",
                    "level": "HIGH",
                    "title": "Negative net cash flow",
                    "evidence": f"Net cash flow is {format_currency(net_cf)} (threshold: 0)",
                    "metric_value": net_cf,
                    "threshold": 0.0,
                })
            elif cf_pct_of_revenue < 5.0 and curr_rev > 0:
                indicators.append({
                    "category": "cashflow",
                    "level": "MEDIUM",
                    "title": "Cash flow near zero",
                    "evidence": f"Net cash flow is {cf_pct_of_revenue:.1f}% of revenue (threshold: 5%)",
                    "metric_value": cf_pct_of_revenue,
                    "threshold": 5.0,
                })
        except Exception:
            logger.exception("Cash flow risk check failed")

        # --- Receivables aging ---
        try:
            aging = self.receivables_svc.get_aging_summary()
            total = aging.total_outstanding
            pct_90_plus = safe_divide(aging.bucket_90_plus, total) * 100 if total else 0.0
            if pct_90_plus > 30.0:
                indicators.append({
                    "category": "receivables",
                    "level": "HIGH",
                    "title": "High proportion of severely overdue receivables",
                    "evidence": f"{pct_90_plus:.1f}% of receivables are 90+ days overdue (threshold: 30%)",
                    "metric_value": pct_90_plus,
                    "threshold": 30.0,
                })
            elif pct_90_plus > 15.0:
                indicators.append({
                    "category": "receivables",
                    "level": "MEDIUM",
                    "title": "Elevated overdue receivables",
                    "evidence": f"{pct_90_plus:.1f}% of receivables are 90+ days overdue (threshold: 15%)",
                    "metric_value": pct_90_plus,
                    "threshold": 15.0,
                })
        except Exception:
            logger.exception("Receivables risk check failed")

        # --- Budget overrun ---
        try:
            year = get_as_of_date().year
            overruns = self.budget_svc.get_overspending_areas(year)
            max_overrun_pct = max((item.variance_pct for item in overruns), default=0.0)
            if max_overrun_pct > 25.0:
                indicators.append({
                    "category": "budget",
                    "level": "HIGH",
                    "title": "Significant budget overrun detected",
                    "evidence": f"Largest budget overrun is {max_overrun_pct:.1f}% over budget (threshold: 25%)",
                    "metric_value": max_overrun_pct,
                    "threshold": 25.0,
                })
            elif max_overrun_pct > 10.0:
                indicators.append({
                    "category": "budget",
                    "level": "MEDIUM",
                    "title": "Budget overrun in one or more areas",
                    "evidence": f"Largest budget overrun is {max_overrun_pct:.1f}% over budget (threshold: 10%)",
                    "metric_value": max_overrun_pct,
                    "threshold": 10.0,
                })
        except Exception:
            logger.exception("Budget overrun risk check failed")

        # --- Anomaly count ---
        try:
            summary = self.anomaly_svc.get_anomaly_summary()
            high_count = summary.get("by_severity", {}).get("high", 0)
            if high_count > 5:
                indicators.append({
                    "category": "anomaly",
                    "level": "HIGH",
                    "title": "Multiple high-severity anomalies detected",
                    "evidence": f"{high_count} high-severity anomalies flagged in the current period (threshold: 5)",
                    "metric_value": float(high_count),
                    "threshold": 5.0,
                })
        except Exception:
            logger.exception("Anomaly risk check failed")

        return sorted(indicators, key=lambda x: _SEVERITY_ORDER.get(x["level"], 99))

    # ------------------------------------------------------------------
    # Public: risks
    # ------------------------------------------------------------------

    def get_risks(self) -> List[InsightCard]:
        """
        Surface top risks as InsightCard objects.
        type='risk', includes evidence and metric_source.
        Sorted by severity: CRITICAL > HIGH > MEDIUM > LOW. Maximum 8 risks.
        """
        indicators = self._get_risk_indicators()
        cards: List[InsightCard] = []
        for ind in indicators[:8]:
            cards.append(
                InsightCard(
                    type="risk",
                    title=ind["title"],
                    body=ind["evidence"],
                    severity=ind["level"],
                    evidence=ind["evidence"],
                    metric_source=ind["category"],
                )
            )
        return cards

    # ------------------------------------------------------------------
    # Public: opportunities
    # ------------------------------------------------------------------

    def get_opportunities(self) -> List[OpportunityItem]:
        """
        Surface opportunities from analytics. Maximum 6 opportunities.
        """
        cs, ce, ps, pe = self._period_bounds()
        opportunities: List[OpportunityItem] = []

        # High-growth, high-margin categories
        try:
            cat_profit = self.revenue_svc.get_revenue_by_category(cs, ce)
            growth_trend = self.revenue_svc.get_revenue_growth_trend(months=12)
            # Average margin from profitability service
            from app.analytics import ProfitabilityService
            prof_svc = ProfitabilityService(self.db)
            cat_margins = {r["category"]: r["gross_margin_pct"] for r in prof_svc.get_profit_by_category(cs, ce)}
            avg_margin = (sum(cat_margins.values()) / len(cat_margins)) if cat_margins else 0.0

            high_growth_months = {}
            for point in growth_trend[-3:]:
                pass  # use overall growth as proxy for category growth

            # Use revenue growth trend to get overall growth
            overall_growth = 0.0
            if growth_trend and growth_trend[-1].get("growth_pct") is not None:
                overall_growth = growth_trend[-1]["growth_pct"] or 0.0

            for cat_data in cat_profit:
                cat_name = cat_data.category
                margin = cat_margins.get(cat_name, 0.0)
                if margin > avg_margin and overall_growth > 20.0:
                    opportunities.append(OpportunityItem(
                        title=f"High-growth high-margin category: {cat_name}",
                        description=f"{cat_name} shows above-average margin ({margin:.1f}%) during a high-growth period.",
                        supporting_metric=f"Category margin: {margin:.1f}% vs avg {avg_margin:.1f}%",
                        estimated_impact="Revenue and margin expansion potential",
                        recommended_action=f"Prioritise investment in {cat_name} to capitalise on growth momentum.",
                    ))
                    if len(opportunities) >= 2:
                        break
        except Exception:
            logger.exception("High-growth category opportunity check failed")

        # Under-utilised budget capacity
        try:
            year = get_as_of_date().year
            underutilized = self.budget_svc.get_underutilized_budget(year)
            for item in underutilized[:2]:
                if item.variance_pct < -20.0:
                    opportunities.append(OpportunityItem(
                        title=f"Budget capacity available: {item.category} / {item.department}",
                        description=(
                            f"{item.category} ({item.department}) has spent "
                            f"{format_currency(item.actual)} against a budget of {format_currency(item.budget)} "
                            f"({abs(item.variance_pct):.1f}% under budget)."
                        ),
                        supporting_metric=f"Budget utilisation: {100 + item.variance_pct:.1f}%",
                        estimated_impact="Reallocation opportunity",
                        recommended_action=f"Consider reallocating unused {item.category} budget to higher-priority areas.",
                    ))
        except Exception:
            logger.exception("Under-utilised budget opportunity check failed")

        # Receivables improvement
        try:
            aging_trend = self.receivables_svc.get_aging_trend(months=3)
            if len(aging_trend) >= 2:
                latest_90_plus = aging_trend[-1].get("bucket_90_plus", 0)
                prev_90_plus = aging_trend[-2].get("bucket_90_plus", 0)
                if latest_90_plus < prev_90_plus and prev_90_plus > 0:
                    improvement_pct = safe_divide(prev_90_plus - latest_90_plus, prev_90_plus) * 100
                    opportunities.append(OpportunityItem(
                        title="Receivables collection improving",
                        description=f"90+ day overdue receivables decreased by {improvement_pct:.1f}% compared to the prior period.",
                        supporting_metric=f"90+ days: {format_currency(latest_90_plus)} (was {format_currency(prev_90_plus)})",
                        estimated_impact="Improved cash conversion cycle",
                        recommended_action="Continue current collections practices and consider early-payment incentives.",
                    ))
        except Exception:
            logger.exception("Receivables improvement opportunity check failed")

        # Margin expansion categories
        try:
            margin_trend = ProfitabilityService(self.db).get_margin_trend(cs, ce)
            if len(margin_trend) >= 3:
                recent = [p["gross_margin_pct"] for p in margin_trend[-3:]]
                if len(recent) == 3 and recent[2] > recent[1] > recent[0]:
                    opportunities.append(OpportunityItem(
                        title="Gross margin expanding",
                        description=f"Gross margin has improved for three consecutive months, reaching {recent[-1]:.1f}%.",
                        supporting_metric=f"Margin trend: {recent[0]:.1f}% → {recent[1]:.1f}% → {recent[2]:.1f}%",
                        estimated_impact="Sustained efficiency improvement",
                        recommended_action="Review cost drivers contributing to margin expansion and reinforce those practices.",
                    ))
        except Exception:
            logger.exception("Margin expansion opportunity check failed")

        return opportunities[:6]

    # ------------------------------------------------------------------
    # Public: recommended actions
    # ------------------------------------------------------------------

    def get_recommended_actions(self) -> List[ActionItem]:
        """
        Generate evidence-based recommended actions. Maximum 6 actions.
        Actions are ONLY generated when the underlying analytics signal is present.
        """
        cs, ce, ps, pe = self._period_bounds()
        actions: List[ActionItem] = []

        # Overdue receivables > 20%
        try:
            aging = self.receivables_svc.get_aging_summary()
            total = aging.total_outstanding
            pct_90_plus = safe_divide(aging.bucket_90_plus, total) * 100 if total else 0.0
            if pct_90_plus > 20.0:
                actions.append(ActionItem(
                    priority="high",
                    title="Review overdue receivables",
                    rationale=f"{pct_90_plus:.1f}% of outstanding receivables are 90+ days overdue.",
                    supporting_evidence=f"90+ day balance: {format_currency(aging.bucket_90_plus)} of {format_currency(total)} total",
                    action_type="investigate",
                ))
        except Exception:
            logger.exception("Receivables action check failed")

        # Budget overrun > 15% in any category
        try:
            year = get_as_of_date().year
            overruns = self.budget_svc.get_overspending_areas(year)
            max_item = max(overruns, key=lambda x: x.variance_pct, default=None)
            if max_item and max_item.variance_pct > 15.0:
                actions.append(ActionItem(
                    priority="high",
                    title="Investigate expense variance",
                    rationale=f"{max_item.category} / {max_item.department} is {max_item.variance_pct:.1f}% over budget.",
                    supporting_evidence=f"Budget: {format_currency(max_item.budget)}, Actual: {format_currency(max_item.actual)}, Variance: {format_currency(max_item.variance)}",
                    action_type="investigate",
                ))
        except Exception:
            logger.exception("Budget overrun action check failed")

        # Revenue declining for 2+ consecutive months
        try:
            growth_trend = self.revenue_svc.get_revenue_growth_trend(months=4)
            recent_growths = [
                p.get("growth_pct") for p in growth_trend[-3:]
                if p.get("growth_pct") is not None
            ]
            if len(recent_growths) >= 2 and all(g < 0 for g in recent_growths[-2:]):
                actions.append(ActionItem(
                    priority="high",
                    title="Analyze revenue decline drivers",
                    rationale="Revenue has declined for two or more consecutive months.",
                    supporting_evidence=f"Recent monthly growth rates: {', '.join(f'{g:.1f}%' for g in recent_growths[-2:])}",
                    action_type="investigate",
                ))
        except Exception:
            logger.exception("Revenue decline action check failed")

        # Anomalies detected in expenses
        try:
            summary = self.anomaly_svc.get_anomaly_summary()
            expense_anomaly_count = summary.get("expense_anomalies", 0)
            if expense_anomaly_count > 0:
                high_count = summary.get("by_severity", {}).get("high", 0)
                actions.append(ActionItem(
                    priority="high" if high_count > 0 else "medium",
                    title="Investigate flagged expense items",
                    rationale=f"{expense_anomaly_count} anomalous expense records detected ({high_count} high-severity).",
                    supporting_evidence=f"Expense anomalies: {expense_anomaly_count} total, {high_count} high-severity",
                    action_type="investigate",
                ))
        except Exception:
            logger.exception("Anomaly action check failed")

        # Margin declining
        try:
            margin_trend = self.kpi_svc.calculate_gross_margin(cs, ce)
            prev_margin = self.kpi_svc.calculate_gross_margin(ps, pe)
            if margin_trend < prev_margin and prev_margin > 0:
                decline = prev_margin - margin_trend
                actions.append(ActionItem(
                    priority="medium",
                    title="Review cost structure and pricing",
                    rationale=f"Gross margin declined by {decline:.1f} percentage points year-over-year.",
                    supporting_evidence=f"Current margin: {margin_trend:.1f}%, Prior period: {prev_margin:.1f}%",
                    action_type="monitor",
                ))
        except Exception:
            logger.exception("Margin decline action check failed")

        # Negative cash flow
        try:
            net_cf = self.kpi_svc.calculate_net_cash_flow(cs, ce)
            if net_cf < 0:
                actions.append(ActionItem(
                    priority="high",
                    title="Monitor cash position closely",
                    rationale="Net cash flow is negative in the current period.",
                    supporting_evidence=f"Net cash flow: {format_currency(net_cf)}",
                    action_type="monitor",
                ))
        except Exception:
            logger.exception("Cash flow action check failed")

        actions.sort(key=lambda a: _PRIORITY_ORDER.get(a.priority, 99))
        return actions[:6]

    # ------------------------------------------------------------------
    # Public: insight cards (executive overview mix)
    # ------------------------------------------------------------------

    def get_insight_cards(self) -> List[InsightCard]:
        """
        Returns a mix of fact/insight/risk/opportunity/action cards for the executive overview.
        Maximum 10 cards.
        """
        cs, ce, ps, pe = self._period_bounds()
        cards: List[InsightCard] = []

        # Fact cards — key financial figures
        try:
            curr_rev = self.kpi_svc.calculate_revenue(cs, ce)
            cards.append(InsightCard(
                type="fact",
                title="Total Revenue",
                body=f"Revenue for the period is {format_currency(curr_rev)}.",
                metric_source="revenue",
                period="last_12_months",
            ))
        except Exception:
            logger.exception("Revenue fact card failed")

        try:
            net_profit = self.kpi_svc.calculate_net_profit(cs, ce)
            net_margin = self.kpi_svc.calculate_net_margin(cs, ce)
            cards.append(InsightCard(
                type="fact",
                title="Net Profit",
                body=f"Net profit is {format_currency(net_profit)} ({net_margin:.1f}% net margin).",
                metric_source="profitability",
                period="last_12_months",
            ))
        except Exception:
            logger.exception("Net profit fact card failed")

        # Top risk card
        risks = self.get_risks()
        if risks:
            cards.append(risks[0])

        # Top opportunity card
        opps = self.get_opportunities()
        if opps:
            opp = opps[0]
            cards.append(InsightCard(
                type="opportunity",
                title=opp.title,
                body=opp.description,
                evidence=opp.supporting_metric,
                metric_source="analytics",
            ))

        # Top action card
        actions = self.get_recommended_actions()
        if actions:
            act = actions[0]
            cards.append(InsightCard(
                type="action",
                title=act.title,
                body=act.rationale,
                evidence=act.supporting_evidence,
                severity=act.priority,
                metric_source=act.action_type,
            ))

        # Fill remaining slots with more risk cards (up to 10 total)
        for risk in risks[1:]:
            if len(cards) >= 10:
                break
            cards.append(risk)

        return cards[:10]
