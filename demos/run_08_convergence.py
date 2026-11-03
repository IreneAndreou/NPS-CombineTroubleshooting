"""Demo 8: non-convergence (slide 14).
  degen  two rateParams on the same process -> the fit fails
  1. default fit                      : status / covQual show the failure
  2. --cminDefaultMinimizerStrategy 0 : status goes "green", problem remains
  3. same fit on Asimov (-t -1)       : still fails -> it's the model, not data
  4. 2D likelihood scan               : the flat valley (degeneracy)
  fixed  one rateParam                -> clean fit

Run through the Combine environment:  bash with_combine.sh demos/run_08_convergence.py
"""
from src import cards, combine, plots, reports


def main():
    cards.conv_cards()
    for c in ["degen", "fixed"]:
        combine.run("text2workspace.py", "conv/toy_%s.txt" % c, "-o", "conv/toy_%s.root" % c)

    combine.run("combine", "-M", "FitDiagnostics", "conv/toy_degen.root", "-n", ".conv_default")
    combine.run("combine", "-M", "FitDiagnostics", "conv/toy_degen.root", "-n", ".conv_strategy0",
                "--cminDefaultMinimizerStrategy", "0")
    combine.run("combine", "-M", "FitDiagnostics", "conv/toy_degen.root", "-n", ".conv_asimov", "-t", "-1")
    combine.run("combine", "-M", "FitDiagnostics", "conv/toy_fixed.root", "-n", ".conv_fixed")

    print("=== Fit health ===")
    pars = ["fakes_norm", "fakes_extra"]
    reports.fit_status("degenerate, default", "fitDiagnostics.conv_default.root", pars)
    reports.fit_status("degenerate, strategy 0", "fitDiagnostics.conv_strategy0.root", pars)
    reports.fit_status("degenerate, Asimov", "fitDiagnostics.conv_asimov.root", pars)
    reports.fit_status("fixed (one rateParam)", "fitDiagnostics.conv_fixed.root", ["fakes_norm"])

    combine.run("combine", "-M", "MultiDimFit", "conv/toy_degen.root", "--algo", "grid", "--points", "900",
                "--redefineSignalPOIs", "fakes_norm,fakes_extra", "-P", "fakes_norm", "-P", "fakes_extra",
                "--setParameterRanges", "fakes_norm=0.2,3:fakes_extra=0.2,3", "-n", ".conv_scan2d")
    plots.scan2d_degenerate()


if __name__ == "__main__":
    main()
