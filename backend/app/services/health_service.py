"""Financial Health Score service implementing the 4-pillar methodology."""

from datetime import date, timedelta
from typing import Any, Dict
from sqlalchemy.orm import Session

from app.analytics.kpis import KPIService
from app.ml.anomaly_detection import AnomalyDetectionService
from app.models import Expense, Invoice, Transaction
from app.utils.date_utils import get_as_of_date
from app.utils.formatters import safe_divide


class FinancialHealthService:
    """Calculates composite financial health score (0-100) across 4 pillars."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.kpi = KPIService(db)
        self.anomaly_svc = AnomalyDetectionService(db)

    def calculate_health_score(self) -> Dict[str, Any]:
        as_of = get_as_of_date()
        curr_start = as_of - timedelta(days=364)

        # ------------------------------------------------------------------
        # Pillar 1: Liquidity & Cash Flow (Weight: 30%)
        # ------------------------------------------------------------------
        rev = self.kpi.calculate_revenue(curr_start, as_of)
        net_cf = self.kpi.calculate_net_cash_flow(curr_start, as_of)
        cf_ratio = safe_divide(net_cf, rev) * 100 if rev > 0 else 0.0

        if cf_ratio >= 20.0:
            p1_score = 95.0
        elif cf_ratio >= 10.0:
            p1_score = 85.0
        elif cf_ratio >= 0.0:
            p1_score = 70.0 + (cf_ratio / 10.0) * 15.0
        elif cf_ratio >= -15.0:
            p1_score = max(20.0, 70.0 + (cf_ratio / 15.0) * 50.0)
        else:
            p1_score = max(5.0, 20.0 + (cf_ratio + 15.0))
        p1_score = round(min(100.0, max(0.0, p1_score)), 1)
        p1_status = "Excellent" if p1_score >= 80 else ("Good" if p1_score >= 65 else ("Fair" if p1_score >= 50 else "Critical"))

        # ------------------------------------------------------------------
        # Pillar 2: Profitability & Margins (Weight: 25%)
        # ------------------------------------------------------------------
        gross_margin = self.kpi.calculate_gross_margin(curr_start, as_of)
        net_margin = self.kpi.calculate_net_margin(curr_start, as_of)
        exp_ratio = safe_divide(self.kpi.calculate_total_expenses(curr_start, as_of), rev) * 100 if rev > 0 else 100.0

        gm_points = min(40.0, max(0.0, (gross_margin / 40.0) * 40.0))
        nm_points = min(40.0, max(0.0, (net_margin / 15.0) * 40.0)) if net_margin > 0 else max(0.0, 20.0 + net_margin)
        er_penalty = max(0.0, (exp_ratio - 70.0) * 0.6)
        p2_score = round(min(100.0, max(0.0, gm_points + nm_points + 20.0 - er_penalty)), 1)
        p2_status = "Excellent" if p2_score >= 80 else ("Good" if p2_score >= 65 else ("Fair" if p2_score >= 50 else "Critical"))

        # ------------------------------------------------------------------
        # Pillar 3: Credit & Receivables Quality (Weight: 25%)
        # ------------------------------------------------------------------
        invoices = (
            self.db.query(Invoice)
            .filter(Invoice.payment_status.in_(["unpaid", "partial", "overdue"]))
            .all()
        )
        total_ar = 0.0
        overdue_60 = 0.0
        overdue_90 = 0.0
        for inv in invoices:
            bal = float(inv.invoice_amount or 0) - float(inv.paid_amount or 0)
            if bal > 0:
                total_ar += bal
                if inv.due_date:
                    due = inv.due_date
                    if isinstance(due, str):
                        due = date.fromisoformat(due)
                    days_over = (as_of - due).days
                    if days_over > 90:
                        overdue_90 += bal
                    elif days_over > 60:
                        overdue_60 += bal


        if total_ar > 0:
            od_60_pct = (overdue_60 / total_ar) * 100
            od_90_pct = (overdue_90 / total_ar) * 100
            p3_score = 100.0 - (od_60_pct * 0.8 + od_90_pct * 1.2)
            p3_score = round(min(100.0, max(10.0, p3_score)), 1)
        else:
            p3_score = 95.0
            od_60_pct = 0.0
            od_90_pct = 0.0

        p3_status = "Excellent" if p3_score >= 80 else ("Good" if p3_score >= 65 else ("Fair" if p3_score >= 50 else "Critical"))

        # ------------------------------------------------------------------
        # Pillar 4: Operational Stability & Anomaly Control (Weight: 20%)
        # ------------------------------------------------------------------
        b_res = self.kpi.calculate_budget_variance(as_of.year)
        budget_var = abs(float(b_res.get("variance_pct", 0.0)))
        try:
            summary = self.anomaly_svc.get_anomaly_summary()
            anomaly_count = summary.get("total_anomalies_count", 0)
        except Exception:
            anomaly_count = 0


        var_penalty = min(40.0, budget_var * 2.0)
        anomaly_penalty = min(40.0, float(anomaly_count) * 0.5)
        p4_score = round(min(100.0, max(15.0, 100.0 - var_penalty - anomaly_penalty)), 1)
        p4_status = "Excellent" if p4_score >= 80 else ("Good" if p4_score >= 65 else ("Fair" if p4_score >= 50 else "Critical"))

        # ------------------------------------------------------------------
        # Composite Calculation
        # ------------------------------------------------------------------
        composite_score = round(
            0.30 * p1_score + 0.25 * p2_score + 0.25 * p3_score + 0.20 * p4_score,
            1
        )

        if composite_score >= 80.0:
            grade = "A"
            status = "Strong Financial Health"
            summary_desc = "Robust balance sheet fundamentals with solid liquidity and well-managed expense controls."
        elif composite_score >= 65.0:
            grade = "B"
            status = "Stable / Moderate Headwinds"
            summary_desc = "Sound core operations with targeted opportunities in aging receivable collections and margin defense."
        elif composite_score >= 50.0:
            grade = "C"
            status = "Vulnerable / Attention Required"
            summary_desc = "Emerging pressures across cash flow burn and budget variance warrant proactive management intervention."
        else:
            grade = "D"
            status = "High Risk Alert"
            summary_desc = "Critical solvency or operational signals detected across multiple financial pillars."

        return {
            "composite_score": composite_score,
            "grade": grade,
            "status": status,
            "summary": summary_desc,
            "as_of_date": as_of.isoformat(),
            "pillars": {
                "liquidity": {
                    "name": "Liquidity & Cash Flow",
                    "weight_pct": 30,
                    "score": p1_score,
                    "status": p1_status,
                    "metrics": [
                        {"label": "Net Cash Flow Ratio", "value": f"{cf_ratio:+.1f}%", "benchmark": "> +15.0%"},
                        {"label": "Net Cash Flow (12m)", "value": f"${net_cf:,.0f}", "benchmark": "Positive"}
                    ]
                },
                "profitability": {
                    "name": "Profitability & Margins",
                    "weight_pct": 25,
                    "score": p2_score,
                    "status": p2_status,
                    "metrics": [
                        {"label": "Gross Margin", "value": f"{gross_margin:.1f}%", "benchmark": "> 40.0%"},
                        {"label": "Net Margin", "value": f"{net_margin:.1f}%", "benchmark": "> 15.0%"},
                        {"label": "Expense / Revenue Ratio", "value": f"{exp_ratio:.1f}%", "benchmark": "< 75.0%"}
                    ]
                },
                "credit": {
                    "name": "Credit & Receivables",
                    "weight_pct": 25,
                    "score": p3_score,
                    "status": p3_status,
                    "metrics": [
                        {"label": "Overdue > 60 Days", "value": f"{od_60_pct:.1f}%", "benchmark": "< 10.0%"},
                        {"label": "Total AR Outstanding", "value": f"${total_ar:,.0f}", "benchmark": "Monitored"}
                    ]
                },
                "stability": {
                    "name": "Operational Stability",
                    "weight_pct": 20,
                    "score": p4_score,
                    "status": p4_status,
                    "metrics": [
                        {"label": "Budget Variance", "value": f"{budget_var:.1f}%", "benchmark": "< 5.0%"},
                        {"label": "Detected Anomalies", "value": str(anomaly_count), "benchmark": "< 20 flags"}
                    ]
                }
            }
        }
