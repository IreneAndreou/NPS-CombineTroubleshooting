"""Backup B3: autoMCStats when an MC error is larger than the yield.

The b5 fakes (yield 1.00) come from a few events, some with negative weights, so
their error is larger than the yield. Three versions:
  as-is    fakes b5 = 1.00 +- 4.00  -> "Poisson not viable", Gaussian
  capped  fakes b5 = 1.00 +- 1.00  -> Poisson with N_eff = 1
  goodmc  fakes b5 = 1.00 +- 0.71  -> well-simulated reference

Run through the Combine environment:  bash with_combine.sh demos/run_B3_mccap.py
"""
from src import cards, combine, combine_outputs, plots

VERSIONS = ["as-is", "capped", "goodmc"]


def main():
    cards.mccap_cards()

    with combine_outputs.in_dir("mccap"):
        for v in VERSIONS:
            combine.run("text2workspace.py", "card_%s.txt" % v, "-o", "ws_%s.root" % v,
                        log="t2w_%s.log" % v)
            combine.run("combine", "-M", "AsymptoticLimits", "ws_%s.root" % v, "-t", "-1",
                        "-n", ".%s.exp" % v, log="exp_%s.log" % v)
            combine.run("combine", "-M", "AsymptoticLimits", "ws_%s.root" % v,
                        "-n", ".%s.obs" % v, log="obs_%s.log" % v)
            combine.run("combine", "-M", "FitDiagnostics", "ws_%s.root" % v,
                        "--saveShapes", "--saveWithUncertainties", "-n", ".%s" % v,
                        log="fd_%s.log" % v)

        print("== how autoMCStats treats fakes in b5")
        for v in VERSIONS:
            print("%-7s %s" % (v, combine_outputs.bin_treatment("t2w_%s.log" % v, bin_no=4,
                                                               process="fakes")))

        print("== limits")
        for v in VERSIONS:
            exp = combine_outputs.first_value("exp_%s.log" % v, "Expected 50.0%")
            obs = combine_outputs.first_value("obs_%s.log" % v, "Observed Limit")
            print("%-7s exp %s  obs %s" % (v, exp, obs))

    plots.mccap()
    plots.mccap_shapes()


if __name__ == "__main__":
    main()
