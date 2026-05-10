import pandas as pd
from statsmodels.tsa.api import VAR

df = pd.read_csv("US_merged_v2.csv", parse_dates=["date"]).set_index("date")

df["yield_curve_slope"] = df["yield_curve_slope"].diff()
df = df.dropna()

model = VAR(df[["EPU", "credit_spread", "yield_curve_slope","bbb_aaa_spread"]])
results = model.select_order(maxlags=12)

print(results.summary())
print(f"AIC optimal lag : {results.aic}")
print(f"BIC optimal lag : {results.bic}")
