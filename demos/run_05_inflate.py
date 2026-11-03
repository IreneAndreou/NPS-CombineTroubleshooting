"""Demo 5: inflating an uncertainty vs. decomposing it (slide 11).
Pseudo-data with NO signal; fakes are 2x under-predicted in b4-b5 only (30x lumi).
  nominal     fakes 30%, all bins
  inflated    fakes 100%, all bins         ("cover it with one big number")
  decomposed  fakes 30% + fakes_closure 100% on b4-b5
Shows: post-fit width of each fakes nuisance (b-only fit), the best-fit r
(s+b fit), and the spurious significance.

Run through the Combine environment:  bash with_combine.sh demos/run_05_inflate.py
"""
from src import cards, combine, plots

MODELS = ["nominal", "inflated", "decomposed"]


def main():
    cards.inflate_cards()

    for m in MODELS:
        combine.run("text2workspace.py", "inflate/toy_%s.txt" % m, "-o", "inflate/toy_%s.root" % m)
        combine.run("combine", "-M", "FitDiagnostics", "inflate/toy_%s.root" % m,
                    "-n", ".infl_%s" % m, "--rMin", "-5", "--rMax", "5")
        log = "inflate/sig_%s.log" % m
        combine.run("combine", "-M", "Significance", "inflate/toy_%s.root" % m,
                    "-n", ".infl_%s" % m, log=log)
        print(open(log).read(), end="")

    print("=== Spurious significance (no signal in the pseudo-data) ===")
    for m in MODELS:
        lines = [l.strip() for l in open("inflate/sig_%s.log" % m) if "Significance:" in l]
        print("%s: %s" % (m, " ".join(lines)))

    plots.inflate()


if __name__ == "__main__":
    main()
