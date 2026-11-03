"""Backup B2: what Combine does with an empty bin. An 11-bin shape card with the
signal peaking at bin 7, and three cases for bin 7: no data, no background MC and
no data, and no background MC with 3 data events.

Run through the Combine environment:  bash with_combine.sh demos/run_B2_emptytest.py
"""
from src import cards, combine, combine_outputs, plots

CASES = ["A_data0", "B_both0", "C_bkg0"]


def main():
    cards.emptytest_cards()

    with combine_outputs.in_dir("emptytest"):
        for c in CASES:
            combine.run("text2workspace.py", "%s.txt" % c, "-o", "%s.ws.root" % c,
                        log="t2w_%s.log" % c)
            combine.run("combine", "-M", "AsymptoticLimits", "%s.ws.root" % c, "-n", "." + c,
                        log="lim_%s.log" % c)
            combine.run("combine", "-M", "Significance", "%s.ws.root" % c, "-n", "." + c,
                        log="sig_%s.log" % c)
            exp = combine_outputs.first_value("lim_%s.log" % c, "Expected 50.0%")
            obs = combine_outputs.first_value("lim_%s.log" % c, "Observed Limit")
            signif = next((l.strip() for l in open("sig_%s.log" % c, encoding="utf-8")
                           if l.startswith("Significance")), "")
            zero = sum(1 for l in open("t2w_%s.log" % c, encoding="utf-8") if "Error is zero" in l)
            print("%-8s exp %s  obs %s  %s  zero-error bins: %d" % (c, exp, obs, signif, zero))

    plots.emptytest()


if __name__ == "__main__":
    main()
