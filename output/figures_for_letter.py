#!/usr/bin/env python3
"""
Generate two composite figures for the PNAS Letter.

Figure 1: Bot approximates human performance
  Panel A: Mean RT vs. Accuracy scatter (bot within human cloud)
  Panel B: ANT network scores (violin + bot + Fan benchmarks)
  Panel C: Cue x Flanker interaction (human vs. bot)

Figure 2: Detectable artifacts remain
  Panel A: QQ correlation distribution with bot position marked
  Panel B: Skewness distribution with bot position marked
  Panel C: Autocorrelation distribution with bot position marked
  Panel D: RT density distributions (bot bimodality vs. human)

Output: JPEG at 300 dpi to output/
"""

import os
import csv
import glob
import re
import statistics
import math
from collections import defaultdict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

# ============================================================
# Setup
# ============================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(SCRIPT_DIR) if os.path.basename(SCRIPT_DIR) != 'bot_or_not_letter' else SCRIPT_DIR
# Handle case where script is in output/ subdirectory
if os.path.basename(SCRIPT_DIR) == 'output':
    BASE = os.path.dirname(SCRIPT_DIR)
ANT_DATA_DIR = os.path.join(BASE, 'data', 'raw', 'ant_data')
BOT_DATA = os.path.join(BASE, 'bot_iterative', 'data', 'v7_3_data.csv')
OUTPUT_DIR = SCRIPT_DIR  # save figures alongside this script

# Style
plt.rcParams.update({
    'font.size': 8,
    'font.family': 'sans-serif',
    'axes.linewidth': 0.8,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.1,
})

# Colorblind-friendly diverging palette (Wong, 2011; Nature Methods)
BOT_COLOR = '#D55E00'    # vermillion (warm)
HUMAN_COLOR = '#0072B2'  # blue (cool)
FAN_COLOR = '#009E73'    # bluish green
GRAY = '#999999'

np.random.seed(42)

# ============================================================
# Data processing (same pipeline as generate_figures.py)
# ============================================================
def parse_filename(fname):
    m = re.match(r'^(\d+)_(\d+)_ant_', os.path.basename(fname))
    return (m.group(1), m.group(2)) if m else (None, None)

def classify_cue(v):
    if not v: return None
    v = v.strip()
    return {'stim/blank.png': 'no_cue', 'stim/centre.png': 'center_cue',
            'stim/both.png': 'double_cue', 'stim/upper.png': 'spatial_cue',
            'stim/lower.png': 'spatial_cue'}.get(v)

def classify_flanker(v):
    if not v: return None
    v = v.strip().lower()
    if 'incong' in v: return 'incongruent'
    elif 'cong' in v: return 'congruent'
    elif 'neutral' in v: return 'neutral'
    return None

print("Processing participant data for letter figures...")
files = sorted(glob.glob(os.path.join(ANT_DATA_DIR, "*.csv")))

human_mean_rts = []
human_accuracies = []
human_alerting = []
human_orienting = []
human_executive = []
human_qq_vals = []
human_skew_vals = []
human_autocorr_lag1 = []
human_all_rts = []
human_condition_rts = defaultdict(list)  # (cue, flanker) -> list of (mean, sd) tuples

seen = set()
n_valid = 0

for filepath in files:
    pid, loc = parse_filename(filepath)
    if pid is None: continue
    key = (pid, loc)
    if key in seen: continue

    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            rows = list(csv.DictReader(f))
    except:
        continue

    main_trials = [r for r in rows if r.get('mainLoop.thisN', '').strip() != '']
    if not main_trials: continue

    skip = False
    for t in main_trials:
        rt_s = t.get('resp.rt', '').strip()
        if rt_s:
            try:
                v = float(rt_s)
                if v > 120 or v < 0.001:
                    skip = True
                    break
            except:
                pass
    if skip: continue

    parsed = []
    for t in main_trials:
        rt_s = t.get('resp.rt', '').strip()
        corr_s = t.get('resp.corr', '').strip()
        if not rt_s or not corr_s: continue
        try:
            rt_ms = float(rt_s) * 1000
            corr = int(float(corr_s))
        except:
            continue
        parsed.append({
            'rt_ms': rt_ms, 'correct': corr,
            'cue': classify_cue(t.get('cue', '')),
            'flanker': classify_flanker(t.get('tar', ''))
        })

    if not parsed: continue
    acc = 100 * sum(1 for t in parsed if t['correct'] == 1) / len(parsed)
    if acc < 75: continue

    seen.add(key)
    n_valid += 1

    correct = [t for t in parsed if t['correct'] == 1]
    clean = [t for t in correct if 200 <= t['rt_ms'] <= 1700]
    if not clean: continue

    rts = [t['rt_ms'] for t in clean]
    mean_rt = statistics.mean(rts)
    human_mean_rts.append(mean_rt)
    human_accuracies.append(acc)
    human_all_rts.extend(rts)

    # Network scores
    cue_rts = defaultdict(list)
    flank_rts = defaultdict(list)
    cond_data = defaultdict(list)
    for t in clean:
        if t['cue']:
            cue_rts[t['cue']].append(t['rt_ms'])
        if t['flanker']:
            flank_rts[t['flanker']].append(t['rt_ms'])
        if t['cue'] and t['flanker']:
            cond_data[(t['cue'], t['flanker'])].append(t['rt_ms'])

    def sm(lst):
        return statistics.mean(lst) if lst else None
    rt_no = sm(cue_rts.get('no_cue', []))
    rt_dbl = sm(cue_rts.get('double_cue', []))
    rt_ctr = sm(cue_rts.get('center_cue', []))
    rt_sp = sm(cue_rts.get('spatial_cue', []))
    rt_c = sm(flank_rts.get('congruent', []))
    rt_i = sm(flank_rts.get('incongruent', []))

    if rt_no and rt_dbl: human_alerting.append(rt_no - rt_dbl)
    if rt_ctr and rt_sp: human_orienting.append(rt_ctr - rt_sp)
    if rt_i and rt_c: human_executive.append(rt_i - rt_c)

    # Condition-level means for cue x flanker plot
    for (c, fl), rtlist in cond_data.items():
        if len(rtlist) > 2:
            human_condition_rts[(c, fl)].append(statistics.mean(rtlist))

    # Psychometric metrics
    n = len(rts)
    if n >= 30:
        # QQ correlation
        sorted_rts = sorted(rts)
        def norm_ppf(p):
            if p <= 0 or p >= 1: return 0
            t = math.sqrt(-2 * math.log(min(p, 1 - p)))
            val = t - (2.515517 + 0.802853*t + 0.010328*t**2) / (1 + 1.432788*t + 0.189269*t**2 + 0.001308*t**3)
            return val if p > 0.5 else -val
        theoretical = [norm_ppf((i + 0.5) / n) for i in range(n)]
        ms = statistics.mean(sorted_rts)
        mt = statistics.mean(theoretical)
        ss = statistics.stdev(sorted_rts)
        st = statistics.stdev(theoretical)
        if ss > 0 and st > 0:
            qq = sum((sorted_rts[i] - ms) * (theoretical[i] - mt) for i in range(n)) / (n - 1) / (ss * st)
            human_qq_vals.append(qq)

        # Skewness
        m = statistics.mean(rts)
        s = statistics.stdev(rts)
        if s > 0:
            human_skew_vals.append(sum(((x - m) / s)**3 for x in rts) / n)

        # Autocorrelation lag-1
        var_rt = statistics.variance(rts)
        if var_rt > 0:
            ac1 = sum((rts[i] - m) * (rts[i + 1] - m) for i in range(n - 1)) / (n - 1) / var_rt
            human_autocorr_lag1.append(ac1)

print(f"Processed {n_valid} valid participants")

# ============================================================
# Process bot data
# ============================================================
with open(BOT_DATA, 'r') as f:
    bot_rows = list(csv.DictReader(f))

def parse_cue_bot(v):
    if not v: return None
    v = v.lower()
    if 'blank' in v: return 'no_cue'
    if 'centre' in v or 'center' in v: return 'center_cue'
    if 'both' in v: return 'double_cue'
    if 'upper' in v or 'lower' in v: return 'spatial_cue'
    return None

def parse_flanker_bot(v):
    if not v: return None
    v = v.lower()
    if 'incong' in v: return 'incongruent'
    if 'cong' in v: return 'congruent'
    if 'neut' in v: return 'neutral'
    return None

bot_main = []
for row in bot_rows:
    if row.get('mainLoop.ran', '').strip() != '1': continue
    if row.get('trial.started', '').strip() == '': continue
    cue = parse_cue_bot(row.get('cue', ''))
    flanker = parse_flanker_bot(row.get('tar', ''))
    if not cue or not flanker: continue
    rt_str = row.get('resp.rt', '').strip()
    corr_str = row.get('resp.corr', '').strip()
    keys_str = row.get('resp.keys', '').strip()
    missed = rt_str == '' or keys_str == '' or keys_str == 'None'
    bot_main.append({
        'cue': cue, 'flanker': flanker,
        'rt_ms': float(rt_str) * 1000 if rt_str else None,
        'correct': int(float(corr_str)) if corr_str else None,
        'missed': missed,
    })

bot_responded = [t for t in bot_main if not t['missed']]
bot_correct = [t for t in bot_responded if t['correct'] == 1]
bot_clean = [t for t in bot_correct if t['rt_ms'] and 200 <= t['rt_ms'] <= 1700]
bot_rts = [t['rt_ms'] for t in bot_clean]
bot_mean_rt = statistics.mean(bot_rts)
bot_acc = 100 * len(bot_correct) / len(bot_responded)

bot_cue_rts = defaultdict(list)
bot_flank_rts = defaultdict(list)
for t in bot_clean:
    bot_cue_rts[t['cue']].append(t['rt_ms'])
    bot_flank_rts[t['flanker']].append(t['rt_ms'])

# ============================================================
# Compute bot psychometric markers (same methods as human)
# ============================================================
def compute_qq(rts):
    n = len(rts)
    sorted_rts = sorted(rts)
    def norm_ppf(p):
        if p <= 0 or p >= 1: return 0
        t = math.sqrt(-2 * math.log(min(p, 1 - p)))
        val = t - (2.515517 + 0.802853*t + 0.010328*t**2) / (1 + 1.432788*t + 0.189269*t**2 + 0.001308*t**3)
        return val if p > 0.5 else -val
    theoretical = [norm_ppf((i + 0.5) / n) for i in range(n)]
    ms, mt = statistics.mean(sorted_rts), statistics.mean(theoretical)
    ss, st = statistics.stdev(sorted_rts), statistics.stdev(theoretical)
    if ss > 0 and st > 0:
        return sum((sorted_rts[i] - ms) * (theoretical[i] - mt) for i in range(n)) / (n - 1) / (ss * st)
    return None

def compute_skewness(rts):
    n = len(rts)
    m, s = statistics.mean(rts), statistics.stdev(rts)
    if s > 0:
        return sum(((x - m) / s)**3 for x in rts) / n
    return None

def compute_autocorr(rts):
    n = len(rts)
    m = statistics.mean(rts)
    var_rt = statistics.variance(rts)
    if var_rt > 0:
        return sum((rts[i] - m) * (rts[i + 1] - m) for i in range(n - 1)) / (n - 1) / var_rt
    return None

bot_qq = compute_qq(bot_rts)
bot_skew = compute_skewness(bot_rts)
bot_ac = compute_autocorr(bot_rts)

# Bot network scores
def sm(lst):
    return statistics.mean(lst) if lst else None
bot_alerting = sm(bot_cue_rts.get('no_cue', [])) - sm(bot_cue_rts.get('double_cue', []))
bot_orienting = sm(bot_cue_rts.get('center_cue', [])) - sm(bot_cue_rts.get('spatial_cue', []))
bot_executive = sm(bot_flank_rts.get('incongruent', [])) - sm(bot_flank_rts.get('congruent', []))

# Z-scores: (bot - human_mean) / human_sd
z_qq = (bot_qq - statistics.mean(human_qq_vals)) / statistics.stdev(human_qq_vals) if human_qq_vals else 0
z_sk = (bot_skew - statistics.mean(human_skew_vals)) / statistics.stdev(human_skew_vals) if human_skew_vals else 0
z_ac = (bot_ac - statistics.mean(human_autocorr_lag1)) / statistics.stdev(human_autocorr_lag1) if human_autocorr_lag1 else 0

# ============================================================
# Print all statistics reported in the manuscript
# ============================================================
print("\n" + "=" * 65)
print("STATISTICS REPORTED IN MANUSCRIPT")
print("=" * 65)

print(f"\n--- Human Participants (N = {n_valid}) ---")
print(f"  Mean RT:          M = {statistics.mean(human_mean_rts):.1f} ms,  SD = {statistics.stdev(human_mean_rts):.1f} ms")
print(f"  Accuracy:         M = {statistics.mean(human_accuracies):.1f}%,    SD = {statistics.stdev(human_accuracies):.1f}%")
print(f"  Alerting:         M = {statistics.mean(human_alerting):.1f} ms,  SD = {statistics.stdev(human_alerting):.1f} ms")
print(f"  Orienting:        M = {statistics.mean(human_orienting):.1f} ms,  SD = {statistics.stdev(human_orienting):.1f} ms")
print(f"  Executive:        M = {statistics.mean(human_executive):.1f} ms,  SD = {statistics.stdev(human_executive):.1f} ms")
print(f"  QQ correlation:   M = {statistics.mean(human_qq_vals):.3f},     SD = {statistics.stdev(human_qq_vals):.3f}")
print(f"  Skewness:         M = {statistics.mean(human_skew_vals):.2f},      SD = {statistics.stdev(human_skew_vals):.2f}")
print(f"  Autocorr lag-1:   M = {statistics.mean(human_autocorr_lag1):.3f},     SD = {statistics.stdev(human_autocorr_lag1):.3f}")

print(f"\n--- Bot v7.3 (Single Run) ---")
print(f"  Mean RT:          {bot_mean_rt:.1f} ms")
print(f"  Accuracy:         {bot_acc:.1f}%")
print(f"  Alerting:         {bot_alerting:.1f} ms")
print(f"  Orienting:        {bot_orienting:.1f} ms")
print(f"  Executive:        {bot_executive:.1f} ms")
print(f"  QQ correlation:   {bot_qq:.3f}    (z = {z_qq:.2f})")
print(f"  Skewness:         {bot_skew:.2f}     (z = {z_sk:.2f})")
print(f"  Autocorr lag-1:   {bot_ac:.3f}    (z = {z_ac:.2f})")

print("=" * 65)

print("\nGenerating letter figures...")

# ============================================================
# FIGURE 1: Bot approximates human performance
# 3 panels: A) RT vs Accuracy, B) Network score violins, C) Cue x Flanker
# ============================================================
fig = plt.figure(figsize=(7.0, 2.8))
gs = gridspec.GridSpec(1, 3, width_ratios=[1, 1, 1.2], wspace=0.4)

# Panel A: RT vs Accuracy scatter
ax_a = fig.add_subplot(gs[0])
ax_a.scatter(
    [r / 1000 for r in human_mean_rts],
    [a / 100 for a in human_accuracies],
    s=6, alpha=0.2, color=HUMAN_COLOR, edgecolors='none', label='Human', rasterized=True
)
ax_a.scatter(
    [bot_mean_rt / 1000], [bot_acc / 100],
    s=100, color=BOT_COLOR, edgecolors='black', linewidth=0.8,
    marker='*', zorder=5, label='Bot'
)
ax_a.axhline(y=0.75, color=GRAY, linestyle='--', linewidth=0.5, alpha=0.4)
ax_a.set_xlabel('Mean RT (s)', fontsize=7)
ax_a.set_ylabel('Mean Accuracy', fontsize=7)
ax_a.set_xlim(0.3, 1.0)
ax_a.set_ylim(0.70, 1.02)
ax_a.legend(fontsize=6, frameon=False, loc='lower left', handletextpad=0.3)
ax_a.set_title('A', fontsize=9, fontweight='bold', loc='left')
ax_a.tick_params(labelsize=6)

# Panel B: Network score violins with bot + Fan
ax_b = fig.add_subplot(gs[1])
data_for_violin = [human_alerting, human_orienting, human_executive]
positions = [1, 2, 3]
vp = ax_b.violinplot(data_for_violin, positions=positions, showmedians=True, widths=0.7)
for pc in vp['bodies']:
    pc.set_facecolor(HUMAN_COLOR)
    pc.set_alpha(0.3)
    pc.set_edgecolor(HUMAN_COLOR)
    pc.set_linewidth(0.5)
vp['cmedians'].set_color(HUMAN_COLOR)
vp['cmedians'].set_linewidth(1)
for partname in ('cbars', 'cmins', 'cmaxes'):
    vp[partname].set_edgecolor(HUMAN_COLOR)
    vp[partname].set_linewidth(0.8)

# Fan benchmarks
ax_b.scatter([1, 2, 3], [47, 51, 84], s=40, marker='D', color=FAN_COLOR,
             zorder=5, label='Fan (2002)', edgecolors='white', linewidth=0.5)
# Bot
ax_b.scatter([1, 2, 3], [65.1, 52.1, 72.6], s=60, marker='*', color=BOT_COLOR,
             zorder=5, label='Bot', edgecolors='black', linewidth=0.5)

ax_b.set_xticks([1, 2, 3])
ax_b.set_xticklabels(['Alert', 'Orient', 'Exec'], fontsize=7)
ax_b.set_ylabel('Network Score (ms)', fontsize=7)
ax_b.legend(fontsize=5.5, frameon=False, loc='upper left', handletextpad=0.3)
ax_b.set_xlim(0.4, 3.6)
ax_b.set_title('B', fontsize=9, fontweight='bold', loc='left')
ax_b.tick_params(labelsize=6)

# Panel C: Cue x Flanker interaction (human solid, bot dashed)
ax_c = fig.add_subplot(gs[2])
cues_order = ['no_cue', 'center_cue', 'double_cue', 'spatial_cue']
cue_labels = ['No\nCue', 'Center', 'Double', 'Spatial']
flankers_order = ['congruent', 'neutral', 'incongruent']
# Colorblind-friendly flanker colors (Wong palette)
flanker_colors = {'congruent': '#009E73', 'neutral': '#0072B2', 'incongruent': '#D55E00'}
flanker_markers = {'congruent': 'o', 'neutral': 's', 'incongruent': '^'}

for fl in flankers_order:
    # Human means
    means_h = []
    for c in cues_order:
        vals = human_condition_rts.get((c, fl), [])
        means_h.append(statistics.mean(vals) if vals else 0)
    ax_c.plot(range(4), means_h, '-', marker=flanker_markers[fl], markersize=4,
              linewidth=1.2, color=flanker_colors[fl], alpha=0.8,
              label=f'{fl.capitalize()} (H)')

    # Bot means
    means_b = []
    for c in cues_order:
        rts_b = [t['rt_ms'] for t in bot_clean if t['cue'] == c and t['flanker'] == fl]
        means_b.append(statistics.mean(rts_b) if rts_b else 0)
    ax_c.plot(range(4), means_b, '--', marker=flanker_markers[fl], markersize=4,
              linewidth=1.0, color=flanker_colors[fl], alpha=0.5,
              label=f'{fl.capitalize()} (B)')

ax_c.set_xticks(range(4))
ax_c.set_xticklabels(cue_labels, fontsize=6)
ax_c.set_ylabel('RT (ms)', fontsize=7)
ax_c.legend(fontsize=4.5, frameon=False, ncol=2, loc='upper right',
            handletextpad=0.3, columnspacing=0.8)
ax_c.set_title('C', fontsize=9, fontweight='bold', loc='left')
ax_c.tick_params(labelsize=6)

plt.savefig(os.path.join(OUTPUT_DIR, 'figure1_bot_approximates_human.jpg'),
            format='jpeg', dpi=300)
plt.close()
print("  Figure 1 saved: figure1_bot_approximates_human.jpg")

# ============================================================
# FIGURE 2: Detectable artifacts
# Panel A: QQ correlation distribution
# Panel B: Skewness distribution
# Panel C: Autocorrelation distribution
# Panel D: RT density distributions (bot bimodal vs human)
# ============================================================
fig = plt.figure(figsize=(7.0, 2.8))
gs = gridspec.GridSpec(1, 4, width_ratios=[1, 1, 1, 1.3], wspace=0.45)

# Panel A: QQ correlation distribution
ax_a = fig.add_subplot(gs[0])
ax_a.hist(
    human_qq_vals,
    bins=35,
    color=HUMAN_COLOR,
    alpha=0.4,
    edgecolor='white',
    linewidth=0.2
)

ax_a.axvline(
    x=bot_qq,
    color=BOT_COLOR,
    linewidth=1.5,
    linestyle='-',
    label='Bot'
)

ax_a.set_xlabel('QQ Corr.', fontsize=7)
ax_a.set_ylabel('Count', fontsize=7)
ax_a.set_title('A', fontsize=9, fontweight='bold', loc='left')

# z_qq already computed above
ax_a.text(
    0.05,
    0.85,
    f'z={z_qq:.2f}',
    transform=ax_a.transAxes,
    fontsize=5.5,
    ha='left',
    va='top',
    color=BOT_COLOR
)

#ax_a.text(
#    bot_qq, ax_a.get_ylim()[1] * 0.95,
#    'Bot', fontsize=5.5, color=BOT_COLOR,
#    ha='center', va='top', fontweight='bold'
#)

ax_a.set_ylim(0, 100)
ax_a.tick_params(labelsize=6)

# Panel B: Skewness distribution
ax_b = fig.add_subplot(gs[1])
ax_b.hist(human_skew_vals, bins=35, color=HUMAN_COLOR, alpha=0.4,
          edgecolor='white', linewidth=0.2, range=(-0.5, 5.5))
ax_b.axvline(x=bot_skew, color=BOT_COLOR, linewidth=1.5, linestyle='-')
ax_b.set_xlabel('Skewness', fontsize=7)
ax_b.set_title('B', fontsize=9, fontweight='bold', loc='left')
# z_sk already computed above
ax_b.text(0.95, 0.85, f'z={z_sk:.2f}', transform=ax_b.transAxes,
          fontsize=5.5, ha='right', va='top', color=BOT_COLOR)
ax_b.set_ylim(0, 100)
ax_b.tick_params(labelsize=6)

# Panel C: Autocorrelation distribution
ax_c = fig.add_subplot(gs[2])
ax_c.hist(human_autocorr_lag1, bins=35, color=HUMAN_COLOR, alpha=0.4,
          edgecolor='white', linewidth=0.2)
ax_c.axvline(x=bot_ac, color=BOT_COLOR, linewidth=1.5, linestyle='-')
ax_c.set_xlabel('Autocorr (lag-1)', fontsize=7)
ax_c.set_title('C', fontsize=9, fontweight='bold', loc='left')
# z_ac already computed above
ax_c.text(0.95, 0.85, f'z={z_ac:.2f}', transform=ax_c.transAxes,
          fontsize=5.5, ha='right', va='top', color=BOT_COLOR)
ax_c.set_ylim(0, 100)
ax_c.tick_params(labelsize=6)

# Panel D: RT distributions
ax_d = fig.add_subplot(gs[3])

bins_range = np.arange(150, 1750, 25)

ax_d.hist(
    human_all_rts,
    bins=bins_range,
    density=True,
    alpha=0.35,
    color=HUMAN_COLOR,
    edgecolor='white',
    linewidth=0.2,
    label=f'Human (N={n_valid})',
    rasterized=True
)

ax_d.hist(
    bot_rts,
    bins=bins_range,
    density=True,
    alpha=0.55,
    color=BOT_COLOR,
    edgecolor='white',
    linewidth=0.2,
    label='Bot'
)

# Mark the bimodal peaks with arrows
ax_d.annotate(
    'Primary\nmode',
    xy=(400, 0.0025),
    xytext=(750, 0.0028),
    fontsize=5,
    color=BOT_COLOR,
    ha='center',
    style='italic',
    arrowprops=dict(arrowstyle='->', color=BOT_COLOR, lw=0.6)
)

ax_d.annotate(
    'Fallback\nmode',
    xy=(1100, 0.001),
    xytext=(1350, 0.002),
    fontsize=5,
    color=BOT_COLOR,
    ha='center',
    style='italic',
    arrowprops=dict(arrowstyle='->', color=BOT_COLOR, lw=0.6)
)

ax_d.set_xlabel('RT (ms)', fontsize=7)
ax_d.set_ylabel('Density', fontsize=7)
ax_d.legend(fontsize=5.5, frameon=False, loc='upper right',
            bbox_to_anchor=(1.0, 1.0), handletextpad=0.3)
ax_d.set_xlim(150, 1700)
ax_d.set_title('D', fontsize=9, fontweight='bold', loc='left')
ax_d.tick_params(labelsize=6)

plt.savefig(os.path.join(OUTPUT_DIR, 'figure2_detectable_artifacts.jpg'),
            format='jpeg', dpi=300)
plt.close()
print("  Figure 2 saved: figure2_detectable_artifacts.jpg")

print("\nDone. Both figures saved to output/")
