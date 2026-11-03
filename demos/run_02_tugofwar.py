"""Demo 2: correlation tug of war (slide 8).
2022 pseudo-data want the fakes normalisation up, 2024 want it down.
  corr   one shared 'fakes' nuisance -> compromise pull, worse GoF
  decor  one nuisance per era        -> each pulls its own way, better GoF
Background-only fits (no signal in the pseudo-data). GoF p-values from toys.

Run through the Combine environment:  bash with_combine.sh demos/run_02_tugofwar.py
(set NTOYS to change the number of GoF toys, default 500)
"""
import os

from src import cards, combine, plots

NTOYS = int(os.environ.get("NTOYS", 500))


def main():
    cards.tug_cards()

    for s in ["corr", "decor"]:
        ws = "tug/toy_tug_%s.root" % s
        combine.run_to_file("tug/toy_tug_%s.txt" % s, "combineCards.py",
                            "y22=tug/toy_2022_%s.txt" % s, "y23=tug/toy_2023_%s.txt" % s,
                            "y24=tug/toy_2024_%s.txt" % s)
        combine.run("text2workspace.py", "tug/toy_tug_%s.txt" % s, "-o", ws)

        # Pulls: background-only fit to the pseudo-data
        combine.run("combine", "-M", "FitDiagnostics", ws, "-n", ".tug_%s" % s)

        # Goodness of fit: observed saturated test statistic + frequentist toys
        combine.run("combine", "-M", "GoodnessOfFit", ws, "--algo", "saturated", "-n", ".tug_%s.obs" % s)
        combine.run("combine", "-M", "GoodnessOfFit", ws, "--algo", "saturated", "-n", ".tug_%s.toys" % s,
                    "-t", str(NTOYS), "--toysFrequentist", "-s", "1234")

    plots.pulls(["Shared fakes nuisance|fitDiagnostics.tug_corr.root|fakes,fakes,fakes",
                 "Fakes per era|fitDiagnostics.tug_decor.root|fakes_2022,fakes_2023,fakes_2024"],
                labels=["2022", "2023", "2024"], truth=[1.5, 0, -1.5], out="pulls_tug")
    plots.gof(["Shared fakes nuisance|tug_corr", "Fakes per era|tug_decor"], out="gof_tug")


if __name__ == "__main__":
    main()
