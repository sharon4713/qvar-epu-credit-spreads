import pandas as pd
from statsmodels.tsa.stattools import adfuller

df = pd.read_csv("US_merged_v2.csv", parse_dates=["date"])

SERIES = {
    "EPU": "EPU",
    "credit_spread": "credit_spread",
    "yield_curve_slope": "yield_curve_slope",
    "bbb_aaa_spread": "bbb_aaa_spread",
}


def run_adf(series, label):
    result = adfuller(series.dropna(), autolag="AIC")
    stat, pval = result[0], result[1]
    stationary = pval < 0.05
    print(f"  Test statistic : {stat:.4f}")
    print(f"  p-value        : {pval:.4f}")
    print(f"  Stationary     : {'Yes' if stationary else 'No'} (5% significance)")
    return stationary


non_stationary = []

print("=== ADF Test — Levels ===\n")
for label, col in SERIES.items():
    print(f"[{label}]")
    stationary = run_adf(df[col], label)
    if not stationary:
        non_stationary.append((label, col))
    print()

if non_stationary:
    print("=== ADF Test — First Differences (non-stationary series) ===\n")
    for label, col in non_stationary:
        diff = df[col].diff().dropna()
        print(f"[Δ{label}]")
        run_adf(diff, label)
        print()
else:
    print("All series are stationary in levels — no differencing needed.")
