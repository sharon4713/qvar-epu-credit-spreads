#!/usr/bin/env python3
"""
QVAR Scenario Stress Testing Tool
(Capital Loss)
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')
os.chdir(os.path.dirname(os.path.abspath(__file__)))


# ── ANSI colours (Windows-compatible) ────────────────────────────────────────
try:
    import ctypes
    ctypes.windll.kernel32.SetConsoleMode(
        ctypes.windll.kernel32.GetStdHandle(-11), 7)
except Exception:
    pass

_USE_COLOUR = sys.stdout.isatty() or os.environ.get('FORCE_COLOR')

class C:
    GREEN  = '\033[92m'  if _USE_COLOUR else ''
    YELLOW = '\033[93m'  if _USE_COLOUR else ''
    RED    = '\033[91m'  if _USE_COLOUR else ''
    CYAN   = '\033[96m'  if _USE_COLOUR else ''
    BOLD   = '\033[1m'   if _USE_COLOUR else ''
    DIM    = '\033[2m'   if _USE_COLOUR else ''
    RESET  = '\033[0m'   if _USE_COLOUR else ''

# ── QVAR coefficients — crd_spr equation, all 5 quantiles ────────────────────
# Source: qvar_results_v3.txt  (row = crd_spr, cols = predictors, lag 1 & 2)
QVAR_CRDSP = {
    0.05: dict(intercept=0.2124,
               EPU_L1=-0.0002, crd_L1=1.1299, yld_L1=-0.0758, bbb_L1=0.1968,  int_L1=-0.0001,
               EPU_L2=-0.0002, crd_L2=-0.2316, yld_L2=-0.0294, bbb_L2=-0.3880, int_L2=0.0007),
    0.25: dict(intercept=0.0799,
               EPU_L1=-0.0001, crd_L1=1.3113, yld_L1=-0.0835, bbb_L1=-0.2359, int_L1=-0.0004,
               EPU_L2=0.0002,  crd_L2=-0.3394, yld_L2=-0.0226, bbb_L2=0.1684,  int_L2=0.0000),
    0.50: dict(intercept=0.0685,
               EPU_L1=0.0001,  crd_L1=1.1975, yld_L1=-0.0535, bbb_L1=0.0267,  int_L1=-0.0003,
               EPU_L2=0.0001,  crd_L2=-0.2271, yld_L2=0.0762,  bbb_L2=0.0083,  int_L2=-0.0002),
    0.75: dict(intercept=0.0565,
               EPU_L1=0.0000,  crd_L1=1.3743, yld_L1=0.0703,  bbb_L1=0.0169,  int_L1=-0.0001,
               EPU_L2=0.0001,  crd_L2=-0.3999, yld_L2=0.0652,  bbb_L2=0.1226,  int_L2=-0.0004),
    0.95: dict(intercept=0.2377,
               EPU_L1=-0.0040, crd_L1=0.9738, yld_L1=-0.0398, bbb_L1=0.4374,  int_L1=0.0051,
               EPU_L2=0.0035,  crd_L2=-0.0478, yld_L2=0.2057,  bbb_L2=-0.3986, int_L2=-0.0035),
}

# EPU sensitivity: EPU equation, credit-spread column, lag 1 (cross-equation response)
# Interpretation: how much EPU is driven by lagged credit spreads, used here as
# a directional proxy for EPU → spread transmission as specified in the brief.
EPU_SENS = {0.05: 27.3609, 0.25: 31.2763, 0.50: 12.5575, 0.75: 4.8695, 0.95: 65.8609}
TAUS = [0.05, 0.25, 0.50, 0.75, 0.95]
CRISIS_TAU = 0.95

REGIME_LABEL = {
    0.05: 'Calm',
    0.25: 'Mild stress',
    0.50: 'Normal',
    0.75: 'Elevated stress',
    0.95: 'Crisis / tail',
}

SCENARIOS = {
    'GFC 2008':        ('2007-09-01', '2009-03-01'),
    'Eurozone Crisis': ('2011-06-01', '2012-12-01'),
    'COVID-19 Shock':  ('2020-01-01', '2020-05-01'),
    'Fed Rate Shock':  ('2021-12-01', '2022-12-01'),
    'Russia-Ukraine War': ('2022-02-01', '2022-12-01'),
}

REQUIRED_COLS = {'date', 'EPU', 'credit_spread', 'yield_curve_slope', 'bbb_aaa_spread'}


# ── Helpers ───────────────────────────────────────────────────────────────────

def banner(title, subtitle='', width=80):
    print('\n' + '=' * width)
    print(f'{C.BOLD}  {title}{C.RESET}')
    if subtitle:
        print(f'  {C.DIM}{subtitle}{C.RESET}')
    print('=' * width)


def section(n, total, title, width=80):
    print('\n' + '─' * width)
    print(f'{C.CYAN}{C.BOLD}  {n}/{total}  {title}{C.RESET}')
    print('─' * width)


def ask(label, default, cast=float):
    """Prompt with default; returns default on blank input or non-TTY."""
    if not sys.stdin.isatty():
        return default
    try:
        raw = input(f'    {label}  (default {default}): ').strip()
        return cast(raw) if raw else default
    except (ValueError, EOFError):
        print(f'    {C.YELLOW}Invalid input — using default {default}{C.RESET}')
        return default


def traffic(pct):
    """Return colour-coded percentage string."""
    s = f'{pct:6.1f}%'
    if pct < 25:
        return C.GREEN  + s + C.RESET
    elif pct < 50:
        return C.YELLOW + s + C.RESET
    else:
        return C.RED    + s + C.RESET


def load_data(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    df = pd.read_csv(path, parse_dates=['date'])
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f'Missing columns: {sorted(missing)}')
    return df.sort_values('date').reset_index(drop=True)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    W = 80

    banner(
        'QUANTILE VAR — SCENARIO STRESS TESTING TOOL',
        f'EPU  →  Credit spread  →  Portfolio capital impact    |    {datetime.now():%Y-%m-%d  %H:%M}',
        width=W,
    )

    # ── Data path ─────────────────────────────────────────────────────────────
    if len(sys.argv) > 1:
        data_path = sys.argv[1]
    else:

        suggestion = 'US_merged_v2.csv'
        if not sys.stdin.isatty():
            data_path = suggestion
        else:
            try:
                raw = input(f'\n  Data file path (default path) [{suggestion}]: ').strip()
                data_path = raw if raw else suggestion
            except EOFError:

                data_path = suggestion

    print(f'\n  Loading: {data_path}')
    try:
        df = load_data(data_path)
    except FileNotFoundError as e:
        print(f'\n  {C.RED}ERROR  File not found: {e}{C.RESET}')
        sys.exit(1)
    except ValueError as e:
        print(f'\n  {C.RED}ERROR  {e}{C.RESET}')
        sys.exit(1)
    print(f'  {C.GREEN}OK{C.RESET}  {len(df):,} observations loaded.')

    # ══════════════════════════════════════════════════════════════════════════
    # 1 — DATA SUMMARY
    # ══════════════════════════════════════════════════════════════════════════
    section(1, 7, 'DATA SUMMARY', W)

    date_range = (f'{df["date"].iloc[0]:%Y-%m}', f'{df["date"].iloc[-1]:%Y-%m}')
    print(f'\n  Date range    :  {date_range[0]}  →  {date_range[1]}')
    print(f'  Observations  :  {len(df):,}  monthly\n')

    stat_cols   = ['EPU', 'credit_spread', 'yield_curve_slope', 'bbb_aaa_spread']
    stat_labels = ['EPU (index)', 'Credit spread (%)', 'Yield curve slope (%)', 'Baa–Aaa spread (%)']

    print(f'  {"Variable":<24}  {"Min":>7}  {"Mean":>7}  {"Median":>7}  {"Max":>7}  {"StdDev":>7}')
    print(f'  {"─"*63}')
    for col, lbl in zip(stat_cols, stat_labels):
        s = df[col].dropna()
        print(f'  {lbl:<24}  {s.min():>7.2f}  {s.mean():>7.2f}  '
              f'{s.median():>7.2f}  {s.max():>7.2f}  {s.std():>7.2f}')

    # ══════════════════════════════════════════════════════════════════════════
    # 2 — HISTORICAL CRISIS SCENARIOS
    # ══════════════════════════════════════════════════════════════════════════
    section(2, 7, 'HISTORICAL CRISIS SCENARIOS — PEAK EPU', W)
    print(f'\n  {"Scenario":<20}  {"Window":<23}  {"Peak EPU":>9}  '
          f'{"Peak Date":<11}  {"Baseline":>9}  {"EPU Shock":>10}')
    print(f'  {"─"*83}')

    scenario_store = {}
    for name, (start, end) in SCENARIOS.items():
        window  = df[(df['date'] >= start) & (df['date'] <= end)]
        pre_df  = df[df['date'] < start]
        if window.empty:
            print(f'  {name:<20}  {C.DIM}no data in window — skipping{C.RESET}')
            continue
        peak_row = window.loc[window['EPU'].idxmax()]
        peak_epu = peak_row['EPU']
        peak_dt  = peak_row['date'].strftime('%Y-%m')
        baseline = pre_df['EPU'].mean() if not pre_df.empty else df['EPU'].mean()
        shock    = peak_epu - baseline
        scenario_store[name] = dict(
            start=start, end=end,
            peak_epu=peak_epu, peak_date=peak_dt,
            baseline_epu=baseline, shock=shock,
            peak_spread=peak_row['credit_spread'],
        )
        window_str = f'{start[:7]} – {end[:7]}'
        print(f'  {name:<20}  {window_str:<23}  {peak_epu:>9.1f}  '
              f'{peak_dt:<11}  {baseline:>9.1f}  {shock:>10.1f}')

    # ══════════════════════════════════════════════════════════════════════════
    # 3 — STRESS IMPACT MATRIX
    # ══════════════════════════════════════════════════════════════════════════
    section(3, 7, f'STRESS IMPACT MATRIX  (τ = {CRISIS_TAU} crisis quantile)', W)

    epu_coef = EPU_SENS[CRISIS_TAU]
    print(f'\n  QVAR EPU sensitivity  at τ={CRISIS_TAU}  :  {epu_coef:.4f}')
    print(f'  Rule  →  spread widening (bps)  =  {epu_coef:.2f} × EPU_Shock ÷ 100\n')
    print(f'  {"Scenario":<20}  {"EPU Shock":>10}  {"Δ Spread (bps)":>14}  '
          f'{"Baseline (%)":>13}  {"Stressed (%)":>12}  {"Widening":>9}')
    print(f'  {"─"*81}')

    for name, r in scenario_store.items():
        delta_bps       = epu_coef * r['shock'] / 100
        pre_spread      = df[df['date'] < r['start']]['credit_spread'].mean()
        stressed_spread = pre_spread + delta_bps / 100
        widening_pct    = delta_bps / 100 / pre_spread * 100
        r['delta_bps']       = delta_bps
        r['baseline_spread'] = pre_spread
        r['stressed_spread'] = stressed_spread
        print(f'  {name:<20}  {r["shock"]:>10.1f}  {delta_bps:>14.2f}  '
              f'{pre_spread:>13.3f}  {stressed_spread:>12.3f}  {widening_pct:>8.1f}%')

    # ══════════════════════════════════════════════════════════════════════════
    # 4 — PORTFOLIO PARAMETERS (interactive)
    # ══════════════════════════════════════════════════════════════════════════
    section(4, 7, 'PORTFOLIO PARAMETERS', W)
    print()

    notional = ask('Portfolio notional ($M)',   500.0, float)
    duration = ask('Portfolio duration (years)',  4.0, float)
    capital  = ask('Capital buffer ($M)',         50.0, float)

    print(f'\n  {"Notional":25s}:  ${notional:>10,.1f}M')
    print(f'  {"Duration":25s}:  {duration:>11.1f} years')
    print(f'  {"Capital buffer":25s}:  ${capital:>10,.1f}M')

    # ══════════════════════════════════════════════════════════════════════════
    # 5 — CAPITAL IMPACT
    # ══════════════════════════════════════════════════════════════════════════
    section(5, 7, 'CAPITAL IMPACT', W)
    print(f'\n  MTM Loss ($M)  =  Notional × Duration × (Δ bps ÷ 10,000)')
    print(f'  Key:      {C.GREEN}GREEN < 25%{C.RESET}   {C.YELLOW}YELLOW 25–50%{C.RESET}   '
          f'{C.RED}RED > 50%{C.RESET}  of capital buffer\n')
    print(f'  {"Scenario":<20}  {"Δ Spread (bps)":>14}  '
          f'{"MTM Loss":>11}  {"% of Capital":>14}  {"Status":<10}')
    print(f'  {"─"*75}')

    for name, r in scenario_store.items():
        mtm  = notional * duration * (r['delta_bps'] / 10_000)
        pct  = mtm / capital * 100
        if pct < 25:
            status = C.GREEN  + 'LOW'       + C.RESET
        elif pct < 50:
            status = C.YELLOW + 'MODERATE'  + C.RESET
        else:
            status = C.RED    + 'MATERIAL'  + C.RESET
        print(f'  {name:<20}  {r["delta_bps"]:>14.2f}  '
              f'${mtm:>9.1f}M  {traffic(pct):>14}  {status}')

    # ══════════════════════════════════════════════════════════════════════════
    # 6 — REGIME ANALYSIS ACROSS ALL QUANTILES
    # ══════════════════════════════════════════════════════════════════════════
    section(6, 7, 'REGIME SENSITIVITY — ALL τ', W)

    median_coef = EPU_SENS[0.50]
    crisis_coef = EPU_SENS[CRISIS_TAU]
    amp_ratio   = crisis_coef / median_coef

    print(f'\n  {"τ":>7}  {"Regime":<18}  {"EPU Coeff":>10}  {"vs Median":>10}  {"Interpretation":<34}')
    print(f'  {"─"*78}')
    for tau in TAUS:
        coef  = EPU_SENS[tau]
        ratio = coef / median_coef
        lbl   = REGIME_LABEL[tau]
        interp = f'1pt EPU  →  {coef:.1f} bps spread'
        if tau == CRISIS_TAU:
            line = f'  {C.RED}  τ={tau:.2f}  {lbl:<18}  {coef:>10.2f}  {ratio:>9.1f}x  {interp:<34}{C.RESET}'
        elif tau == 0.50:
            line = f'  {C.GREEN}  τ={tau:.2f}  {lbl:<18}  {coef:>10.2f}  {ratio:>9.1f}x  {interp:<34}{C.RESET}'
        else:
            line = f'    τ={tau:.2f}  {lbl:<18}  {coef:>10.2f}  {ratio:>9.1f}x  {interp:<34}'
        print(line)

    print(f'\n  {C.BOLD}Amplification ratio  τ=0.95 / τ=0.50  =  {amp_ratio:.1f}x{C.RESET}')
    print(f'  EPU-to-spread transmission is {amp_ratio:.1f}× stronger in crisis vs normal regimes.')
    print(f'  Non-linear EPU pass-through is the key finding of the multivariate QVAR.')

    # ══════════════════════════════════════════════════════════════════════════
    # 7 — IN-SAMPLE COVERAGE CHECK
    # ══════════════════════════════════════════════════════════════════════════
    section(7, 7, 'IN-SAMPLE COVERAGE CHECK  (τ = 0.95 model validation)', W)

    c95 = QVAR_CRDSP[0.95]
    chk = df.copy()
    chk['d_yld']   = chk['yield_curve_slope'].diff()
    chk['epu_int'] = chk['EPU'] * chk['bbb_aaa_spread']
    chk = chk.dropna(subset=['d_yld']).reset_index(drop=True)

    chk['pred_q95'] = (
        c95['intercept']
        + c95['EPU_L1'] * chk['EPU'].shift(1)
        + c95['crd_L1'] * chk['credit_spread'].shift(1)
        + c95['yld_L1'] * chk['d_yld'].shift(1)
        + c95['bbb_L1'] * chk['bbb_aaa_spread'].shift(1)
        + c95['int_L1'] * chk['epu_int'].shift(1)
        + c95['EPU_L2'] * chk['EPU'].shift(2)
        + c95['crd_L2'] * chk['credit_spread'].shift(2)
        + c95['yld_L2'] * chk['d_yld'].shift(2)
        + c95['bbb_L2'] * chk['bbb_aaa_spread'].shift(2)
        + c95['int_L2'] * chk['epu_int'].shift(2)
    )

    valid     = chk.dropna(subset=['pred_q95', 'credit_spread'])
    n_total   = len(valid)
    n_covered = int((valid['credit_spread'] <= valid['pred_q95']).sum())
    emp_cov   = n_covered / n_total * 100
    diff      = emp_cov - 95.0

    print(f'\n  Observations (after 2 lags)  :  {n_total}')
    print(f'  Covered (actual ≤ pred τ=0.95):  {n_covered}  ({emp_cov:.1f}%)')
    print(f'  Expected nominal coverage     :  95.0%')

    diff_col = C.GREEN if abs(diff) <= 3 else C.YELLOW if abs(diff) <= 6 else C.RED
    print(f'  Coverage differential         :  {diff_col}{diff:+.1f} pp{C.RESET}')

    if abs(diff) <= 3:
        verdict = C.GREEN  + 'PASS'     + C.RESET + '  — Empirical coverage consistent.'
    elif abs(diff) <= 6:
        verdict = C.YELLOW + 'MARGINAL' + C.RESET + '  — Minor deviation; review for structural breaks.'
    else:
        verdict = C.RED    + 'FLAG'     + C.RESET + '  — Major deviation; model may be mis-specified.'
    print(f'\n  Verdict:  {verdict}')

    # ── Footer ────────────────────────────────────────────────────────────────
    print('\n' + '=' * W)
    print(f'{C.BOLD}  METHODOLOGY{C.RESET}')
    print(f'  {"─"*76}')
    print(f'  Model    :  Multivariate QVAR  |  5 variables  |  2 lags  |  {len(df):,} monthly obs')
    print(f'  Period   :  {date_range[0]} – {date_range[1]}')
    print(f'  Spread Δ :  EPU_sens(τ=0.95) × EPU_Shock ÷ 100   [bps]')
    print(f'  MTM loss :  Notional × Duration × (Δ bps ÷ 10,000)')
    print(f'  Coverage :  actual credit_spread ≤ predicted τ=0.95 quantile')
    print('=' * W)
    print()


if __name__ == '__main__':
    main()