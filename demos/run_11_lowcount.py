"""Demo 11: low counts, asymptotic vs toys (slide 17).
The counting toy with all yields scaled by s = 1, 0.3, 0.1, 0.03, 0.01;
observed data = rounded background (no signal). For each s:
  AsymptoticLimits                        observed + expected
  HybridNew --LHCmode LHC-limits          observed (toys)
  HybridNew ... --expectedFromGrid 0.5    expected median (toys)
Fixed seed (-s 123), so the toy results are reproducible. The five scales run
in parallel.

Run through the Combine environment:  bash with_combine.sh demos/run_11_lowcount.py
"""
from concurrent.futures import ThreadPoolExecutor

from src import cards, combine, plots

SCALES = [1, 0.3, 0.1, 0.03, 0.01]
TOYOPTS = ["--LHCmode", "LHC-limits", "-T", "1000", "--rRelAcc", "0.02", "-s", "123"]


def run_scale(s):
    card = "lowcount/toy_s%g.txt" % s
    ws = "lowcount/toy_s%g.root" % s
    log = "lowcount/log_s%g.txt" % s
    combine.run("text2workspace.py", card, "-o", ws, log=log)
    combine.run("combine", "-M", "AsymptoticLimits", ws, "-n", ".lc_asym_s%g" % s, log=log, append=True)
    combine.run("combine", "-M", "HybridNew", ws, *TOYOPTS, "-n", ".lc_toys_s%g" % s, log=log, append=True)
    combine.run("combine", "-M", "HybridNew", ws, *TOYOPTS, "--expectedFromGrid", "0.5",
                "-n", ".lc_toysexp_s%g" % s, log=log, append=True)


def main():
    cards.lowcount_cards()
    with ThreadPoolExecutor(max_workers=len(SCALES)) as pool:
        for future in [pool.submit(run_scale, s) for s in SCALES]:
            future.result()   # re-raises any failure

    print("=== Asymptotic vs toys ===")
    plots.lowcount()


if __name__ == "__main__":
    main()
