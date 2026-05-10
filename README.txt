# Quantile VAR: How Geopolitical Risk Affects Credit Markets

## Research Question
How does economic policy uncertainty (EPU) drive corporate credit spreads?
Does this relationship intensify during market crises?
How does credit quality (BBB-AAA spread) moderate this transmission?

## Key Findings
- **Calm markets (τ=0.05):** EPU has minimal effect on credit spreads
- **Crisis markets (τ=0.95):** EPU drives spreads strongly (coefficient 65.86 at lag 1)
- **Credit quality interaction:** Low-rated firms amplify EPU impact

## Data & Methodology
- **Variables:** EPU, BAA corporate spreads, yield curve slope, BBB-AAA quality spread, EPU×BBB-AAA interaction
- **Model:** Multivariate quantile VAR with 2 lags
- **Quantiles:** 0.05, 0.25, 0.50, 0.75, 0.95
- **Sample:** 2005-2025 (251 monthly observations)

## Results
Credit spread Pseudo-R² exceeds 0.80 across all quantiles. 
The interaction term shows that when BBB-AAA spreads are wide (credit stress),
EPU shocks hit even harder.

## For Risk Managers
Use EPU as an early warning for credit spread widening.
In crises, credit quality selection becomes critical.

## Files
- `data/US_merged_v2.csv` — Cleaned dataset
- `scripts/adf_test.py` — Stationarity tests
- `scripts/lag_selection.py` — VAR lag selection
- `scripts/qvar_estimation.py` — Main QVAR estimation
- `results/qvar_results.txt` — Full coefficient output