import numpy as np
import pandas as pd
import yfinance as yf
import os

BASE = r'C:\Users\simeo\OneDrive\Desktop\qvar-epu-credit-spreads'

TICKERS = ['AAPL', 'MSFT', 'JPM', 'AMZN', 'F', 'TSLA', 'GM', 'BAC']
NAMES = {
    'AAPL': 'Apple',          'MSFT': 'Microsoft',
    'JPM':  'JPMorgan',       'AMZN': 'Amazon',
    'F':    'Ford',           'TSLA': 'Tesla',
    'GM':   'General Motors', 'BAC':  'Bank of America',
}
RATINGS = {
    'AAPL': 'AAA', 'MSFT': 'AA',  'JPM':  'A',
    'AMZN': 'AA',  'F':    'BBB', 'TSLA': 'BB',
    'GM':   'BB',  'BAC':  'A',
}

# ── Download adjusted close prices ───────────────────────────────────────────
# Start one month early so the 30-day rolling window is full by 2015-01-01
print("Downloading price data from Yahoo Finance...")
raw = yf.download(TICKERS, start='2014-12-01', end='2024-12-01',
                  auto_adjust=True, progress=False)

# Handle MultiIndex (multi-ticker) vs flat (single-ticker) columns
if isinstance(raw.columns, pd.MultiIndex):
    prices = raw['Close']
else:
    prices = raw[['Close']]
    prices.columns = TICKERS

print(f"Downloaded {len(prices)} daily rows for {list(prices.columns)}\n")

# ── Rolling 30-day annualised volatility (daily log returns) ─────────────────
log_ret = np.log(prices / prices.shift(1))            # daily log returns
vol_daily = log_ret.rolling(30).std() * np.sqrt(252)  # annualised

# Resample to month-start to match US_merged_v2.csv's YYYY-MM-01 dates
vol_monthly = vol_daily.resample('MS').mean()
vol_monthly = vol_monthly.loc['2015-01-01':'2024-01-01']

# ── Load EPU data ─────────────────────────────────────────────────────────────
df_epu = pd.read_csv(os.path.join(BASE, 'US_merged_v2.csv'), parse_dates=['date'])
df_epu = df_epu.set_index('date')[['EPU']]

# ── Merge on date (inner join) ────────────────────────────────────────────────
df = vol_monthly.join(df_epu, how='inner')
print(f"Merged dataset: {len(df)} monthly observations "
      f"({df.index[0].date()} → {df.index[-1].date()})\n")

# ── Build summary ─────────────────────────────────────────────────────────────
rows = []
for ticker in TICKERS:
    if ticker not in df.columns:
        print(f"  WARNING: {ticker} not in downloaded data, skipping.")
        continue
    sub      = df[[ticker, 'EPU']].dropna()
    avg_vol  = sub[ticker].mean()
    corr     = sub[ticker].corr(sub['EPU'])
    n_obs    = len(sub)
    rows.append({
        'Ticker':  ticker,
        'Company': NAMES[ticker],
        'Rating':  RATINGS[ticker],
        'AvgVol':  avg_vol,
        'CorrEPU': corr,
        'N':       n_obs,
    })

summary = pd.DataFrame(rows)

# ── Print & save ──────────────────────────────────────────────────────────────
SEP  = '=' * 75
SEP2 = '-' * 75

lines = []

def emit(text=''):
    lines.append(text)
    print(text)

emit(SEP)
emit('  TICKER VOLATILITY SUMMARY  |  2015–2024')
emit('  Volatility: 30-day rolling annualised log-return std dev (resamp. monthly)')
emit('  EPU source: US_merged_v2.csv')
emit(SEP)
emit()
emit(f"  {'Company':<18} {'Ticker':<7} {'Rating':<8} "
     f"{'Avg Vol':>10} {'Corr(EPU)':>12} {'N':>5}")
emit(f"  {SEP2}")

for _, r in summary.iterrows():
    emit(f"  {r['Company']:<18} {r['Ticker']:<7} {r['Rating']:<8} "
         f"{r['AvgVol']:>10.4f} {r['CorrEPU']:>12.4f} {r['N']:>5}")

emit()
emit(SEP)
emit('  NOTES')
emit(SEP)
emit('  Rating proxies are illustrative (not official Moody\'s/S&P ratings).')
emit('  Correlation is Pearson between monthly EPU and monthly avg volatility.')
emit('  Avg Vol is in annualised decimal units (e.g. 0.30 = 30% p.a.).')
emit(SEP)

# Also print the time-series vol data head for diagnostics
emit()
emit('  Sample of monthly volatility data (first 5 rows):')
emit(f"  {vol_monthly.head().to_string()}")
emit()

# Save summary text
out_txt = os.path.join(BASE, 'ticker_volatility_summary.txt')
with open(out_txt, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')
print(f"\nSaved: {out_txt}")

# Save full volatility + EPU table as CSV for further analysis
out_csv = os.path.join(BASE, 'ticker_volatility.csv')
df_out  = df[TICKERS + ['EPU']].copy()
df_out.index.name = 'date'
df_out.to_csv(out_csv)
print(f"Saved: {out_csv}")
