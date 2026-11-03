"""Card and input writers for the demos.

counting_card() writes the shared counting-card layout. The *_cards() and shapes_root()
functions write each demo's cards (or its input ROOT file) into the directory named
after the demo, relative to the working directory (the repo root).
"""
import math
import os
import re

import ROOT

PROCS = ["sig", "WZ", "fakes"]
DASHES = "-" * 60


def counting_card(header, yields, data, systs, procs=None, w=9, n=14, rate_fmt="%g",
                  labels=None, extra=()):
    """Return the text of a counting card.

    header:  one-line comment, written as "# header".
    yields:  {process: [yield per bin]}.
    data:    observed count per bin (also sets the number of bins).
    systs:   [(name, size, processes)] lnN nuisances; a process not listed
             gets "-" in its columns.
    w, n:    column widths for the bin/process cells and the row labels.
    rate_fmt: format of the rate cells.
    labels:  bin names, default b1, b2, ...
    extra:   lines appended after the nuisances (e.g. rateParam rows).
    """
    procs = procs or PROCS
    nb = len(data)
    labels = labels or ["b%d" % (i + 1) for i in range(nb)]
    cols = [(i, p) for i in range(nb) for p in procs]
    L = ["# " + header,
         "imax %d" % nb, "jmax %d" % (len(procs) - 1), "kmax *", DASHES,
         "bin".ljust(n) + "".join(lab.ljust(w) for lab in labels),
         "observation".ljust(n) + "".join(("%g" % d).ljust(w) for d in data),
         DASHES,
         "bin".ljust(n) + "".join(labels[i].ljust(w) for i, _ in cols),
         "process".ljust(n) + "".join(p.ljust(w) for _, p in cols),
         "process".ljust(n) + "".join(str(procs.index(p)).ljust(w) for _, p in cols),
         "rate".ljust(n) + "".join((rate_fmt % yields[p][i]).ljust(w) for i, p in cols),
         DASHES]
    for name, size, with_procs in systs:
        L.append((name + " lnN").ljust(n)
                 + "".join((size if p in with_procs else "-").ljust(w) for _, p in cols))
    L.extend(extra)
    return "\n".join(L) + "\n"


def shape_histo(name, values, scale=1.0, errors=None):
    """A TH1D with one bin per value (bin i+1 = values[i] * scale).

    Bin errors are set only when errors is given, so the default keeps ROOT's own."""
    h = ROOT.TH1D(name, name, len(values), 0, len(values))
    for i, y in enumerate(values, start=1):
        h.SetBinContent(i, scale * y)
        if errors is not None:
            h.SetBinError(i, errors[i - 1])
    return h


# The three nuisances used by the toy in every counting-card demo.
TOY_SYSTS = [("lumi", "1.02", {"sig", "WZ"}),
             ("wz_xs", "1.10", {"WZ"}),
             ("fakes", "1.30", {"fakes"})]


def bonly_cards():
    """Card for the background-only post-fit demo (slide 16).

The data contain a REAL signal (r = 1, Asimov, 10x lumi). The model has the
"decomposed" fakes uncertainties from slide 11: fakes 30% on all bins plus
fakes_closure 100% on b4-b5 only. In the background-only fit, fakes_closure
can absorb (part of) the signal in b4-b5, so the post-fit looks fine.

  bonly/shapes.root, bonly/toy_bonly.txt"""
    ROOT.gROOT.SetBatch(True)
    SCALE = 10.0
    NB = 5
    SIG = [1, 2, 4, 8, 10]
    WZ = [120, 60, 25, 10, 4]
    FAKES = [40, 20, 8, 3, 1]
    CLOSURE = 2.00          # fakes_closure: 100% on b4-b5

    CARD = """# background-only post-fit demo: data contain signal (r = 1), 10x lumi
imax 1
jmax 2
kmax *
------------------------------------------------------------
shapes * * shapes.root $PROCESS $PROCESS_$SYSTEMATIC
------------------------------------------------------------
bin          SR
observation  -1
------------------------------------------------------------
bin          SR     SR     SR
process      sig    WZ     fakes
process      0      1      2
rate         -1     -1     -1
------------------------------------------------------------
lumi           lnN    1.02   1.02   -
wz_xs          lnN    -      1.10   -
fakes          lnN    -      -      1.30
fakes_closure  shape  -      -      1
"""

    os.makedirs("bonly", exist_ok=True)
    f = ROOT.TFile("bonly/shapes.root", "RECREATE")
    for name, ys in [("sig", SIG), ("WZ", WZ), ("fakes", FAKES)]:
        shape_histo(name, ys, scale=SCALE).Write()
    # fakes_closure: x2 up / x0.5 down in b4-b5 only (log-symmetric, like lnN 2.0)
    for tag, k in [("Up", CLOSURE), ("Down", 1.0 / CLOSURE)]:
        h = ROOT.TH1D("fakes_fakes_closure" + tag, "", NB, 0, NB)
        for i, y in enumerate(FAKES, start=1):
            h.SetBinContent(i, SCALE * y * (k if i >= 4 else 1.0))
        h.Write()
    d = ROOT.TH1D("data_obs", "data_obs", NB, 0, NB)
    for i in range(NB):
        d.SetBinContent(i + 1, SCALE * (SIG[i] + WZ[i] + FAKES[i]))
    d.Write()
    f.Close()
    with open("bonly/toy_bonly.txt", "w", encoding="utf-8") as out:
        out.write(CARD)
    print("Wrote bonly/toy_bonly.txt (data = background + signal, r = 1)")


def conv_cards():
    """Cards for the non-convergence demo (slide 14).

Starts from toy.txt and adds free-floating fakes normalisations:
  conv/toy_degen.txt  TWO rateParams on fakes (fakes_norm, fakes_extra).
                      Only their product changes the prediction, so the
                      likelihood is flat along norm x extra = const:
                      the fit cannot pick a point on that valley.
                      (Real-life version: the same normalisation floated
                      twice, e.g. once per-channel and once globally.)
  conv/toy_fixed.txt  the fix: one rateParam (fakes_norm)."""
    base = open("inputs/toy.txt", encoding="utf-8").read().rstrip("\n")
    os.makedirs("conv", exist_ok=True)
    with open("conv/toy_degen.txt", "w", encoding="utf-8") as f:
        f.write(base + "\nfakes_norm  rateParam * fakes 1 [0,10]"
                       "\nfakes_extra rateParam * fakes 1 [0,10]\n")
    with open("conv/toy_fixed.txt", "w", encoding="utf-8") as f:
        f.write(base + "\nfakes_norm  rateParam * fakes 1 [0,10]\n")
    print("Wrote conv/toy_degen.txt and conv/toy_fixed.txt")


def degen_cards():
    """Cards for the signal-background degeneracy demo (slide 15).

WZ normalisation floats freely (wz_norm rateParam). Three setups, 10x lumi,
one 5-bin shape channel "SR" (+ optional control region "CR"):

  distinct   WZ falls with the bin index (as in the baseline toy), the signal
             rises: the fit can tell them apart.
  degen      WZ has a signal-like shape (mostly b4-b5, e.g. a background with
             the same kinematics as the signal): r and wz_norm can trade
             events, giving a long diagonal valley.
  degen_cr   the fix: degen + a WZ-enriched control region (1 bin, no signal)
             that measures wz_norm independently.

The observed data are not used: everything runs on Asimov data (-t -1).

  degen/shapes_<setup>.root, degen/toy_<setup>.txt"""
    ROOT.gROOT.SetBatch(True)
    SCALE = 10.0
    NB = 5
    SIG = [1, 2, 4, 8, 10]
    FAKES = [40, 20, 8, 3, 1]
    WZ_FALLING = [120, 60, 25, 10, 4]                 # total 219
    WZ_SIGLIKE = [9, 18, 35, 70, 87]                  # total 219, shape ~ signal
    CR_WZ, CR_OTHER = 2000.0, 200.0                   # control region yields (10x lumi)

    SR_CARD = """# degeneracy demo: {setup}
imax {imax}
jmax 2
kmax *
------------------------------------------------------------
shapes * SR {root} $PROCESS $PROCESS_$SYSTEMATIC
{cr_shapes}------------------------------------------------------------
bin          SR{cr_bin}
observation  -1{cr_obs}
------------------------------------------------------------
bin          SR     SR     SR{cr_cols_bin}
process      sig    WZ     fakes{cr_cols_proc}
process      0      1      2{cr_cols_idx}
rate         -1     -1     -1{cr_cols_rate}
------------------------------------------------------------
lumi    lnN  1.02   1.02   -{cr_lumi}
fakes   lnN  -      -      1.30{cr_fakes}
wz_norm rateParam * WZ 1 [0,5]
"""


    def write(setup, wz, with_cr):
        root = "shapes_%s.root" % setup
        f = ROOT.TFile("degen/" + root, "RECREATE")
        for name, ys in [("sig", SIG), ("WZ", wz), ("fakes", FAKES)]:
            shape_histo(name, ys, scale=SCALE).Write()
        d = ROOT.TH1D("data_obs", "data_obs", NB, 0, NB)
        for i in range(NB):
            d.SetBinContent(i + 1, SCALE * (wz[i] + FAKES[i] + SIG[i]))   # r = 1
        d.Write()
        f.Close()
        cr = dict(cr_shapes="", cr_bin="", cr_obs="", cr_cols_bin="", cr_cols_proc="",
                  cr_cols_idx="", cr_cols_rate="", cr_lumi="", cr_fakes="")
        if with_cr:
            cr = dict(cr_shapes="shapes * CR FAKE\n", cr_bin="     CR",
                      cr_obs="     %g" % (CR_WZ + CR_OTHER),
                      cr_cols_bin="     CR     CR",
                      cr_cols_proc="     WZ     fakes",
                      cr_cols_idx="     1      2",
                      cr_cols_rate="     %g   %g" % (CR_WZ, CR_OTHER),
                      cr_lumi="      1.02   -", cr_fakes="      -      1.30")
        with open("degen/toy_%s.txt" % setup, "w", encoding="utf-8") as out:
            out.write(SR_CARD.format(setup=setup, imax=2 if with_cr else 1, root=root, **cr))


    os.makedirs("degen", exist_ok=True)
    write("distinct", WZ_FALLING, False)
    write("degen", WZ_SIGLIKE, False)
    write("degen_cr", WZ_SIGLIKE, True)
    print("Wrote degen/toy_{distinct,degen,degen_cr}.txt")


def empty_cards():
    """Cards for the empty-bin demo (slide 12).

Story: the background MC has no events in the tail bin b5, so the template
says 0 there. The data still have 6 events in b5 (the true background is ~5,
as in the baseline toy). A common "fix" is a tiny floor on the empty bin.

  empty/toy_floor_<f>.txt   b5 background = f (WZ = f, fakes = 0),
                            for f in FLOORS; everything else as toy.txt
  empty/toy_merged.txt      the fix: b4 and b5 merged into one wider bin, which
                            has enough MC events to estimate its background
                            (the sum of the true b4 and b5 backgrounds)

Signal in b5 stays at 10, observed data stay as in toy.txt."""
    YIELDS = {
        "sig":   [1, 2, 4, 8, 10],
        "WZ":    [120, 60, 25, 10, 4],
        "fakes": [40, 20, 8, 3, 1],
    }
    DATA = [160, 80, 35, 14, 6]
    FLOORS = [0.001, 0.01, 0.1, 0.5, 1, 2, 5]


    def card(yields, data, header):
        return counting_card(header, yields, data, TOY_SYSTS)


    os.makedirs("empty", exist_ok=True)
    for f in FLOORS:
        y = {p: list(v) for p, v in YIELDS.items()}
        y["WZ"][4], y["fakes"][4] = f, 0.0
        with open("empty/toy_floor_%g.txt" % f, "w", encoding="utf-8") as out:
            out.write(card(y, DATA, "b5 background MC empty, floored to %g" % f))

    # fix: merge b4+b5 into a bin wide enough for the MC to populate it
    y = {p: v[:3] + [v[3] + v[4]] for p, v in YIELDS.items()}
    with open("empty/toy_merged.txt", "w", encoding="utf-8") as out:
        out.write(card(y, DATA[:3] + [DATA[3] + DATA[4]],
                       "b4 and b5 merged into one bin with a proper background estimate"))
    print("floors:", " ".join("%g" % f for f in FLOORS))


def float_cards():
    """Cards for the floating vs. constrained background demo (slide 10).

Same counting toy as toy.txt. WZ normalisation is either
  constrained:  wz_xs lnN 1.10                  (prior holds it within 10%)
  floating:     wz_norm rateParam * WZ 1 [0,5]  (no prior: data alone set it)
and the card either keeps all 5 bins ("withCR": b1-b2 are WZ-dominated and
act as a control region) or only b3-b5 ("noCR": the signal-rich bins only).

  float/toy_<constrained|floating>_<withCR|noCR>.txt"""
    YIELDS = {
        "sig":   [1, 2, 4, 8, 10],
        "WZ":    [120, 60, 25, 10, 4],
        "fakes": [40, 20, 8, 3, 1],
    }
    DATA = [160, 80, 35, 14, 6]
    BINSETS = {"withCR": [0, 1, 2, 3, 4], "noCR": [2, 3, 4]}


    def card(bins, wz_mode):
        labels = ["b%d" % (i + 1) for i in bins]
        nuis = [("lumi", "1.02", {"sig", "WZ"}), ("fakes", "1.30", {"fakes"})]
        if wz_mode == "constrained":
            nuis.insert(1, ("wz_xs", "1.10", {"WZ"}))
        extra = ["wz_norm rateParam * WZ 1 [0,5]"] if wz_mode == "floating" else ()
        return counting_card("toy, bins %s, WZ %s" % (",".join(labels), wz_mode),
                                   {p: [YIELDS[p][i] for i in bins] for p in PROCS},
                                   [DATA[i] for i in bins], nuis, labels=labels, extra=extra)


    os.makedirs("float", exist_ok=True)
    for cr, bins in BINSETS.items():
        for mode in ["constrained", "floating"]:
            with open("float/toy_%s_%s.txt" % (mode, cr), "w", encoding="utf-8") as f:
                f.write(card(bins, mode))
    print("Wrote 4 cards in float/")


def gof_cards():
    """Cards for the "bad GoF but fine limit?" demo (slide 18).

Baseline toy at 10x luminosity, one 5-bin shape channel, no signal in the
data. The data are Poisson-fluctuated background (fixed seed, the same draw for
all variants) plus one local mismodelling of NSIGMA x sqrt(background):

  good   data = background
  misA   excess in b1 (no signal sensitivity there)
  misB   excess in b5 (the most signal-rich bin)

  gof/shapes_<v>.root, gof/toy_<v>.txt"""
    ROOT.gROOT.SetBatch(True)
    SCALE = 10.0
    NB = 5
    SIG = [1, 2, 4, 8, 10]
    WZ = [120, 60, 25, 10, 4]
    FAKES = [40, 20, 8, 3, 1]
    NSIGMA = float(os.environ.get("GOF_NSIGMA", 3.5))
    SEED = int(os.environ.get("GOF_SEED", 3))  # one of three draws checked; all show the same pattern
    VARIANTS = {"good": None, "misA": 0, "misB": 4}   # bin index with the excess

    CARD = """# bad-GoF demo: {v}
imax 1
jmax 2
kmax *
------------------------------------------------------------
shapes * * shapes_{v}.root $PROCESS
------------------------------------------------------------
bin          SR
observation  -1
------------------------------------------------------------
bin          SR     SR     SR
process      sig    WZ     fakes
process      0      1      2
rate         -1     -1     -1
------------------------------------------------------------
lumi    lnN  1.02   1.02   -
wz_xs   lnN  -      1.10   -
fakes   lnN  -      -      1.30
"""

    os.makedirs("gof", exist_ok=True)
    rng = ROOT.TRandom3(SEED)
    base = [rng.Poisson(SCALE * (WZ[i] + FAKES[i])) for i in range(NB)]
    for v, b in VARIANTS.items():
        f = ROOT.TFile("gof/shapes_%s.root" % v, "RECREATE")
        for name, ys in [("sig", SIG), ("WZ", WZ), ("fakes", FAKES)]:
            shape_histo(name, ys, scale=SCALE).Write()
        d = ROOT.TH1D("data_obs", "data_obs", NB, 0, NB)
        data = []
        for i in range(NB):
            bkg = SCALE * (WZ[i] + FAKES[i])
            n = base[i] + (round(NSIGMA * bkg ** 0.5) if i == b else 0)
            d.SetBinContent(i + 1, n)
            data.append(n)
        d.Write()
        f.Close()
        with open("gof/toy_%s.txt" % v, "w", encoding="utf-8") as out:
            out.write(CARD.format(v=v))
        print("%-5s data %s" % (v, data))


def inflate_cards():
    """Cards for the "inflate the uncertainty to cover it" demo (slide 11).

Story: a closure test shows the fakes estimate is 2x too LOW in the signal
bins (b4-b5) and fine elsewhere. The pseudo-data contain NO signal: they are
the expected background with fakes x2 in b4-b5 (exact expected values, i.e.
an Asimov-like dataset, so the result is the *expected* bias). 30x luminosity
(roughly full Run 2 + Run 3 for a rare process), so the data constrain the
fakes clearly. Override with INFL_SCALE / INFL_NONCLOSURE.

Three models of the fakes uncertainty:
  nominal    fakes lnN 1.30 on all bins (ignores the closure problem)
  inflated   fakes lnN 2.00 on all bins (one big number "to cover it")
  decomposed fakes lnN 1.30 on all bins + fakes_closure lnN 2.00 on b4-b5 only

  inflate/toy_<model>.txt"""
    SCALE = float(os.environ.get("INFL_SCALE", 30.0))
    YIELDS = {
        "sig":   [1, 2, 4, 8, 10],
        "WZ":    [120, 60, 25, 10, 4],
        "fakes": [40, 20, 8, 3, 1],
    }
    NB = 5
    SR = {3, 4}            # b4, b5
    NONCLOSURE = float(os.environ.get("INFL_NONCLOSURE", 2.0))  # true / predicted fakes in the SR
    KAPPA = "%.2f" % NONCLOSURE   # the "covering" uncertainty matches the closure: 2x -> 100%

    y = {p: [SCALE * v for v in YIELDS[p]] for p in PROCS}
    obs = [y["WZ"][i] + y["fakes"][i] * (NONCLOSURE if i in SR else 1.0) for i in range(NB)]

    MODELS = {
        "nominal":    [("fakes", "1.30", range(NB))],
        "inflated":   [("fakes", KAPPA, range(NB))],
        "decomposed": [("fakes", "1.30", range(NB)), ("fakes_closure", KAPPA, SR)],
    }


    def card(model):
        w, n = 9, 20
        cols = [(i, p) for i in range(NB) for p in PROCS]
        L = ["# pseudo-data: no signal, fakes x%.1f in b4-b5, %gx lumi; model: %s"
             % (NONCLOSURE, SCALE, model),
             "imax %d" % NB, "jmax 2", "kmax *", "-" * 60,
             "bin".ljust(n) + "".join(("b%d" % (i + 1)).ljust(w) for i in range(NB)),
             "observation".ljust(n) + "".join(("%g" % o).ljust(w) for o in obs),
             "-" * 60,
             "bin".ljust(n) + "".join(("b%d" % (i + 1)).ljust(w) for i, _ in cols),
             "process".ljust(n) + "".join(p.ljust(w) for _, p in cols),
             "process".ljust(n) + "".join(str(PROCS.index(p)).ljust(w) for _, p in cols),
             "rate".ljust(n) + "".join(("%g" % y[p][i]).ljust(w) for i, p in cols),
             "-" * 60,
             "lumi lnN".ljust(n) + "".join(("1.02" if p != "fakes" else "-").ljust(w) for _, p in cols),
             "wz_xs lnN".ljust(n) + "".join(("1.10" if p == "WZ" else "-").ljust(w) for _, p in cols)]
        for name, size, bins in MODELS[model]:
            L.append((name + " lnN").ljust(n) + "".join(
                (size if (p == "fakes" and i in bins) else "-").ljust(w) for i, p in cols))
        return "\n".join(L) + "\n"


    os.makedirs("inflate", exist_ok=True)
    for m in MODELS:
        with open("inflate/toy_%s.txt" % m, "w", encoding="utf-8") as f:
            f.write(card(m))
    print("pseudo-data (no signal):", [round(o, 1) for o in obs])


def lowcount_cards():
    """Cards for the low-count demo (slide 17): asymptotic vs toy-based limits.

The baseline counting toy with every yield scaled by a luminosity factor s.
The observed data are set to the rounded expected background (no signal),
so the observed limit should sit near the median expected one.

  lowcount/toy_s<s>.txt   for s in SCALES"""
    SCALES = [1.0, 0.3, 0.1, 0.03, 0.01]
    YIELDS = {
        "sig":   [1, 2, 4, 8, 10],
        "WZ":    [120, 60, 25, 10, 4],
        "fakes": [40, 20, 8, 3, 1],
    }
    NB = 5


    def card(s):
        y = {p: [s * v for v in YIELDS[p]] for p in PROCS}
        obs = [int(round(y["WZ"][i] + y["fakes"][i])) for i in range(NB)]
        txt = counting_card("low-count demo: all yields x%g, data = rounded background" % s,
                                  y, obs, TOY_SYSTS, w=10, rate_fmt="%.4g")
        return txt, obs, [y["WZ"][i] + y["fakes"][i] for i in range(NB)]


    os.makedirs("lowcount", exist_ok=True)
    for s in SCALES:
        txt, obs, bkg = card(s)
        with open("lowcount/toy_s%g.txt" % s, "w", encoding="utf-8") as f:
            f.write(txt)
        print("s = %-5g background per bin: %s  -> data %s"
              % (s, " ".join("%.1f" % b for b in bkg), obs))


def mass_cards():
    """Cards for the localised-signal / mass-grid demo (slide 20).

A falling background over m = 200-1000 GeV (40 bins of 20 GeV) and a narrow
resonance (Gaussian, 10 GeV resolution) at a hypothesised mass M. The data
are Poisson-fluctuated background (fixed seed) PLUS a real signal injected
at M_TRUE = 530 GeV, between the points of a 100 GeV grid.

One card per mass hypothesis M = 200, 210, ..., 1000 GeV:
  mass/mass.root             bkg, data_obs, sig_M<M> for every M
  mass/card_M<M>.txt         sig = sig_M<M>, bkg with a 10% normalisation unc."""
    ROOT.gROOT.SetBatch(True)
    LO, HI, NB = 200.0, 1000.0, 40
    RES = 10.0                      # signal resolution (GeV)
    SIG_YIELD = 20.0                # expected signal events at r = 1, any mass
    M_TRUE, N_INJ = 530.0, 40.0     # injected signal: mass, events
    BKG_NORM, BKG_SLOPE = 4000.0, 150.0
    SEED = int(os.environ.get("MASS_SEED", 1))
    MASSES = list(range(200, 1001, 10))


    def gauss_hist(name, m0, n):
        h = ROOT.TH1D(name, name, NB, LO, HI)
        for i in range(1, NB + 1):
            a, b = h.GetBinLowEdge(i), h.GetBinLowEdge(i + 1)
            frac = 0.5 * (math.erf((b - m0) / (RES * 2 ** 0.5)) - math.erf((a - m0) / (RES * 2 ** 0.5)))
            h.SetBinContent(i, n * frac)
        return h


    os.makedirs("mass", exist_ok=True)
    f = ROOT.TFile("mass/mass.root", "RECREATE")
    bkg = ROOT.TH1D("bkg", "bkg", NB, LO, HI)
    for i in range(1, NB + 1):
        a, b = bkg.GetBinLowEdge(i), bkg.GetBinLowEdge(i + 1)
        bkg.SetBinContent(i, BKG_NORM * (math.exp(-(a - LO) / BKG_SLOPE) - math.exp(-(b - LO) / BKG_SLOPE)))
    bkg.Write()
    inj = gauss_hist("injected", M_TRUE, N_INJ)
    inj.Write()
    rng = ROOT.TRandom3(SEED)
    data = ROOT.TH1D("data_obs", "data_obs", NB, LO, HI)
    for i in range(1, NB + 1):
        data.SetBinContent(i, rng.Poisson(bkg.GetBinContent(i) + inj.GetBinContent(i)))
    data.Write()
    for m in MASSES:
        gauss_hist("sig_M%d" % m, m, SIG_YIELD).Write()
    f.Close()

    CARD = """# mass-grid demo: signal hypothesis M = {m} GeV
imax 1
jmax 1
kmax *
------------------------------------------------------------
shapes sig      * mass.root sig_M{m}
shapes bkg      * mass.root bkg
shapes data_obs * mass.root data_obs
------------------------------------------------------------
bin          SR
observation  -1
------------------------------------------------------------
bin          SR     SR
process      sig    bkg
process      0      1
rate         -1     -1
------------------------------------------------------------
lumi      lnN    1.02   -
bkg_norm  lnN    -      1.10
"""
    for m in MASSES:
        with open("mass/card_M%d.txt" % m, "w", encoding="utf-8") as out:
            out.write(CARD.format(m=m))
    print("Wrote %d mass cards; injected %.0f signal events at %.0f GeV"
          % (len(MASSES), N_INJ, M_TRUE))


def mcstat_cards():
    """Cards for the autoMCStats demo (slide 9).

Same toy as toy_shapes.txt (one 5-bin channel). Bin errors emulate finite MC:
a process filled with events of weight w has error sqrt(w * y) in a bin with
yield y. "nominal" uses the baseline weights; "poor" gives the fakes weight 3
(a small fake-enriched sample), which pushes b5 below the threshold of 10
effective events, so autoMCStats switches to one nuisance per process there.

Variants (mcstat/toy_<name>.txt):
  nominal_off     nominal MC, no autoMCStats
  nominal_t10     nominal MC, autoMCStats 10          (= toy_shapes.txt)
  poor_off        poor fakes MC, no autoMCStats
  poor_t10        poor fakes MC, autoMCStats 10       -> b5 per-process
  poor_t0         threshold 0:    every bin one Gaussian on the total
  poor_t1000      threshold 1000: every bin one nuisance per process
  zero_t10        poor MC, but no fakes MC event passed b5: 0 +- 0
                  -> autoMCStats has nothing to work with
  zerofix_t10     same, with the error set to w * 1.84 (the 68% Poisson upper
                  limit for 0 observed MC events, times the event weight)
  negative_t10    poor MC, with b5 fakes at -1 from negative weights"""
    ROOT.gROOT.SetBatch(True)
    NB = 5
    YIELDS = {
        "sig":   [1, 2, 4, 8, 10],
        "WZ":    [120, 60, 25, 10, 4],
        "fakes": [40, 20, 8, 3, 1],
    }
    DATA = [160, 80, 35, 14, 6]
    W_NOMINAL = {"sig": 0.05, "WZ": 0.2, "fakes": 0.5}
    W_POOR = dict(W_NOMINAL, fakes=3.0)

    CARD = """# {header}
imax 1
jmax 2
kmax *
------------------------------------------------------------
shapes * * {root} $PROCESS $PROCESS_$SYSTEMATIC
------------------------------------------------------------
bin          SR
observation  -1
------------------------------------------------------------
bin          SR     SR     SR
process      sig    WZ     fakes
process      0      1      2
rate         -1     -1     -1
------------------------------------------------------------
lumi    lnN  1.02   1.02   -
wz_xs   lnN  -      1.10   -
fakes   lnN  -      -      1.30
{mcstats}
"""


    def write_root(path, weights, b5_fakes=None):
        """b5_fakes: optional (content, error) override for fakes in bin 5."""
        f = ROOT.TFile(path, "RECREATE")
        for p, ys in YIELDS.items():
            h = ROOT.TH1D(p, p, NB, 0, NB)
            for i, y in enumerate(ys, start=1):
                h.SetBinContent(i, y)
                h.SetBinError(i, (weights[p] * y) ** 0.5)
            if p == "fakes" and b5_fakes is not None:
                h.SetBinContent(5, b5_fakes[0])
                h.SetBinError(5, b5_fakes[1])
            h.Write()
        hd = ROOT.TH1D("data_obs", "data_obs", NB, 0, NB)
        for i, n in enumerate(DATA, start=1):
            hd.SetBinContent(i, n)
        hd.Write()
        f.Close()


    os.makedirs("mcstat", exist_ok=True)
    w = W_POOR["fakes"]
    write_root("mcstat/nominal.root", W_NOMINAL)
    write_root("mcstat/poor.root", W_POOR)
    write_root("mcstat/zero.root", W_POOR, b5_fakes=(0.0, 0.0))
    write_root("mcstat/zerofix.root", W_POOR, b5_fakes=(0.0, 1.84 * w))
    write_root("mcstat/negative.root", W_POOR, b5_fakes=(-1.0, (w * 1.0) ** 0.5))

    VARIANTS = [
        ("nominal_off", "nominal", None),
        ("nominal_t10", "nominal", 10),
        ("poor_off", "poor", None),
        ("poor_t10", "poor", 10),
        ("poor_t0", "poor", 0),
        ("poor_t1000", "poor", 1000),
        ("zero_t10", "zero", 10),
        ("zerofix_t10", "zerofix", 10),
        ("negative_t10", "negative", 10),
    ]
    for name, root, thr in VARIANTS:
        mc = "" if thr is None else "* autoMCStats %d 0 1" % thr
        with open("mcstat/toy_%s.txt" % name, "w", encoding="utf-8") as out:
            out.write(CARD.format(header="autoMCStats demo: " + name,
                                  root=root + ".root", mcstats=mc))
    print("Wrote %d cards in mcstat/" % len(VARIANTS))


def shapes_root():
    """Build toy_shapes.root: the toy.txt yields as 5-bin histograms.

Bin errors emulate finite MC statistics: each process is assumed to be
filled with events of a fixed weight w, so the error on a bin with
yield y is sqrt(w * y). Fakes get the largest weight (poorest MC stats),
which matters for the autoMCStats demo."""
    YIELDS = {
        "sig":   [1, 2, 4, 8, 10],
        "WZ":    [120, 60, 25, 10, 4],
        "fakes": [40, 20, 8, 3, 1],
    }
    WEIGHTS = {"sig": 0.05, "WZ": 0.2, "fakes": 0.5}
    DATA = [160, 80, 35, 14, 6]
    NBINS = 5

    out = ROOT.TFile("toy_shapes.root", "RECREATE")

    for proc, ys in YIELDS.items():
        h = ROOT.TH1D(proc, proc, NBINS, 0, NBINS)
        for i, y in enumerate(ys, start=1):
            h.SetBinContent(i, y)
            h.SetBinError(i, (WEIGHTS[proc] * y) ** 0.5)
        h.Write()

    hd = ROOT.TH1D("data_obs", "data_obs", NBINS, 0, NBINS)
    for i, n in enumerate(DATA, start=1):
        hd.SetBinContent(i, n)
        hd.SetBinError(i, n ** 0.5)
    hd.Write()

    out.Close()
    print("Wrote toy_shapes.root")


def spiky_cards():
    """Cards for the spiky-template demo (slide 13).

WZ gets a shape uncertainty 'wz_shape'. The physical effect is a smooth tilt:
0% in b1 rising linearly to +-20% in b5. Four ways to put it in the card:

  smooth    up/down = nominal x (1 +- tilt)                    (the truth)
  spiky     the same tilt, but each template also carries independent
            bin-by-bin noise of 10% (as from low-statistics MC variations):
            up and down fluctuate separately, so in some bins both move the
            same way
  smoothed  patch 1: a straight line fitted to the spiky up/down ratios
  lnN       patch 2: the spiky templates replaced by one normalisation
            uncertainty with the average size in the signal bins (b4-b5)
  none      no WZ shape uncertainty at all (reference)

Yields: the baseline toy at 10x luminosity, so the data can constrain things.
Fixed seed for the noise, so the templates are reproducible.

  spiky/shapes_<variant>.root, spiky/toy_<variant>.txt"""
    ROOT.gROOT.SetBatch(True)
    SCALE = 10.0
    NB = 5
    YIELDS = {
        "sig":   [1, 2, 4, 8, 10],
        "WZ":    [120, 60, 25, 10, 4],
        "fakes": [40, 20, 8, 3, 1],
    }
    TILT = [0.0, 0.05, 0.10, 0.15, 0.20]   # true relative effect per bin
    NOISE = 0.10                           # bin-by-bin noise on the spiky templates
    SEED = int(os.environ.get("SPIKY_SEED", 15))  # a typical draw: limit and constraint near the medians of 30 draws

    rng = ROOT.TRandom3(SEED)
    nom = {p: [SCALE * v for v in YIELDS[p]] for p in YIELDS}

    ratios = {
        "smooth": ([1 + t for t in TILT], [1 - t for t in TILT]),
        "spiky": ([1 + t + rng.Gaus(0, NOISE) for t in TILT],
                  [1 - t + rng.Gaus(0, NOISE) for t in TILT]),
    }


    def line_fit(ys):
        """Least-squares straight line through (bin index, ratio - 1), forced
    through 0 effect at b1 is NOT imposed: a plain linear fit."""
        xs = list(range(NB))
        n = float(NB)
        mx, my = sum(xs) / n, sum(ys) / n
        b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
        a = my - b * mx
        return [a + b * x for x in xs]


    up_s, dn_s = ratios["spiky"]
    ratios["smoothed"] = (line_fit(up_s), line_fit(dn_s))

    # lnN patch: average size of the spiky up/down shift in b4-b5
    lnn = 1 + 0.5 * sum(0.5 * (abs(up_s[i] - 1) + abs(dn_s[i] - 1)) for i in (3, 4))

    CARD = """# spiky-template demo: {variant}
imax 1
jmax 2
kmax *
------------------------------------------------------------
shapes * * shapes_{variant}.root $PROCESS $PROCESS_$SYSTEMATIC
------------------------------------------------------------
bin          SR
observation  -1
------------------------------------------------------------
bin          SR     SR     SR
process      sig    WZ     fakes
process      0      1      2
rate         -1     -1     -1
------------------------------------------------------------
lumi      lnN    1.02   1.02   -
wz_xs     lnN    -      1.10   -
fakes     lnN    -      -      1.30
{extra}
"""

    os.makedirs("spiky", exist_ok=True)
    for variant in ["none", "smooth", "spiky", "smoothed", "lnN"]:
        f = ROOT.TFile("spiky/shapes_%s.root" % variant, "RECREATE")
        for p, ys in nom.items():
            shape_histo(p, ys).Write()
        d = ROOT.TH1D("data_obs", "data_obs", NB, 0, NB)
        for i in range(NB):
            d.SetBinContent(i + 1, nom["WZ"][i] + nom["fakes"][i])
        d.Write()
        if variant in ratios:
            for tag, rr in zip(["Up", "Down"], ratios[variant]):
                h = ROOT.TH1D("WZ_wz_shape" + tag, "", NB, 0, NB)
                for i in range(NB):
                    h.SetBinContent(i + 1, nom["WZ"][i] * rr[i])
                h.Write()
            extra = "wz_shape  shape  -      1      -"
        elif variant == "lnN":
            extra = "wz_shape  lnN    -      %.3f  -" % lnn
        else:
            extra = ""
        f.Close()
        with open("spiky/toy_%s.txt" % variant, "w", encoding="utf-8") as out:
            out.write(CARD.format(variant=variant, extra=extra))

    print("bin       " + "".join("%8s" % ("b%d" % (i + 1)) for i in range(NB)))
    for v in ["smooth", "spiky", "smoothed"]:
        up, dn = ratios[v]
        print("%-8s up" % v + "".join("%+8.1f%%" % (100 * (u - 1)) for u in up))
        print("%-8s dn" % v + "".join("%+8.1f%%" % (100 * (x - 1)) for x in dn))
    print("lnN patch: %.3f" % lnn)


# ---- eras: the toy split into 2022/2023/2024 cards (demo 1, and the tug-of-war demo) ----

# Integrated luminosity per era in fb^-1 (approximate; swap in your analysis's).
ERA_LUMI = {"2022": 34.7, "2023": 27.8, "2024": 109.0}
ERA_LIST = list(ERA_LUMI)
ERA_FRAC = {e: ERA_LUMI[e] / sum(ERA_LUMI.values()) for e in ERA_LIST}
ERA_NB = 5
ERA_YIELDS = {
    "sig":   [1, 2, 4, 8, 10],
    "WZ":    [120, 60, 25, 10, 4],
    "fakes": [40, 20, 8, 3, 1],
}
ERA_DATA = [160, 80, 35, 14, 6]
ERA_ALL_BINS = set(range(ERA_NB))
# (name, size, processes, bins it applies to)
ERA_BASE_NUIS = [
    ("lumi", 1.02, {"sig", "WZ"}, ERA_ALL_BINS),
    ("wz_xs", 1.10, {"WZ"}, ERA_ALL_BINS),
    ("fakes", 1.30, {"fakes"}, ERA_ALL_BINS),
]
ERA_EXTRAP = ("wz_extrap", 1.30, {"WZ"}, {3, 4})   # b4, b5


def era_split_int(n):
    """Split integer n into per-era integers proportional to luminosity
    (largest-remainder rounding). Any split gives the same stacked result."""
    raw = [n * ERA_FRAC[e] for e in ERA_LIST]
    out = [int(x) for x in raw]
    order = sorted(range(len(ERA_LIST)), key=lambda k: raw[k] - out[k], reverse=True)
    for k in order[: n - sum(out)]:
        out[k] += 1
    return out


def era_write_card(path, yields, obs, nuis, rename, header):
    """yields: {proc: [ERA_NB floats]}, obs: [ERA_NB], nuis: list of (name, size, procs, bins),
    rename: {base name: name used in this card}."""
    w, n = 10, 18
    nb, procs = ERA_NB, ["sig", "WZ", "fakes"]
    cols = [(i, p) for i in range(nb) for p in procs]
    lines = ["# " + header,
             "imax %d" % nb, "jmax 2", "kmax *", DASHES,
             "bin".ljust(n) + "".join(("b%d" % (i + 1)).ljust(w) for i in range(nb)),
             "observation".ljust(n) + "".join(("%g" % o).ljust(w) for o in obs),
             DASHES,
             "bin".ljust(n) + "".join(("b%d" % (i + 1)).ljust(w) for i, _ in cols),
             "process".ljust(n) + "".join(p.ljust(w) for _, p in cols),
             "process".ljust(n) + "".join(str(procs.index(p)).ljust(w) for _, p in cols),
             "rate".ljust(n) + "".join(("%.7g" % yields[p][i]).ljust(w) for i, p in cols),
             DASHES]
    for base, size, nuis_procs, bins in nuis:
        vals = [("%g" % size if (p in nuis_procs and i in bins) else "-") for i, p in cols]
        lines.append((rename.get(base, base) + " lnN ").ljust(n)
                     + "".join(v.ljust(w) for v in vals))
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def era_yields(era, scale=1.0, fakes_scale=1.0):
    y = {p: [scale * v * ERA_FRAC[era] for v in ERA_YIELDS[p]] for p in ["sig", "WZ", "fakes"]}
    y["fakes"] = [v * fakes_scale for v in y["fakes"]]
    return y


def era_asimov_obs(y):
    return [round(y["WZ"][i] + y["fakes"][i], 3) for i in range(ERA_NB)]


def era_cards(scale=1.0):
    """Write eras/ (or eras_x<scale>/) cards: one per era and scenario, plus the merged hifakes card."""
    era_data_split = [era_split_int(int(round(scale * n))) for n in ERA_DATA]  # [bin][era]
    outdir = "eras" if scale == 1.0 else "eras_x%g" % scale
    os.makedirs(outdir, exist_ok=True)
    for k, era in enumerate(ERA_LIST):
        obs = [era_data_split[i][k] for i in range(ERA_NB)]
        y = era_yields(era, scale)
        out = lambda s: "%s/toy_%s_%s.txt" % (outdir, era, s)
        era_write_card(out("corr"), y, obs, ERA_BASE_NUIS, {},
                       "%s, all nuisances correlated across eras" % era)
        era_write_card(out("wzdecor"), y, obs, ERA_BASE_NUIS, {"wz_xs": "wz_xs_" + era},
                       "%s, wz_xs decorrelated per era" % era)
        era_write_card(out("extrap_corr"), y, obs, ERA_BASE_NUIS + [ERA_EXTRAP], {},
                       "%s, + 30%% WZ extrapolation unc. in b4-b5, correlated" % era)
        era_write_card(out("extrap_decor"), y, obs, ERA_BASE_NUIS + [ERA_EXTRAP],
                       {"wz_extrap": "wz_extrap_" + era},
                       "%s, + 30%% WZ extrapolation unc. in b4-b5, decorrelated" % era)
        yh = era_yields(era, scale, 3.0 if era == "2024" else 1.0)
        era_write_card(out("hifakes"), yh, era_asimov_obs(yh), ERA_BASE_NUIS, {},
                       "%s, 2024 has 3x fakes (expected-only demo)" % era)

    merged = {p: [0.0] * ERA_NB for p in ["sig", "WZ", "fakes"]}
    for era in ERA_LIST:
        yh = era_yields(era, scale, 3.0 if era == "2024" else 1.0)
        for p in merged:
            merged[p] = [a + b for a, b in zip(merged[p], yh[p])]
    era_write_card(outdir + "/toy_merged_hifakes.txt", merged, era_asimov_obs(merged),
                   ERA_BASE_NUIS, {}, "all eras merged, 2024 has 3x fakes (expected-only demo)")

    # Effective prior uncertainty on the total WZ yield: correlated eras add
    # linearly (10%), independent eras add in quadrature: 10% * sqrt(sum f_i^2).
    eff = 10.0 * sum(f * f for f in ERA_FRAC.values()) ** 0.5
    print("Era fractions: " + ", ".join("%s %.1f%%" % (e, 100 * ERA_FRAC[e]) for e in ERA_LIST))
    print("Effective prior on total WZ: correlated 10.0%%, decorrelated %.1f%% "
          "(equal eras would give %.1f%%)" % (eff, 10.0 / len(ERA_LIST) ** 0.5))


# ---- tug of war: pseudo-data with the fakes nuisance pulled per era (demo 2) ----

TUG_SHIFT_SIGMA = {"2022": +1.5, "2023": 0.0, "2024": -1.5}
TUG_FAKES_LNN = 1.30
TUG_CARD = """# {era}: pseudo-data with fakes shifted {shift:+.1f} sigma, 10x lumi; {desc}
imax 1
jmax 2
kmax *
------------------------------------------------------------
shapes * * shapes_{era}.root $PROCESS
------------------------------------------------------------
bin          SR
observation  -1
------------------------------------------------------------
bin          SR     SR     SR
process      sig    WZ     fakes
process      0      1      2
rate         -1     -1     -1
------------------------------------------------------------
lumi      lnN  1.02   1.02   -
wz_xs     lnN  -      1.10   -
{fname:<9} lnN  -      -      1.30
"""


def tug_cards(scale=10.0):
    """Shape cards and pseudo-data for the tug-of-war demo, at `scale` x luminosity."""
    ROOT.gROOT.SetBatch(True)
    seed = int(os.environ.get("TUG_SEED", 29))  # fixed so the demo reproduces; not chosen by a seed scan
    rng = ROOT.TRandom3(seed)
    os.makedirs("tug", exist_ok=True)
    for era in ERA_LIST:
        y = era_yields(era, scale)
        shift = TUG_FAKES_LNN ** TUG_SHIFT_SIGMA[era]
        mean = [y["WZ"][i] + shift * y["fakes"][i] for i in range(ERA_NB)]
        obs = [rng.Poisson(m) for m in mean]
        print("%s: fakes x%.2f -> mean %s -> pseudo-data %s"
              % (era, shift, [round(m, 1) for m in mean], obs))

        f = ROOT.TFile("tug/shapes_%s.root" % era, "RECREATE")
        for name, vals in [("sig", y["sig"]), ("WZ", y["WZ"]), ("fakes", y["fakes"]),
                           ("data_obs", obs)]:
            shape_histo(name, vals).Write()
        f.Close()

        for tag, fname, desc in [("corr", "fakes", "shared fakes nuisance"),
                                 ("decor", "fakes_" + era, "fakes per era")]:
            with open("tug/toy_%s_%s.txt" % (era, tag), "w", encoding="utf-8") as out:
                out.write(TUG_CARD.format(era=era, shift=TUG_SHIFT_SIGMA[era], desc=desc, fname=fname))


def parse_card(path):
    """Process names and {nuisance: (type, [value per process])} of a single-bin card."""
    procs, nuis = None, {}
    for line in open(path, encoding="utf-8"):
        f = line.split()
        if not f or f[0].startswith("#"):
            continue
        if f[0] == "process" and procs is None:
            procs = f[1:]
        elif len(f) > 2 and f[1] in ("lnN", "shape") and procs:
            nuis[f[0]] = (f[1], f[2:2 + len(procs)])
    return procs, nuis


# ---- stacked era card: the recipe for the stacking demo (demo 14) ----

def stack_inputs(scale=1.0):
    """Per-era inputs for the stacking demo: one shape card + ROOT file per era.

The toy (5 bins: sig, WZ, fakes) split into 2022 / 2023 / 2024 by luminosity.
Uncertainties, chosen to cover the cases you meet when merging:

  correlated across eras, same size     lumi_corr 1.0%, wz_xs 10%, fakes 30%   (lnN)
  correlated across eras, size differs  jes (shape on sig+WZ):
                                          2022: 2, 3, 4, 6, 8 %   (b1..b5)
                                          2023: 3, 4, 5, 8, 10 %
                                          2024: 4, 5, 7, 10, 14 %
  anti-correlated across eras           trig_eff (lnN on sig+WZ): +2% in 2022 and 2023,
                                        -3% in 2024 (same source, opposite sign; kappa < 1)
  one era only (uncorrelated)           lumi_2022 1.5%, lumi_2023 1.5%, lumi_2024 2.0% (lnN)
                                        wz_extrap_<era>: 30% on WZ in b4-b5 (shape),
                                          e.g. a CR->SR extrapolation from a separate
                                          control region per era
The naming carries the correlation: a name ending in _<era> exists in one era only.
All sizes are illustrative.

MC statistical errors: sqrt(w * y) with weights sig 0.05, WZ 0.2, fakes 0.5.

Run it through its run_NN_*.py file (see docs/slide_map.md).
  scale 1 (default): data = toy data split per era      -> stack/x1/
  scale N:           yields x N, data = Asimov (bkg)    -> stack/xN/"""
    ROOT.gROOT.SetBatch(True)
    ROOT.TH1.AddDirectory(False)
    OUT = "stack/x%g" % scale
    LUMI = {"2022": 34.7, "2023": 27.8, "2024": 109.0}
    ERAS = list(LUMI)
    FRAC = {e: LUMI[e] / sum(LUMI.values()) for e in ERAS}
    NB = 5
    YIELDS = {"sig": [1, 2, 4, 8, 10], "WZ": [120, 60, 25, 10, 4], "fakes": [40, 20, 8, 3, 1]}
    WEIGHT = {"sig": 0.05, "WZ": 0.2, "fakes": 0.5}
    DATA = [160, 80, 35, 14, 6]
    JES = {"2022": [0.02, 0.03, 0.04, 0.06, 0.08], "2023": [0.03, 0.04, 0.05, 0.08, 0.10],
           "2024": [0.04, 0.05, 0.07, 0.10, 0.14]}
    LUMI_ERA = {"2022": 1.015, "2023": 1.015, "2024": 1.020}
    TRIG = {"2022": 1.02, "2023": 1.02, "2024": 0.97}
    EXTRAP = 0.30


    def split_int(n):
        raw = [n * FRAC[e] for e in ERAS]
        out = [int(x) for x in raw]
        order = sorted(range(len(ERAS)), key=lambda k: raw[k] - out[k], reverse=True)
        for k in order[: n - sum(out)]:
            out[k] += 1
        return out


    def hist(name, vals, errs=None):
        return shape_histo(name, vals, errors=errs or [0.0] * len(vals))


    def main():
        os.makedirs(OUT, exist_ok=True)
        split = [split_int(n) for n in DATA]
        for k, e in enumerate(ERAS):
            y = {p: [scale * v * FRAC[e] for v in YIELDS[p]] for p in PROCS}
            f = ROOT.TFile("%s/shapes_%s.root" % (OUT, e), "RECREATE")
            for p in PROCS:
                hist(p, y[p], [math.sqrt(WEIGHT[p] * v) for v in y[p]]).Write()
            for p in ["sig", "WZ"]:
                hist(p + "_jesUp", [v * (1 + d) for v, d in zip(y[p], JES[e])]).Write()
                hist(p + "_jesDown", [v * (1 - d) for v, d in zip(y[p], JES[e])]).Write()
            ex = [EXTRAP if i >= 3 else 0.0 for i in range(NB)]
            hist("WZ_wz_extrap_%sUp" % e, [v * (1 + d) for v, d in zip(y["WZ"], ex)]).Write()
            hist("WZ_wz_extrap_%sDown" % e, [v * (1 - d) for v, d in zip(y["WZ"], ex)]).Write()
            data = ([split[i][k] for i in range(NB)] if scale == 1.0
                    else [y["WZ"][i] + y["fakes"][i] for i in range(NB)])
            hist("data_obs", data).Write()
            f.Close()
            card = [
                "# era %s" % e, "imax 1", "jmax 2", "kmax *", "-" * 60,
                "shapes * * shapes_%s.root $PROCESS $PROCESS_$SYSTEMATIC" % e, "-" * 60,
                "bin          SR", "observation  -1", "-" * 60,
                "bin                  SR      SR      SR",
                "process              sig     WZ      fakes",
                "process              0       1       2",
                "rate                 -1      -1      -1", "-" * 60,
                "lumi_corr       lnN  1.01    1.01    -",
                "lumi_%s       lnN  %g   %g   -" % (e, LUMI_ERA[e], LUMI_ERA[e]),
                "trig_eff        lnN  %g    %g    -" % (TRIG[e], TRIG[e]),
                "wz_xs           lnN  -       1.10    -",
                "fakes           lnN  -       -       1.30",
                "jes             shape 1      1       -",
                "wz_extrap_%s  shape -      1       -" % e,
                "* autoMCStats 10 0 1",
            ]
            with open("%s/card_%s.txt" % (OUT, e), "w", encoding="utf-8") as out:
                out.write("\n".join(card) + "\n")
        print("Wrote per-era inputs to %s (scale %g)" % (OUT, scale))

    main()


def stack_card(d, naive=False):
    """Stack per-era shape cards into ONE card, keeping every correlation right.

The recipe (the name of a nuisance is its correlation):
  1. Nominal templates and data: add the eras.
     TH1::Add also adds the MC statistical errors in quadrature, so
     autoMCStats on the merged card sees the right MC precision.
  2. Shape nuisance present in all eras with the SAME name (correlated):
     merged Up = sum over eras of that era's Up template.
  3. Shape nuisance present in ONE era only (e.g. name ends in _2024):
     keep it as its own nuisance, same name, and shift only that era:
     merged Up = merged nominal - nominal_era + Up_era.
  4. lnN with the same name in several eras (correlated or anti-correlated):
     kappa_stacked - 1 = sum_e (y_e / y_tot) * (kappa_e - 1)   (per process).
     Signs are kept: kappa < 1 in one era (anti-correlated) partly cancels.
     lnN in one era only: kappa_stacked = 1 + (y_era / y_total) * (kappa_era - 1).
     This is exact when each era is the same fraction of the process in every
     bin. If not, turn the lnN into a shape (Up = nominal * kappa) first.

--naive does what is easy to get wrong: era-only nuisances are renamed to one
common name and summed as if correlated (lumi_<era> -> lumi_era,
wz_extrap_<era> -> wz_extrap).

Run it through its run_NN_*.py file (see docs/slide_map.md).
  reads  <dir>/card_<era>.txt and <dir>/shapes_<era>.root
  writes <dir>/card_stacked[_naive].txt and shapes_stacked[_naive].root
Assumes single-bin shape cards like the ones from cards.stack_inputs()."""
    ROOT.gROOT.SetBatch(True)
    ROOT.TH1.AddDirectory(False)
    ERAS = ["2022", "2023", "2024"]




    def common(name, naive):
        """Name in the merged card. Naive: drop the era tag (wrongly correlates)."""
        return re.sub(r"_(%s)$" % "|".join(ERAS), "_era" if name.startswith("lumi") else "", name) \
            if naive else name


    def main():
        tag = "stacked_naive" if naive else "stacked"
        cards = {e: parse_card("%s/card_%s.txt" % (d, e)) for e in ERAS}
        procs = cards[ERAS[0]][0]
        files = {e: ROOT.TFile.Open("%s/shapes_%s.root" % (d, e)) for e in ERAS}
        get = lambda e, n: files[e].Get(n)

        nom = {p: get(ERAS[0], p).Clone(p) for p in procs}
        for p in procs:
            for e in ERAS[1:]:
                nom[p].Add(get(e, p))
        data = get(ERAS[0], "data_obs").Clone("data_obs")
        for e in ERAS[1:]:
            data.Add(get(e, "data_obs"))
        yld = {(e, p): get(e, p).Integral() for e in ERAS for p in procs}
        ytot = {p: nom[p].Integral() for p in procs}

        # merged nuisances: name -> {"type", "eras": set, per-era values}
        merged = {}
        for e in ERAS:
            for n, (typ, vals) in cards[e][1].items():
                m = merged.setdefault(common(n, naive), {"type": typ, "src": {}})
                m["src"][e] = (n, vals)

        out_hists = list(nom.values()) + [data]
        lines = []
        for mname, m in merged.items():
            if m["type"] == "lnN":
                row = []
                for k, p in enumerate(procs):
                    acc, used = 0.0, False
                    for e, (n, vals) in m["src"].items():
                        if vals[k] != "-":
                            used = True
                            acc += yld[(e, p)] * (float(vals[k]) - 1.0)
                    row.append("%.5g" % (1.0 + acc / ytot[p]) if used else "-")
                lines.append("%-16s lnN   " % mname + "  ".join("%-8s" % v for v in row))
            else:
                row = []
                for k, p in enumerate(procs):
                    if all(vals[k] == "-" for (_, vals) in m["src"].values()):
                        row.append("-")
                        continue
                    row.append("1")
                    for side in ["Up", "Down"]:
                        h = nom[p].Clone("%s_%s%s" % (p, mname, side))
                        for e, (n, vals) in m["src"].items():
                            if vals[k] == "-":
                                continue
                            # replace this era's nominal by its shifted template
                            h.Add(get(e, p), -1.0)
                            h.Add(get(e, "%s_%s%s" % (p, n, side)), 1.0)
                        for b in range(1, h.GetNbinsX() + 1):
                            h.SetBinError(b, 0.0)
                        out_hists.append(h)
                lines.append("%-16s shape " % mname + "  ".join("%-8s" % v for v in row))

        fo = ROOT.TFile("%s/shapes_%s.root" % (d, tag), "RECREATE")
        for h in out_hists:
            h.Write()
        fo.Close()
        card = ["# %s: eras %s stacked by stack_eras.py%s" % (tag, "+".join(ERAS), " (NAIVE)" if naive else ""),
                "imax 1", "jmax %d" % (len(procs) - 1), "kmax *", "-" * 60,
                "shapes * * shapes_%s.root $PROCESS $PROCESS_$SYSTEMATIC" % tag, "-" * 60,
                "bin          SR", "observation  -1", "-" * 60,
                "bin                    " + "  ".join("%-8s" % "SR" for _ in procs),
                "process                " + "  ".join("%-8s" % p for p in procs),
                "process                " + "  ".join("%-8d" % i for i in range(len(procs))),
                "rate                   " + "  ".join("%-8s" % "-1" for _ in procs), "-" * 60] \
            + lines + ["* autoMCStats 10 0 1"]
        with open("%s/card_%s.txt" % (d, tag), "w", encoding="utf-8") as f:
            f.write("\n".join(card) + "\n")
        print("Wrote %s/card_%s.txt" % (d, tag))

    main()


# ---- stacking backup: generic systematics A-F, shape and lnN, per era (backup slides) ----

STACK_MC_WEIGHT = {"sig": 0.05, "WZ": 0.2, "fakes": 0.5}   # MC stat error: sqrt(w * y) per bin
STACK_TILT = [0.0, 0.25, 0.5, 0.75, 1.0]                   # shape of a tilt, 0 in b1 -> 1 in b5
# lnN: name -> (process, {era: kappa})
STACK_LNN = {
    "A": ("WZ", {"2022": 1.10, "2023": 1.10, "2024": 1.10}),
    "C": ("WZ", {"2022": 1.15, "2023": 1.15, "2024": 0.85}),
    "F": ("fakes", {"2022": 1.30, "2023": 1.30, "2024": 1.30}),
}
# shape: name -> (process, {era: relative shift per bin of the Up template})
STACK_SHAPE = {
    "B": ("WZ", {"2022": [0.20 * t for t in STACK_TILT], "2023": [0.25 * t for t in STACK_TILT],
                 "2024": [0.30 * t for t in STACK_TILT]}),
    "D": ("fakes", {"2022": [0.20 * t for t in STACK_TILT], "2023": [0.20 * t for t in STACK_TILT],
                    "2024": [-0.20 * t for t in STACK_TILT]}),
}
for _e in ERA_LIST:   # single-era: E_<era>
    STACK_SHAPE["E_" + _e] = ("WZ", {_e: [0, 0, 0, 0.20, 0.20]})


def stack_systs_inputs(scale=1.0):
    """Per-era shape cards and ROOT files with the generic systematics A-F.

    scale 1: the toy data split per era. scale N: yields x N, data = background Asimov.
    Writes stack_systs/x<scale>/.
    """
    ROOT.TH1.AddDirectory(False)   # histograms stay with the code, not the open file

    out = "stack_systs/x%g" % scale
    os.makedirs(out, exist_ok=True)
    zeros = [0.0] * ERA_NB                  # shape histograms without bin errors
    split = [era_split_int(n) for n in ERA_DATA]
    for k, e in enumerate(ERA_LIST):
        y = {p: [scale * v * ERA_FRAC[e] for v in ERA_YIELDS[p]] for p in ["sig", "WZ", "fakes"]}
        f = ROOT.TFile("%s/shapes_%s.root" % (out, e), "RECREATE")
        for p in y:
            shape_histo(p, y[p], errors=[math.sqrt(STACK_MC_WEIGHT[p] * v) for v in y[p]]).Write()
        rows = []
        for name, (p, per_era) in STACK_SHAPE.items():
            if e not in per_era:
                continue
            d = per_era[e]
            shape_histo("%s_%sUp" % (p, name), [v * (1 + s) for v, s in zip(y[p], d)],
                        errors=zeros).Write()
            shape_histo("%s_%sDown" % (p, name), [v * (1 - s) for v, s in zip(y[p], d)],
                        errors=zeros).Write()
            rows.append("%-8s shape  " % name
                        + "  ".join("%-6s" % ("1" if q == p else "-") for q in ["sig", "WZ", "fakes"]))
        data = ([split[i][k] for i in range(ERA_NB)] if scale == 1.0
                else [y["WZ"][i] + y["fakes"][i] for i in range(ERA_NB)])
        shape_histo("data_obs", data, errors=zeros).Write()
        f.Close()
        lnn = ["%-8s lnN    " % name
               + "  ".join("%-6s" % ("%g" % kap[e] if q == p else "-") for q in ["sig", "WZ", "fakes"])
               for name, (p, kap) in STACK_LNN.items()]
        card = [
            "# era %s" % e, "imax 1", "jmax 2", "kmax *", DASHES,
            "shapes * * shapes_%s.root $PROCESS $PROCESS_$SYSTEMATIC" % e, DASHES,
            "bin          SR", "observation  -1", DASHES,
            "bin                SR      SR      SR",
            "process            sig     WZ      fakes",
            "process            0       1       2",
            "rate               -1      -1      -1", DASHES,
        ] + lnn + rows + ["* autoMCStats 10 0 1"]
        with open("%s/card_%s.txt" % (out, e), "w", encoding="utf-8") as fh:
            fh.write("\n".join(card) + "\n")
    print("Wrote per-era inputs to %s (scale %g)" % (out, scale))


def stack_systs_card(d):
    """Merge the per-era cards in d into one card (correlations kept by name)."""
    ROOT.TH1.AddDirectory(False)   # histograms stay with the code, not the open file

    cards = {e: parse_card("%s/card_%s.txt" % (d, e)) for e in ERA_LIST}
    procs = cards[ERA_LIST[0]][0]
    files = {e: ROOT.TFile.Open("%s/shapes_%s.root" % (d, e)) for e in ERA_LIST}

    def get(e, n):
        return files[e].Get(n)

    nom = {p: get(ERA_LIST[0], p).Clone(p) for p in procs}
    for p in procs:
        for e in ERA_LIST[1:]:
            nom[p].Add(get(e, p))
    data = get(ERA_LIST[0], "data_obs").Clone("data_obs")
    for e in ERA_LIST[1:]:
        data.Add(get(e, "data_obs"))
    yld = {(e, p): get(e, p).Integral() for e in ERA_LIST for p in procs}
    ytot = {p: nom[p].Integral() for p in procs}

    # merged nuisances: name -> {"type", "src": {era: (name, values)}}
    merged = {}
    for e in ERA_LIST:
        for n, (typ, vals) in cards[e][1].items():
            m = merged.setdefault(n, {"type": typ, "src": {}})
            m["src"][e] = (n, vals)

    out_hists = list(nom.values()) + [data]
    lines = []
    for mname, m in merged.items():
        if m["type"] == "lnN":
            row = []
            for k, p in enumerate(procs):
                acc, used = 0.0, False
                for e, (n, vals) in m["src"].items():
                    if vals[k] != "-":
                        used = True
                        acc += yld[(e, p)] * (float(vals[k]) - 1.0)
                row.append("%.5g" % (1.0 + acc / ytot[p]) if used else "-")
            lines.append("%-16s lnN   " % mname + "  ".join("%-8s" % v for v in row))
        else:
            row = []
            for k, p in enumerate(procs):
                if all(vals[k] == "-" for (_, vals) in m["src"].values()):
                    row.append("-")
                    continue
                row.append("1")
                for side in ["Up", "Down"]:
                    h = nom[p].Clone("%s_%s%s" % (p, mname, side))
                    for e, (n, vals) in m["src"].items():
                        if vals[k] == "-":
                            continue
                        # replace this era's nominal by its shifted template
                        h.Add(get(e, p), -1.0)
                        h.Add(get(e, "%s_%s%s" % (p, n, side)), 1.0)
                    for b in range(1, h.GetNbinsX() + 1):
                        h.SetBinError(b, 0.0)
                    out_hists.append(h)
            lines.append("%-16s shape " % mname + "  ".join("%-8s" % v for v in row))

    tag = "stacked"
    fo = ROOT.TFile("%s/shapes_%s.root" % (d, tag), "RECREATE")
    for h in out_hists:
        h.Write()
    fo.Close()
    card = ["# %s: eras %s stacked by stack_eras.py" % (tag, "+".join(ERA_LIST)),
            "imax 1", "jmax %d" % (len(procs) - 1), "kmax *", DASHES,
            "shapes * * shapes_%s.root $PROCESS $PROCESS_$SYSTEMATIC" % tag, DASHES,
            "bin          SR", "observation  -1", DASHES,
            "bin                    " + "  ".join("%-8s" % "SR" for _ in procs),
            "process                " + "  ".join("%-8s" % p for p in procs),
            "process                " + "  ".join("%-8d" % i for i in range(len(procs))),
            "rate                   " + "  ".join("%-8s" % "-1" for _ in procs), DASHES] \
        + lines + ["* autoMCStats 10 0 1"]
    with open("%s/card_%s.txt" % (d, tag), "w", encoding="utf-8") as f:
        f.write("\n".join(card) + "\n")
    print("Wrote %s/card_%s.txt" % (d, tag))


# ---- empty-bin backup: what Combine does with an empty bin (11-bin shape card) ----

EMPTYTEST_CASES = {
    "A_data0": dict(bkg7=None, data7=0),     # data empty, prediction fine
    "B_both0": dict(bkg7=0.0, data7=0),      # bkg MC empty AND data empty
    "C_bkg0": dict(bkg7=0.0, data7=3),       # bkg MC empty, data has events
}
EMPTYTEST_CARD = """imax 1
jmax 1
kmax *
---
shapes * * %s.root $PROCESS
---
bin SR
observation -1
---
bin SR SR
process sig bkg
process 0 1
rate -1 -1
---
bkg_norm lnN - 1.10
* autoMCStats 10 0 1
"""


def emptytest_cards():
    """Card and ROOT file per case, with bin 7 of the background or data emptied."""
    ROOT.TH1.AddDirectory(False)   # histograms stay with the code, not the open file

    nb = 11
    bkg = [100 * math.exp(-0.35 * i) for i in range(nb)]
    sig = [0.5 + 3 * math.exp(-0.5 * ((i - 7) / 1.5) ** 2) for i in range(nb)]
    os.makedirs("emptytest", exist_ok=True)
    for case, o in EMPTYTEST_CASES.items():
        b = list(bkg)
        d = [round(x) for x in bkg]
        if o["bkg7"] is not None:
            b[6] = o["bkg7"]
        d[6] = o["data7"]
        f = ROOT.TFile("emptytest/%s.root" % case, "RECREATE")
        for name, vals, w in [("bkg", b, 0.2), ("sig", sig, 0.05)]:
            shape_histo(name, vals, errors=[math.sqrt(w * x) for x in vals]).Write()
        shape_histo("data_obs", d).Write()
        f.Close()
        with open("emptytest/%s.txt" % case, "w", encoding="utf-8") as fh:
            fh.write(EMPTYTEST_CARD % case)
        print(case, "bkg bin7 =", b[6], " data bin7 =", d[6], " sig bin7 = %.2f" % sig[6])


# ---- autoMCStats with an MC error larger than the yield (backup demo B3) ----

MCCAP_ERR = 4.00                          # as-is MC error on the b5 fakes (yield 1.00)
MCCAP_B5_FAKES_ERR = {"as-is": MCCAP_ERR, "capped": 1.00, "goodmc": math.sqrt(0.5 * 1.0)}
MCCAP_CARD = """# MC error > yield demo: {v}
imax 1
jmax 2
kmax *
------------------------------------------------------------
shapes * * shapes_{v}.root $PROCESS
------------------------------------------------------------
bin          SR
observation  -1
------------------------------------------------------------
bin          SR     SR     SR
process      sig    WZ     fakes
process      0      1      2
rate         -1     -1     -1
------------------------------------------------------------
lumi    lnN  1.02   1.02   -
wz_xs   lnN  -      1.10   -
fakes   lnN  -      -      1.30
* autoMCStats 20 0 1
"""


def cap_errors(h):
    """The recipe: never let a bin error exceed |content|. Returns the capped bins."""
    out = []
    for i in range(1, h.GetNbinsX() + 1):
        n, e = abs(h.GetBinContent(i)), h.GetBinError(i)
        if e > n:
            out.append((i, h.GetBinContent(i), e))
            h.SetBinError(i, n)
    return out


def mccap_cards():
    """Shape cards and ROOT files for the three versions of the b5 fakes error."""
    ROOT.TH1.AddDirectory(False)
    os.makedirs("mccap", exist_ok=True)
    for v, err5 in MCCAP_B5_FAKES_ERR.items():
        f = ROOT.TFile("mccap/shapes_%s.root" % v, "RECREATE")
        for p, ys in ERA_YIELDS.items():
            h = shape_histo(p, ys, errors=[math.sqrt(STACK_MC_WEIGHT[p] * y) for y in ys])
            if p == "fakes" and v != "goodmc":
                h.SetBinError(5, MCCAP_ERR)           # negative-weight sample
                if v == "capped":
                    for i, c, e in cap_errors(h):
                        print("capped: fakes b%d  %.2f +- %.2f -> +- %.2f" % (i, c, e, abs(c)))
            h.Write()
        shape_histo("data_obs", ERA_DATA).Write()
        f.Close()
        with open("mccap/card_%s.txt" % v, "w", encoding="utf-8") as out:
            out.write(MCCAP_CARD.format(v=v))
    for v, e in MCCAP_B5_FAKES_ERR.items():
        print("%-7s fakes b5 = 1.00 +- %.2f  (%.0f%%, N_eff = %.2f)" % (v, e, 100 * e, 1 / e ** 2))
