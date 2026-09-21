"""Financial risk classification using XGBoost with rule-based labelling."""

import calendar
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.analytics.kpis import KPIService
from app.models import Budget, CashFlow, Expense, Invoice, Transaction
from app.schemas.risk import RiskIndicator, RiskScore
from app.utils.formatters import safe_divide
from app.utils.date_utils import get_as_of_date

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_ARTIFACTS_DIR = Path(__file__).parent.parent.parent.parent / "ml" / "artifacts"
_MODEL_PATH = _ARTIFACTS_DIR / "risk_classifier.pkl"

# ---------------------------------------------------------------------------
# Feature column order (must be consistent between training and inference)
# ---------------------------------------------------------------------------
_FEATURE_COLUMNS = [
    "revenue_growth_3m",
    "expense_growth_3m",
    "gross_margin",
    "margin_change_3m",
    "net_margin",
    "cash_flow_ratio",
    "expense_revenue_ratio",
    "receivables_aging_score",
    "budget_overrun_score",
    "revenue_volatility",
]

_FEATURE_NAMES = {
    "revenue_growth_3m": "Revenue Growth Trend",
    "expense_growth_3m": "Expense Growth Rate",
    "gross_margin": "Gross Margin Level",
    "margin_change_3m": "Margin Compression",
    "net_margin": "Net Margin Level",
    "cash_flow_ratio": "Cash Flow Health",
    "expense_revenue_ratio": "Expense-to-Revenue Ratio",
    "receivables_aging_score": "Receivables Aging",
    "budget_overrun_score": "Budget Overrun Level",
    "revenue_volatility": "Revenue Stability",
}

_RISK_LABELS = {0: "LOW", 1: "MEDIUM", 2: "HIGH"}
_METHODOLOGY = (
    "XGBoost multi-class classifier trained on 24 months of rolling financial features. "
    "Risk is derived from revenue growth, margin health, cash flow, and operational efficiency signals."
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _month_bounds(year: int, month: int) -> Tuple[date, date]:
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


def _prev_month(year: int, month: int) -> Tuple[int, int]:
    if month == 1:
        return year - 1, 12
    return year, month - 1


def _months_back(year: int, month: int, n: int) -> Tuple[int, int]:
    m = month - n
    y = year
    while m <= 0:
        m += 12
        y -= 1
    return y, m


class FinancialRiskClassifier:
    """Classify current financial risk level using XGBoost or rule-based fallback."""

    MODEL_PATH: Path = _MODEL_PATH

    def __init__(self, db: Session) -> None:
        self.db = db
        self._kpi = KPIService(db)
        self._model = None

    # ------------------------------------------------------------------
    # Feature extraction
    # ------------------------------------------------------------------

    def _extract_features_for_month(self, year: int, month: int) -> dict:
        """Compute all 10 risk features for a given calendar month."""
        s, e = _month_bounds(year, month)

        # Revenue this month & 3 months ago
        rev_curr = self._kpi.calculate_revenue(s, e)
        y3m, m3m = _months_back(year, month, 3)
        s3m, e3m = _month_bounds(y3m, m3m)
        rev_3m_ago = self._kpi.calculate_revenue(s3m, e3m)
        revenue_growth_3m = safe_divide(rev_curr - rev_3m_ago, rev_3m_ago) * 100

        # Expenses this month & 3 months ago
        exp_curr = self._kpi.calculate_total_expenses(s, e)
        exp_3m_ago = self._kpi.calculate_total_expenses(s3m, e3m)
        expense_growth_3m = safe_divide(exp_curr - exp_3m_ago, exp_3m_ago) * 100

        # Margins
        gross_margin = self._kpi.calculate_gross_margin(s, e)
        net_margin = self._kpi.calculate_net_margin(s, e)

        gm_3m_ago = self._kpi.calculate_gross_margin(s3m, e3m)
        margin_change_3m = gross_margin - gm_3m_ago

        # Cash flow ratio
        net_cf = self._kpi.calculate_net_cash_flow(s, e)
        cash_flow_ratio = safe_divide(net_cf, rev_curr) * 100 if rev_curr else 0.0

        # Expense-to-revenue ratio
        expense_revenue_ratio = safe_divide(exp_curr, rev_curr) * 100 if rev_curr else 0.0

        # Receivables aging score: weighted bucket score (0–100)
        try:
            aging_stmt = text(
                """
                SELECT
                    SUM(CASE WHEN :as_of_date - due_date BETWEEN 0  AND 30  THEN invoice_amount - paid_amount ELSE 0 END) AS b0,
                    SUM(CASE WHEN :as_of_date - due_date BETWEEN 31 AND 60  THEN invoice_amount - paid_amount ELSE 0 END) AS b31,
                    SUM(CASE WHEN :as_of_date - due_date BETWEEN 61 AND 90  THEN invoice_amount - paid_amount ELSE 0 END) AS b61,
                    SUM(CASE WHEN :as_of_date - due_date > 90              THEN invoice_amount - paid_amount ELSE 0 END) AS b90,
                    SUM(invoice_amount - paid_amount) AS total
                FROM invoices
                WHERE payment_status IN ('unpaid','partial','overdue')
                """
            )
            row = self.db.execute(aging_stmt, {"as_of_date": get_as_of_date()}).fetchone()
            total_ar = float(row.total or 0)
            if total_ar > 0:
                b0 = float(row.b0 or 0)
                b31 = float(row.b31 or 0)
                b61 = float(row.b61 or 0)
                b90 = float(row.b90 or 0)
                receivables_aging_score = min(
                    100.0,
                    (b31 * 25 + b61 * 50 + b90 * 100) / total_ar,
                )
            else:
                receivables_aging_score = 0.0
        except Exception:
            logger.debug("Receivables aging score failed", exc_info=True)
            receivables_aging_score = 0.0

        # Budget overrun score: average overspend % across categories (capped 0–100)
        try:
            budget_rows = (
                self.db.query(
                    Budget.category_id,
                    func.sum(Budget.budget_amount).label("budgeted"),
                )
                .filter(Budget.period_year == year, Budget.period_month == month)
                .group_by(Budget.category_id)
                .all()
            )
            if budget_rows:
                variances = []
                for br in budget_rows:
                    cat_exp = float(
                        self.db.query(func.sum(Expense.amount))
                        .filter(
                            Expense.category_id == br.category_id,
                            Expense.status == "approved",
                            Expense.expense_date >= s,
                            Expense.expense_date <= e,
                        )
                        .scalar()
                        or 0
                    )
                    budgeted = float(br.budgeted or 0)
                    if budgeted > 0:
                        overspend_pct = max(0.0, safe_divide(cat_exp - budgeted, budgeted) * 100)
                        variances.append(overspend_pct)
                budget_overrun_score = min(100.0, float(np.mean(variances))) if variances else 0.0
            else:
                budget_overrun_score = 0.0
        except Exception:
            logger.debug("Budget overrun score failed", exc_info=True)
            budget_overrun_score = 0.0

        # Revenue volatility: coefficient of variation over last 6 months
        try:
            monthly_revs = []
            for i in range(6):
                yi, mi = _months_back(year, month, i)
                si, ei = _month_bounds(yi, mi)
                monthly_revs.append(self._kpi.calculate_revenue(si, ei))
            arr = np.array(monthly_revs)
            mean_rev = float(arr.mean())
            revenue_volatility = safe_divide(float(arr.std()), mean_rev) * 100 if mean_rev else 0.0
        except Exception:
            logger.debug("Revenue volatility failed", exc_info=True)
            revenue_volatility = 0.0

        return {
            "revenue_growth_3m": round(revenue_growth_3m, 4),
            "expense_growth_3m": round(expense_growth_3m, 4),
            "gross_margin": round(gross_margin, 4),
            "margin_change_3m": round(margin_change_3m, 4),
            "net_margin": round(net_margin, 4),
            "cash_flow_ratio": round(cash_flow_ratio, 4),
            "expense_revenue_ratio": round(expense_revenue_ratio, 4),
            "receivables_aging_score": round(receivables_aging_score, 4),
            "budget_overrun_score": round(budget_overrun_score, 4),
            "revenue_volatility": round(revenue_volatility, 4),
        }

    # ------------------------------------------------------------------
    # Rule-based label derivation
    # ------------------------------------------------------------------

    @staticmethod
    def _label_from_features(features: dict) -> int:
        """Deterministic rule-based risk label: 0=LOW, 1=MEDIUM, 2=HIGH."""
        gm = features["gross_margin"]
        nm = features["net_margin"]
        rev_growth = features["revenue_growth_3m"]
        cf_ratio = features["cash_flow_ratio"]
        overrun = features["budget_overrun_score"]

        high = (
            nm < 5
            or rev_growth < -10
            or cf_ratio < -5
            or overrun > 50
        )
        if high:
            return 2

        low = (
            nm > 15
            and rev_growth >= 0
            and cf_ratio >= 0
            and overrun <= 10
        )
        if low:
            return 0

        return 1

    # ------------------------------------------------------------------
    # Training data generation
    # ------------------------------------------------------------------

    def _generate_training_data(self) -> Tuple[pd.DataFrame, pd.Series]:
        """Build features + labels for the last 24 calendar months."""
        today = get_as_of_date()
        records = []
        labels = []
        for i in range(1, 25):
            year, month = _months_back(today.year, today.month, i)
            try:
                feats = self._extract_features_for_month(year, month)
                label = self._label_from_features(feats)
                records.append(feats)
                labels.append(label)
            except Exception:
                logger.debug("Feature extraction failed for %d-%02d", year, month, exc_info=True)

        if not records:
            return pd.DataFrame(columns=_FEATURE_COLUMNS), pd.Series(dtype=int)

        X = pd.DataFrame(records)[_FEATURE_COLUMNS].fillna(0.0)
        y = pd.Series(labels, dtype=int)
        return X, y

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(self) -> dict:
        """Train XGBoost on 24-month history; save model; return CV metrics."""
        try:
            from xgboost import XGBClassifier
            from sklearn.model_selection import StratifiedKFold
            from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
            from sklearn.preprocessing import label_binarize
        except ImportError as exc:
            logger.error("XGBoost / sklearn not installed: %s", exc)
            raise

        X, y = self._generate_training_data()
        if len(X) < 12:
            logger.warning("Only %d training samples — using rule-based fallback", len(X))
            return {"status": "insufficient_data", "samples": len(X)}

        skf = StratifiedKFold(n_splits=min(5, len(y.unique())), shuffle=False)
        precision_scores, recall_scores, f1_scores, auc_scores = [], [], [], []

        for train_idx, val_idx in skf.split(X, y):
            X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_tr, y_val = y.iloc[train_idx], y.iloc[val_idx]
            clf = XGBClassifier(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.1,
                use_label_encoder=False,
                eval_metric="mlogloss",
                random_state=42,
                verbosity=0,
            )
            clf.fit(X_tr, y_tr)
            y_pred = clf.predict(X_val)
            y_prob = clf.predict_proba(X_val)

            precision_scores.append(precision_score(y_val, y_pred, average="weighted", zero_division=0))
            recall_scores.append(recall_score(y_val, y_pred, average="weighted", zero_division=0))
            f1_scores.append(f1_score(y_val, y_pred, average="weighted", zero_division=0))
            classes = sorted(y.unique())
            try:
                y_bin = label_binarize(y_val, classes=classes)
                if y_bin.shape[1] > 1:
                    auc_scores.append(roc_auc_score(y_bin, y_prob[:, :y_bin.shape[1]], multi_class="ovr"))
            except Exception:
                pass

        # Final model on full data
        final_clf = XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            use_label_encoder=False,
            eval_metric="mlogloss",
            random_state=42,
            verbosity=0,
        )
        final_clf.fit(X, y)
        self._model = final_clf

        _ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(final_clf, self.MODEL_PATH)
        logger.info("Risk classifier saved to %s", self.MODEL_PATH)

        return {
            "status": "trained",
            "samples": len(X),
            "precision": round(float(np.mean(precision_scores)), 4) if precision_scores else 0.0,
            "recall": round(float(np.mean(recall_scores)), 4) if recall_scores else 0.0,
            "f1": round(float(np.mean(f1_scores)), 4) if f1_scores else 0.0,
            "auc_roc": round(float(np.mean(auc_scores)), 4) if auc_scores else None,
        }

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def _load_model(self) -> Optional[object]:
        """Load model from disk; train if not found."""
        if self._model is not None:
            return self._model
        if self.MODEL_PATH.exists():
            try:
                self._model = joblib.load(self.MODEL_PATH)
                logger.info("Risk classifier loaded from %s", self.MODEL_PATH)
                return self._model
            except Exception:
                logger.warning("Failed to load model from disk; retraining.", exc_info=True)
        try:
            self.train()
        except Exception:
            logger.warning("Training failed; will use rule-based fallback.", exc_info=True)
        return self._model

    # ------------------------------------------------------------------
    # Prediction helpers
    # ------------------------------------------------------------------

    def _rule_based_risk(self, features: dict) -> Tuple[str, float]:
        """Return (level_str, score_0_100) from deterministic rules."""
        label = self._label_from_features(features)
        # Map label to a synthetic score in [0,100]
        nm = features["net_margin"]
        rev_growth = features["revenue_growth_3m"]
        base_scores = {2: 75.0, 1: 45.0, 0: 20.0}
        score = base_scores[label]
        # Small adjustments for extremes
        if label == 2:
            score = min(95.0, score + abs(min(nm, 0)) * 0.5)
        elif label == 0:
            score = max(5.0, score - max(rev_growth, 0) * 0.2)
        return _RISK_LABELS[label], round(score, 1)

    @staticmethod
    def _indicator_level(value: float, thresholds: Tuple[float, float]) -> str:
        """Classify a numeric value into LOW / MEDIUM / HIGH based on (low_threshold, high_threshold)."""
        low_t, high_t = thresholds
        if value <= low_t:
            return "LOW"
        if value <= high_t:
            return "MEDIUM"
        return "HIGH"

    def _build_indicators(
        self, features: dict, importances: Optional[dict] = None
    ) -> List[RiskIndicator]:
        """Map feature values to human-readable RiskIndicator objects."""
        indicators = []

        def _add(feature_key: str, value: float, threshold: float, description: str, evidence: str, invert: bool = False) -> None:
            imp = (importances or {}).get(feature_key, 0.0)
            level = "HIGH" if (value < threshold if not invert else value > threshold) else "LOW"
            indicators.append(
                RiskIndicator(
                    name=_FEATURE_NAMES[feature_key],
                    level=level,
                    value=round(value, 2),
                    threshold=threshold,
                    description=description,
                    evidence=evidence,
                )
            )

        gm = features["gross_margin"]
        nm = features["net_margin"]
        rg = features["revenue_growth_3m"]
        cf = features["cash_flow_ratio"]
        er = features["expense_revenue_ratio"]
        eg = features["expense_growth_3m"]
        mc = features["margin_change_3m"]
        ra = features["receivables_aging_score"]
        bo = features["budget_overrun_score"]
        rv = features["revenue_volatility"]

        _add("gross_margin", gm, 20.0, "Gross margin percentage", f"{gm:.1f}% gross margin")
        _add("net_margin", nm, 10.0, "Net profit as % of revenue", f"{nm:.1f}% net margin")
        _add("revenue_growth_3m", rg, 0.0, "3-month revenue growth rate", f"{rg:+.1f}% over 3 months")
        _add("cash_flow_ratio", cf, 0.0, "Net cash flow as % of revenue", f"{cf:+.1f}% cash flow ratio")
        _add("expense_revenue_ratio", er, 80.0, "Expenses as % of revenue", f"{er:.1f}% expense ratio", invert=True)
        _add("expense_growth_3m", eg, 10.0, "3-month expense growth rate", f"{eg:+.1f}% expense growth", invert=True)
        _add("margin_change_3m", mc, -5.0, "Gross margin change over 3 months", f"{mc:+.1f}pp margin change")
        _add("receivables_aging_score", ra, 30.0, "Weighted receivables aging (0=current, 100=90+ days)", f"Aging score {ra:.1f}/100", invert=True)
        _add("budget_overrun_score", bo, 20.0, "Average budget overspend %", f"Overrun score {bo:.1f}/100", invert=True)
        _add("revenue_volatility", rv, 20.0, "Coefficient of variation of monthly revenue (6m)", f"{rv:.1f}% CV", invert=True)

        return indicators

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def predict_current_risk(self) -> RiskScore:
        """Predict risk level for the most recent complete month."""
        generated_at = datetime.utcnow().isoformat() + "Z"
        today = get_as_of_date()
        # Most recent complete month
        first_of_current = today.replace(day=1)
        last_complete = first_of_current - timedelta(days=1)
        year, month = last_complete.year, last_complete.month

        features = self._extract_features_for_month(year, month)
        model = self._load_model()

        if model is not None:
            try:
                X = pd.DataFrame([features])[_FEATURE_COLUMNS].fillna(0.0)
                pred_label = int(model.predict(X)[0])
                prob = model.predict_proba(X)[0]
                overall_level = _RISK_LABELS.get(pred_label, "MEDIUM")
                # Score = weighted sum: LOW→25, MED→55, HIGH→85
                score = float(prob[0] * 25 + prob[1] * 55 + (prob[2] if len(prob) > 2 else 0) * 85)
                importances = dict(zip(_FEATURE_COLUMNS, model.feature_importances_))
            except Exception:
                logger.warning("Model prediction failed; using rule-based fallback.", exc_info=True)
                overall_level, score = self._rule_based_risk(features)
                importances = None
        else:
            overall_level, score = self._rule_based_risk(features)
            importances = None

        indicators = self._build_indicators(features, importances)

        return RiskScore(
            overall_level=overall_level,
            overall_score=round(score, 1),
            indicators=indicators,
            methodology=_METHODOLOGY,
            generated_at=generated_at,
        )

    def get_risk_trend(self, months: int = 6) -> List[dict]:
        """Predict risk level for each of the last N complete months."""
        today = get_as_of_date()
        results = []
        model = self._load_model()

        for i in range(1, months + 1):
            year, month = _months_back(today.year, today.month, i)
            try:
                features = self._extract_features_for_month(year, month)
                if model is not None:
                    try:
                        X = pd.DataFrame([features])[_FEATURE_COLUMNS].fillna(0.0)
                        pred_label = int(model.predict(X)[0])
                        prob = model.predict_proba(X)[0]
                        level = _RISK_LABELS.get(pred_label, "MEDIUM")
                        score = float(prob[0] * 25 + prob[1] * 55 + (prob[2] if len(prob) > 2 else 0) * 85)
                    except Exception:
                        level, score = self._rule_based_risk(features)
                else:
                    level, score = self._rule_based_risk(features)

                results.append({
                    "month": date(year, month, 1).strftime("%Y-%m"),
                    "level": level,
                    "score": round(score, 1),
                })
            except Exception:
                logger.debug("Risk trend failed for %d-%02d", year, month, exc_info=True)

        results.sort(key=lambda x: x["month"])
        return results


# ---------------------------------------------------------------------------
# Standalone training entry-point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from app.database.connection import SessionLocal

    logging.basicConfig(level=logging.INFO)
    db = SessionLocal()
    try:
        classifier = FinancialRiskClassifier(db)
        metrics = classifier.train()
        print("Training complete:", metrics)
    finally:
        db.close()
