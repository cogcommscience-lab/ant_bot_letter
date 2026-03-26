# Human Participant ANT Data

## Overview

This directory contains Attention Network Test (ANT) data from human participants collected as part of a multi-site study. Data collection is ongoing across three university sites: UC Davis (USA), Michigan State University (USA), and Vrije Universiteit Amsterdam (the Netherlands). Participants are recruited from student populations and complete the ANT in online settings via Pavlovia.

## Directory Structure

```
data/
├── README.md           (this file)
└─raw/
    └── ant_data/       (1,150 raw participant CSV files)─
```

## Raw Data (`raw/ant_data/`)

Each CSV file represents one participant session. Filenames follow the format:

```
{participant_id}_{location_code}_ant_ver113_{date}.csv
```

- `participant_id`: Numeric participant identifier
- `location_code`: Numeric site identifier
- `ant_ver113`: ANT version identifier
- `date`: Timestamp of the session (YYYY-MM-DD_HHhMM.SS.mmm)

### Key Columns in Raw CSV Files

| Column | Description |
|--------|-------------|
| `mainLoop.thisN` | Trial number within main experimental block (empty for practice trials) |
| `cue` | Cue stimulus filename (determines cue condition) |
| `tar` | Target stimulus filename (determines flanker condition) |
| `resp.rt` | Response time in **seconds** from target onset |
| `resp.corr` | Correctness (1 = correct, 0 = incorrect) |
| `resp.keys` | Key pressed by participant |

### Cue Condition Mapping

| Filename | Condition |
|----------|-----------|
| `stim/blank.png` | No cue |
| `stim/centre.png` | Center cue |
| `stim/both.png` | Double cue |
| `stim/upper.png` | Spatial cue (target above fixation) |
| `stim/lower.png` | Spatial cue (target below fixation) |

### Flanker Condition Mapping

Target filenames containing `incong` = incongruent, `cong` = congruent, `neutral` = neutral.

## Processed Data (`processed/ant_processed.csv`)

This file contains one row per valid participant (N = 796) with the following columns:

| Column | Description |
|--------|-------------|
| `id` | Participant identifier |
| `location` | Site code |
| `mean_rt` | Mean correct RT in ms (after outlier exclusion) |
| `accuracy` | Overall accuracy (%) |
| `err_cong` | Error rate for congruent trials (%) |
| `err_incong` | Error rate for incongruent trials (%) |
| `err_neut` | Error rate for neutral trials (%) |
| `alerting` | Alerting network score (ms): RT(no cue) - RT(double cue) |
| `orienting` | Orienting network score (ms): RT(center cue) - RT(spatial cue) |
| `executive` | Executive control score (ms): RT(incongruent) - RT(congruent) |
| `n_total` | Total valid main trials |
| `n_clean_rt` | Trials used for RT analyses (correct, non-outlier) |
| `rt_no_cue` through `rt_neut` | Condition-level mean RTs |

## Data Cleaning Procedure

Applied in order, following standard ANT procedures (Fan et al., 2002):

1. **Invalid filenames** excluded (n = 110): Did not match expected naming convention
2. **No main trials** excluded (n = 74): `mainLoop.thisN` column empty for all rows
3. **Empty files** excluded (n = 35): Zero data rows
4. **Inattentive** excluded (n = 29): Any trial with RT > 120 s or RT < 0.001 s
5. **Low accuracy** excluded (n = 99): Overall accuracy below 75%
6. **Duplicates** resolved (n = 6): First occurrence kept per participant ID + location

Within valid participants:
- Error trials excluded from RT analyses
- RT outliers excluded: RT < 200 ms or RT > 1,700 ms
- RTs converted from seconds to milliseconds (raw files store seconds)

## ANT Index Calculation

Following Fan et al. (2002):

- **Alerting** = Mean RT(no cue) − Mean RT(double cue)
- **Orienting** = Mean RT(center cue) − Mean RT(spatial cue)
- **Executive** = Mean RT(incongruent) − Mean RT(congruent)

## Summary Statistics (N = 796)

| Metric | M | SD |
|--------|---|-----|
| Mean RT (ms) | 591.8 | 97.8 |
| Accuracy (%) | 96.0 | 4.4 |
| Alerting (ms) | 57.6 | 41.9 |
| Orienting (ms) | 43.2 | 44.2 |
| Executive (ms) | 103.3 | 56.1 |

## References

Fan, J., McCandliss, B. D., Sommer, T., Raz, A., & Posner, M. I. (2002). Testing the efficiency and independence of attentional networks. *Journal of Cognitive Neuroscience*, 14(3), 340–347.
