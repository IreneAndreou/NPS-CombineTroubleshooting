"""Demo 3: autoMCStats (slide 9). Expected limits (-t -1) for the same toy with
nominal vs. poor fakes MC statistics, with and without autoMCStats,
thresholds 0 / 10 / 1000 (b5 drops into per-process mode at 10),
and two failure modes: a b5 fakes bin with no MC events (0 +- 0, and the
"1.84 x weight" patch), and a negative b5 fakes yield from negative weights.

Run through the Combine environment:  bash with_combine.sh demos/run_03_automcstats.py
"""
import re

from src import cards, combine, plots

VARIANTS = ["nominal_off", "nominal_t10", "poor_off", "poor_t10", "poor_t0", "poor_t1000",
            "zero_t10", "zerofix_t10", "negative_t10"]


def main():
    cards.mcstat_cards()

    for v in VARIANTS:
        combine.run("text2workspace.py", "mcstat/toy_%s.txt" % v, "-o", "mcstat/toy_%s.root" % v,
                    log="mcstat/t2w_%s.log" % v)
        combine.run("combine", "-M", "AsymptoticLimits", "mcstat/toy_%s.root" % v,
                    "-t", "-1", "-n", ".mc_%s.exp" % v)

    # How autoMCStats treated each bin, and how many nuisances it made
    for v in ["nominal_t10", "poor_t10", "poor_t1000"]:
        print("=== %s: autoMCStats bin treatment ===" % v)
        lines = open("mcstat/t2w_%s.log" % v).read().splitlines()
        for line in lines:
            if "=> " in line:
                print(line)
        n = sum(1 for line in lines
                if re.search(r"=> (Total parameter|Parameter|Product|Poisson not viable)", line))
        print("    nuisances created: %d" % n)

    plots.limit_table([("Nominal MC, no autoMCStats", "mc_nominal_off", True),
                       ("Nominal MC, autoMCStats 10", "mc_nominal_t10", True),
                       ("Poor fakes MC, no autoMCStats", "mc_poor_off", True),
                       ("Poor fakes MC, threshold 10", "mc_poor_t10", True),
                       ("Poor fakes MC, threshold 0", "mc_poor_t0", True),
                       ("Poor fakes MC, threshold 1000", "mc_poor_t1000", True)],
                      out="limits_mcstats")
    plots.limit_table([("Poor fakes MC, threshold 10", "mc_poor_t10", True),
                       ("b5 fakes: no MC events, 0 +- 0", "mc_zero_t10", True),
                       ("b5 fakes: 0 +- 1.84 x weight", "mc_zerofix_t10", True),
                       ("b5 fakes: negative yield (-1)", "mc_negative_t10", True)],
                      out="limits_mcstats_failures")


if __name__ == "__main__":
    main()
