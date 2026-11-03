"""Demo 10: why the background-only post-fit matters (slide 16).
The data contain a REAL signal (r = 1, Asimov, 10x lumi). The model has a
fakes closure uncertainty (100%) on b4-b5, the "decomposed" fix of slide 11.
  fit_b (background-only): fakes_closure is pulled hard to absorb the signal
  fit_s (signal+background): signal found, no pulls

Run through the Combine environment:  bash with_combine.sh demos/run_10_bonly.py
"""
from src import cards, combine, plots, reports


def main():
    cards.bonly_cards()
    combine.run("text2workspace.py", "bonly/toy_bonly.txt", "-o", "bonly/toy_bonly.root")
    combine.run("combine", "-M", "FitDiagnostics", "bonly/toy_bonly.root", "-n", ".bonly",
                "--saveShapes", "--saveWithUncertainties")
    combine.run("combine", "-M", "Significance", "bonly/toy_bonly.root", "-n", ".bonly")

    print("=== Pulls: background-only vs signal+background ===")
    reports.fit_status("data with signal", "fitDiagnostics.bonly.root", ["r", "fakes_closure"])
    reports.fit_status("data with signal", "fitDiagnostics.bonly.root", ["fakes", "wz_xs"])
    plots.bonly_postfit()


if __name__ == "__main__":
    main()
