"""Demo 9: signal-background degeneracy (slide 15). WZ normalisation floats
freely (rateParam). 10x lumi, Asimov data with signal (r = 1):
  distinct  WZ falls, signal rises          -> r measured, small correlation
  degen     WZ has a signal-like shape      -> r and wz_norm trade events
  degen_cr  degen + WZ control region       -> degeneracy broken
For each: fit health, r +- error, corr(r, wz_norm), expected limit, 2D scan.

Run through the Combine environment:  bash with_combine.sh demos/run_09_degeneracy.py
"""
from src import cards, combine, plots, reports

SETUPS = ["distinct", "degen", "degen_cr"]


def main():
    cards.degen_cards()

    for s in SETUPS:
        combine.run("text2workspace.py", "degen/toy_%s.txt" % s, "-o", "degen/toy_%s.root" % s)
        combine.run("combine", "-M", "FitDiagnostics", "degen/toy_%s.root" % s, "-t", "-1",
                    "--expectSignal", "1", "--rMin", "-3", "--rMax", "5", "-n", ".dg_%s" % s)
        combine.run("combine", "-M", "AsymptoticLimits", "degen/toy_%s.root" % s,
                    "-t", "-1", "-n", ".dg_%s.exp" % s)
        combine.run("combine", "-M", "MultiDimFit", "degen/toy_%s.root" % s, "-t", "-1",
                    "--expectSignal", "1", "--algo", "grid", "--points", "1600",
                    "--redefineSignalPOIs", "r,wz_norm", "-P", "r", "-P", "wz_norm",
                    "--setParameterRanges", "r=-3,5:wz_norm=0.4,1.6", "-n", ".dg_scan_%s" % s)

    print("=== Fit health and signal strength (Asimov, true r = 1) ===")
    for s in SETUPS:
        reports.fit_status(s, "fitDiagnostics.dg_%s.root" % s, ["r", "wz_norm"], fits=("fit_s",))

    plots.limit_table([("Distinct shapes", "dg_distinct", True),
                       ("Signal-like WZ", "dg_degen", True),
                       ("Signal-like WZ + control region", "dg_degen_cr", True)],
                      out="limits_degeneracy")
    plots.scan2d_r_wznorm()


if __name__ == "__main__":
    main()
