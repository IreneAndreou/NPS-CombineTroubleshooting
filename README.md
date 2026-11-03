# Combine troubleshooting tutorial

Code and cards for the talk "Combine troubleshooting" (CMS NPS general meeting, 27 Oct 2026: [agenda](https://indico.cern.ch/event/1718767/#3-combine-troubleshooting)). One toy analysis (5 bins, 3 components: signal, WZ, fakes) is broken one problem at a time. Each demo is a Python run file, `demos/run_NN_<topic>.py`, and every number and plot on the slides comes from running these files. [docs/slide_map.md](docs/slide_map.md) lists which file and plot goes with which slide.

## Setup

Run on lxplus (EL9). Combine v11.1.0 comes from CVMFS, so nothing needs to be installed.

    git clone <repo-url> NPS-CombineTroubleshooting
    cd NPS-CombineTroubleshooting
    bash with_combine.sh demos/run_00_baseline.py

`with_combine.sh` loads the Combine environment from CVMFS and runs the demo from the repo root. The Combine tools are shell aliases that run inside a container; `with_combine.sh` exports the variables that define that container command, and `demos/src/combine.py` builds the same command from Python.

Batch submission is not covered; the demos run interactively. To install Combine in a CMSSW area instead (needed for batch), use `bash install_combine.sh` and then `cmsenv` before running a demo directly.

## Running a demo

    bash with_combine.sh demos/run_01_eras.py

Each run writes its cards, ROOT files and logs into the repo root, and its plots into `plots/`. Running all 15 demos in order takes about 40 minutes on lxplus.

## Layout

| Path | What it is |
|---|---|
| `with_combine.sh` | Entry point: loads Combine and runs a demo file from the repo root |
| `demos/run_NN_*.py` | One file per demo: the Combine commands and the plots, in the order of the slide |
| `demos/run_B1_stack_systs.py`, `demos/run_B2_emptytest.py`, `demos/run_B3_mccap.py` | Backup-slide demos: stacking with generic systematics, the empty-bin test, and autoMCStats with an MC error larger than the yield |
| `demos/src/cards.py` | Card and input writers: the counting-card writer and one function per demo's cards |
| `demos/src/plots.py` | Figure functions, one per plot (each writes `plots/<name>.pdf` and `.png`) |
| `demos/src/reports.py` | Text printouts from fit outputs (fit health, post-fit uncertainties) |
| `demos/src/combine.py` | Runs Combine tools from Python, through the same container as the aliases |
| `demos/src/rootutil.py` | ROOT style, saving, and the `isolated` decorator (each figure in its own process) |
| `demos/src/combine_outputs.py` | Combine output file names and limit readers |
| `inputs/toy.txt`, `inputs/toy_shapes.txt` | The toy counting card (shown on the slides) and the same toy as one shape channel with autoMCStats |
| `plots/` | Final figures used on the slides |
| `docs/slide_map.md` | Slide-by-slide guide: run file, plot, and expected numbers |

## Checking a run

Each demo prints its limits and fit results. The numbers to compare with the slides are in [docs/slide_map.md](docs/slide_map.md). Where a run and a slide disagree, the note there says which one to trust and what is still open.
