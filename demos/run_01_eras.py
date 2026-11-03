"""Demo 1: eras. Run after run_00_baseline.py (needs toy.root and its limits).
  corr          3 eras, all correlated          -> identical to merged
  wzdecor       wz_xs decorrelated per era      -> barely moves (small effect in b4-b5)
  extrap_corr   + 30% WZ extrapolation in b4-b5 -> limit gets worse
  extrap_decor  ... decorrelated per era        -> recovers much of it (1/sqrt(3))
  hifakes       2024 has 3x fakes: merged vs. split (expected only)
Why they differ: in b4, 10% of WZ is ~1 event, 30% is ~3, vs. a stat. unc. of ~4.

Run through the Combine environment:  bash with_combine.sh demos/run_01_eras.py
"""
from src import cards, combine, plots

CASES = ["corr", "wzdecor", "extrap_corr", "extrap_decor", "hifakes"]
OBS_CASES = ["corr", "wzdecor", "extrap_corr", "extrap_decor"]


def main():
    cards.era_cards()

    for s in CASES:
        combine.run_to_file("eras/toy_eras_%s.txt" % s, "combineCards.py",
                            "y22=eras/toy_2022_%s.txt" % s, "y23=eras/toy_2023_%s.txt" % s,
                            "y24=eras/toy_2024_%s.txt" % s)
        combine.run("text2workspace.py", "eras/toy_eras_%s.txt" % s, "-o", "eras/toy_eras_%s.root" % s)
        combine.run("combine", "-M", "AsymptoticLimits", "eras/toy_eras_%s.root" % s,
                    "-t", "-1", "-n", ".eras_%s.exp" % s)
    for s in OBS_CASES:
        combine.run("combine", "-M", "AsymptoticLimits", "eras/toy_eras_%s.root" % s,
                    "-n", ".eras_%s.obs" % s)

    combine.run("text2workspace.py", "eras/toy_merged_hifakes.txt", "-o", "eras/toy_merged_hifakes.root")
    combine.run("combine", "-M", "AsymptoticLimits", "eras/toy_merged_hifakes.root",
                "-t", "-1", "-n", ".merged_hifakes.exp")

    plots.limit_table([("Merged (baseline)", "toy", False),
                       ("3 eras, all correlated", "eras_corr", False),
                       ("3 eras, wz_xs decorrelated", "eras_wzdecor", False),
                       ("+ WZ extrap. 30%, correlated", "eras_extrap_corr", False),
                       ("+ WZ extrap. 30%, decorrelated", "eras_extrap_decor", False)],
                      out="limits_eras")
    plots.limit_table([("Merged (2024: 3x fakes)", "merged_hifakes", True),
                       ("Split by era (2024: 3x fakes)", "eras_hifakes", True)],
                      out="limits_eras_hifakes")


if __name__ == "__main__":
    main()
