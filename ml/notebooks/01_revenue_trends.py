"""FinGuard AI — EDA 01: Revenue Trends & Seasonality Analysis.

Analyzes:
1. Overall monthly revenue trend (Jan 2023 – Mar 2025).
2. Year-over-Year (YoY) growth rates and revenue momentum.
3. Category-level performance (Software/SaaS vs Electronics vs Consulting).
4. Quarterly seasonality patterns (Q4 surge vs Q1 dip).
"""

import sys
from pathlib import Path

# Add project root and notebooks dir to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "ml" / "notebooks"))

import pandas as pd
from data_loader import load_dataset


def run_revenue_eda():
    print("=" * 70)
    print(" FinGuard AI — Exploratory Data Analysis: Revenue Trends")
    print("=" * 70)

    data = load_dataset()
    txns = data["transactions"]
    cats = data["categories"]

    # Filter to completed sales
    sales = txns[(txns["transaction_type"] == "sale") & (txns["status"] == "completed")].copy()
    sales = sales.merge(cats, on="category_id", suffixes=("", "_cat"))

    print(f"\nTotal Completed Sales Transactions: {len(sales):,}")
    print(f"Total Gross Revenue: ${sales['amount'].sum():,.2f}")
    print(f"Average Order Value: ${sales['amount'].mean():,.2f}")
    print(f"Median Order Value:  ${sales['amount'].median():,.2f}")

    # 1. Monthly Revenue Aggregation
    sales["month"] = sales["transaction_date"].dt.to_period("M")
    monthly = sales.groupby("month").agg(
        revenue=("amount", "sum"),
        orders=("transaction_id", "count"),
        avg_basket=("amount", "mean"),
    ).reset_index()
    monthly["growth_pct"] = monthly["revenue"].pct_change() * 100

    print("\n--- Monthly Revenue Summary (Last 6 Months) ---")
    for _, row in monthly.tail(6).iterrows():
        growth_str = f"{row['growth_pct']:+.1f}%" if pd.notnull(row['growth_pct']) else "   N/A"
        print(f"  {row['month']}: ${row['revenue']:>12,.2f} | {row['orders']:>4} orders | MoM Growth: {growth_str}")

    # 2. YoY Comparison (2023 vs 2024 vs 2025 Q1)
    sales["year"] = sales["transaction_date"].dt.year
    yearly = sales.groupby("year")["amount"].agg(["sum", "count"]).rename(columns={"sum": "total_revenue", "count": "tx_count"})
    yearly["yoy_growth"] = yearly["total_revenue"].pct_change() * 100
    print("\n--- Year-Over-Year Revenue Performance ---")
    for yr, row in yearly.iterrows():
        growth_str = f"{row['yoy_growth']:+.1f}%" if pd.notnull(row['yoy_growth']) else "Base Year"
        print(f"  Year {yr}: ${row['total_revenue']:>14,.2f} ({int(row['tx_count']):>5} txns) | YoY: {growth_str}")

    # 3. Category Breakdown
    cat_summary = sales.groupby("name")["amount"].agg(
        revenue="sum", share=lambda x: (x.sum() / sales["amount"].sum()) * 100
    ).sort_values("revenue", ascending=False)

    print("\n--- Revenue by Category ---")
    for cat, row in cat_summary.iterrows():
        print(f"  {cat:<26}: ${row['revenue']:>12,.2f} ({row['share']:>5.1f}% share)")

    # 4. Quarterly Seasonality
    sales["quarter"] = sales["transaction_date"].dt.to_period("Q")
    sales["quarter_num"] = sales["transaction_date"].dt.quarter
    seasonality = sales.groupby("quarter_num")["amount"].mean()
    base_mean = seasonality.mean()
    season_index = (seasonality / base_mean) * 100

    print("\n--- Seasonality Index by Calendar Quarter ---")
    for q_num, idx in season_index.items():
        note = " (Peak holiday demand surge)" if q_num == 4 else (" (Annual procurement lull)" if q_num == 1 else "")
        print(f"  Q{q_num}: Index {idx:6.1f}{note}")

    print("\n[EDA 01 Completed Successfully]")


if __name__ == "__main__":
    run_revenue_eda()
