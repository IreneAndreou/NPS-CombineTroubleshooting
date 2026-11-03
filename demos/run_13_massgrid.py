"""Demo 13: a localised signal missed by a coarse mass grid (slide 20).
Falling background, narrow resonance (10 GeV resolution), a real signal
injected at 530 GeV. For every mass hypothesis 200-1000 GeV in 10 GeV steps:
observed + expected limit and local significance. The plot compares the
full 10 GeV scan with what a 100 GeV grid (200, 300, ..., 1000) would show.

Run through the Combine environment:  bash with_combine.sh demos/run_13_massgrid.py
"""
from concurrent.futures import ThreadPoolExecutor

from src import cards, combine, plots

NPROC = 4
MASSES = list(range(200, 1001, 10))


def run_mass(m):
    """Limit and significance at one mass, run inside mass/ like the shell version."""
    card = "card_M%d.txt" % m
    ws = "card_M%d.root" % m
    log = "mass/log_M%d.txt" % m
    combine.run("text2workspace.py", card, "-o", ws, "-m", m, log=log, cwd="mass")
    combine.run("combine", "-M", "AsymptoticLimits", ws, "-m", m, "-n", ".mass",
                log=log, append=True, cwd="mass")
    combine.run("combine", "-M", "Significance", ws, "-m", m, "-n", ".mass",
                log=log, append=True, cwd="mass")


def main():
    cards.mass_cards()
    with ThreadPoolExecutor(max_workers=NPROC) as pool:
        for future in [pool.submit(run_mass, m) for m in MASSES]:
            future.result()   # re-raises any failure

    plots.massgrid()


if __name__ == "__main__":
    main()
