"""Demo 7: spiky shape templates (slide 13). WZ shape uncertainty, 10x lumi,
Asimov data (no randomness from the data):
  none      no WZ shape uncertainty (reference)
  smooth    the true effect: a smooth tilt, 0% in b1 to 20% in b5
  spiky     the same tilt + 10% bin-by-bin noise (low-stat MC templates)
  smoothed  patch 1: straight-line fit to the spiky ratios
  lnN       patch 2: normalisation-only uncertainty of the same size
For each: expected limit, and post-fit/prior width of wz_shape (b-only fit).

Run through the Combine environment:  bash with_combine.sh demos/run_07_spiky.py
"""
from src import cards, combine, plots, reports

VARIANTS = ["none", "smooth", "spiky", "smoothed", "lnN"]


def main():
    cards.spiky_cards()

    for v in VARIANTS:
        combine.run("text2workspace.py", "spiky/toy_%s.txt" % v, "-o", "spiky/toy_%s.root" % v)
        combine.run("combine", "-M", "AsymptoticLimits", "spiky/toy_%s.root" % v,
                    "-t", "-1", "-n", ".spiky_%s.exp" % v)
        combine.run("combine", "-M", "FitDiagnostics", "spiky/toy_%s.root" % v,
                    "-t", "-1", "--expectSignal", "0", "-n", ".spiky_%s" % v,
                    "--saveShapes", "--saveWithUncertainties")

    print("=== wz_shape post-fit / prior width (background-only Asimov fit) ===")
    for v in ["smooth", "spiky", "smoothed", "lnN"]:
        reports.fit_error(v, "fitDiagnostics.spiky_%s.root" % v, "wz_shape")

    plots.spiky_templates()
    plots.spiky_bkg()
    plots.limit_table([("No WZ shape uncertainty", "spiky_none", True),
                       ("Smooth template (the truth)", "spiky_smooth", True),
                       ("Spiky template", "spiky_spiky", True),
                       ("Patch: straight-line fit", "spiky_smoothed", True),
                       ("Patch: lnN of same size", "spiky_lnN", True)],
                      out="limits_spiky")


if __name__ == "__main__":
    main()
