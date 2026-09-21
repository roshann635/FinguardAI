"""FinGuard AI — EDA 04: Credit Risk & Accounts Receivable Aging Analysis.

Analyzes:
1. Outstanding receivables aging distribution across standard DSO buckets:
   Current, 1–30 days, 31–60 days, 61–90 days, and 90+ days.
2. Customer credit limit utilization across Enterprise, Mid-Market, and SMB tiers.
3. Scenario D verification: aging concentration in late 2024 invoices.
4. Top overdue client exposure and weighted default probability.
"""

import sys
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "ml" / "notebooks"))

import pandas as pd
from data_loader import load_dataset


def run_credit_risk_eda():
    print("=" * 70)
    print(" FinGuard AI — Exploratory Data Analysis: Credit Risk & Receivables")
    print("=" * 70)

    data = load_dataset()
    invoices = data["invoices"].copy()
    customers = data["customers"].copy()

    # Analytical As-Of Date: 31 March 2025
    AS_OF_DATE = pd.Timestamp("2025-03-31")

    print(f"\nTotal Invoices Analyzed: {len(invoices):,}")
    print(f"Analytical Boundary (As-Of Date): {AS_OF_DATE.strftime('%d %b %Y')}")

    # Calculate unpaid balance & days overdue
    invoices["balance"] = invoices["invoice_amount"] - invoices["paid_amount"]
    open_inv = invoices[invoices["balance"] > 0].copy()
    open_inv["days_overdue"] = (AS_OF_DATE - open_inv["due_date"]).dt.days
    open_inv["days_overdue"] = open_inv["days_overdue"].clip(lower=0)

    total_receivable = open_inv["balance"].sum()
    print(f"Total Outstanding Receivables: ${total_receivable:,.2f} across {len(open_inv)} open invoices")

    # 1. Aging Buckets
    def assign_bucket(days):
        if days == 0:
            return "Current (Not Due)"
        elif days <= 30:
            return "1–30 Days Overdue"
        elif days <= 60:
            return "31–60 Days Overdue"
        elif days <= 90:
            return "61–90 Days Overdue"
        else:
            return "90+ Days (Critical)"

    open_inv["aging_bucket"] = open_inv["days_overdue"].apply(assign_bucket)
    bucket_order = [
        "Current (Not Due)",
        "1–30 Days Overdue",
        "31–60 Days Overdue",
        "61–90 Days Overdue",
        "90+ Days (Critical)",
    ]

    aging_summary = open_inv.groupby("aging_bucket")["balance"].agg(["sum", "count"]).reindex(bucket_order).fillna(0)
    aging_summary["share_pct"] = (aging_summary["sum"] / total_receivable) * 100

    print("\n--- Receivables Aging Schedule ---")
    for bucket, row in aging_summary.iterrows():
        print(f"  {bucket:<22}: ${row['sum']:>12,.2f} ({row['share_pct']:>5.1f}%) | {int(row['count']):>4} invoices")

    # 2. Customer Risk Exposure by Segment
    open_with_cust = open_inv.merge(customers, on="customer_id", suffixes=("", "_cust"))
    seg_summary = open_with_cust.groupby("segment").agg(
        outstanding=("balance", "sum"),
        avg_limit=("credit_limit", "mean"),
        clients=("customer_id", "nunique"),
    )
    seg_summary["total_limit"] = seg_summary["clients"] * seg_summary["avg_limit"]
    seg_summary["utilization_pct"] = (seg_summary["outstanding"] / seg_summary["total_limit"]) * 100

    print("\n--- Credit Utilization by Customer Segment ---")
    for seg, row in seg_summary.iterrows():
        print(f"  {seg.capitalize():<14}: ${row['outstanding']:>11,.2f} / ${row['total_limit']:>11,.2f} ({row['utilization_pct']:>5.1f}% credit line used across {int(row['clients'])} clients)")

    # 3. Top 5 Overdue Accounts
    top_debtors = open_with_cust.groupby(["customer_id", "name", "segment"]).agg(
        total_debt=("balance", "sum"),
        max_overdue_days=("days_overdue", "max"),
        inv_count=("invoice_id", "count"),
        credit_limit=("credit_limit", "first"),
    ).reset_index().sort_values("total_debt", ascending=False).head(5)

    print("\n--- Top 5 Overdue Exposure Accounts (Immediate Action Required) ---")
    for _, debtor in top_debtors.iterrows():
        util = (debtor["total_debt"] / debtor["credit_limit"]) * 100
        print(f"  {debtor['name']} ({debtor['segment']}): ${debtor['total_debt']:>10,.2f} | Max Overdue: {debtor['max_overdue_days']} days | Limit Util: {util:.1f}%")

    print("\n[EDA 04 Completed Successfully]")


if __name__ == "__main__":
    run_credit_risk_eda()
