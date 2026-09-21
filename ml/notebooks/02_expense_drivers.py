"""FinGuard AI — EDA 02: Expense Drivers & Margin Compression Analysis.

Analyzes:
1. Operational expenses by department and category.
2. Expense-to-Revenue ratios across quarters (Scenario B: margin compression in Q3 2024).
3. Unusual expense surge in October 2024 (Scenario F: ~3x Operations spike).
4. Budget vs. Actual variance analysis across fiscal years (Scenario H: Q3/Q4 overruns).
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "ml" / "notebooks"))

import pandas as pd
from data_loader import load_dataset


def run_expense_eda():
    print("=" * 70)
    print(" FinGuard AI — Exploratory Data Analysis: Expense Drivers & Margins")
    print("=" * 70)

    data = load_dataset()
    expenses = data["expenses"].copy()
    txns = data["transactions"].copy()
    depts = data["departments"].copy()
    cats = data["categories"].copy()
    budgets = data["budgets"].copy()

    expenses = expenses.merge(depts, on="department_id", suffixes=("", "_dept"))
    expenses = expenses.merge(cats, on="category_id", suffixes=("", "_cat"))

    print(f"\nTotal Expense Records: {len(expenses):,}")
    print(f"Total Operating Expenses: ${expenses['amount'].sum():,.2f}")
    print(f"Mean Expense Amount:      ${expenses['amount'].mean():,.2f}")
    print(f"Max Single Expense:       ${expenses['amount'].max():,.2f}")

    # 1. Expenses by Department
    dept_summary = expenses.groupby("name")["amount"].agg(["sum", "mean", "count"]).rename(
        columns={"sum": "total_exp", "mean": "avg_exp", "count": "tx_count"}
    ).sort_values("total_exp", ascending=False)

    print("\n--- Expense Distribution by Department ---")
    for dept, row in dept_summary.iterrows():
        pct = (row["total_exp"] / expenses["amount"].sum()) * 100
        print(f"  {dept:<18}: ${row['total_exp']:>11,.2f} ({pct:>5.1f}%) | Avg: ${row['avg_exp']:>7,.2f} ({int(row['tx_count'])} bills)")

    # 2. Monthly Revenue vs Expense Comparison (Margin Compression Analysis)
    sales = txns[(txns["transaction_type"] == "sale") & (txns["status"] == "completed")].copy()
    sales["month"] = sales["transaction_date"].dt.to_period("M")
    expenses["month"] = expenses["expense_date"].dt.to_period("M")

    m_rev = sales.groupby("month")["amount"].sum().rename("revenue")
    m_exp = expenses.groupby("month")["amount"].sum().rename("expenses")
    pnl = pd.concat([m_rev, m_exp], axis=1).fillna(0)
    pnl["net_margin"] = pnl["revenue"] - pnl["expenses"]
    pnl["margin_pct"] = (pnl["net_margin"] / pnl["revenue"]) * 100
    pnl["exp_to_rev"] = (pnl["expenses"] / pnl["revenue"]) * 100

    print("\n--- Revenue vs Expense & Margin Trend (Focus: 2024 H2) ---")
    h2_2024 = pnl.loc["2024-06":"2024-12"]
    for m, row in h2_2024.iterrows():
        flag = " <--- MARGIN COMPRESSION" if row["exp_to_rev"] > 60 else ""
        print(f"  {m}: Rev ${row['revenue']:>10,.2f} | Exp ${row['expenses']:>10,.2f} | Margin {row['margin_pct']:>5.1f}% (Exp/Rev: {row['exp_to_rev']:>5.1f}%){flag}")

    # 3. Detect the October 2024 Operations Spike
    oct_ops = expenses[(expenses["month"] == "2024-10") & (expenses["name"] == "Operations")]
    normal_ops = expenses[(expenses["month"] != "2024-10") & (expenses["name"] == "Operations")]
    print("\n--- Deep Dive: October 2024 Operations Expense Spike ---")
    print(f"  Oct 2024 Operations Total:    ${oct_ops['amount'].sum():>10,.2f} across {len(oct_ops)} records (Avg: ${oct_ops['amount'].mean():,.2f})")
    print(f"  Historical Monthly Ops Avg:   ${normal_ops.groupby('month')['amount'].sum().mean():>10,.2f}")
    mult = oct_ops['amount'].sum() / normal_ops.groupby('month')['amount'].sum().mean()
    print(f"  Anomaly Ratio: {mult:.2f}x standard monthly Operations spend")

    # 4. Budget Variance Analysis
    if not budgets.empty:
        b_summary = budgets.groupby("fiscal_year").agg(
            budgeted=("budgeted_amount", "sum"),
            actual=("actual_amount", "sum"),
        )
        b_summary["variance"] = b_summary["actual"] - b_summary["budgeted"]
        b_summary["variance_pct"] = (b_summary["variance"] / b_summary["budgeted"]) * 100

        print("\n--- Budget vs. Actual Variance by Fiscal Year ---")
        for yr, row in b_summary.iterrows():
            v_sign = "+" if row["variance"] > 0 else ""
            print(f"  FY {yr}: Budget ${row['budgeted']:>11,.2f} | Actual ${row['actual']:>11,.2f} | Variance: {v_sign}${row['variance']:>10,.2f} ({v_sign}{row['variance_pct']:.1f}%)")

    print("\n[EDA 02 Completed Successfully]")


if __name__ == "__main__":
    run_expense_eda()
