"""Demo 12: bad GoF / pulls vs. "fine" limits (slide 18). No signal in the data
(Poisson-fluctuated background, 10x lumi, fixed seed) plus one 3.5 sigma
local mismodelling:
  good  none
  misA  excess in b1 (no signal there)  -> nuisances pulled, limit too strong
  misB  excess in b5 (signal-rich bin)  -> fake signal; s+b GoF cannot see it
For each: observed/expected limit, significance, pulls, and the saturated GoF
with the signal floating (default) and background-only (--fixedSignalStrength 0).

Run through the Combine environment:  bash with_combine.sh demos/run_12_gof.py
"""
from src import cards, combine, plots

VARIANTS = ["good", "misA", "misB"]
NTOYS = 300


def main():
    cards.gof_cards()

    for v in VARIANTS:
        card = "gof/toy_%s.txt" % v
        ws = "gof/toy_%s.root" % v
        combine.run("text2workspace.py", card, "-o", ws)
        combine.run("combine", "-M", "AsymptoticLimits", ws, "-n", ".gof_%s" % v)
        combine.run("combine", "-M", "Significance", ws, "-n", ".gof_%s" % v, log="gof/sig_%s.log" % v)
        print(open("gof/sig_%s.log" % v).read(), end="")
        combine.run("combine", "-M", "FitDiagnostics", ws, "-n", ".gof_%s" % v)
        for m in ["sb", "b"]:
            extra = ["--fixedSignalStrength", "0"] if m == "b" else []
            combine.run("combine", "-M", "GoodnessOfFit", ws, "--algo", "saturated", *extra,
                        "-n", ".gof_%s_%s.obs" % (v, m))
            combine.run("combine", "-M", "GoodnessOfFit", ws, "--algo", "saturated", *extra,
                        "-n", ".gof_%s_%s.toys" % (v, m), "-t", str(NTOYS), "--toysFrequentist", "-s", "1234")

    plots.gof_vs_limits()


if __name__ == "__main__":
    main()
