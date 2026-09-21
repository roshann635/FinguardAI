"""FinGuard AI — EDA 03: Cash Flow Dynamics & Liquidity Analysis.

Analyzes:
1. Cash inflows (customer receipts) vs outflows (vendor disbursements).
2. Net operating cash flow monthly trajectory (Jan 2023 – Mar 2025).
3. Cumulative liquidity curve and cash reserves trajectory.
4. Working capital seasonality and cyclical liquidity troughs.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "ml" / "notebooks"))

import pandas as pd
from data_loader import load_dataset


def run_cashflow_eda():
    print("=" * 70)
    print(" FinGuard AI — Exploratory Data Analysis: Cash Flow & Liquidity")
    print("=" * 70)

    data = load_dataset()
    cf = data["cash_flows"].copy()

    if cf.empty:
        print("No cash flow data available.")
        return

    print(f"\nTotal Cash Flow Records: {len(cf):,}")
    inflows = cf[cf["flow_type"] == "inflow"]["amount"].sum()
    outflows = cf[cf["flow_type"] == "outflow"]["amount"].sum()
    net_cf = inflows - outflows

    print(f"Total Cash Inflows:   ${inflows:>14,.2f}")
    print(f"Total Cash Outflows:  ${outflows:>14,.2f}")
    print(f"Net Cumulative Flow:  ${net_cf:>14,.2f} ({'Surplus' if net_cf >= 0 else 'Deficit'})")

    # 1. Monthly Inflow/Outflow Breakdown
    cf["month"] = cf["flow_date"].dt.to_period("M")
    m_in = cf[cf["flow_type"] == "inflow"].groupby("month")["amount"].sum().rename("inflows")
    m_out = cf[cf["flow_type"] == "outflow"].groupby("month")["amount"].sum().rename("outflows")
    monthly_cf = pd.concat([m_in, m_out], axis=1).fillna(0)
    monthly_cf["net"] = monthly_cf["inflows"] - monthly_cf["outflows"]
    monthly_cf["cumulative"] = monthly_cf["net"].cumsum()

    print("\n--- Recent Monthly Cash Flow Dynamics (Last 6 Months) ---")
    for m, row in monthly_cf.tail(6).iterrows():
        status = "SURPLUS" if row["net"] >= 0 else "DEFICIT"
        print(f"  {m}: In ${row['inflows']:>10,.2f} | Out ${row['outflows']:>10,.2f} | Net ${row['net']:>10,.2f} | Cum: ${row['cumulative']:>11,.2f} [{status}]")

    # 2. Quarterly Cash Velocity
    cf["quarter"] = cf["flow_date"].dt.to_period("Q")
    q_cf = cf.groupby(["quarter", "flow_type"])["amount"].sum().unstack(fill_value=0)
    q_cf["net"] = q_cf.get("inflow", 0) - q_cf.get("outflow", 0)
    print("\n--- Quarterly Net Cash Velocity ---")
    for q, row in q_cf.iterrows():
        sign = "+" if row["net"] >= 0 else ""
        print(f"  {q}: Inflows ${row.get('inflow', 0):>11,.2f} | Outflows ${row.get('outflow', 0):>11,.2f} | Net: {sign}${row['net']:>10,.2f}")

    # 3. Liquidity Health Indicators
    burn_months = monthly_cf[monthly_cf["net"] < 0]
    print("\n--- Liquidity Health Metrics ---")
    print(f"  Total Months Observed:        {len(monthly_cf)}")
    print(f"  Months with Positive Cash Flow: {len(monthly_cf) - len(burn_months)} ({((len(monthly_cf) - len(burn_months))/len(monthly_cf))*100:.1f}%)")
    print(f"  Months with Deficit Cash Flow:  {len(burn_months)}")
    print(f"  Average Monthly Net Flow:     ${monthly_cf['net'].mean():>10,.2f}")
    print(f"  Lowest Single Month Net:      ${monthly_cf['net'].min():>10,.2f} (in {monthly_cf['net'].idxmin()})")
    print(f"  Peak Single Month Net:        ${monthly_cf['net'].max():>10,.2f} (in {monthly_cf['net'].idxmax()})")

    print("\n[EDA 03 Completed Successfully]")


if __name__ == "__main__":
    run_cashflow_eda()
