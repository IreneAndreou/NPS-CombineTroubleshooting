"""Demo 4: floating vs. constrained WZ normalisation (slide 10).
  constrained  wz_xs lnN 1.10                 (prior)
  floating     wz_norm rateParam * WZ 1 [0,5] (data only)
  withCR       all 5 bins: b1-b2 are WZ-dominated and act as a control region
  noCR         only b3-b5, the signal-rich bins
For each: post-fit WZ normalisation uncertainty (background-only Asimov fit)
and the expected limit.

Run through the Combine environment:  bash with_combine.sh demos/run_04_floating.py
"""
from src import cards, combine, plots, reports

VARIANTS = ["constrained_withCR", "floating_withCR", "constrained_noCR", "floating_noCR"]


def main():
    cards.float_cards()

    for v in VARIANTS:
        combine.run("text2workspace.py", "float/toy_%s.txt" % v, "-o", "float/toy_%s.root" % v)
        combine.run("combine", "-M", "AsymptoticLimits", "float/toy_%s.root" % v,
                    "-t", "-1", "-n", ".float_%s.exp" % v)
        combine.run("combine", "-M", "FitDiagnostics", "float/toy_%s.root" % v,
                    "-t", "-1", "--expectSignal", "0", "-n", ".float_%s" % v)

    print("=== Post-fit WZ normalisation uncertainty (background-only Asimov) ===")
    for v in VARIANTS:
        reports.wz_norm_uncertainty(v, "fitDiagnostics.float_%s.root" % v)

    plots.limit_table([("Constrained WZ (10% prior), with CR", "float_constrained_withCR", True),
                       ("Floating WZ, with CR", "float_floating_withCR", True),
                       ("Constrained WZ (10% prior), no CR", "float_constrained_noCR", True),
                       ("Floating WZ, no CR", "float_floating_noCR", True)],
                      out="limits_floating")


if __name__ == "__main__":
    main()
