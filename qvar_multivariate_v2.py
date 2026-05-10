import numpy as np
import pandas as pd
from statsmodels.regression.quantile_regression import QuantReg

BASE   = r'C:\Users\simeo\OneDrive\Desktop\qvar'
LAGS   = 2
TAUS   = [0.05, 0.25, 0.50, 0.75, 0.95]
VARS   = ['EPU', 'credit_spread', 'yield_curve_slope', 'bbb_aaa_spread', 'epu_bbb_aaa']
SHORT  = ['EPU', 'crd_spr', 'yld_slp', 'bbb_aaa', 'epu_int']
N      = len(VARS)
W      = 11

SEP  = "=" * 72
SEP2 = "-" * 72
lines = []

def emit(*args):
    text = " ".join(str(a) for a in args)
    lines.append(text)
    print(text)

def emit_blank():
    lines.append("")
    print()

# ── Load & transform ────────────────────────────────────────────────────────
df = pd.read_csv(f'{BASE}/US_merged_v2.csv', parse_dates=['date'])
df = df.sort_values('date').reset_index(drop=True)

df['yield_curve_slope'] = df['yield_curve_slope'].diff()
df['epu_bbb_aaa']       = df['EPU'] * df['bbb_aaa_spread']
df = df.dropna().reset_index(drop=True)

emit(f"Observations after differencing & dropna: {len(df)}")
emit(f"Date range: {df['date'].iloc[0].date()} → {df['date'].iloc[-1].date()}")
emit_blank()

# ── Build lagged regressor matrix ───────────────────────────────────────────
data = df[VARS].to_numpy()
T    = len(data)

X = np.column_stack(
    [np.ones(T - LAGS)] +
    [data[LAGS - lag : T - lag] for lag in range(1, LAGS + 1)]
)
Y = data[LAGS:]

# ── Helpers ─────────────────────────────────────────────────────────────────
def tick_loss(u, tau):
    return u * np.where(u >= 0, tau, tau - 1)

def pseudo_r2(y, y_hat, tau):
    resid = y - y_hat
    null  = y - np.quantile(y, tau)
    denom = tick_loss(null, tau).sum()
    return 1.0 - tick_loss(resid, tau).sum() / denom if denom != 0 else np.nan

# ── Estimation ───────────────────────────────────────────────────────────────
sep  = '─' * (18 + W * N)
head = f"  {'':16}" + ''.join(f'{s:>{W}}' for s in SHORT)

emit(SEP)
emit('  MULTIVARIATE QUANTILE VAR  |  5 Variables, 2 Lags')
emit('  yield_curve_slope is first-differenced; epu_bbb_aaa = EPU × bbb_aaa')
emit(SEP)

for tau in TAUS:
    emit_blank()
    emit('─' * 72)
    emit(f'  τ = {tau:.2f}')
    emit('─' * 72)

    coefs  = np.zeros((N, 1 + LAGS * N))
    fitted = np.zeros_like(Y)

    for i in range(N):
        res           = QuantReg(Y[:, i], X).fit(q=tau, max_iter=10000, p_tol=1e-6)
        coefs[i]      = res.params
        fitted[:, i]  = res.fittedvalues

    # Intercepts
    emit_blank()
    emit('  Intercepts')
    emit(head)
    row = ''.join(f'{coefs[i, 0]:>{W}.4f}' for i in range(N))
    emit(f"  {'':16}{row}")

    # Lag coefficient matrices
    for lag in range(1, LAGS + 1):
        c0 = 1 + (lag - 1) * N
        emit_blank()
        emit(f'  Lag {lag} coefficient matrix  (row = dep. var, col = predictor at lag {lag})')
        emit(sep)
        emit(head)
        emit(sep)
        for i in range(N):
            row = ''.join(f'{coefs[i, c0 + j]:>{W}.4f}' for j in range(N))
            emit(f"  {SHORT[i]:16}{row}")
        emit(sep)

    # Fit statistics
    emit_blank()
    emit('  Fit statistics')
    emit(f"  {'Variable':16} {'Pseudo-R²':>12} {'MAE':>10}")
    for i in range(N):
        pr2 = pseudo_r2(Y[:, i], fitted[:, i], tau)
        mae = np.mean(np.abs(Y[:, i] - fitted[:, i]))
        emit(f"  {SHORT[i]:16} {pr2:>12.4f} {mae:>10.4f}")

emit_blank()
emit(SEP)
emit('  Done.')
emit(SEP)

with open(f'{BASE}/qvar_results_v3.txt', "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print("\nSaved qvar_results_v3.txt")