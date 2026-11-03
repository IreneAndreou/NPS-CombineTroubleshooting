"""Backup B1: stacking with generic systematics (A-F: correlated, anti-correlated,
size-differs and single-era, shape and lnN). The per-era cards are merged into
one card with the correlations kept by name, and compared with combineCards.

Run through the Combine environment:  bash with_combine.sh demos/run_B1_stack_systs.py
"""
import os
import shutil

from src import cards, combine, combine_outputs, plots

D = "stack_systs/x1"
TAGS = ["eras", "stacked"]


def main():
    cards.stack_systs_inputs(1.0)
    cards.stack_systs_card(D)

    with combine_outputs.in_dir(D):
        combine.run_to_file("card_eras.txt", "combineCards.py",
                            "y22=card_2022.txt", "y23=card_2023.txt", "y24=card_2024.txt")
        for t in TAGS:
            combine.run("text2workspace.py", "card_%s.txt" % t, "-o", "ws_%s.root" % t,
                        log="t2w_%s.log" % t)
            combine.run("combine", "-M", "AsymptoticLimits", "ws_%s.root" % t, "-t", "-1",
                        "-n", ".%s.exp" % t, log="exp_%s.log" % t)
            combine.run("combine", "-M", "AsymptoticLimits", "ws_%s.root" % t,
                        "-n", ".%s.obs" % t, log="obs_%s.log" % t)

        print("== stacking with generic systematics (x1 luminosity)")
        for t in TAGS:
            exp = combine_outputs.first_value("exp_%s.log" % t, "Expected 50.0%")
            obs = combine_outputs.first_value("obs_%s.log" % t, "Observed Limit")
            nuis, mc = combine_outputs.count_nuisances("card_%s.txt" % t, "t2w_%s.log" % t)
            print("%-8s exp %s  obs %s  nuisances %s (MC stat %s)" % (t, exp, obs, nuis, mc))

        plots.limit_table([("3 per-era cards (combineCards)", "eras", False),
                           ("1 stacked card", "stacked", False)],
                          out="limits_stack_systs")
    os.makedirs("plots", exist_ok=True)
    for ext in ["pdf", "png"]:
        shutil.copy("%s/plots/limits_stack_systs.%s" % (D, ext), "plots/")

    plots.stack_systs(D)
    plots.stack_yields(D)


if __name__ == "__main__":
    main()
