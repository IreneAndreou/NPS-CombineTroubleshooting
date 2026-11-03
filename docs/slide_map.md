# Slide map

Each row: the slide(s), the demo script that produces the numbers, the plot(s) in `plots/`, and the numbers the run gives. Run a demo from the repo root:

    bash with_combine.sh demos/run_NN_<topic>.py

Numbers are from the benchmark run of this repo. "Slide" values are what the talk shows.

| Slide | Topic | Script | Plots (`plots/`) | Run numbers |
|---|---|---|---|---|
| 2-4 | Toy, baseline, first checks | `run_00_baseline.py` | `limits_baseline`, `prefit` | counting card: exp 0.49, obs 0.59; shape card + autoMCStats: exp 0.53, obs 0.63 |
| 6 | Stacking, 3 eras correlated | `run_01_eras.py` | `limits_eras` | merged 0.49 (= 3 eras correlated) |
| 7 | Decorrelating wz_xs, WZ extrapolation | `run_01_eras.py` | `limits_eras` | wz_xs decorrelated 0.49; +30% extrapolation: correlated 0.55, decorrelated 0.52 |
| 8 | 2024 has 3x fakes | `run_01_eras.py` | `limits_eras_hifakes` | merged (0.54) vs split by era (0.53) (expected only) |
| 9 | Tug of war | `run_02_tugofwar.py` | `pulls_tug`, `gof_tug` | shared nuisance p = 0.016; per-era p = 0.372; pulls +1.10, +0.65, -0.86 |
| 10-14 | autoMCStats | `run_03_automcstats.py` | `limits_mcstats`, `limits_mcstats_failures` | nominal, autoMCStats 10: exp 0.53; poor fakes, threshold 10: exp 0.59 |
| 15 | Floating vs constrained WZ | `run_04_floating.py` | `limits_floating` | WZ post-fit uncertainty: 7.6%, 11.7%, 8.9%, 20.0% |
| 16-17 | Inflating the fakes uncertainty | `run_05_inflate.py` | `inflate` | spurious significance: nominal 3.8 sigma, inflated 3.8 sigma; decomposed 0.2 sigma |
| 18-19 | Empty bins | `run_06_emptybins.py` | `empty_bins`, `empty_bins_fit` | floored b5: fitted r = 0.53; b4+b5 merged: fitted r = 0.12 |
| 20-21 | Spiky templates | `run_07_spiky.py` | `spiky_templates`, `spiky_bkg`, `limits_spiky` | expected: none 0.14, smooth 0.18, spiky 0.16, patch 0.18, lnN 0.14 |
| 23-24 | Non-convergence | `run_08_convergence.py` | (text output, see log) | fit status and covariance per minimiser setting |
| 25 | Signal-background degeneracy | `run_09_degeneracy.py` | `scan2d_r_wznorm`, `scan2d_degenerate`, `limits_degeneracy` | distinct shapes: exp 0.14; signal-like WZ: exp 9.3; with control region: exp 0.56 |
| 26 | Background-only post-fit | `run_10_bonly.py` | `bonly_postfit` | significance 7.3 sigma |
| 27 | Low counts, asymptotic vs toys | `run_11_lowcount.py` | `lowcount` | observed asymptotic vs toys: -2, -3, -7, -17, -23 %; expected: 0, -2, -3, 0, -8 % |
| 29-30 | Pulls and GoF | `run_12_gof.py` | `gof_vs_limits` | no mismodelling: GoF p 0.78; excess in b1: p 0.027; excess in b5: 3.35 sigma, p 0.76 (b-only p 0.007) |
| 31 | Localised signal, mass grid | `run_13_massgrid.py` | `massgrid` | 10 GeV grid: 3.4 sigma at 530 GeV; 100 GeV grid: max 1.4 sigma at 600 GeV |
| 33-34 | Unblinding checklist | (none) | (none) | links to the CMS NPS COMBINE twiki and contacts, and CAT experts |

## Backup slides

| Backup slides | Topic | Script | Plots (`plots/`) | Run numbers |
|---|---|---|---|---|
| 36-38 | Stacking with generic systematics (A-F: correlated, anti-correlated, size differs, single-era) | `run_B1_stack_systs.py` | `limits_stack_systs`, `stack_systs`, `stack_yields` | per-era cards exp 0.596 / obs 0.693; stacked card exp 0.598 / obs 0.698 |
| 39 | Empty bins: what Combine does with an empty bin (11-bin card, bin 7) | `run_B2_emptytest.py` | `emptytest` | A (no data in bin 7): exp 1.13 / obs 0.70; B (no background MC, no data): exp 0.53 / obs 0.53; C (no background MC, 3 data events): exp 0.53 / obs 1.32 |
| 40-41 | autoMCStats when the MC error is larger than the yield (b5 fakes) | `run_B3_mccap.py` | `mccap`, `mccap_shapes` | as-is 1.00 +- 4.00: exp 0.715 / obs 0.820; capped 1.00 +- 1.00: exp 0.529 / obs 0.634. b5 total background uncertainty, pre-fit: 91%, 41%
