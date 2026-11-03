"""Demo 6: empty bins (slide 12). The background MC is empty in the tail bin b5,
but the data still have 6 events there. Scan the "tiny floor" put in the
empty bin (1e-3 ... 5 events) and compare with the fix (merge b4+b5).
For each: expected limit, observed limit, significance of the "excess".

Run through the Combine environment:  bash with_combine.sh demos/run_06_emptybins.py
"""
from src import cards, combine, plots

TAGS = ["floor_0.001", "floor_0.01", "floor_0.1", "floor_0.5", "floor_1", "floor_2", "floor_5", "merged"]


def main():
    cards.empty_cards()

    for t in TAGS:
        combine.run("text2workspace.py", "empty/toy_%s.txt" % t, "-o", "empty/toy_%s.root" % t)
        combine.run("combine", "-M", "AsymptoticLimits", "empty/toy_%s.root" % t,
                    "-t", "-1", "-n", ".empty_%s.exp" % t)
        combine.run("combine", "-M", "AsymptoticLimits", "empty/toy_%s.root" % t,
                    "-n", ".empty_%s.obs" % t)
        combine.run("combine", "-M", "Significance", "empty/toy_%s.root" % t,
                    "-n", ".empty_%s" % t, log="empty/sig_%s.log" % t)

    plots.empty_bins()

    # Pre-fit / post-fit yields: why the floored bin turns into "signal"
    for t in ["floor_0.01", "merged"]:
        combine.run("combine", "-M", "FitDiagnostics", "empty/toy_%s.root" % t, "-n", ".empty_%s" % t)
    plots.empty_bins_fit()


if __name__ == "__main__":
    main()
