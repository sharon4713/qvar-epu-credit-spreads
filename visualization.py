import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import os

BASE = r'C:\Users\simeo\OneDrive\Desktop\qvar'

COMPANIES = [
    {'ticker': 'AAPL', 'name': 'Apple',          'rating': 'AAA', 'avg_vol': 0.2646, 'corr_epu': 0.5253},
    {'ticker': 'MSFT', 'name': 'Microsoft',      'rating': 'AA',  'avg_vol': 0.2466, 'corr_epu': 0.3715},
    {'ticker': 'JPM',  'name': 'JPMorgan',       'rating': 'A',   'avg_vol': 0.2387, 'corr_epu': 0.5346},
    {'ticker': 'AMZN', 'name': 'Amazon',         'rating': 'AA',  'avg_vol': 0.3057, 'corr_epu': 0.3317},
    {'ticker': 'F',    'name': 'Ford',           'rating': 'BBB', 'avg_vol': 0.3257, 'corr_epu': 0.4192},
    {'ticker': 'TSLA', 'name': 'Tesla',          'rating': 'BB',  'avg_vol': 0.5365, 'corr_epu': 0.5332},
    {'ticker': 'GM',   'name': 'Gen. Motors',    'rating': 'BB',  'avg_vol': 0.3269, 'corr_epu': 0.5327},
    {'ticker': 'BAC',  'name': 'BofA',           'rating': 'A',   'avg_vol': 0.2766, 'corr_epu': 0.5080},
]

RATING_ORDER  = ['AAA', 'AA', 'A', 'BBB', 'BB']
RATING_COLOR  = {'AAA': '#2ca02c', 'AA': '#1f77b4', 'A': '#e6c822', 'BBB': '#ff7f0e', 'BB': '#d62728'}
RATING_TAU    = {'AAA': 0.05,      'AA': 0.25,      'A': 0.50,      'BBB': 0.75,      'BB': 0.95}

TAUS = np.array([0.05, 0.25, 0.50, 0.75, 0.95])

EPU_CRDSP_L1  = np.array([-0.0002, -0.0001,  0.0001,  0.0000, -0.0040])
EPU_CRDSP_L2  = np.array([-0.0002,  0.0002,  0.0001,  0.0001,  0.0035])
EPU_CRDSP_CUM = EPU_CRDSP_L1 + EPU_CRDSP_L2

EPU_BBBSP_L1  = np.array([ 0.0002,  0.0002,  0.0002,  0.0001, -0.0017])
EPU_BBBSP_L2  = np.array([-0.0004, -0.0003, -0.0005, -0.0002,  0.0003])
EPU_BBBSP_CUM = EPU_BBBSP_L1 + EPU_BBBSP_L2

PSEUDO_R2_CRDSP = np.array([0.7496, 0.7813, 0.8018, 0.8071, 0.8190])

EPU_SHOCK = 100

for c in COMPANIES:
    idx = RATING_ORDER.index(c['rating'])
    tau = RATING_TAU[c['rating']]
    tau_idx = np.where(TAUS == tau)[0][0]
    c['tau']              = tau
    c['spread_sens_bps']  = EPU_CRDSP_CUM[tau_idx] * EPU_SHOCK * 100
    c['bbbsp_sens_bps']   = EPU_BBBSP_CUM[tau_idx] * EPU_SHOCK * 100
    c['color']            = RATING_COLOR[c['rating']]

# ── Dark mode style ───────────────────────────────────────────────────────────
BG        = '#0f0f0f'
PANEL_BG  = '#1a1a1a'
TEXT      = '#e0e0e0'
GRID      = '#2e2e2e'
SPINE     = '#444444'

plt.rcParams.update({
    'font.family':          'DejaVu Sans',
    'font.size':            11,
    'text.color':           TEXT,
    'axes.facecolor':       PANEL_BG,
    'axes.edgecolor':       SPINE,
    'axes.labelcolor':      TEXT,
    'axes.spines.top':      False,
    'axes.spines.right':    False,
    'axes.grid':            True,
    'grid.color':           GRID,
    'grid.alpha':           1.0,
    'figure.facecolor':     BG,
    'figure.dpi':           150,
    'xtick.color':          TEXT,
    'ytick.color':          TEXT,
    'legend.facecolor':     '#222222',
    'legend.edgecolor':     SPINE,
    'legend.labelcolor':    TEXT,
})

legend_patches = [
    mpatches.Patch(color=RATING_COLOR[r], label=r) for r in RATING_ORDER
]

# ═══════════════════════════════════════════════════════════════════════════════
# PLOT 1
# ═══════════════════════════════════════════════════════════════════════════════
fig1, ax1 = plt.subplots(figsize=(10, 7))
fig1.suptitle('Company volatility vs EPU correlation\n'
              '(color = rating proxy, 2015–2024)', fontsize=10, fontweight='bold', y=0.98, color=TEXT)

vols  = np.array([c['avg_vol']  for c in COMPANIES])
corrs = np.array([c['corr_epu'] for c in COMPANIES])

m, b = np.polyfit(vols, corrs, 1)
xfit = np.linspace(vols.min() * 0.95, vols.max() * 1.05, 100)
ax1.plot(xfit, m * xfit + b, '--', color='#888888', linewidth=1.2,
         alpha=0.8, label=f'Trend  (slope={m:.2f})', zorder=1)

vol_by_rating = {}
for c in COMPANIES:
    vol_by_rating.setdefault(c['rating'], []).append(c['avg_vol'])

for rating, vlist in vol_by_rating.items():
    ax1.axvspan(min(vlist) - 0.005, max(vlist) + 0.005,
                color=RATING_COLOR[rating], alpha=0.08, zorder=0)

for c in COMPANIES:
    ax1.scatter(c['avg_vol'], c['corr_epu'],
                color=c['color'], s=160, zorder=3, edgecolors='#0f0f0f', linewidths=1.2)
    ax1.annotate(
        f"{c['name']}\n({c['ticker']})",
        xy=(c['avg_vol'], c['corr_epu']),
        xytext=(8, 4), textcoords='offset points',
        fontsize=7, color=TEXT,
        bbox=dict(boxstyle='round,pad=0.2', fc='#222222', alpha=0.8, ec='none')
    )

ax1.set_xlabel('Average annualised volatility (30-day rolling)', fontsize=9)
ax1.set_ylabel('Pearson corr. with EPU', fontsize=9)
ax1.set_xlim(0.20, 0.60)
ax1.set_ylim(0.28, 0.60)
ax1.legend(handles=legend_patches + [Line2D([0], [0], ls='--', color='#888888', label='Trendline')],
           title='Rating proxy', framealpha=0.9, fontsize=7)

plt.tight_layout()
out1 = os.path.join(BASE, 'qvar_ticker_bridge_vol.png')
fig1.savefig(out1, bbox_inches='tight', facecolor=BG)
plt.close(fig1)
print(f"Saved: {out1}")

# ═══════════════════════════════════════════════════════════════════════════════
# PLOT 2
# ═══════════════════════════════════════════════════════════════════════════════
fig2, ax2 = plt.subplots(figsize=(10, 7))
fig2.suptitle('Company volatility vs QVAR-inferred credit spread sensitivity to EPU\n'
              'Sensitivity = (Lag1+Lag2) EPU coefficient × 100-unit EPU shock',
              fontsize=10, fontweight='bold', y=0.98, color=TEXT)

sens = np.array([c['spread_sens_bps'] for c in COMPANIES])
vols = np.array([c['avg_vol']         for c in COMPANIES])

ax2.axhline(0, color='#888888', linewidth=0.8, alpha=0.7, linestyle='-')

m2, b2 = np.polyfit(vols, sens, 1)
xfit2 = np.linspace(vols.min() * 0.95, vols.max() * 1.05, 100)
ax2.plot(xfit2, m2 * xfit2 + b2, '--', color='#888888', linewidth=1.2, alpha=0.8,
         label=f'Trend  (slope={m2:.1f} bps/vol-unit)')

tau_sens = {tau: EPU_CRDSP_CUM[i] * EPU_SHOCK * 100 for i, tau in enumerate(TAUS)}
for rating, tau in RATING_TAU.items():
    s = tau_sens[tau]
    ax2.axhline(s, color=RATING_COLOR[rating], linewidth=0.8, linestyle=':', alpha=0.6)
    ax2.text(0.205, s + 0.15, f'τ={tau}', fontsize=7,
             color=RATING_COLOR[rating], alpha=0.9)

for c in COMPANIES:
    ax2.scatter(c['avg_vol'], c['spread_sens_bps'],
                color=c['color'], s=160, zorder=3, edgecolors='#0f0f0f', linewidths=1.2)
    ax2.annotate(
        f"{c['name']}\n({c['ticker']})",
        xy=(c['avg_vol'], c['spread_sens_bps']),
        xytext=(8, 4), textcoords='offset points',
        fontsize=7, color=TEXT,
        bbox=dict(boxstyle='round,pad=0.2', fc='#222222', alpha=0.8, ec='none')
    )

ax2.set_xlabel('Average Annualised Volatility (30-day rolling)', fontsize=9)
ax2.set_ylabel('Spread Response to +100-unit EPU Shock (bps)\n, cumulative over 2 month period', fontsize=11)
ax2.set_xlim(0.20, 0.60)
ax2.legend(handles=legend_patches + [Line2D([0], [0], ls='--', color='#888888', label='Trendline')],
           title='Rating proxy (→ QVAR τ)', framealpha=0.9, fontsize=8)

ax2.text(0.99, 0.02,
         'AAA→τ=0.05  AA→τ=0.25  A→τ=0.50  BBB→τ=0.75  BB→τ=0.95',
         transform=ax2.transAxes, fontsize=7, ha='right', va='bottom', color='#aaaaaa',
         style='italic')

plt.tight_layout()
out2 = os.path.join(BASE, 'qvar_ticker_bridge_spreads.png')
fig2.savefig(out2, bbox_inches='tight', facecolor=BG)
plt.close(fig2)
print(f"Saved: {out2}")

# ═══════════════════════════════════════════════════════════════════════════════
# PLOT 3
# ═══════════════════════════════════════════════════════════════════════════════
fig3, (ax3a, ax3b) = plt.subplots(2, 1, figsize=(11, 10), sharex=True,
                                   gridspec_kw={'height_ratios': [3, 2]})
fig3.suptitle('QVAR: EPU effect on spreads across quantiles\nwith company volatility overlay',
              fontsize=10, fontweight='bold', y=0.99, color=TEXT)

tau_labels = [f'τ={t}' for t in TAUS]
x = np.arange(len(TAUS))

bps_crdsp_l1  = EPU_CRDSP_L1  * EPU_SHOCK * 100
bps_crdsp_l2  = EPU_CRDSP_L2  * EPU_SHOCK * 100
bps_crdsp_cum = EPU_CRDSP_CUM * EPU_SHOCK * 100
bps_bbbsp_cum = EPU_BBBSP_CUM * EPU_SHOCK * 100

ax3a.axhline(0, color='#888888', linewidth=0.7, alpha=0.6)

ax3a.bar(x - 0.18, bps_crdsp_l1, width=0.18, label='Credit spread: Lag 1',
         color='#4c78a8', alpha=0.85)
ax3a.bar(x,         bps_crdsp_l2, width=0.18, label='Credit spread: Lag 2',
         color='#4c78a8', alpha=0.40)
ax3a.plot(x, bps_crdsp_cum, 'o-', color='#79aec8', linewidth=2.2, markersize=7,
          label='Credit spread: Cumulative (L1+L2)', zorder=4)
ax3a.plot(x, bps_bbbsp_cum, 's--', color='#ff6b6b', linewidth=2.0, markersize=7,
          label='Baa–Aaa spread: Cumulative (L1+L2)', zorder=4)

for i, (tau, rating) in enumerate(zip(TAUS, ['AAA', 'AA', 'A', 'BBB', 'BB'])):
    ax3a.axvspan(i - 0.5, i + 0.5, color=RATING_COLOR[rating], alpha=0.10, zorder=0)
    ax3a.text(i, ax3a.get_ylim()[1] if ax3a.get_ylim()[1] > 0 else 1,
              rating, ha='center', va='bottom', fontsize=8.5,
              color=RATING_COLOR[rating], fontweight='bold')

ax3a.set_ylabel('EPU effect on spread (bps)\nper +100-unit EPU shock', fontsize=9)
ax3a.legend(fontsize=8, loc='lower left', framealpha=0.9)
ax3a.set_title('EPU → Spread coefficient magnitude across quantiles', fontsize=9, color=TEXT)

plotted_labels = set()
for c in COMPANIES:
    tau_idx = np.where(TAUS == c['tau'])[0][0]
    label = c['rating'] if c['rating'] not in plotted_labels else None
    ax3b.hlines(c['avg_vol'], tau_idx - 0.45, tau_idx + 0.45,
                colors=c['color'], linewidth=2.5, linestyles='-', alpha=0.9)
    ax3b.scatter(tau_idx, c['avg_vol'], color=c['color'], s=80, zorder=5,
                 edgecolors='#0f0f0f', linewidths=1.0)
    ax3b.annotate(
        c['ticker'],
        xy=(tau_idx, c['avg_vol']),
        xytext=(5, 2), textcoords='offset points',
        fontsize=8, color=c['color']
    )
    if label:
        plotted_labels.add(c['rating'])

ax3b_r2 = ax3b.twinx()
ax3b_r2.plot(x, PSEUDO_R2_CRDSP, 'D:', color='#aaaaaa', linewidth=1.4, markersize=5,
             alpha=0.8, label='crd_spr Pseudo-R²')
ax3b_r2.set_ylabel('QVAR Pseudo-R²', fontsize=9, color='#aaaaaa')
ax3b_r2.tick_params(axis='y', colors='#aaaaaa', labelsize=8)
ax3b_r2.set_ylim(0.70, 0.87)
ax3b_r2.legend(fontsize=8, loc='upper left', framealpha=0.9)
ax3b_r2.set_facecolor(PANEL_BG)

ax3b.set_xlim(-0.5, 4.5)
ax3b.set_xticks(x)
ax3b.set_xticklabels(tau_labels, fontsize=10)
ax3b.set_xlabel('Quantiles(τ)  ←  low stress                               high stress  →', fontsize=9)
ax3b.set_ylabel('Avg Annualised\nVolatility', fontsize=10)
ax3b.set_title('Company volatilities at their rating-mapped quantiles '
               '(dotted = QVAR model fit quality)', fontsize=9, color=TEXT)

for i, rating in enumerate(['AAA', 'AA', 'A', 'BBB', 'BB']):
    ax3b.axvspan(i - 0.5, i + 0.5, color=RATING_COLOR[rating], alpha=0.08, zorder=0)

plt.tight_layout(rect=[0, 0, 1, 0.97])
out3 = os.path.join(BASE, 'qvar_quantile_overlay.png')
fig3.savefig(out3, bbox_inches='tight', facecolor=BG)
plt.close(fig3)
print(f"Saved: {out3}")

print("\nAll 3 plots saved successfully.")