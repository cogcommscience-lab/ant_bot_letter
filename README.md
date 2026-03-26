# Behavioral Bots Are Feasible but Constrained

Data and code for a PNAS Letter to the Editor responding to Westwood (2025), contributing to the debate about whether AI bots threaten the integrity of online behavioral research.

**Authors:** Richard Huskey, Ziyu Zhao, Jacob T. Fisher, Douglas A. Parry

**Manuscript:** `huskey_zhao_fisher_parry_pnas_letter_bots.docx`

---

## Repository Structure

```
bot_or_not_letter/
├── README.md                                       (this file)
├── huskey_zhao_fisher_parry_pnas_letter_bots.docx  (manuscript)
├── data/
│   ├── README.md                                   (data documentation)
│   └── raw/
│       └── ant_data/                               (1,150 raw CSV files, one per participant session)
│
├── bot_iterative/
│   └── data/
│       └── v7_3_data.csv                           (bot v7.3 single-run ANT output, 288 trials)
│
└── output/
    ├── figures_for_letter.py                       (figure generation and statistics)
    ├── figure1_bot_approximates_human.jpg          (Figure 1, 300 dpi)
    └── figure2_detectable_artifacts.jpg            (Figure 2, 300 dpi)
```

---

## Overview

An AI agent (bot v7.3) was built to autonomously complete the Attention Network Test (ANT; Fan et al., 2002). Its behavioral output is compared against 796 human participants collected across three university sites (UC Davis, Michigan State University, Vrije Universiteit Amsterdam) via Pavlovia. The bot was engineered through iterative prompt refinement of Claude Opus, using pixel-level screen detection and an ex-Gaussian reaction time model to simulate human-like response timing.

---

## Reproducing the Results

All figures and statistics reported in the manuscript are generated from raw data by a single script:

```bash
python3 output/figures_for_letter.py
```

**Requirements:** Python 3 with `matplotlib` and `numpy`.

The script:
1. Reads all 1,150 human participant CSVs from `data/raw/ant_data/`
2. Reads the bot data from `bot_iterative/data/v7_3_data.csv`
3. Applies exclusion criteria and computes ANT network scores and psychometric markers
4. Prints all statistics reported in the manuscript to the console
5. Outputs two JPEG figures at 300 dpi to `output/`

**Figure 1** — *Bot approximates human ANT performance*
- Panel A: Mean RT vs. accuracy (bot within human cloud)
- Panel B: ANT network scores (violin plots with bot and Fan 2002 benchmarks)
- Panel C: Cue × flanker interaction (human vs. bot)

**Figure 2** — *Detectable artifacts remain in bot data*
- Panel A: QQ correlation distribution with bot z-score
- Panel B: Skewness distribution with bot z-score
- Panel C: Lag-1 autocorrelation distribution with bot z-score
- Panel D: RT density distributions (bot bimodality vs. human unimodality)

---

## Data Processing Pipeline

All processing is self-contained in `output/figures_for_letter.py`. No intermediate files are required.

### Human Data

1. Parse filenames matching `{participant_id}_{location_code}_ant_ver113_{timestamp}.csv`
2. Exclude participants with: invalid filenames (110), no main trials (74), empty files (35), inattentive responding (RT > 120 s or < 0.001 s; 29), low accuracy (< 75%; 99), or duplicate sessions (6)
3. For valid participants (*N* = 796): filter to correct trials, exclude RT outliers (< 200 ms or > 1700 ms), convert RTs from seconds to milliseconds
4. Compute per-participant: mean RT, accuracy, ANT network scores, QQ correlation, skewness, and lag-1 autocorrelation

### Bot Data

1. Filter to main experimental trials (`mainLoop.ran == 1`)
2. Apply identical RT cleaning (200–1700 ms)
3. Compute identical metrics and psychometric markers
4. Compute z-scores against human distributions

### ANT Network Scores (Fan et al., 2002)

| Index | Formula | Interpretation |
|-------|---------|---------------|
| **Alerting** | RT(no cue) − RT(double cue) | Benefit of temporal warning signal |
| **Orienting** | RT(center cue) − RT(spatial cue) | Benefit of spatial information |
| **Executive control** | RT(incongruent) − RT(congruent) | Cost of flanker conflict |

### Psychometric Markers (Van der Stigchel et al., 2026)

| Marker | Description |
|--------|-------------|
| **QQ correlation** | Correlation between sorted RTs and theoretical normal quantiles |
| **Skewness** | Third standardized moment of the RT distribution |
| **Lag-1 autocorrelation** | Serial dependence between consecutive trial RTs |

---

## Key Variable Definitions

### Raw CSV Columns

| Column | Description |
|--------|-------------|
| `mainLoop.thisN` | Trial number within main block (0–47); empty for practice/instruction rows |
| `cue` | Cue stimulus filename (maps to cue condition; see below) |
| `tar` | Target stimulus filename (maps to flanker condition via substring) |
| `resp.rt` | Response time in **seconds** from target onset |
| `resp.corr` | Correctness: 1 = correct, 0 = incorrect |
| `resp.keys` | Key pressed (left/right) |
| `mainLoop.ran` | Main loop indicator (1 = experimental trial) |

### Cue Mapping

| Filename | Condition |
|----------|-----------|
| `stim/blank.png` | No cue |
| `stim/centre.png` | Center cue |
| `stim/both.png` | Double cue |
| `stim/upper.png` / `stim/lower.png` | Spatial cue |

### Flanker Mapping

Target filenames containing `incong` → incongruent, `cong` → congruent, `neutral` → neutral.

---

## Summary Statistics

### Human Participants (*N* = 796)

| Metric | *M* | *SD* |
|--------|-----|------|
| Mean RT (ms) | 591.8 | 97.8 |
| Accuracy (%) | 96.0 | 4.4 |
| Alerting (ms) | 57.6 | 41.9 |
| Orienting (ms) | 43.2 | 44.2 |
| Executive (ms) | 103.3 | 56.1 |
| QQ correlation | 0.929 | 0.038 |
| Skewness | 1.75 | 0.76 |
| Autocorr lag-1 | 0.117 | 0.097 |

### Bot v7.3 (Single Run)

| Metric | Value | *z* |
|--------|-------|-----|
| Mean RT (ms) | 614.7 | — |
| Accuracy (%) | 95.8 | — |
| Alerting (ms) | 65.1 | — |
| Orienting (ms) | 52.1 | — |
| Executive (ms) | 72.6 | — |
| QQ correlation | 0.925 | −0.09 |
| Skewness | 1.17 | −0.77 |
| Autocorr lag-1 | 0.244 | +1.31 |

---

## References

- Fan, J., McCandliss, B. D., Sommer, T., Raz, A., & Posner, M. I. (2002). Testing the efficiency and independence of attentional networks. *Journal of Cognitive Neuroscience*, 14(3), 340–347.
- MacLeod, J. W., et al. (2010). Appraising the ANT: Psychometric and theoretical considerations. *Neuropsychology*, 24(5), 637–651.
- Van der Stigchel, S., et al. (2026). Will online behavioral research follow the fate of online survey research? *PNAS*, 123(8), e2535585123.
- Wagenmakers, E.-J., & Brown, S. (2007). On the linear relation between the mean and the standard deviation of a response time distribution. *Psychological Review*, 114(3), 830–841.
- Westwood, S. J. (2025). The potential existential threat of large language models to online survey research. *PNAS*, 122(2), e2518075122.
- Wong, B. (2011). Points of view: Color blindness. *Nature Methods*, 8(6), 441.
