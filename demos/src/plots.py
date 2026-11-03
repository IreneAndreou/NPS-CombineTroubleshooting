"""Figures for the demos. Each function writes plots/<name>.pdf and .png (plots/ is
relative to the working directory, the repo root when run through with_combine.sh)."""
import array
import math
import os

import ROOT

from src import cards, combine_outputs, rootutil


@rootutil.isolated
def bonly_postfit():
    """Background-only vs signal+background post-fit (slide 16).

Data contain a real signal (r = 1). Three panels:
  left:   post-fit of the background-only fit (fit_b)
  middle: post-fit of the signal+background fit (fit_s)
  right:  nuisance pulls in the two fits (prior units)
A nuisance pulled in one fit but not the other is absorbing the signal.

Run it through its run_NN_*.py file (see docs/slide_map.md)."""
    rootutil.setup(ticks=True, end_error=5)
    FONT = rootutil.FONT
    NB = 5
    COL = {"WZ": ROOT.TColor.GetColor("#e8a33d"), "fakes": ROOT.TColor.GetColor("#8c8c8c"),
           "sig": ROOT.TColor.GetColor("#7b3294")}
    BLUE = ROOT.TColor.GetColor("#2c7bb6")
    RED = ROOT.TColor.GetColor("#c0392b")
    NUIS = ["fakes_closure", "fakes", "wz_xs", "lumi"]

    f = ROOT.TFile.Open("fitDiagnostics.bonly.root")


    def h(path, name):
        src = f.Get(path)
        out = ROOT.TH1F(name, "", NB, 0, NB)
        if src:
            for i in range(1, NB + 1):
                out.SetBinContent(i, src.GetBinContent(i))
        return out


    data_src = f.Get("shapes_prefit/SR/data")
    data = [data_src.GetPointY(i) for i in range(NB)]
    pull_values = {}
    for fit in ["fit_b", "fit_s"]:
        p = f.Get(fit).floatParsFinal()
        pull_values[fit] = [(p.find(n).getVal(), p.find(n).getError()) for n in NUIS]
        if fit == "fit_s":
            r = p.find("r")
            rval = (r.getVal(), r.getError())

    c = ROOT.TCanvas("c", "", 1800, 620)
    widths = [0.36, 0.36, 0.28]
    x0 = 0.0
    keep = []


    def axis_style(hh, ytitle, xlabels):
        for ax in [hh.GetXaxis(), hh.GetYaxis()]:
            ax.SetLabelFont(FONT)
            ax.SetLabelSize(21)
            ax.SetTitleFont(FONT)
            ax.SetTitleSize(22)
        hh.GetYaxis().SetTitle(ytitle)
        hh.GetYaxis().SetTitleOffset(1.6)
        for i, lab in enumerate(xlabels):
            hh.GetXaxis().SetBinLabel(i + 1, lab)
        hh.GetXaxis().SetLabelSize(24)


    for k, (fit, title) in enumerate([("fit_b", "background-only fit"),
                                      ("fit_s", "signal + background fit")]):
        c.cd()
        pad = ROOT.TPad("p%d" % k, "", x0, 0, x0 + widths[k], 1)
        x0 += widths[k]
        pad.SetLeftMargin(0.15)
        pad.SetRightMargin(0.03)
        pad.SetTopMargin(0.10)
        pad.SetBottomMargin(0.12)
        pad.SetLogy()
        pad.Draw()
        pad.cd()
        d = "shapes_" + fit
        wz, fk, sg = h(d + "/SR/WZ", "wz%d" % k), h(d + "/SR/fakes", "fk%d" % k), h(d + "/SR/total_signal", "sg%d" % k)
        fr = ROOT.TH1F("fr%d" % k, "", NB, 0, NB)
        fr.SetMinimum(20)
        fr.SetMaximum(3e4)
        axis_style(fr, "Events", ["b%d" % (i + 1) for i in range(NB)])
        fr.Draw("axis")
        # stack by hand: sig on top of WZ on top of fakes
        l1 = fk.Clone("l1_%d" % k)
        l2 = fk.Clone("l2_%d" % k)
        l2.Add(wz)
        l3 = l2.Clone("l3_%d" % k)
        l3.Add(sg)
        for hh, col in [(l3, COL["sig"]), (l2, COL["WZ"]), (l1, COL["fakes"])]:
            hh.SetFillColor(col)
            hh.SetLineColor(ROOT.kBlack)
            hh.Draw("hist same")
        gd = ROOT.TGraph()
        for i, n in enumerate(data):
            gd.SetPoint(i, i + 0.5, n)
        gd.SetMarkerStyle(20)
        gd.SetMarkerSize(1.6)
        gd.Draw("p same")
        leg = ROOT.TLegend(0.45, 0.62, 0.95, 0.88)
        leg.SetBorderSize(0)
        leg.SetFillStyle(0)
        leg.SetTextFont(FONT)
        leg.SetTextSize(19)
        leg.AddEntry(gd, "Data (contains signal)", "p")
        if fit == "fit_s":
            leg.AddEntry(l3, "Signal, r = %.2f #pm %.2f" % rval, "f")
        leg.AddEntry(l2, "WZ (post-fit)", "f")
        leg.AddEntry(l1, "Fakes (post-fit)", "f")
        leg.Draw()
        t = ROOT.TLatex()
        t.SetNDC()
        t.SetTextFont(FONT)
        t.SetTextSize(22)
        t.DrawLatex(0.15, 0.92, "#bf{Toy} #it{%s}" % title)
        if fit == "fit_b":
            n = ROOT.TLatex()
            n.SetTextFont(FONT)
            n.SetTextSize(19)
            n.SetTextAlign(22)
            n.SetTextColor(RED)
            n.DrawLatex(3.5, 600, "fakes inflated")
            n.DrawLatex(3.5, 420, "to eat the excess")
            keep.append(n)
        pad.RedrawAxis()
        keep += [pad, fr, l1, l2, l3, gd, leg, t]

    # ---- pulls ----
    c.cd()
    pad = ROOT.TPad("pp", "", x0, 0, 1, 1)
    pad.SetLeftMargin(0.30)
    pad.SetRightMargin(0.04)
    pad.SetTopMargin(0.10)
    pad.SetBottomMargin(0.12)
    pad.Draw()
    pad.cd()
    m = len(NUIS)
    fr = ROOT.TH2F("frp", "", 10, -1.5, 4, m, 0, m)
    for i, n in enumerate(NUIS):
        fr.GetYaxis().SetBinLabel(m - i, n)
    for ax in [fr.GetXaxis(), fr.GetYaxis()]:
        ax.SetLabelFont(FONT)
        ax.SetLabelSize(21)
        ax.SetTitleFont(FONT)
        ax.SetTitleSize(22)
    fr.GetYaxis().SetTickLength(0)
    fr.GetXaxis().SetTitle("Post-fit #theta (prior units)")
    fr.GetXaxis().SetTitleOffset(1.2)
    fr.Draw()
    band = ROOT.TBox(-1, 0, 1, m)
    band.SetFillColorAlpha(ROOT.kGray, 0.4)
    band.Draw()
    zero = ROOT.TLine(0, 0, 0, m)
    zero.SetLineStyle(2)
    zero.Draw()
    leg = ROOT.TLegend(0.62, 0.14, 0.97, 0.30)
    leg.SetNColumns(1)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextFont(FONT)
    leg.SetTextSize(19)
    for fit, col, mk, off, lab in [("fit_b", RED, 21, +0.15, "b-only"), ("fit_s", BLUE, 20, -0.15, "s+b")]:
        g = ROOT.TGraphAsymmErrors()
        for i, (v, e) in enumerate(pull_values[fit]):
            g.SetPoint(i, v, m - i - 0.5 + off)
            g.SetPointError(i, e, e, 0, 0)
        g.SetMarkerStyle(mk)
        g.SetMarkerSize(1.6)
        g.SetMarkerColor(col)
        g.SetLineColor(col)
        g.SetLineWidth(3)
        g.Draw("p same")
        leg.AddEntry(g, lab, "pe")
        keep.append(g)
    leg.Draw()
    t = ROOT.TLatex()
    t.SetNDC()
    t.SetTextFont(FONT)
    t.SetTextSize(22)
    t.DrawLatex(0.30, 0.92, "#bf{Nuisance pulls}")
    pad.RedrawAxis()
    keep += [pad, fr, band, zero, leg, t]

    rootutil.save(c, "bonly_postfit")


@rootutil.isolated
def empty_bins():
    """Empty-bin demo plot (slide 12): expected and observed limit (left) and
significance (right) vs. the background floor put in the empty bin b5.
Dashed lines: the fix (b4+b5 merged, proper background estimate).

Reads higgsCombine.empty_<tag>.{exp,obs}.AsymptoticLimits... and
empty/sig_<tag>.log from run_06_emptybins.py.
Run it through its run_NN_*.py file (see docs/slide_map.md)."""
    rootutil.setup(ticks=True)
    FLOORS = [0.001, 0.01, 0.1, 0.5, 1, 2, 5]
    FONT = rootutil.FONT
    BLUE = ROOT.TColor.GetColor("#2c7bb6")
    RED = ROOT.TColor.GetColor("#c0392b")


    def limit(tag, kind, q):
        f = ROOT.TFile.Open("higgsCombine.empty_%s.%s.AsymptoticLimits.mH120.root" % (tag, kind))
        out = {round(e.quantileExpected, 3): e.limit for e in f.Get("limit")}
        f.Close()
        return out[q]


    def signif(tag):
        for line in open("empty/sig_%s.log" % tag, encoding="utf-8"):
            if line.startswith("Significance:"):
                return float(line.split()[1])


    tags = ["floor_%g" % f for f in FLOORS]
    exp = [limit(t, "exp", 0.5) for t in tags]
    obs = [limit(t, "obs", -1.0) for t in tags]
    sig = [signif(t) for t in tags]
    m_exp, m_obs, m_sig = limit("merged", "exp", 0.5), limit("merged", "obs", -1.0), signif("merged")
    for f, e, o, z in zip(FLOORS, exp, obs, sig):
        print("floor %-6g exp %.3f  obs %.3f  significance %.1f" % (f, e, o, z))
    print("merged      exp %.3f  obs %.3f  significance %.1f" % (m_exp, m_obs, m_sig))


    def frame(pad, name, ymin, ymax, ytitle):
        pad.cd()
        pad.SetLogx()
        pad.SetLeftMargin(0.15)
        pad.SetRightMargin(0.04)
        pad.SetTopMargin(0.10)
        pad.SetBottomMargin(0.15)
        h = ROOT.TH1F(name, "", 10, 5e-4, 10)
        h.SetMinimum(ymin)
        h.SetMaximum(ymax)
        for ax in [h.GetXaxis(), h.GetYaxis()]:
            ax.SetLabelFont(FONT)
            ax.SetLabelSize(22)
            ax.SetTitleFont(FONT)
            ax.SetTitleSize(24)
        h.GetXaxis().SetTitle("Background put in the empty bin b5 (events)")
        h.GetXaxis().SetTitleOffset(1.3)
        h.GetYaxis().SetTitle(ytitle)
        h.GetYaxis().SetTitleOffset(1.5)
        h.Draw("axis")
        return h


    def graph(xs, ys, color, style):
        g = ROOT.TGraph(len(xs))
        for i, (x, y) in enumerate(zip(xs, ys)):
            g.SetPoint(i, x, y)
        g.SetLineColor(color)
        g.SetMarkerColor(color)
        g.SetMarkerStyle(style)
        g.SetMarkerSize(1.6)
        g.SetLineWidth(3)
        return g


    def hline(y, color):
        l = ROOT.TLine(5e-4, y, 10, y)
        l.SetLineColor(color)
        l.SetLineStyle(2)
        l.SetLineWidth(3)
        return l


    def header(pad, right):
        t = ROOT.TLatex()
        t.SetNDC()
        t.SetTextFont(FONT)
        t.SetTextSize(24)
        t.DrawLatex(pad.GetLeftMargin(), 0.92, "#bf{Toy analysis} #it{empty bin}")
        t.SetTextAlign(31)
        t.DrawLatex(1 - pad.GetRightMargin(), 0.92, right)
        return t


    c = ROOT.TCanvas("c", "", 1500, 600)
    pl = ROOT.TPad("pl", "", 0, 0, 0.5, 1)
    pr = ROOT.TPad("pr", "", 0.5, 0, 1, 1)
    pl.Draw()
    pr.Draw()
    keep = []

    # left: limits
    f1 = frame(pl, "f1", 0, 1.6, "95% CL upper limit on r")
    ge, go = graph(FLOORS, exp, BLUE, 20), graph(FLOORS, obs, ROOT.kBlack, 21)
    le, lo = hline(m_exp, BLUE), hline(m_obs, ROOT.kBlack)
    for o in (le, lo):
        o.Draw()
    ge.Draw("lp same")
    go.Draw("lp same")
    leg = ROOT.TLegend(0.17, 0.66, 0.70, 0.88)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextFont(FONT)
    leg.SetTextSize(21)
    leg.AddEntry(go, "Observed", "lp")
    leg.AddEntry(ge, "Expected (median)", "lp")
    leg.AddEntry(lo, "Dashed: b4+b5 merged (the fix)", "l")
    leg.Draw()
    keep += [f1, ge, go, le, lo, leg, header(pl, "data: 6 events in b5")]

    # right: significance
    pr.cd()
    f2 = frame(pr, "f2", 0, 11, "Significance of the \"excess\" (#sigma)")
    gs = graph(FLOORS, sig, RED, 20)
    ls = hline(m_sig, RED)
    five = ROOT.TLine(5e-4, 5, 10, 5)
    five.SetLineColor(ROOT.kGray + 1)
    five.SetLineStyle(3)
    five.SetLineWidth(2)
    five.Draw()
    ls.Draw()
    gs.Draw("lp same")
    t = ROOT.TLatex()
    t.SetTextFont(FONT)
    t.SetTextSize(20)
    t.SetTextColor(ROOT.kGray + 2)
    t.DrawLatex(1.5, 5.25, "5#sigma")
    leg2 = ROOT.TLegend(0.45, 0.70, 0.95, 0.88)
    leg2.SetBorderSize(0)
    leg2.SetFillStyle(0)
    leg2.SetTextFont(FONT)
    leg2.SetTextSize(21)
    leg2.AddEntry(gs, "Floored empty bin", "lp")
    leg2.AddEntry(ls, "b4+b5 merged (the fix)", "l")
    leg2.Draw()
    keep += [f2, gs, ls, five, t, leg2, header(pr, "no signal injected")]

    rootutil.save(c, "empty_bins")


@rootutil.isolated
def empty_bins_fit():
    """Pre-fit / post-fit yields per bin for the empty-bin demo (slide 12).

Two panels: the floored card (b5 background = 0.01) and the fix (b4+b5
merged). In each: pre-fit background stack, data, the background-only
post-fit total, and the s+b post-fit total with the fitted signal.

Yields are the card rates scaled by the lnN factors kappa**theta, with theta
the nuisance values from FitDiagnostics (the signal scaled by the fitted r).
Read from the datacard and the fit files only: the RooWorkspace needs the
Combine libraries, which are not loaded in this Python.

Run it through its run_NN_*.py file (see docs/slide_map.md)."""
    rootutil.setup(ticks=True)

    PANELS = [("floor_0.01", "Empty b5, floored to 0.01", ["b1", "b2", "b3", "b4", "b5"]),
              ("merged", "Fix: b4+b5 merged", ["b1", "b2", "b3", "b4+b5"])]
    PROCS = ["sig", "WZ", "fakes"]
    FONT = rootutil.FONT
    COL = {"WZ": ROOT.TColor.GetColor("#e8a33d"), "fakes": ROOT.TColor.GetColor("#8c8c8c")}
    BLUE = ROOT.TColor.GetColor("#2c7bb6")
    RED = ROOT.TColor.GetColor("#c0392b")


    def read_card(card):
        """Columns of a text datacard: bin and process per column, the rates, and the
        lnN nuisances as {name: {column: kappa}}."""
        lines = [l.split() for l in open(card, encoding="utf-8") if l.strip() and not l.startswith("#")]
        bins = [w for w in lines if w[0] == "bin"][-1][1:]     # the per-column bin row
        procs = [w for w in lines if w[0] == "process"][0][1:]  # process names
        rates = [float(x) for x in [w for w in lines if w[0] == "rate"][0][1:]]
        nuis = {}
        for w in lines:
            if len(w) > 2 and w[1] == "lnN":
                nuis[w[0]] = {j: float(x) for j, x in enumerate(w[2:]) if x != "-"}
        return bins, procs, rates, nuis


    def expected(card, theta, r):
        """{proc: [per-bin yield]} and the card's bin labels. theta = {} gives the pre-fit;
        the signal is scaled by r."""
        bins, procs, rates, nuis = read_card(card)
        labels = list(dict.fromkeys(bins))
        out = {p: [0.0] * len(labels) for p in PROCS}
        for j, (b, p) in enumerate(zip(bins, procs)):
            y = rates[j]
            for name, kappa in nuis.items():
                if j in kappa:
                    y *= kappa[j] ** theta.get(name, 0.0)
            if p == "sig":
                y *= r
            out[p][labels.index(b)] += y
        return out, labels


    def data(card):
        """Observed counts per bin, from the datacard's observation line."""
        for line in open(card, encoding="utf-8"):
            if line.startswith("observation"):
                return [float(x) for x in line.split()[1:]]


    c = ROOT.TCanvas("c", "", 1500, 620)
    pads = [ROOT.TPad("p%d" % k, "", 0.5 * k, 0, 0.5 * (k + 1), 1) for k in range(2)]
    keep = []
    for k, (tag, title, labels) in enumerate(PANELS):
        c.cd()
        pads[k].Draw()
        pads[k].cd()
        pads[k].SetLogy()
        pads[k].SetLeftMargin(0.14)
        pads[k].SetRightMargin(0.04)
        pads[k].SetTopMargin(0.10)
        pads[k].SetBottomMargin(0.12)

        card = "empty/toy_%s.txt" % tag
        ff = ROOT.TFile.Open("fitDiagnostics.empty_%s.root" % tag)
        fit_b, fit_s = ff.Get("fit_b"), ff.Get("fit_s")
        theta_b = {p.GetName(): p.getVal() for p in fit_b.floatParsFinal()}
        theta_s = {p.GetName(): p.getVal() for p in fit_s.floatParsFinal()}
        r = theta_s["r"]

        nb = len(labels)
        pre, card_labels = expected(card, {}, 1.0)
        assert len(card_labels) == nb, "%s: card has %d bins" % (card, len(card_labels))
        postb, _ = expected(card, theta_b, 0.0)
        posts, _ = expected(card, theta_s, r)
        obs = data(card)

        print("== %s  (s+b best-fit r = %.2f)" % (title, r))
        print("   %-6s %8s %8s %10s %10s %10s" % ("bin", "data", "bkg pre", "bkg b-only", "bkg s+b", "sig s+b"))
        for i, lab in enumerate(labels):
            print("   %-6s %8.0f %8.2f %10.2f %10.2f %10.2f" % (
                lab, obs[i], pre["WZ"][i] + pre["fakes"][i],
                postb["WZ"][i] + postb["fakes"][i],
                posts["WZ"][i] + posts["fakes"][i], posts["sig"][i]))

        stack = ROOT.THStack("st%d" % k, "")
        hs = {}
        for proc in ["fakes", "WZ"]:
            h = ROOT.TH1F("%s%d" % (proc, k), "", nb, 0, nb)
            for i in range(nb):
                h.SetBinContent(i + 1, max(pre[proc][i], 1e-6))
            h.SetFillColor(COL[proc])
            h.SetLineColor(ROOT.kBlack)
            stack.Add(h)
            hs[proc] = h
        hb = ROOT.TH1F("hb%d" % k, "", nb, 0, nb)
        hsb = ROOT.TH1F("hsb%d" % k, "", nb, 0, nb)
        for i in range(nb):
            hb.SetBinContent(i + 1, postb["WZ"][i] + postb["fakes"][i])
            hsb.SetBinContent(i + 1, posts["WZ"][i] + posts["fakes"][i] + posts["sig"][i])
        hb.SetLineColor(BLUE)
        hb.SetLineWidth(4)
        hb.SetLineStyle(2)
        hsb.SetLineColor(RED)
        hsb.SetLineWidth(4)
        gd = ROOT.TGraphAsymmErrors()
        for i, n in enumerate(obs):
            lo = 0.0 if n == 0 else ROOT.Math.gamma_quantile(0.1586555, n, 1.0)
            hi = ROOT.Math.gamma_quantile_c(0.1586555, n + 1, 1.0)
            gd.SetPoint(i, i + 0.5, n)
            gd.SetPointError(i, 0, 0, n - lo, hi - n)
        gd.SetMarkerStyle(20)
        gd.SetMarkerSize(1.6)
        gd.SetLineWidth(2)

        stack.SetMinimum(0.005)
        stack.SetMaximum(5e4)
        stack.Draw("hist")
        ax = stack.GetXaxis()
        for i, lab in enumerate(labels):
            ax.SetBinLabel(i + 1, lab)
        for a in [stack.GetXaxis(), stack.GetYaxis()]:
            a.SetLabelFont(FONT)
            a.SetLabelSize(24)
            a.SetTitleFont(FONT)
            a.SetTitleSize(24)
        stack.GetYaxis().SetTitle("Events")
        stack.GetYaxis().SetTitleOffset(1.4)
        hsb.Draw("hist same")
        hb.Draw("hist same")
        gd.Draw("p same")

        leg = ROOT.TLegend(0.40, 0.60, 0.95, 0.88)
        leg.SetBorderSize(0)
        leg.SetFillStyle(0)
        leg.SetTextFont(FONT)
        leg.SetTextSize(20)
        leg.AddEntry(gd, "Data (no signal)", "pe")
        leg.AddEntry(hs["WZ"], "WZ (pre-fit)", "f")
        leg.AddEntry(hs["fakes"], "Fakes (pre-fit)", "f")
        leg.AddEntry(hb, "Post-fit bkg, b-only fit", "l")
        leg.AddEntry(hsb, "Post-fit s+b, fitted r = %.2f" % r, "l")
        leg.Draw()
        t = ROOT.TLatex()
        t.SetNDC()
        t.SetTextFont(FONT)
        t.SetTextSize(24)
        t.DrawLatex(0.14, 0.92, "#bf{Toy analysis} #it{%s}" % title)
        if tag.startswith("floor"):
            note = ROOT.TLatex()
            note.SetTextFont(FONT)
            note.SetTextSize(19)
            note.SetTextAlign(22)
            note.SetTextColor(RED)
            note.DrawLatex(nb - 0.5, 1.2, "fit cannot raise")
            note.DrawLatex(nb - 0.5, 0.45, "0.01 #rightarrow 6")
            note.DrawLatex(nb - 0.5, 0.17, "#Rightarrow signal")
            keep.append(note)
        pads[k].RedrawAxis()
        keep += [stack, hs, hb, hsb, gd, leg, t]
        ff.Close()

    rootutil.save(c, "empty_bins_fit")


@rootutil.isolated
def gof_vs_limits():
    """Bad GoF / pulls vs. "fine" limits (slide 18). Three panels:
  left:   data vs. background per bin, (data - bkg)/sqrt(bkg), per variant
  middle: observed limit (dashed: expected median) and the significance
  right:  saturated GoF p-value with the signal floating (default) and
          background-only (--fixedSignalStrength 0)
Prints the b-only pulls of wz_xs and fakes as well.

Run it through its run_NN_*.py file (see docs/slide_map.md)."""
    rootutil.setup(ticks=True)
    FONT = rootutil.FONT
    NB = 5
    VARS = [("good", "no mismodelling", ROOT.kGray + 2),
            ("misA", "A: excess in b1", ROOT.TColor.GetColor("#e8a33d")),
            ("misB", "B: excess in b5", ROOT.TColor.GetColor("#c0392b"))]


    def tree_vals(fn):
        f = ROOT.TFile.Open(fn)
        out = [(e.quantileExpected, e.limit) for e in f.Get("limit")]
        f.Close()
        return out


    res = {}
    for v, label, col in VARS:
        f = ROOT.TFile.Open("gof/shapes_%s.root" % v)
        d, wz, fk = f.Get("data_obs"), f.Get("WZ"), f.Get("fakes")
        resid = [(d.GetBinContent(i) - wz.GetBinContent(i) - fk.GetBinContent(i))
                 / (wz.GetBinContent(i) + fk.GetBinContent(i)) ** 0.5 for i in range(1, NB + 1)]
        f.Close()
        lim = dict(tree_vals("higgsCombine.gof_%s.AsymptoticLimits.mH120.root" % v))
        z = 0.0
        for line in open("gof/sig_%s.log" % v, encoding="utf-8"):
            if line.startswith("Significance:"):
                z = float(line.split()[1])
        p = {}
        for m in ["sb", "b"]:
            o = tree_vals("higgsCombine.gof_%s_%s.obs.GoodnessOfFit.mH120.root" % (v, m))[0][1]
            t = [x for _, x in tree_vals("higgsCombine.gof_%s_%s.toys.GoodnessOfFit.mH120.1234.root" % (v, m))]
            p[m] = sum(x >= o for x in t) / float(len(t))
        fd = ROOT.TFile.Open("fitDiagnostics.gof_%s.root" % v)
        pb = fd.Get("fit_b").floatParsFinal()
        pull_vals = {n: pb.find(n).getVal() for n in ["wz_xs", "fakes"]}
        fd.Close()
        res[v] = dict(resid=resid, obs=lim[-1], exp=lim[0.5], z=z, p=p, pulls=pull_vals)
        print("%-5s obs %.3f exp %.3f (obs/exp %.2f)  signif %.2f  GoF p: s+b %.3f  b-only %.3f"
              "   b-only pulls: wz_xs %+.2f fakes %+.2f"
              % (v, lim[-1], lim[0.5], lim[-1] / lim[0.5], z, p["sb"], p["b"],
                 pull_vals["wz_xs"], pull_vals["fakes"]))

    c = ROOT.TCanvas("c", "", 1800, 600)
    widths = [0.38, 0.31, 0.31]
    x0 = 0.0
    pads = []
    for k, w in enumerate(widths):
        c.cd()
        p = ROOT.TPad("p%d" % k, "", x0, 0, x0 + w, 1)
        x0 += w
        p.SetLeftMargin(0.16 if k == 0 else 0.20)
        p.SetRightMargin(0.04)
        p.SetTopMargin(0.10)
        p.SetBottomMargin(0.14)
        p.Draw()
        pads.append(p)
    keep = []


    def frame(name, nx, xlabels, ymin, ymax, ytitle):
        h = ROOT.TH1F(name, "", nx, 0, nx)
        h.SetMinimum(ymin)
        h.SetMaximum(ymax)
        for ax in [h.GetXaxis(), h.GetYaxis()]:
            ax.SetLabelFont(FONT)
            ax.SetLabelSize(21)
            ax.SetTitleFont(FONT)
            ax.SetTitleSize(22)
        for i, lab in enumerate(xlabels):
            h.GetXaxis().SetBinLabel(i + 1, lab)
        h.GetXaxis().SetLabelSize(22)
        h.GetYaxis().SetTitle(ytitle)
        h.GetYaxis().SetTitleOffset(1.5)
        return h


    def title(pad, text):
        t = ROOT.TLatex()
        t.SetNDC()
        t.SetTextFont(FONT)
        t.SetTextSize(22)
        t.DrawLatex(pad.GetLeftMargin(), 0.92, text)
        return t


    # ---- left: residuals ----
    pads[0].cd()
    f0 = frame("f0", NB, ["b%d" % (i + 1) for i in range(NB)], -3, 7, "(data #minus bkg) / #sqrt{bkg}")
    f0.Draw("axis")
    zero = ROOT.TLine(0, 0, NB, 0)
    zero.SetLineStyle(2)
    zero.Draw()
    leg = ROOT.TLegend(0.18, 0.16, 0.58, 0.34)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextFont(FONT)
    leg.SetTextSize(19)
    for k, (v, label, col) in enumerate(VARS):
        g = ROOT.TGraph()
        for i, r in enumerate(res[v]["resid"]):
            g.SetPoint(i, i + 0.5 + (k - 1) * 0.18, r)
        g.SetMarkerStyle([24, 21, 20][k])
        g.SetMarkerSize(1.8)
        g.SetMarkerColor(col)
        g.Draw("p same")
        leg.AddEntry(g, label, "p")
        keep.append(g)
    leg.Draw()
    sig = ROOT.TLatex()
    sig.SetTextFont(FONT)
    sig.SetTextSize(18)
    sig.SetTextColor(ROOT.TColor.GetColor("#7b3294"))
    sig.SetTextAlign(22)
    sig.DrawLatex(4.0, -2.4, "signal lives here #rightarrow")
    keep += [f0, zero, leg, sig, title(pads[0], "#bf{Toy} #it{data vs. background, no signal}")]

    # ---- middle: observed limit and significance ----
    pads[1].cd()
    f1 = frame("f1", 3, ["none", "A", "B"], 0, 0.5, "Observed 95% CL limit on r")
    f1.Draw("axis")
    exp = sum(res[v]["exp"] for v, _, _ in VARS) / 3.0
    eline = ROOT.TLine(0, exp, 3, exp)
    eline.SetLineStyle(2)
    eline.SetLineWidth(2)
    eline.Draw()
    tl = ROOT.TLatex()
    tl.SetTextFont(FONT)
    tl.SetTextSize(19)
    tl.SetTextAlign(22)
    for k, (v, label, col) in enumerate(VARS):
        o = res[v]["obs"]
        b = ROOT.TBox(k + 0.2, 0, k + 0.8, o)
        b.SetFillColor(col)
        b.Draw()
        keep.append(b)
        tl.SetTextColor(ROOT.kBlack)
        tl.DrawLatex(k + 0.5, o + 0.02, "%.3f" % o)
        tl.SetTextColor(col)
        tl.DrawLatex(k + 0.5, o + 0.05, "%.1f#sigma" % res[v]["z"])
    te = ROOT.TLatex()
    te.SetNDC()
    te.SetTextFont(FONT)
    te.SetTextSize(18)
    te.DrawLatex(0.23, 0.83, "dashed: expected median (%.2f)" % exp)
    pads[1].RedrawAxis()
    keep += [f1, eline, tl, te, title(pads[1], "#bf{Limit} #it{and significance}")]

    # ---- right: GoF p-values ----
    pads[2].cd()
    f2 = frame("f2", 3, ["none", "A", "B"], 0, 1.15, "GoF p-value (saturated)")
    f2.Draw("axis")
    cut = ROOT.TLine(0, 0.05, 3, 0.05)
    cut.SetLineColor(ROOT.kRed + 1)
    cut.SetLineStyle(2)
    cut.SetLineWidth(2)
    cut.Draw()
    leg2 = ROOT.TLegend(0.22, 0.74, 0.95, 0.88)
    leg2.SetBorderSize(0)
    leg2.SetFillStyle(0)
    leg2.SetTextFont(FONT)
    leg2.SetTextSize(18)
    hs, hb = ROOT.TH1F("hs", "", 1, 0, 1), ROOT.TH1F("hb", "", 1, 0, 1)
    hs.SetFillColor(ROOT.TColor.GetColor("#9ecae1"))
    hb.SetFillColor(ROOT.TColor.GetColor("#2c7bb6"))
    leg2.AddEntry(hs, "signal floating (default)", "f")
    leg2.AddEntry(hb, "background-only", "f")
    for k, (v, label, col) in enumerate(VARS):
        for j, (m, h) in enumerate([("sb", hs), ("b", hb)]):
            pv = max(res[v]["p"][m], 0.004)
            b = ROOT.TBox(k + 0.15 + 0.35 * j, 0, k + 0.48 + 0.35 * j, pv)
            b.SetFillColor(h.GetFillColor())
            b.Draw()
            keep.append(b)
    tc = ROOT.TLatex()
    tc.SetTextFont(FONT)
    tc.SetTextSize(17)
    tc.SetTextColor(ROOT.kRed + 1)
    tc.DrawLatex(0.05, 0.075, "p = 0.05")
    leg2.Draw()
    pads[2].RedrawAxis()
    keep += [f2, cut, leg2, hs, hb, tc, title(pads[2], "#bf{Goodness of fit}")]

    rootutil.save(c, "gof_vs_limits")


@rootutil.isolated
def inflate():
    """Two-panel summary for the inflate-vs-decompose demo (slide 11).

Left:  constraint plot. Grey band = prior +-1 sigma of each fakes nuisance,
       point = post-fit value +-1 sigma from the background-only fit, both as
       a % change of the fakes yield (lnN: kappa**theta - 1).
Right: best-fit r +-1 sigma from the s+b fit, on pseudo-data with NO signal.

Run it through its run_NN_*.py file (see docs/slide_map.md)."""
    rootutil.setup(ticks=True, end_error=6)

    K = float(os.environ.get("INFL_NONCLOSURE", 2.0))  # must match cards.inflate_cards()
    MODELS = [  # (tag, short label, [(nuisance, kappa)])
        ("nominal", "Nominal", [("fakes", 1.30)]),
        ("inflated", "Inflated", [("fakes", K)]),
        ("decomposed", "Decomposed", [("fakes", 1.30), ("fakes_closure", K)]),
    ]
    LONG = {"nominal": "fakes 30%", "inflated": "fakes %.0f%%" % (100 * (K - 1)),
            "decomposed": "fakes 30%% + closure %.0f%% (b4-b5)" % (100 * (K - 1))}

    rows, rfits = [], []
    for tag, label, nuis in MODELS:
        f = ROOT.TFile.Open("fitDiagnostics.infl_%s.root" % tag)
        fb = f.Get("fit_b").floatParsFinal()
        r = f.Get("fit_s").floatParsFinal().find("r")
        z = None
        try:  # spurious significance from run_05's Significance step
            for line in open("inflate/sig_%s.log" % tag, encoding="utf-8"):
                if line.startswith("Significance:"):
                    z = float(line.split()[1])
        except IOError:
            pass
        rfits.append((label, r.getVal(), r.getError(), z))
        print("%-11s %-34s r = %+.2f +- %.2f   significance %s"
              % (label, LONG[tag], r.getVal(), r.getError(), "-" if z is None else "%.1f" % z))
        for name, kappa in nuis:
            p = fb.find(name)
            th, err = p.getVal(), p.getError()
            pct = lambda t: 100 * (kappa ** t - 1)
            rows.append(("%s: %s" % (label, name), pct(1), pct(-1),
                         pct(th), pct(th - err), pct(th + err)))
            print("    %-14s prior +%.0f/%.0f%%   post-fit %+.0f%% (+%.0f/-%.0f%%)"
                  % (name, pct(1), pct(-1), pct(th), pct(th + err) - pct(th), pct(th) - pct(th - err)))
        f.Close()

    FONT = rootutil.FONT
    BLUE = ROOT.TColor.GetColor("#2c7bb6")
    GREY = ROOT.TColor.GetColor("#d0d0d0")


    def style_axes(h, ylab=20):
        for ax, size in [(h.GetXaxis(), 22), (h.GetYaxis(), ylab)]:
            ax.SetLabelFont(FONT)
            ax.SetLabelSize(size)
            ax.SetTitleFont(FONT)
            ax.SetTitleSize(24)
        h.GetXaxis().SetTitleOffset(1.25)
        h.GetYaxis().SetTickLength(0)


    def header(pad, left_text, right_text):
        t = ROOT.TLatex()
        t.SetNDC()
        t.SetTextFont(FONT)
        t.SetTextSize(24)
        t.SetTextAlign(11)
        t.DrawLatex(pad.GetLeftMargin(), 1 - pad.GetTopMargin() + 0.02, left_text)
        t.SetTextAlign(31)
        t.DrawLatex(1 - pad.GetRightMargin(), 1 - pad.GetTopMargin() + 0.02, right_text)
        return t


    W, H = 1500, 580
    c = ROOT.TCanvas("c", "", W, H)
    left = ROOT.TPad("l", "", 0.0, 0.0, 0.57, 1.0)
    right = ROOT.TPad("r", "", 0.57, 0.0, 1.0, 1.0)
    for p in (left, right):
        p.SetTopMargin(0.12)
        p.SetBottomMargin(0.15)
        p.Draw()
    keep = []

    # ---- left: constraint plot ----
    left.cd()
    left.SetLeftMargin(0.33)
    left.SetRightMargin(0.03)
    n = len(rows)
    xlo = min(-60, 1.1 * min(r[2] for r in rows))
    xhi = max(100, 1.1 * max(max(r[1], r[5]) for r in rows))
    fr = ROOT.TH2F("fl", "", 10, xlo, xhi, n + 1, 0, n + 1)  # top row: legend
    for i, row in enumerate(rows):
        fr.GetYaxis().SetBinLabel(n - i, row[0])
    fr.GetYaxis().SetBinLabel(n + 1, "")
    style_axes(fr)
    fr.GetXaxis().SetTitle("Change in fakes yield (%)")
    fr.Draw()
    g = ROOT.TGraphAsymmErrors()
    for i, (lab, up, dn, c0, lo, hi) in enumerate(rows):
        y = n - i - 0.5
        b = ROOT.TBox(dn, y - 0.32, up, y + 0.32)
        b.SetFillColor(GREY)
        b.Draw()
        keep.append(b)
        g.SetPoint(i, c0, y)
        g.SetPointError(i, c0 - lo, hi - c0, 0, 0)
    zero = ROOT.TLine(0, 0, 0, n)  # stops below the legend row
    zero.SetLineStyle(2)
    zero.Draw()
    g.SetMarkerStyle(20)
    g.SetMarkerSize(1.8)
    g.SetMarkerColor(BLUE)
    g.SetLineColor(BLUE)
    g.SetLineWidth(3)
    g.Draw("p same")
    leg = ROOT.TLegend(0.35, 0.745, 0.96, 0.87)
    leg.SetNColumns(2)
    leg.SetBorderSize(0)
    leg.SetFillColor(0)
    leg.SetFillStyle(1001)
    leg.SetTextFont(FONT)
    leg.SetTextSize(20)
    hb = ROOT.TH1F("hb", "", 1, 0, 1)
    hb.SetFillColor(GREY)
    hb.SetLineColor(GREY)
    leg.AddEntry(hb, "Prior #pm1#sigma", "f")
    leg.AddEntry(g, "Post-fit #pm1#sigma (b-only)", "pe")
    leg.Draw()
    left.RedrawAxis()
    keep += [fr, g, zero, leg, hb,
             header(left, "#bf{Toy analysis} #it{fakes constraints}", "pseudo-data, no signal")]

    # ---- right: best-fit r ----
    right.cd()
    right.SetLeftMargin(0.24)
    right.SetRightMargin(0.05)
    m = len(rfits)
    rlo = min(-0.1, min(v - e for _, v, e, _ in rfits) - 0.05)
    rhi = 2.0 * max(v + e for _, v, e, _ in rfits)
    fr2 = ROOT.TH2F("fr", "", 10, rlo, rhi, m, 0, m)
    fr2.GetXaxis().SetNdivisions(505)
    for i, (lab, _, _, _) in enumerate(rfits):
        fr2.GetYaxis().SetBinLabel(m - i, lab)
    style_axes(fr2, 22)
    fr2.GetXaxis().SetTitle("Best-fit r")
    fr2.Draw()
    z = ROOT.TLine(0, 0, 0, m)
    z.SetLineStyle(2)
    z.Draw()
    g2 = ROOT.TGraphAsymmErrors()
    t = ROOT.TLatex()
    t.SetTextFont(FONT)
    t.SetTextSize(20)
    t.SetTextAlign(12)
    for i, (lab, v, e, z) in enumerate(rfits):
        y = m - i - 0.5
        g2.SetPoint(i, v, y)
        g2.SetPointError(i, e, e, 0, 0)
        t.SetTextColor(ROOT.kBlack)
        t.DrawLatex(rlo + 0.70 * (rhi - rlo), y + 0.13, "%+.2f #pm %.2f" % (v, e))
        if z is not None:
            t.SetTextColor(ROOT.kRed + 1 if z >= 3 else ROOT.kBlack)
            t.DrawLatex(rlo + 0.70 * (rhi - rlo), y - 0.15, "#bf{%.1f#sigma}" % z)
    g2.SetMarkerStyle(20)
    g2.SetMarkerSize(1.8)
    g2.SetLineWidth(3)
    g2.Draw("p same")
    right.RedrawAxis()
    keep += [fr2, z, g2, t, header(right, "#bf{Toy analysis}", "true r = 0")]

    rootutil.save(c, "inflate")


@rootutil.isolated
def lowcount():
    """Asymptotic vs toy-based (HybridNew) limits as the event count drops
(slide 17).

Left:  95% CL limit on r vs. the background in the signal bins (b4+b5).
       Observed: toys as points (toy-statistics error bars), asymptotic as a
       solid line. Expected median: toys as a solid line, asymptotic dashed.
Right: ratio asymptotic / toys. Below 1 = asymptotic is too optimistic.
       Observed as points, expected as a line.

Run it through its run_NN_*.py file (see docs/slide_map.md)."""
    rootutil.setup(ticks=True, end_error=5)
    FONT = rootutil.FONT
    SCALES = [1.0, 0.3, 0.1, 0.03, 0.01]
    BKG_SR = 18.0           # background in b4+b5 at s = 1
    BLACK = ROOT.kBlack
    TOY = BLACK                             # toys (HybridNew)
    ASY = ROOT.TColor.GetColor("#1f5fa0")   # asymptotic


    rows = []
    for s in SCALES:
        a_obs = combine_outputs.read_limit("higgsCombine.lc_asym_s%g.AsymptoticLimits.mH120.root" % s, -1)[0]
        a_exp = combine_outputs.read_limit("higgsCombine.lc_asym_s%g.AsymptoticLimits.mH120.root" % s, 0.5)[0]
        t_obs = combine_outputs.read_limit("higgsCombine.lc_toys_s%g.HybridNew.mH120.123.root" % s, -1)
        t_exp = combine_outputs.read_limit("higgsCombine.lc_toysexp_s%g.HybridNew.mH120.123.quant0.500.root" % s, 0.5)
        rows.append((s, BKG_SR * s, a_obs, a_exp, t_obs, t_exp))
        print("s=%-5g bkg(b4+b5)=%5.2f  observed: asym %.3f toys %.3f+-%.3f (%+.0f%%)"
              "   expected: asym %.3f toys %.3f+-%.3f (%+.0f%%)"
              % (s, BKG_SR * s, a_obs, t_obs[0], t_obs[1], 100 * (a_obs / t_obs[0] - 1),
                 a_exp, t_exp[0], t_exp[1], 100 * (a_exp / t_exp[0] - 1)))


    def bold_cross(xs, ys, half_y, col, fx=1.07, width=4):
        """Bold x at each (x, y): two thick diagonals. Half-width is multiplicative
        in x (log axis), half-height is absolute in y (half_y, one value per point)."""
        lines = []
        for x, y, dy in zip(xs, ys, half_y):
            for x1, y1, x2, y2 in [(x / fx, y - dy, x * fx, y + dy),
                                   (x / fx, y + dy, x * fx, y - dy)]:
                line = ROOT.TLine(x1, y1, x2, y2)
                line.SetLineColor(col)
                line.SetLineWidth(width)
                lines.append(line)
        return lines


    def legend_proxy(col):
        """Marker-style x for the legend, matching the bold cross colour."""
        g = ROOT.TGraph(1)
        g.SetPoint(0, 1, 1)
        g.SetMarkerStyle(5)
        g.SetMarkerSize(3.2)
        g.SetMarkerColor(col)
        return g


    def style(h, ytitle):
        for ax in [h.GetXaxis(), h.GetYaxis()]:
            ax.SetLabelFont(FONT)
            ax.SetLabelSize(21)
            ax.SetTitleFont(FONT)
            ax.SetTitleSize(23)
        h.GetXaxis().SetTitle("Expected background in the signal bins b4+b5 (events)")
        h.GetXaxis().SetTitleOffset(1.3)
        h.GetYaxis().SetTitle(ytitle)
        h.GetYaxis().SetTitleOffset(1.5)
        h.GetXaxis().SetMoreLogLabels()
        h.GetXaxis().SetNoExponent()


    c = ROOT.TCanvas("c", "", 1600, 620)
    pl = ROOT.TPad("pl", "", 0, 0, 0.5, 1)
    pr = ROOT.TPad("pr", "", 0.5, 0, 1, 1)
    for p in (pl, pr):
        p.SetLogx()
        p.SetLeftMargin(0.13)
        p.SetRightMargin(0.04)
        p.SetTopMargin(0.10)
        p.SetBottomMargin(0.15)
        p.Draw()
    keep = []

    # ---- left: the limits ----
    pl.cd()
    pl.SetLogy()
    fr = ROOT.TH1F("fr", "", 10, 0.1, 30)
    fr.SetMinimum(0.4)
    fr.SetMaximum(20)
    style(fr, "95% CL upper limit on r")
    fr.Draw("axis")
    leg = ROOT.TLegend(0.50, 0.62, 0.95, 0.88)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextFont(FONT)
    leg.SetTextSize(19)
    # Colour = method: HybridNew (toys) black, asymptotic blue.
    # Observed = x markers (both methods); expected = lines (solid toys, dashed asymptotic).
    for k, label in enumerate(["Observed", "Expected"]):
        ga = ROOT.TGraph()
        gt = ROOT.TGraphErrors() if k == 0 else ROOT.TGraph()
        for i, (s, b, ao, ae, to, te) in enumerate(rows):
            a, t = (ao, to) if k == 0 else (ae, te)
            ga.SetPoint(i, b, a)
            gt.SetPoint(i, b, t[0])
            if k == 0:
                gt.SetPointError(i, 0, t[1])
        if k == 0:
            # observed: bold x markers; toys carry toy-statistics error bars
            xs = [r[1] for r in rows]
            ya = [r[2] for r in rows]
            yt = [r[4][0] for r in rows]
            crosses_a = bold_cross(xs, ya, [0.07 * y for y in ya], ASY)
            crosses_t = bold_cross(xs, yt, [0.07 * y for y in yt], TOY)
            for line in crosses_a + crosses_t:
                line.Draw()
            gt.SetLineColor(TOY)
            gt.SetLineWidth(3)
            gt.Draw("e same")
            proxy_t, proxy_a = legend_proxy(TOY), legend_proxy(ASY)
            leg.AddEntry(proxy_t, "Observed, toys (HybridNew)", "p")
            leg.AddEntry(proxy_a, "Observed, asymptotic", "p")
            keep += crosses_a + crosses_t + [proxy_t, proxy_a]
        else:
            # expected: solid line for toys, dashed for asymptotic
            ga.SetLineColor(ASY)
            ga.SetLineStyle(2)
            ga.SetLineWidth(4)
            ga.Draw("l same")
            gt.SetLineColor(TOY)
            gt.SetLineStyle(1)
            gt.SetLineWidth(4)
            gt.Draw("l same")
            leg.AddEntry(gt, "Expected, toys (HybridNew)", "l")
            leg.AddEntry(ga, "Expected, asymptotic", "l")
        keep += [ga, gt]
    leg.Draw()
    t = ROOT.TLatex()
    t.SetNDC()
    t.SetTextFont(FONT)
    t.SetTextSize(23)
    t.DrawLatex(0.13, 0.92, "#bf{Toy analysis} #it{luminosity scaled down}")
    pl.RedrawAxis()
    keep += [fr, leg, t]

    # ---- right: ratio ----
    pr.cd()
    fr2 = ROOT.TH1F("fr2", "", 10, 0.1, 30)
    fr2.SetMinimum(0.7)
    fr2.SetMaximum(1.1)
    style(fr2, "Asymptotic / toys")
    fr2.Draw("axis")
    band = ROOT.TBox(0.1, 0.95, 30, 1.05)
    band.SetFillColorAlpha(ROOT.kGray, 0.4)
    band.Draw()
    one = ROOT.TLine(0.1, 1, 30, 1)
    one.SetLineStyle(2)
    one.Draw()
    leg2 = ROOT.TLegend(0.50, 0.20, 0.95, 0.36)
    leg2.SetBorderSize(0)
    leg2.SetFillStyle(0)
    leg2.SetTextFont(FONT)
    leg2.SetTextSize(19)
    # One colour for the whole ratio panel: observed = x, expected = line.
    for k, label in enumerate(["Observed", "Expected"]):
        col = BLACK
        if k == 0:
            # observed: bold x markers (no uncertainty band)
            xs = [b * 0.94 for (s, b, ao, ae, to, te) in rows]
            ys = [ao / to[0] for (s, b, ao, ae, to, te) in rows]
            crosses = bold_cross(xs, ys, [0.012] * len(xs), col)
            for line in crosses:
                line.Draw()
            proxy = legend_proxy(col)
            leg2.AddEntry(proxy, label, "p")
            keep += crosses + [proxy]
        else:
            # expected: line
            g = ROOT.TGraph()
            for i, (s, b, ao, ae, to, te) in enumerate(rows):
                g.SetPoint(i, b, ae / te[0])
            g.SetLineColor(col)
            g.SetLineStyle(1)
            g.SetLineWidth(4)
            g.Draw("l same")
            leg2.AddEntry(g, label, "l")
            keep.append(g)
    leg2.Draw()
    note = ROOT.TLatex()
    note.SetTextFont(FONT)
    note.SetTextSize(19)
    note.SetTextColor(ROOT.kRed + 1)
    note.DrawLatex(0.13, 0.73, "asymptotic too optimistic")
    note.SetTextColor(ROOT.kGray + 2)
    note.DrawLatex(3.0, 1.07, "#pm5%")
    t2 = ROOT.TLatex()
    t2.SetNDC()
    t2.SetTextFont(FONT)
    t2.SetTextSize(23)
    t2.DrawLatex(0.13, 0.92, "#bf{Toy analysis} #it{ratio}")
    pr.RedrawAxis()
    keep += [fr2, band, one, leg2, note, t2]

    rootutil.save(c, "lowcount")


@rootutil.isolated
def massgrid():
    """Localised signal vs. mass-grid spacing (slide 20). Three stacked panels,
shared mass axis:
  top:    the spectrum: background, data, injected signal (530 GeV)
  middle: observed / expected 95% CL limit vs. mass: fine 10 GeV scan
          vs. a 100 GeV grid joined by straight lines (interpolation)
  bottom: local significance vs. mass, same two grids

Run it through its run_NN_*.py file (see docs/slide_map.md)."""
    rootutil.setup(ticks=True)
    FONT = rootutil.FONT
    FINE = list(range(200, 1001, 10))
    COARSE = list(range(200, 1001, 100))
    M_TRUE = 530
    RED = ROOT.TColor.GetColor("#c0392b")
    BLUE = ROOT.TColor.GetColor("#2c7bb6")
    ORANGE = ROOT.TColor.GetColor("#e8a33d")


    def limits(m):
        f = ROOT.TFile.Open("mass/higgsCombine.mass.AsymptoticLimits.mH%d.root" % m)
        out = {round(e.quantileExpected, 3): e.limit for e in f.Get("limit")}
        f.Close()
        return out[-1.0], out[0.5]


    def signif(m):
        f = ROOT.TFile.Open("mass/higgsCombine.mass.Significance.mH%d.root" % m)
        z = [e.limit for e in f.Get("limit")][0]
        f.Close()
        return z


    res = {m: limits(m) + (signif(m),) for m in FINE}
    best = max(FINE, key=lambda m: res[m][2])
    bestc = max(COARSE, key=lambda m: res[m][2])
    print("fine grid  : max local significance %.2f sigma at %d GeV" % (res[best][2], best))
    print("coarse grid: max local significance %.2f sigma at %d GeV" % (res[bestc][2], bestc))
    for m in [500, 530, 600]:
        print("  M=%d  obs %.2f  exp %.2f  signif %.2f" % ((m,) + res[m]))

    c = ROOT.TCanvas("c", "", 1100, 1150)
    pads = []
    edges = [(0.66, 1.0), (0.36, 0.66), (0.0, 0.36)]
    for k, (y0, y1) in enumerate(edges):
        c.cd()
        p = ROOT.TPad("p%d" % k, "", 0, y0, 1, y1)
        p.SetLeftMargin(0.12)
        p.SetRightMargin(0.03)
        p.SetTopMargin(0.12 if k == 0 else 0.02)
        p.SetBottomMargin(0.02 if k < 2 else 0.20)
        p.Draw()
        pads.append(p)
    keep = []


    def frame(name, ymin, ymax, ytitle, xlabels):
        h = ROOT.TH1F(name, "", 10, 200, 1000)
        h.SetMinimum(ymin)
        h.SetMaximum(ymax)
        for ax in [h.GetXaxis(), h.GetYaxis()]:
            ax.SetLabelFont(FONT)
            ax.SetLabelSize(21 if xlabels or ax == h.GetYaxis() else 0)
            ax.SetTitleFont(FONT)
            ax.SetTitleSize(23)
        h.GetYaxis().SetTitle(ytitle)
        h.GetYaxis().SetTitleOffset(1.6)
        h.GetYaxis().SetNdivisions(505)
        if xlabels:
            h.GetXaxis().SetTitle("Signal mass hypothesis M (GeV)")
            h.GetXaxis().SetTitleOffset(1.0)
        h.Draw("axis")
        return h


    def vline(pad_ymin, pad_ymax):
        l = ROOT.TLine(M_TRUE, pad_ymin, M_TRUE, pad_ymax)
        l.SetLineColor(RED)
        l.SetLineStyle(3)
        l.SetLineWidth(2)
        l.Draw()
        return l


    def grid_markers(ymin, ymax):
        out = []
        for m in COARSE:
            l = ROOT.TLine(m, ymin, m, ymin + 0.06 * (ymax - ymin))
            l.SetLineColor(ROOT.kGray + 2)
            l.SetLineWidth(3)
            l.Draw()
            out.append(l)
        return out


    # ---- top: spectrum ----
    pads[0].cd()
    pads[0].SetLogy()
    f = ROOT.TFile.Open("mass/mass.root")
    bkg, inj, data = [f.Get(n).Clone(n + "_c") for n in ["bkg", "injected", "data_obs"]]
    f.Close()
    fr0 = frame("fr0", 0.5, 5e3, "Events / 20 GeV", False)
    bkg.SetFillColor(ORANGE)
    bkg.SetLineColor(ROOT.kBlack)
    bkg.Draw("hist same")
    tot = bkg.Clone("tot")
    tot.Add(inj)
    tot.SetLineColor(RED)
    tot.SetLineWidth(3)
    tot.SetFillStyle(0)
    tot.Draw("hist same")
    gd = ROOT.TGraphAsymmErrors(data)
    for i in range(gd.GetN()):
        gd.SetPointEXlow(i, 0)
        gd.SetPointEXhigh(i, 0)
    gd.SetLineColor(ROOT.kBlack)
    gd.SetLineWidth(2)
    gd.SetMarkerStyle(20)
    gd.SetMarkerSize(1.2)
    gd.Draw("p same")
    leg = ROOT.TLegend(0.55, 0.55, 0.96, 0.85)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextFont(FONT)
    leg.SetTextSize(19)
    leg.AddEntry(gd, "Data", "pe")
    leg.AddEntry(bkg, "Background", "f")
    leg.AddEntry(tot, "+ real signal at %d GeV" % M_TRUE, "l")
    leg.Draw()
    t = ROOT.TLatex()
    t.SetNDC()
    t.SetTextFont(FONT)
    t.SetTextSize(23)
    t.DrawLatex(0.12, 0.90, "#bf{Toy analysis} #it{narrow resonance, 10 GeV resolution}")
    pads[0].RedrawAxis()
    keep += [fr0, bkg, tot, gd, leg, t, vline(0.5, 5e3)]

    # ---- middle: limits ----
    pads[1].cd()
    lmax = 1.25 * max(r[0] for r in res.values())
    fr1 = frame("fr1", 0, lmax, "95% CL limit on r", False)
    gf_o, gf_e, gc_o, gc_e = ROOT.TGraph(), ROOT.TGraph(), ROOT.TGraph(), ROOT.TGraph()
    for i, m in enumerate(FINE):
        gf_o.SetPoint(i, m, res[m][0])
        gf_e.SetPoint(i, m, res[m][1])
    for i, m in enumerate(COARSE):
        gc_o.SetPoint(i, m, res[m][0])
        gc_e.SetPoint(i, m, res[m][1])
    for g, col, ls, w, mk in [(gf_e, ROOT.kGray + 2, 2, 2, 0), (gf_o, ROOT.kBlack, 1, 3, 0),
                              (gc_o, BLUE, 1, 3, 21)]:
        g.SetLineColor(col)
        g.SetLineStyle(ls)
        g.SetLineWidth(w)
        g.SetMarkerColor(col)
        g.SetMarkerStyle(mk if mk else 1)
        g.SetMarkerSize(1.6)
        g.Draw("lp same" if mk else "l same")
    leg1 = ROOT.TLegend(0.55, 0.62, 0.96, 0.95)
    leg1.SetBorderSize(0)
    leg1.SetFillStyle(0)
    leg1.SetTextFont(FONT)
    leg1.SetTextSize(19)
    leg1.AddEntry(gf_o, "Observed, 10 GeV scan", "l")
    leg1.AddEntry(gf_e, "Expected, 10 GeV scan", "l")
    leg1.AddEntry(gc_o, "Observed, 100 GeV grid", "lp")
    leg1.Draw()
    pads[1].RedrawAxis()
    keep += [fr1, gf_o, gf_e, gc_o, gc_e, leg1, vline(0, lmax)] + grid_markers(0, lmax)

    # ---- bottom: local significance ----
    pads[2].cd()
    zmax = 1.3 * max(r[2] for r in res.values())
    fr2 = frame("fr2", 0, zmax, "Local significance (#sigma)", True)
    gz_f, gz_c = ROOT.TGraph(), ROOT.TGraph()
    for i, m in enumerate(FINE):
        gz_f.SetPoint(i, m, res[m][2])
    for i, m in enumerate(COARSE):
        gz_c.SetPoint(i, m, res[m][2])
    gz_f.SetLineColor(ROOT.kBlack)
    gz_f.SetLineWidth(3)
    gz_f.Draw("l same")
    gz_c.SetLineColor(BLUE)
    gz_c.SetMarkerColor(BLUE)
    gz_c.SetMarkerStyle(21)
    gz_c.SetMarkerSize(1.6)
    gz_c.SetLineWidth(3)
    gz_c.Draw("lp same")
    note = ROOT.TLatex()
    note.SetTextFont(FONT)
    note.SetTextSize(19)
    note.SetTextColor(ROOT.kBlack)
    note.DrawLatex(best + 15, res[best][2] - 0.15, "%.1f#sigma at %d GeV" % (res[best][2], best))
    note.SetTextColor(BLUE)
    note.DrawLatex(750, 0.75 * zmax, "100 GeV grid: max %.1f#sigma" % res[bestc][2])
    pads[2].RedrawAxis()
    keep += [fr2, gz_f, gz_c, note, vline(0, zmax)] + grid_markers(0, zmax)

    rootutil.save(c, "massgrid")


@rootutil.isolated
def prefit():
    """Pre-fit stacked plot of the toy: WZ + fakes, signal on top, data points.

Reads toy_shapes.root (made by cards.shapes_root()). The grey band is the pre-fit
background uncertainty: lnN normalisations (lumi 2% and wz_xs 10% on WZ,
fakes 30%) added in quadrature with the MC-stat bin errors.

Run it through its run_NN_*.py file (see docs/slide_map.md)."""
    rootutil.setup(ticks=False)
    ROOT.gStyle.SetOptTitle(0)

    LNN = {"WZ": [0.02, 0.10], "fakes": [0.30]}   # relative lnN sizes per process
    COLORS = {"WZ": ROOT.TColor.GetColor("#e8a33d"), "fakes": ROOT.TColor.GetColor("#8c8c8c")}
    LABELS = {"WZ": "WZ", "fakes": "Nonprompt (fakes)"}

    f = ROOT.TFile.Open("toy_shapes.root")
    h = {p: f.Get(p) for p in ["sig", "WZ", "fakes", "data_obs"]}
    nb = h["data_obs"].GetNbinsX()

    # --- background stack (fakes at the bottom) ---
    stack = ROOT.THStack("stack", "")
    for p in ["fakes", "WZ"]:
        h[p].SetFillColor(COLORS[p])
        h[p].SetLineColor(ROOT.kBlack)
        h[p].SetLineWidth(1)
        stack.Add(h[p])

    # --- total background + uncertainty band ---
    tot = h["WZ"].Clone("tot")
    tot.Add(h["fakes"])
    for i in range(1, nb + 1):
        var = 0.0
        for p, sizes in LNN.items():
            y = h[p].GetBinContent(i)
            var += sum((s * y) ** 2 for s in sizes)   # normalisation uncertainties
            var += h[p].GetBinError(i) ** 2           # MC statistics
        tot.SetBinError(i, var ** 0.5)
    tot.SetFillColor(ROOT.kBlack)
    tot.SetFillStyle(3354)
    tot.SetMarkerSize(0)
    tot.SetLineWidth(0)

    # --- signal stacked on top of the background, as a line ---
    sig_on_top = tot.Clone("sig_on_top")
    sig_on_top.Add(h["sig"])
    sig_on_top.SetFillStyle(0)
    sig_on_top.SetLineColor(ROOT.TColor.GetColor("#c0392b"))
    sig_on_top.SetLineWidth(3)
    sig_on_top.SetLineStyle(2)

    # --- data with Garwood (Poisson) intervals ---
    data = ROOT.TGraphAsymmErrors()
    for i in range(1, nb + 1):
        n = h["data_obs"].GetBinContent(i)
        lo = 0.0 if n == 0 else ROOT.Math.gamma_quantile(0.1586555, n, 1.0)
        hi = ROOT.Math.gamma_quantile_c(0.1586555, n + 1, 1.0)
        x = h["data_obs"].GetBinCenter(i)
        data.SetPoint(i - 1, x, n)
        data.SetPointError(i - 1, 0, 0, n - lo, hi - n)
    data.SetMarkerStyle(20)
    data.SetMarkerSize(1.3)
    data.SetLineWidth(2)

    # --- draw ---
    c = ROOT.TCanvas("c", "", 900, 700)
    c.SetLeftMargin(0.13)
    c.SetBottomMargin(0.12)
    c.SetLogy()
    stack.SetMinimum(0.5)
    stack.SetMaximum(2000)
    stack.Draw("hist")
    ax = stack.GetXaxis()
    for i in range(1, nb + 1):
        ax.SetBinLabel(i, "b%d" % i)
    ax.SetLabelSize(0.055)
    stack.GetYaxis().SetTitle("Events")
    stack.GetYaxis().SetTitleSize(0.05)
    stack.GetYaxis().SetLabelSize(0.045)
    tot.Draw("e2 same")
    sig_on_top.Draw("hist same")
    data.Draw("p same")

    leg = ROOT.TLegend(0.55, 0.62, 0.88, 0.88)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextSize(0.038)
    leg.AddEntry(data, "Data", "pe")
    leg.AddEntry(h["WZ"], LABELS["WZ"], "f")
    leg.AddEntry(h["fakes"], LABELS["fakes"], "f")
    leg.AddEntry(tot, "Bkg. uncertainty (pre-fit)", "f")
    leg.AddEntry(sig_on_top, "Signal (r = 1) + bkg.", "l")
    leg.Draw()

    txt = ROOT.TLatex()
    txt.SetNDC()
    txt.SetTextSize(0.045)
    txt.DrawLatex(0.15, 0.91, "#bf{Toy analysis} #it{pre-fit}")

    rootutil.save(c, "prefit")


@rootutil.isolated
def scan2d_degenerate():
    """2D likelihood scan of the two degenerate fakes normalisations (slide 14).

Colour: 2*DeltaNLL from MultiDimFit --algo grid. Dashed: fakes_norm x
fakes_extra = best-fit product, the flat valley along which the fit cannot
choose. Star: the point the minimizer happened to stop at.

Run it through its run_NN_*.py file (see docs/slide_map.md)."""
    rootutil.setup(ticks=False)
    ROOT.gStyle.SetPalette(ROOT.kBird)
    ROOT.gStyle.SetNumberContours(60)
    FONT = rootutil.FONT

    f = ROOT.TFile.Open("higgsCombine.conv_scan2d.MultiDimFit.mH120.root")
    t = f.Get("limit")
    pts, best = [], None
    for e in t:
        if e.quantileExpected == -1:      # best-fit point
            best = (e.fakes_norm, e.fakes_extra)
            continue
        pts.append((e.fakes_norm, e.fakes_extra, 2 * e.deltaNLL))
    f.Close()

    xs = sorted(set(round(p[0], 6) for p in pts))
    ys = sorted(set(round(p[1], 6) for p in pts))
    dx, dy = xs[1] - xs[0], ys[1] - ys[0]
    h = ROOT.TH2F("h", "", len(xs), xs[0] - dx / 2, xs[-1] + dx / 2,
                  len(ys), ys[0] - dy / 2, ys[-1] + dy / 2)
    for x, y, z in pts:
        h.Fill(x, y, min(z, 20))
    h.SetMinimum(0)
    h.SetMaximum(20)

    c = ROOT.TCanvas("c", "", 900, 780)
    c.SetLeftMargin(0.13)
    c.SetRightMargin(0.16)
    c.SetTopMargin(0.09)
    c.SetBottomMargin(0.12)
    for ax in [h.GetXaxis(), h.GetYaxis(), h.GetZaxis()]:
        ax.SetLabelFont(FONT)
        ax.SetLabelSize(22)
        ax.SetTitleFont(FONT)
        ax.SetTitleSize(24)
    h.GetXaxis().SetTitle("fakes_norm")
    h.GetYaxis().SetTitle("fakes_extra")
    h.GetZaxis().SetTitle("2#DeltaNLL")
    h.GetYaxis().SetTitleOffset(1.4)
    h.GetZaxis().SetTitleOffset(1.3)
    h.Draw("colz")

    prod = best[0] * best[1] if best else 1.0
    valley = ROOT.TF1("valley", "%f/x" % prod, 0.2, 3)
    valley.SetLineColor(ROOT.kRed + 1)
    valley.SetLineStyle(2)
    valley.SetLineWidth(3)
    valley.Draw("same")
    if best:
        m = ROOT.TMarker(best[0], best[1], 29)
        m.SetMarkerSize(3)
        m.SetMarkerColor(ROOT.kRed + 1)
        m.Draw()

    t2 = ROOT.TLatex()
    t2.SetNDC()
    t2.SetTextFont(FONT)
    t2.SetTextSize(24)
    t2.DrawLatex(0.13, 0.93, "#bf{Toy analysis} #it{two rateParams on fakes}")
    t2.SetTextSize(21)
    t2.SetTextColor(ROOT.kRed + 1)
    t2.DrawLatex(0.50, 0.80, "flat valley: norm #times extra = %.2f" % prod)
    t2.DrawLatex(0.50, 0.75, "the fit cannot pick a point on it")
    c.RedrawAxis()
    rootutil.save(c, "scan2d_degenerate")


@rootutil.isolated
def scan2d_r_wznorm():
    """2D likelihood scans of r vs wz_norm for the degeneracy demo (slide 15).

Three panels, same axes: distinct shapes / signal-like WZ / signal-like WZ +
control region. Colour: 2*DeltaNLL. White line: 68% CL contour (2DNLL = 2.30).
Star: true values (r = 1, wz_norm = 1; Asimov data with signal).

Run it through its run_NN_*.py file (see docs/slide_map.md)."""
    rootutil.setup(ticks=False)
    ROOT.gStyle.SetPalette(ROOT.kBird)
    ROOT.gStyle.SetNumberContours(60)
    FONT = rootutil.FONT
    ZMAX = 12
    PANELS = [("distinct", "distinct shapes"),
              ("degen", "signal-like WZ"),
              ("degen_cr", "signal-like WZ + CR")]


    def scan_hist(tag, k):
        f = ROOT.TFile.Open("higgsCombine.dg_scan_%s.MultiDimFit.mH120.root" % tag)
        pts = [(e.r, e.wz_norm, 2 * e.deltaNLL) for e in f.Get("limit") if e.quantileExpected != -1]
        f.Close()
        xs = sorted(set(round(p[0], 6) for p in pts))
        ys = sorted(set(round(p[1], 6) for p in pts))
        dx, dy = xs[1] - xs[0], ys[1] - ys[0]
        h = ROOT.TH2F("h%d" % k, "", len(xs), xs[0] - dx / 2, xs[-1] + dx / 2,
                      len(ys), ys[0] - dy / 2, ys[-1] + dy / 2)
        # start every cell at the maximum: points where the fit failed (e.g.
        # negative r with a small background gives negative yields) stay "far"
        for ix in range(1, h.GetNbinsX() + 1):
            for iy in range(1, h.GetNbinsY() + 1):
                h.SetBinContent(ix, iy, ZMAX)
        for x, y, z in pts:
            if z == z and abs(z) < 1e9:   # skip NaN / inf
                h.SetBinContent(h.FindBin(x, y), min(max(z, 0), ZMAX))
        h.SetMinimum(0)
        h.SetMaximum(ZMAX)
        return h


    c = ROOT.TCanvas("c", "", 1650, 600)
    widths = [0.31, 0.31, 0.38]   # last pad holds the colour bar
    x0 = 0.0
    keep = []
    for k, ((tag, title), w) in enumerate(zip(PANELS, widths)):
        c.cd()
        p = ROOT.TPad("p%d" % k, "", x0, 0, x0 + w, 1)
        x0 += w
        p.SetLeftMargin(0.17 * 0.31 / w)
        p.SetRightMargin(0.03 if k < 2 else 0.20)
        p.SetTopMargin(0.10)
        p.SetBottomMargin(0.14)
        p.Draw()
        p.cd()
        h = scan_hist(tag, k)
        for ax in [h.GetXaxis(), h.GetYaxis(), h.GetZaxis()]:
            ax.SetLabelFont(FONT)
            ax.SetLabelSize(21)
            ax.SetTitleFont(FONT)
            ax.SetTitleSize(23)
        h.GetXaxis().SetTitle("r (signal strength)")
        h.GetYaxis().SetTitle("wz_norm (WZ normalisation)")
        h.GetZaxis().SetTitle("2#DeltaNLL")
        h.GetXaxis().SetTitleOffset(1.2)
        h.GetYaxis().SetTitleOffset(1.5)
        h.GetZaxis().SetTitleOffset(1.2)
        h.Draw("colz" if k == 2 else "col")
        cont = h.Clone("cont%d" % k)
        cont.SetContour(1, array.array("d", [2.30]))
        cont.SetLineColor(ROOT.kWhite)
        cont.SetLineWidth(3)
        cont.Draw("cont3 same")
        star = ROOT.TMarker(1.0, 1.0, 29)
        star.SetMarkerSize(3)
        star.SetMarkerColor(ROOT.kRed + 1)
        star.Draw()
        t = ROOT.TLatex()
        t.SetNDC()
        t.SetTextFont(FONT)
        t.SetTextSize(23)
        t.DrawLatex(p.GetLeftMargin(), 0.92, "#bf{Toy} #it{%s}" % title)
        p.RedrawAxis()
        keep += [p, h, cont, star, t]

    rootutil.save(c, "scan2d_r_wznorm")


@rootutil.isolated
def spiky_bkg():
    """Why the spiky template changes the limit (slide 13).

One column, shared bin axis, so each bin lines up top to bottom:
  Top:    the toy at 10x luminosity: background stack, signal, Asimov data
          -> where the signal is.
  Bottom: uncertainty on the total background from wz_shape, per bin, as a %
          of the background: prior (dashed) and post-fit (solid; prior x
          post-fit width of wz_shape, background-only fit), for the smooth
          truth and the spiky template. Grey: statistical precision of the
          data (1/sqrt(N)). Template effect = (up - down)/2.
Highlighted across both panels: b4 (where the spike is) and b5 (where the
signal is).

Run it through its run_NN_*.py file (see docs/slide_map.md)."""
    rootutil.setup(ticks=True)
    FONT = rootutil.FONT
    NB = 5
    COL = {"WZ": ROOT.TColor.GetColor("#e8a33d"), "fakes": ROOT.TColor.GetColor("#8c8c8c")}
    RED = ROOT.TColor.GetColor("#c0392b")
    SIGCOL = ROOT.TColor.GetColor("#7b3294")
    HL_SPIKE = ROOT.TColor.GetColor("#fde0dd")   # light red: the spike
    HL_SIG = ROOT.TColor.GetColor("#e8e0f0")     # light purple: the signal
    SPIKE_BIN, SIG_BIN = 4, 5                    # 1-based


    def get(variant, name):
        f = ROOT.TFile.Open("spiky/shapes_%s.root" % variant)
        h = f.Get(name).Clone("%s_%s" % (variant, name))
        f.Close()
        return h


    def post_width(variant):
        f = ROOT.TFile.Open("fitDiagnostics.spiky_%s.root" % variant)
        w = f.Get("fit_b").floatParsFinal().find("wz_shape").getError()
        f.Close()
        return w


    def style(h, labels, ytitle):
        for ax in [h.GetXaxis(), h.GetYaxis()]:
            ax.SetLabelFont(FONT)
            ax.SetLabelSize(22)
            ax.SetTitleFont(FONT)
            ax.SetTitleSize(23)
        h.GetYaxis().SetTitle(ytitle)
        h.GetYaxis().SetTitleOffset(1.7)
        for i in range(NB):
            h.GetXaxis().SetBinLabel(i + 1, "b%d" % (i + 1) if labels else "")
        if labels:
            h.GetXaxis().SetLabelSize(28)
            h.GetXaxis().SetLabelOffset(0.015)


    def highlight(ymin, ymax):
        out = []
        for b, col in [(SPIKE_BIN, HL_SPIKE), (SIG_BIN, HL_SIG)]:
            box = ROOT.TBox(b - 1, ymin, b, ymax)
            box.SetFillColor(col)
            box.Draw()
            out.append(box)
        return out


    wz, fk, sg = get("smooth", "WZ"), get("smooth", "fakes"), get("smooth", "sig")
    bkg = [wz.GetBinContent(i + 1) + fk.GetBinContent(i + 1) for i in range(NB)]

    c = ROOT.TCanvas("c", "", 1100, 1000)
    top = ROOT.TPad("top", "", 0, 0.52, 1, 1)
    bot = ROOT.TPad("bot", "", 0, 0, 1, 0.52)
    for p in (top, bot):
        p.SetLeftMargin(0.12)
        p.SetRightMargin(0.03)
        p.Draw()
    top.SetTopMargin(0.10)
    top.SetBottomMargin(0.015)
    bot.SetTopMargin(0.015)
    bot.SetBottomMargin(0.14)
    keep = []

    # ---- top: where the signal is ----
    top.cd()
    top.SetLogy()
    fr1 = ROOT.TH1F("fr1", "", NB, 0, NB)
    fr1.SetMinimum(5)
    fr1.SetMaximum(3e4)
    style(fr1, False, "Events")
    fr1.Draw("axis")
    keep += highlight(5, 3e4)
    # stacked by hand: total (WZ on top of fakes), then fakes in front
    tot = wz.Clone("tot")
    tot.Add(fk)
    for h, name in [(tot, "WZ"), (fk, "fakes"), (wz, "WZ")]:
        h.SetFillColor(COL[name])
        h.SetLineColor(ROOT.kBlack)
    tot.Draw("hist same")
    fk.Draw("hist same")
    sb = wz.Clone("sb")
    sb.Add(fk)
    sb.Add(sg)
    sb.SetLineColor(SIGCOL)
    sb.SetLineWidth(4)
    sb.SetLineStyle(2)
    sb.SetFillStyle(0)
    sb.Draw("hist same")
    gd = ROOT.TGraph()
    for i, b in enumerate(bkg):
        gd.SetPoint(i, i + 0.5, b)
    gd.SetMarkerStyle(20)
    gd.SetMarkerSize(1.6)
    gd.Draw("p same")
    leg = ROOT.TLegend(0.14, 0.63, 0.46, 0.88)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextFont(FONT)
    leg.SetTextSize(19)
    leg.AddEntry(gd, "Data (Asimov, no signal)", "p")
    leg.AddEntry(wz, "WZ", "f")
    leg.AddEntry(fk, "Fakes", "f")
    leg.AddEntry(sb, "Signal (r = 1) + bkg", "l")
    leg.Draw()
    lab = ROOT.TLatex()
    lab.SetTextFont(FONT)
    lab.SetTextSize(20)
    lab.SetTextAlign(22)
    lab.SetTextColor(RED)
    lab.DrawLatex(SPIKE_BIN - 0.5, 1.3e4, "#bf{the spike}")
    lab.SetTextColor(SIGCOL)
    lab.DrawLatex(SIG_BIN - 0.5, 1.3e4, "#bf{the signal}")
    lab.SetTextColor(SIGCOL)
    lab.SetTextSize(18)
    lab.DrawLatex(SIG_BIN - 0.5, 4.5e3, "sig = 2#times bkg")
    t = ROOT.TLatex()
    t.SetNDC()
    t.SetTextFont(FONT)
    t.SetTextSize(24)
    t.DrawLatex(0.12, 0.92, "#bf{Toy analysis} #it{spiky WZ shape template}")
    t.SetTextAlign(31)
    t.SetTextSize(20)
    t.DrawLatex(0.97, 0.92, "10#times lumi")
    top.RedrawAxis()
    keep += [fr1, tot, sb, gd, leg, lab, t]

    # ---- bottom: background uncertainty per bin ----
    bot.cd()
    fr2 = ROOT.TH1F("fr2", "", NB, 0, NB)
    fr2.SetMinimum(0)
    fr2.SetMaximum(26)
    style(fr2, True, "WZ-shape unc. on bkg (%)")
    fr2.Draw("axis")
    keep += highlight(0, 26)
    stat = ROOT.TH1F("stat", "", NB, 0, NB)
    for i, b in enumerate(bkg):
        stat.SetBinContent(i + 1, 100.0 / b ** 0.5)
    stat.SetFillColor(ROOT.TColor.GetColor("#d9d9d9"))
    stat.SetFillStyle(3001)
    stat.SetLineColor(ROOT.TColor.GetColor("#bdbdbd"))
    stat.Draw("hist same")

    leg2 = ROOT.TLegend(0.14, 0.58, 0.58, 0.95)
    leg2.SetBorderSize(0)
    leg2.SetFillStyle(0)
    leg2.SetTextFont(FONT)
    leg2.SetTextSize(19)
    leg2.AddEntry(stat, "Data statistical precision", "f")
    vals = {}
    for variant, label, col in [("smooth", "Smooth (truth)", ROOT.kBlack), ("spiky", "Spiky", RED)]:
        up, dn = get(variant, "WZ_wz_shapeUp"), get(variant, "WZ_wz_shapeDown")
        w = post_width(variant)
        pre = ROOT.TH1F("pre_" + variant, "", NB, 0, NB)
        post = ROOT.TH1F("post_" + variant, "", NB, 0, NB)
        for i in range(NB):
            eff = 100 * abs(up.GetBinContent(i + 1) - dn.GetBinContent(i + 1)) / 2 / bkg[i]
            pre.SetBinContent(i + 1, eff)
            post.SetBinContent(i + 1, eff * w)
        for h, ls, lw in [(pre, 2, 2), (post, 1, 5)]:
            h.SetLineColor(col)
            h.SetLineStyle(ls)
            h.SetLineWidth(lw)
            h.Draw("hist same")
        leg2.AddEntry(pre, "%s, prior" % label, "l")
        leg2.AddEntry(post, "%s, post-fit" % label, "l")
        vals[variant] = (pre, post)
        keep += [up, dn, pre, post]
    leg2.Draw()

    # numbers where it matters
    num = ROOT.TLatex()
    num.SetTextFont(FONT)
    num.SetTextSize(19)
    num.SetTextAlign(22)
    num.SetTextColor(RED)
    p_spike = vals["spiky"][0].GetBinContent(SPIKE_BIN)
    num.DrawLatex(SPIKE_BIN - 0.5, p_spike + 1.6, "prior %.0f%%" % p_spike)
    num.DrawLatex(SPIKE_BIN - 0.5, p_spike + 3.4, "#bf{data reject it}")
    num.SetTextColor(ROOT.kBlack)
    s_true = vals["smooth"][1].GetBinContent(SIG_BIN)
    s_spik = vals["spiky"][1].GetBinContent(SIG_BIN)
    num.DrawLatex(SIG_BIN - 0.5, 24.2, "#bf{post-fit}")
    num.DrawLatex(SIG_BIN - 0.5, 22.3, "truth %.0f%%" % s_true)
    num.SetTextColor(RED)
    num.DrawLatex(SIG_BIN - 0.5, 20.4, "spiky %.0f%%" % s_spik)
    bot.RedrawAxis()
    keep += [fr2, stat, leg2, num]

    rootutil.save(c, "spiky_bkg")


@rootutil.isolated
def spiky_templates():
    """Template ratios for the spiky-template demo (slide 13): WZ up/down
variations divided by nominal, per bin, for the true smooth tilt, the spiky
version, and the smoothed patch.

Run it through its run_NN_*.py file (see docs/slide_map.md)."""
    rootutil.setup(ticks=True)
    FONT = rootutil.FONT

    VARIANTS = [  # (variant, label, color, line style, marker); drawn in this order
        ("smoothed", "Patch: straight-line fit", ROOT.TColor.GetColor("#2c7bb6"), 1, 0),
        ("spiky", "Spiky template (low-stat MC)", ROOT.TColor.GetColor("#c0392b"), 1, 20),
        ("smooth", "True effect (smooth tilt)", ROOT.kBlack, 2, 0),
    ]
    LEGEND_ORDER = ["smooth", "spiky", "smoothed"]

    c = ROOT.TCanvas("c", "", 1000, 620)
    c.SetLeftMargin(0.12)
    c.SetRightMargin(0.04)
    c.SetTopMargin(0.10)
    c.SetBottomMargin(0.12)
    fr = ROOT.TH1F("fr", "", 5, 0, 5)
    for i in range(5):
        fr.GetXaxis().SetBinLabel(i + 1, "b%d" % (i + 1))
    fr.SetMinimum(0.62)
    fr.SetMaximum(1.42)
    for ax in [fr.GetXaxis(), fr.GetYaxis()]:
        ax.SetLabelFont(FONT)
        ax.SetLabelSize(24)
        ax.SetTitleFont(FONT)
        ax.SetTitleSize(26)
    fr.GetYaxis().SetTitle("WZ variation / nominal")
    fr.GetYaxis().SetTitleOffset(1.3)
    fr.Draw("axis")
    one = ROOT.TLine(0, 1, 5, 1)
    one.SetLineColor(ROOT.kGray + 1)
    one.Draw()

    keep = []
    entries = {}
    leg = ROOT.TLegend(0.14, 0.68, 0.62, 0.88)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextFont(FONT)
    leg.SetTextSize(21)
    for v, label, col, ls, mk in VARIANTS:
        f = ROOT.TFile.Open("spiky/shapes_%s.root" % v)
        nom = f.Get("WZ")
        for tag, width in [("Up", 4), ("Down", 2)]:
            h = f.Get("WZ_wz_shape" + tag).Clone("%s_%s" % (v, tag))
            h.Divide(nom)
            h.SetLineColor(col)
            h.SetLineStyle(ls)
            h.SetLineWidth(width)
            h.SetMarkerColor(col)
            if mk:  # spiky: markers only, filled = up, open = down
                h.SetMarkerStyle(20 if tag == "Up" else 24)
                h.SetMarkerSize(2.0)
                h.Draw("p same")
                entries.setdefault(v, []).append((h, "%s, %s" % (label, tag.lower()), "p"))
            else:
                h.Draw("hist same")
                if tag == "Up":
                    entries.setdefault(v, []).append((h, label, "l"))
            keep.append(h)
        f.Close()
    for v in LEGEND_ORDER:
        for h, label, opt in entries[v]:
            leg.AddEntry(h, label, opt)
    leg.Draw()
    t = ROOT.TLatex()
    t.SetNDC()
    t.SetTextFont(FONT)
    t.SetTextSize(24)
    t.DrawLatex(0.12, 0.92, "#bf{Toy analysis} #it{WZ shape uncertainty}")
    t.SetTextAlign(31)
    t.SetTextSize(20)
    t.DrawLatex(0.96, 0.92, "lines: thick = up, thin = down")
    c.RedrawAxis()
    rootutil.save(c, "spiky_templates")


@rootutil.isolated
def pulls(fits, labels, out, truth=None, ytitle="Post-fit #theta  (prior units)"):
    """Plot post-fit nuisance values (pulls) from FitDiagnostics background-only fits.

Each --fit gives one marker series: "Label|fitDiagnostics file|n1,n2,n3", where
the nuisance names line up with --labels (one x position each). Repeating a
name (e.g. one shared nuisance) plots the same value at every position.
Optionally --truth "1.5,0,-1.5" marks the shifts injected into the pseudo-data.

lnN nuisances have a unit-Gaussian prior: the grey band is the prior +-1 sigma.

Usage:
  pulls(fits=["Shared|fitDiagnostics.a.root|fakes,fakes,fakes", "Per era|fitDiagnostics.b.root|fakes_2022,fakes_2023,fakes_2024"], labels=[...], out=NAME)"""
    rootutil.setup(ticks=False)


    n = len(labels)
    COLORS = [ROOT.TColor.GetColor(c) for c in ["#2c7bb6", "#d7191c", "#1a9641", "#7b3294"]]
    MARKERS = [20, 21, 22, 23]

    series = []
    for spec in fits:
        label, fname, names = spec.split("|")
        f = ROOT.TFile.Open(fname)
        fit = f.Get("fit_b")
        status = fit.status()
        pars = fit.floatParsFinal()
        vals = []
        for nm in names.split(","):
            p = pars.find(nm)
            vals.append((p.getVal(), p.getError()))
        f.Close()
        series.append((label, vals))
        print("%-24s (fit status %d) " % (label, status)
              + "  ".join("%s %+.2f +- %.2f" % (l, v, e) for l, (v, e) in zip(labels, vals)))

    W, H = 1100, 650
    c = ROOT.TCanvas("c", "", W, H)
    c.SetLeftMargin(0.12)
    c.SetRightMargin(0.04)
    c.SetTopMargin(0.14)
    c.SetBottomMargin(0.12)
    frame = ROOT.TH1F("frame", "", n, 0, n)
    for i, l in enumerate(labels):
        frame.GetXaxis().SetBinLabel(i + 1, l)
    frame.SetMinimum(-3)
    frame.SetMaximum(3)
    for ax in [frame.GetXaxis(), frame.GetYaxis()]:
        ax.SetLabelFont(43)
        ax.SetLabelSize(28)
        ax.SetTitleFont(43)
        ax.SetTitleSize(28)
    frame.GetYaxis().SetTitle(ytitle)
    frame.GetYaxis().SetTitleOffset(1.3)
    frame.Draw("axis")

    band = ROOT.TBox(0, -1, n, 1)
    band.SetFillColorAlpha(ROOT.kGray, 0.45)
    band.Draw()
    zero = ROOT.TLine(0, 0, n, 0)
    zero.SetLineStyle(2)
    zero.Draw()

    keep = []
    leg = ROOT.TLegend(0.12, 0.87, 0.96, 0.99)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetNColumns(len(series) + (1 if truth is not None else 0))
    leg.SetTextFont(43)
    leg.SetTextSize(26)

    if truth is not None:
        gt = ROOT.TGraph()
        for i, t in enumerate(truth):
            gt.SetPoint(i, i + 0.5, t)
        gt.SetMarkerStyle(29)
        gt.SetMarkerSize(3.2)
        gt.SetMarkerColor(ROOT.kGray + 2)
        gt.Draw("p same")
        keep.append(gt)
        leg.AddEntry(gt, "Injected shift", "p")

    ns = len(series)
    for k, (label, vals) in enumerate(series):
        g = ROOT.TGraphErrors()
        for i, (v, e) in enumerate(vals):
            x = i + 0.5 + (k - (ns - 1) / 2.0) * 0.18
            g.SetPoint(i, x, v)
            g.SetPointError(i, 0, e)
        g.SetMarkerStyle(MARKERS[k])
        g.SetMarkerSize(2.2)
        g.SetMarkerColor(COLORS[k])
        g.SetLineColor(COLORS[k])
        g.SetLineWidth(3)
        g.Draw("p same")
        keep.append(g)
        leg.AddEntry(g, label, "pe")

    leg.Draw()
    c.RedrawAxis()
    rootutil.save(c, out)


@rootutil.isolated
def gof(gof_specs, out, seed="1234", algo="saturated"):
    """Plot GoodnessOfFit toy distributions with the observed value and p-value.

Each --gof "Label|tag" reads
  higgsCombine.<tag>.obs.GoodnessOfFit.mH120.root         (observed)
  higgsCombine.<tag>.toys.GoodnessOfFit.mH120.<seed>.root (toys)
p-value = fraction of toys with test statistic >= observed.

Run it through its run_NN_*.py file (see docs/slide_map.md)."Label|tag" [--gof ...] [--seed 1234]"""
    rootutil.setup(ticks=False)



    def values(fname):
        f = ROOT.TFile.Open(fname)
        out = [e.limit for e in f.Get("limit")]
        f.Close()
        return out


    panels = []
    for spec in gof_specs:
        label, tag = spec.split("|")
        obs = values("higgsCombine.%s.obs.GoodnessOfFit.mH120.root" % tag)[0]
        toys = values("higgsCombine.%s.toys.GoodnessOfFit.mH120.%s.root" % (tag, seed))
        p = sum(1 for t in toys if t >= obs) / float(len(toys))
        panels.append((label, obs, toys, p))
        print("%-24s observed %.2f   p-value %.3f  (%d toys)" % (label, obs, p, len(toys)))

    n = len(panels)
    c = ROOT.TCanvas("c", "", 550 * n, 520)
    c.Divide(n, 1, 0.002, 0.002)
    xmax = 1.15 * max(max(max(t), o) for _, o, t, _ in panels)
    keep = []
    blue = ROOT.TColor.GetColor("#2c7bb6")
    for k, (label, obs, toys, p) in enumerate(panels):
        pad = c.cd(k + 1)
        pad.SetLeftMargin(0.16)
        pad.SetBottomMargin(0.15)
        pad.SetTopMargin(0.16)
        h = ROOT.TH1F("h%d" % k, "", 30, 0, xmax)
        for t in toys:
            h.Fill(t)
        h.SetFillColorAlpha(blue, 0.35)
        h.SetLineColor(blue)
        h.SetLineWidth(2)
        for ax in [h.GetXaxis(), h.GetYaxis()]:
            ax.SetLabelFont(43)
            ax.SetLabelSize(22)
            ax.SetTitleFont(43)
            ax.SetTitleSize(24)
        h.GetXaxis().SetTitle("Test statistic (%s)" % algo)
        h.GetYaxis().SetTitle("Toys")
        h.GetYaxis().SetTitleOffset(1.5)
        h.SetMaximum(1.3 * h.GetMaximum())
        h.Draw("hist")
        ar = ROOT.TArrow(obs, 0.55 * h.GetMaximum(), obs, 0, 0.025, "|>")
        ar.SetLineColor(ROOT.kRed + 1)
        ar.SetFillColor(ROOT.kRed + 1)
        ar.SetLineWidth(4)
        ar.Draw()
        t = ROOT.TLatex()
        t.SetNDC()
        t.SetTextFont(43)
        t.SetTextSize(26)
        t.DrawLatex(0.17, 0.89, "#bf{%s}" % label)
        t.SetTextSize(24)
        t.DrawLatex(0.55, 0.76, "#color[2]{observed}")
        t.DrawLatex(0.55, 0.69, "p = %.3f" % p)
        keep += [h, ar, t]

    rootutil.save(c, out)


@rootutil.isolated
def limit_table(specs, out="limits_baseline"):
    """Compare AsymptoticLimits results as horizontal expected bands.

For each row: green/yellow bands and dashed median from the Asimov run
(higgsCombine.<tag>.exp...), observed as a black point from the run on data
(higgsCombine.<tag>.obs...), unless the row is marked expected-only.

Usage:
  limit_table([("Label", "tag", False), ("Label", "tag", True)], out=NAME)   # True = expected only
Writes plots/<NAME>.pdf and .png."""
    rootutil.setup(ticks=False)



    rows = []
    for label, tag, exp_only in specs:
        exp = combine_outputs.read_quantiles(combine_outputs.limit_file(tag, "exp"))
        obs = None if exp_only else combine_outputs.read_quantiles(combine_outputs.limit_file(tag, "obs"))[-1.0]
        rows.append((label, exp, obs))
        print("%-34s exp median %.4f  obs %s" % (label, exp[0.5], "-" if obs is None else "%.4f" % obs))

    n = len(rows)
    # Fixed pixel layout: text sizes stay the same whatever the number of rows.
    W, ROW_H, TOP, BOT, LEFT, RIGHT = 1200, 70, 90, 100, 430, 40
    H = TOP + BOT + ROW_H * n
    c = ROOT.TCanvas("c", "", W, H)
    c.SetLeftMargin(LEFT / W)
    c.SetRightMargin(RIGHT / W)
    c.SetTopMargin(TOP / H)
    c.SetBottomMargin(BOT / H)
    xmax = 1.35 * max(max(r[1].values()) for r in rows)
    frame = ROOT.TH2F("frame", "", 10, 0, xmax, n, 0, n)
    for i, (label, _, _) in enumerate(rows):
        frame.GetYaxis().SetBinLabel(n - i, label)
    rootutil.axis_style(frame, label_size=26, title_size=28)
    frame.GetXaxis().SetTitle("95% CL upper limit on r")
    frame.GetXaxis().SetTitleOffset(1.3)
    frame.GetYaxis().SetTickLength(0)
    frame.Draw()

    keep = []
    green, yellow = rootutil.GREEN, rootutil.YELLOW
    num = ROOT.TLatex()
    num.SetTextFont(rootutil.FONT)
    num.SetTextSize(20)
    num.SetTextAlign(32)  # right, vertically centred
    for i, (label, exp, obs) in enumerate(rows):
        y0, y1 = n - i - 0.8, n - i - 0.2
        for lo, hi, col in [(0.025, 0.975, yellow), (0.16, 0.84, green)]:
            b = ROOT.TBox(exp[lo], y0, exp[hi], y1)
            b.SetFillColor(col)
            b.Draw()
            keep.append(b)
        m = ROOT.TLine(exp[0.5], y0, exp[0.5], y1)
        m.SetLineStyle(2)
        m.SetLineWidth(3)
        m.Draw()
        keep.append(m)
        text = "exp %.2f" % exp[0.5]
        if obs is not None:
            p = ROOT.TMarker(obs, 0.5 * (y0 + y1), 20)
            p.SetMarkerSize(2)
            p.Draw()
            keep.append(p)
            text += "   obs %.2f" % obs
        num.DrawLatex(0.98 * xmax, 0.5 * (y0 + y1), text)

    leg = ROOT.TLegend(LEFT / W, 1 - (TOP - 15) / H, 1 - RIGHT / W, 1 - 10 / H)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetNColumns(4)
    leg.SetTextFont(rootutil.FONT)
    leg.SetTextSize(26)
    dummy_obs = ROOT.TMarker(0, 0, 20)
    dummy_obs.SetMarkerSize(2)
    dummy_med = ROOT.TLine()
    dummy_med.SetLineStyle(2)
    dummy_med.SetLineWidth(3)
    dummy_g, dummy_y = ROOT.TH1F("g", "", 1, 0, 1), ROOT.TH1F("y", "", 1, 0, 1)
    dummy_g.SetFillColor(green)
    dummy_g.SetLineColor(green)
    dummy_y.SetFillColor(yellow)
    dummy_y.SetLineColor(yellow)
    if any(r[2] is not None for r in rows):
        leg.AddEntry(dummy_obs, "Observed", "p")
    leg.AddEntry(dummy_med, "Exp. median", "l")
    leg.AddEntry(dummy_g, "68% exp.", "f")
    leg.AddEntry(dummy_y, "95% exp.", "f")
    leg.Draw()
    c.RedrawAxis()

    rootutil.save(c, out)


@rootutil.isolated
def stack_systs(d="stack_systs/x1"):
    """How each systematic looks per era and in the stacked card (Up / nominal).

Four panels: B (correlated, size differs), C (anti-correlated rate),
D (anti-correlated shape), E (one per era). Thin coloured lines: the era
cards. Thick black: the stacked card (yield-weighted combination).

Usage: python3 plot_stack_systs.py <dir>   (after stack_eras.py) -> plots/stack_systs.*"""
    rootutil.setup(ticks=True)
    FONT = 43
    ERAS = ["2022", "2023", "2024"]
    WID = {"2022": 6, "2023": 2, "2024": 2}   # 2022 drawn wide underneath: visible when 2022 = 2023
    COL = {"2022": ROOT.TColor.GetColor("#2c7bb6"), "2023": ROOT.TColor.GetColor("#e8a33d"),
           "2024": ROOT.TColor.GetColor("#c0392b")}
    FILES = {t: ROOT.TFile.Open("%s/shapes_%s.root" % (d, t)) for t in ERAS + ["stacked"]}
    CARDS = {t: cards.parse_card("%s/card_%s.txt" % (d, t)) for t in ERAS + ["stacked"]}
    NB = 5


    def ratio(tag, proc, syst):
        """Up / nominal per bin, from a shape template or an lnN value."""
        procs, nuis = CARDS[tag]
        if syst not in nuis:
            return None
        typ, vals = nuis[syst]
        k = procs.index(proc)
        if vals[k] == "-":
            return None
        nom = FILES[tag].Get(proc)
        if typ == "lnN":
            return [float(vals[k])] * NB
        up = FILES[tag].Get("%s_%sUp" % (proc, syst))
        return [up.GetBinContent(b) / nom.GetBinContent(b) for b in range(1, NB + 1)]


    def graph(vals, col, width, style=1):
        g = ROOT.TGraph()
        for i, v in enumerate(vals):          # step line across each bin
            g.SetPoint(2 * i, i, v)
            g.SetPoint(2 * i + 1, i + 1, v)
        g.SetLineColor(col)
        g.SetLineWidth(width)
        g.SetLineStyle(style)
        return g


    PANELS = [("B", "WZ", "B: correlated, size differs"),
              ("C", "WZ", "C: anti-correlated rate"),
              ("D", "fakes", "D: anti-correlated shape"),
              ("E", "WZ", "E_<era>: one per era")]

    c = ROOT.TCanvas("c", "", 1400, 900)
    c.Divide(2, 2, 0.002, 0.002)
    keep = []
    for k, (syst, proc, title) in enumerate(PANELS):
        p = c.cd(k + 1)
        p.SetLeftMargin(0.14)
        p.SetRightMargin(0.03)
        p.SetTopMargin(0.12)
        p.SetBottomMargin(0.14)
        fr = ROOT.TH1F("fr%d" % k, "", NB, 0, NB)
        fr.SetMinimum(0.7)
        fr.SetMaximum(1.4)
        for i in range(NB):
            fr.GetXaxis().SetBinLabel(i + 1, "b%d" % (i + 1))
        for ax in [fr.GetXaxis(), fr.GetYaxis()]:
            ax.SetLabelFont(FONT)
            ax.SetLabelSize(22)
            ax.SetTitleFont(FONT)
            ax.SetTitleSize(22)
        fr.GetYaxis().SetTitle("%s: Up / nominal" % proc)
        fr.GetYaxis().SetTitleOffset(1.7)
        fr.GetYaxis().SetNdivisions(507)
        fr.Draw("axis")
        one = ROOT.TLine(0, 1, NB, 1)
        one.SetLineColor(ROOT.kGray + 1)
        one.SetLineStyle(2)
        one.Draw()
        leg = ROOT.TLegend(0.17, 0.62, 0.62, 0.86)
        leg.SetBorderSize(0)
        leg.SetFillStyle(0)
        leg.SetTextFont(FONT)
        leg.SetTextSize(18)
        leg.SetNColumns(2)
        items = []
        if syst == "E":
            for e in ERAS:
                r_era, r_stk = ratio(e, proc, "E_" + e), ratio("stacked", proc, "E_" + e)
                g1, g2 = graph(r_era, COL[e], WID[e]), graph(r_stk, COL[e], 4, 2)
                items += [g1, g2]
                leg.AddEntry(g1, "%s card" % e, "l")
                leg.AddEntry(g2, "stacked E_%s" % e, "l")
        else:
            for e in ERAS:
                g = graph(ratio(e, proc, syst), COL[e], WID[e])
                items.append(g)
                leg.AddEntry(g, "%s card" % e, "l")
            g = graph(ratio("stacked", proc, syst), ROOT.kBlack, 4)
            items.append(g)
            leg.AddEntry(g, "stacked card", "l")
        for g in items:
            g.Draw("l same")
        leg.Draw()
        t = ROOT.TLatex()
        t.SetNDC()
        t.SetTextFont(FONT)
        t.SetTextSize(22)
        t.DrawLatex(0.14, 0.91, "#bf{Toy analysis} #it{%s}" % title)
        p.RedrawAxis()
        keep += [fr, one, leg, t] + items

    rootutil.save(c, "stack_systs")


@rootutil.isolated
def stack_yields(d="stack_systs/x1"):
    """The underlying histograms: each era card and the stacked card.

Four panels (2022, 2023, 2024, stacked): WZ + fakes stacked, signal (r = 1)
on top as a dashed line, data as points, total background uncertainty as a
hatched band (MC stat + all systematics at +-1 sigma, added in quadrature).

Usage: python3 plot_stack_yields.py <dir>  (after stack_eras.py) -> plots/stack_yields.*"""
    rootutil.setup(ticks=True)
    ROOT.gStyle.SetHatchesLineWidth(1)
    ROOT.gStyle.SetHatchesLineWidth(1)
    FONT = 43
    TAGS = [("2022", "2022 card (20%)"), ("2023", "2023 card (16%)"),
            ("2024", "2024 card (64%)"), ("stacked", "Stacked card (all eras)")]
    ORANGE = ROOT.TColor.GetColor("#e8a33d")
    GREY = ROOT.TColor.GetColor("#8c8c8c")
    RED = ROOT.TColor.GetColor("#c0392b")
    NB = 5


    def bkg_unc(tag, f, procs, nuis):
        """Per-bin total background uncertainty: MC stat + every systematic."""
        var = [0.0] * NB
        for p in ["WZ", "fakes"]:
            nom = f.Get(p)
            for b in range(NB):
                var[b] += nom.GetBinError(b + 1) ** 2
        for name, (typ, vals) in nuis.items():   # each nuisance moves all bkg together
            for b in range(NB):
                shift = 0.0
                for p in ["WZ", "fakes"]:
                    v = vals[procs.index(p)]
                    if v == "-":
                        continue
                    n = f.Get(p).GetBinContent(b + 1)
                    if typ == "lnN":
                        shift += n * (float(v) - 1.0)
                    else:
                        shift += f.Get("%s_%sUp" % (p, name)).GetBinContent(b + 1) - n
                var[b] += shift ** 2
        return [math.sqrt(v) for v in var]


    c = ROOT.TCanvas("c", "", 1400, 1000)
    c.Divide(2, 2, 0.002, 0.002)
    keep = []
    for k, (tag, title) in enumerate(TAGS):
        f = ROOT.TFile.Open("%s/shapes_%s.root" % (d, tag))
        procs, nuis = cards.parse_card("%s/card_%s.txt" % (d, tag))
        wz, fk, sg, dt = [f.Get(n).Clone("%s_%d" % (n, k)) for n in ["WZ", "fakes", "sig", "data_obs"]]
        p = c.cd(k + 1)
        p.SetLogy()
        p.SetLeftMargin(0.13)
        p.SetRightMargin(0.03)
        p.SetTopMargin(0.10)
        p.SetBottomMargin(0.12)
        tot = wz.Clone("tot_%d" % k)
        tot.Add(fk)
        fr = ROOT.TH1F("fr%d" % k, "", NB, 0, NB)
        fr.SetMinimum(0.1)
        fr.SetMaximum(40 * tot.GetMaximum())
        for i in range(NB):
            fr.GetXaxis().SetBinLabel(i + 1, "b%d" % (i + 1))
        for ax in [fr.GetXaxis(), fr.GetYaxis()]:
            ax.SetLabelFont(FONT)
            ax.SetLabelSize(22)
            ax.SetTitleFont(FONT)
            ax.SetTitleSize(22)
        fr.GetYaxis().SetTitle("Events")
        fr.GetYaxis().SetTitleOffset(1.5)
        fr.Draw("axis")
        # stack by hand: fakes, then fakes + WZ on top
        for h, col in [(tot, ORANGE), (fk, GREY)]:
            h.SetFillColor(col)
            h.SetLineColor(ROOT.kBlack)
            h.SetLineWidth(1)
            h.Draw("hist same")
        unc = bkg_unc(tag, f, procs, nuis)
        band = tot.Clone("band_%d" % k)
        for b in range(NB):
            band.SetBinError(b + 1, unc[b])
        band.SetFillStyle(3354)
        band.SetFillColor(ROOT.kBlack)
        band.SetMarkerSize(0)
        band.Draw("e2 same")
        sb = tot.Clone("sb_%d" % k)
        sb.Add(sg)
        sb.SetFillStyle(0)
        sb.SetLineColor(RED)
        sb.SetLineStyle(2)
        sb.SetLineWidth(3)
        sb.Draw("hist same")
        gd = ROOT.TGraphAsymmErrors(dt)
        for i in range(gd.GetN()):
            n = dt.GetBinContent(i + 1)
            gd.SetPointEXlow(i, 0)
            gd.SetPointEXhigh(i, 0)
            gd.SetPointEYlow(i, math.sqrt(n))
            gd.SetPointEYhigh(i, math.sqrt(n))
        gd.SetMarkerStyle(20)
        gd.SetMarkerSize(1.3)
        gd.SetLineWidth(2)
        gd.SetLineColor(ROOT.kBlack)
        gd.Draw("p same")
        leg = ROOT.TLegend(0.50, 0.58, 0.96, 0.88)
        leg.SetBorderSize(0)
        leg.SetFillStyle(0)
        leg.SetTextFont(FONT)
        leg.SetTextSize(18)
        leg.AddEntry(gd, "Data", "pe")
        leg.AddEntry(tot, "WZ", "f")
        leg.AddEntry(fk, "Fakes", "f")
        leg.AddEntry(band, "Bkg. unc. (all syst. + MC stat)", "f")
        leg.AddEntry(sb, "Signal (r = 1) + bkg.", "l")
        leg.Draw()
        t = ROOT.TLatex()
        t.SetNDC()
        t.SetTextFont(FONT)
        t.SetTextSize(22)
        t.DrawLatex(0.13, 0.92, "#bf{Toy analysis} #it{%s}" % title)
        p.RedrawAxis()
        keep += [f, fr, tot, fk, band, sb, gd, leg, t, wz, sg, dt]

    rootutil.save(c, "stack_yields")


@rootutil.isolated
def emptytest():
    """The underlying histograms for the empty-bin backup: cases A, B, C.

Background (filled), signal r = 1 on top (dashed), data (points), bin 7
highlighted. Usage: python3 plot_emptytest.py (after run_15) -> plots/emptytest.*"""
    rootutil.setup(ticks=True)
    FONT = 43
    NB = 11
    ORANGE = ROOT.TColor.GetColor("#e8a33d")
    RED = ROOT.TColor.GetColor("#c0392b")
    CASES = [("A_data0", "A: bin 7 has no data"),
             ("B_both0", "B: bin 7 has no bkg. MC, no data"),
             ("C_bkg0", "C: bin 7 has no bkg. MC, 3 data events")]

    c = ROOT.TCanvas("c", "", 1800, 560)
    c.Divide(3, 1, 0.002, 0.002)
    keep = []
    for k, (case, title) in enumerate(CASES):
        f = ROOT.TFile.Open("emptytest/%s.root" % case)
        bkg, sig, dat = [f.Get(n).Clone("%s_%d" % (n, k)) for n in ["bkg", "sig", "data_obs"]]
        p = c.cd(k + 1)
        p.SetLogy()
        p.SetLeftMargin(0.13)
        p.SetRightMargin(0.03)
        p.SetTopMargin(0.10)
        p.SetBottomMargin(0.12)
        fr = ROOT.TH1F("fr%d" % k, "", NB, 0, NB)
        fr.SetMinimum(0.3)
        fr.SetMaximum(1e5)
        for i in range(NB):
            fr.GetXaxis().SetBinLabel(i + 1, "%d" % (i + 1))
        for ax in [fr.GetXaxis(), fr.GetYaxis()]:
            ax.SetLabelFont(FONT)
            ax.SetLabelSize(20)
            ax.SetTitleFont(FONT)
            ax.SetTitleSize(20)
        fr.GetXaxis().SetTitle("Bin")
        fr.GetXaxis().SetTitleOffset(1.1)
        fr.GetYaxis().SetTitle("Events")
        fr.GetYaxis().SetTitleOffset(1.4)
        fr.Draw("axis")
        box = ROOT.TBox(6, 0.3, 7, 1e5)
        box.SetFillColorAlpha(RED, 0.12)
        box.Draw()
        bkg.SetFillColor(ORANGE)
        bkg.SetLineColor(ROOT.kBlack)
        bkg.Draw("hist same")
        sb = bkg.Clone("sb_%d" % k)
        sb.Add(sig)
        sb.SetFillStyle(0)
        sb.SetLineColor(RED)
        sb.SetLineStyle(2)
        sb.SetLineWidth(3)
        sb.Draw("hist same")
        gd = ROOT.TGraphAsymmErrors()
        for i in range(NB):
            n = dat.GetBinContent(i + 1)
            if n <= 0:
                continue
            j = gd.GetN()
            gd.SetPoint(j, i + 0.5, n)
            gd.SetPointError(j, 0, 0, math.sqrt(n), math.sqrt(n))
        gd.SetMarkerStyle(20)
        gd.SetMarkerSize(1.3)
        gd.SetLineWidth(2)
        gd.Draw("p same")
        t = ROOT.TLatex()
        t.SetTextFont(FONT)
        t.SetTextSize(18)
        t.SetTextColor(RED)
        b7, d7 = bkg.GetBinContent(7), dat.GetBinContent(7)
        t.DrawLatex(6.05, 400, "bin 7:")
        t.DrawLatex(6.05, 180, "bkg %s" % ("0" if b7 == 0 else "%.0f" % b7))
        t.DrawLatex(6.05, 80, "data %d" % d7)
        leg = ROOT.TLegend(0.62, 0.62, 0.97, 0.88)
        leg.SetBorderSize(0)
        leg.SetFillStyle(0)
        leg.SetTextFont(FONT)
        leg.SetTextSize(17)
        leg.AddEntry(gd, "Data", "pe")
        leg.AddEntry(bkg, "Background", "f")
        leg.AddEntry(sb, "Signal (r = 1) + bkg.", "l")
        leg.Draw()
        tt = ROOT.TLatex()
        tt.SetNDC()
        tt.SetTextFont(FONT)
        tt.SetTextSize(20)
        tt.DrawLatex(0.13, 0.92, "#bf{Toy} #it{%s}" % title)
        p.RedrawAxis()
        keep += [f, fr, box, bkg, sb, gd, t, leg, tt, sig, dat]

    rootutil.save(c, "emptytest")


@rootutil.isolated
def mccap():
    """What the constraint on the b5 fakes yield looks like (demo 16).

Left: relative MC error -> effective number of MC events, N_eff = 1 / rel.err^2.
Right: the constraint on the fakes yield in b5 (true 1.00):
  as-is (+-400%): Gaussian, allows a negative yield
  capped (+-100%): Poisson with N_eff = 1, yield >= 0

Usage: python3 plot_mccap.py  -> plots/mccap.*"""
    rootutil.setup(ticks=True)
    FONT = 43
    RED = ROOT.TColor.GetColor("#c0392b")
    BLUE = ROOT.TColor.GetColor("#2c7bb6")
    Y0 = 1.0
    ERR = 4.0

    c = ROOT.TCanvas("c", "", 1500, 560)
    pl = ROOT.TPad("pl", "", 0, 0, 0.45, 1)
    pr = ROOT.TPad("pr", "", 0.45, 0, 1, 1)
    for p in (pl, pr):
        p.SetLeftMargin(0.14)
        p.SetRightMargin(0.04)
        p.SetTopMargin(0.10)
        p.SetBottomMargin(0.15)
        p.Draw()
    keep = []


    def style(h, xt, yt):
        for ax in [h.GetXaxis(), h.GetYaxis()]:
            ax.SetLabelFont(FONT)
            ax.SetLabelSize(21)
            ax.SetTitleFont(FONT)
            ax.SetTitleSize(22)
        h.GetXaxis().SetTitle(xt)
        h.GetXaxis().SetTitleOffset(1.2)
        h.GetYaxis().SetTitle(yt)
        h.GetYaxis().SetTitleOffset(1.4)


    def header(text):
        t = ROOT.TLatex()
        t.SetNDC()
        t.SetTextFont(FONT)
        t.SetTextSize(22)
        t.DrawLatex(0.14, 0.92, text)
        return t


    # ---- left: N_eff vs relative error
    pl.cd()
    pl.SetLogy()
    fr = ROOT.TH1F("fr", "", 10, 0, 4.5)
    fr.SetMinimum(0.02)
    fr.SetMaximum(300)
    style(fr, "Relative MC error (error / yield)", "Effective MC events  N_{eff} = 1 / (rel. err)^{2}")
    fr.Draw("axis")
    shade = ROOT.TBox(1.0, 0.02, 4.5, 300)
    shade.SetFillColorAlpha(RED, 0.12)
    shade.Draw()
    g = ROOT.TGraph()
    for i in range(1, 451):
        x = i / 100.0
        if x >= 0.06:
            g.SetPoint(g.GetN(), x, 1 / x ** 2)
    g.SetLineWidth(3)
    g.Draw("l same")
    one = ROOT.TLine(0, 1, 4.5, 1)
    one.SetLineStyle(2)
    one.Draw()
    pts = ROOT.TGraph()
    for x in [0.1, 0.5, 1.0, 4.0]:
        pts.SetPoint(pts.GetN(), x, 1 / x ** 2)
    pts.SetMarkerStyle(20)
    pts.SetMarkerSize(1.5)
    pts.Draw("p same")
    lab = ROOT.TLatex()
    lab.SetTextFont(FONT)
    lab.SetTextSize(18)
    for x, s in [(0.1, "10%: 100 events"), (0.5, "50%: 4 events"), (1.0, "100%: 1 event")]:
        lab.DrawLatex(x + 0.03, 1.25 / x ** 2, s)
    lab.DrawLatex(2.5, 0.032, "400%: 0.06 events")
    lab.SetTextColor(RED)
    lab.DrawLatex(2.0, 80, "< 1 event:")
    lab.DrawLatex(2.0, 45, "Poisson not viable")
    pl.RedrawAxis()
    keep += [fr, shade, g, one, pts, lab, header("#bf{autoMCStats} #it{how many MC events is a yield worth?}")]

    # ---- right: constraint on the b5 fakes yield
    pr.cd()
    fr2 = ROOT.TH1F("fr2", "", 10, -12, 14)
    fr2.SetMinimum(0)
    fr2.SetMaximum(1.7)
    style(fr2, "Fakes yield in b5 (events)", "Constraint (max = 1)")
    fr2.Draw("axis")
    neg = ROOT.TBox(-12, 0, 0, 1.7)
    neg.SetFillColorAlpha(RED, 0.10)
    neg.Draw()
    gauss, pois = ROOT.TGraph(), ROOT.TGraph()
    for i in range(0, 2601):
        y = -12 + i * 0.01
        gauss.SetPoint(gauss.GetN(), y, math.exp(-0.5 * ((y - Y0) / ERR) ** 2))
        if y >= 0:   # N_eff = 1: L(v) ~ v exp(-v), v = y / Y0, normalised to max 1 at v = 1
            v = y / Y0
            pois.SetPoint(pois.GetN(), y, v * math.exp(1 - v))
    gauss.SetLineColor(RED)
    gauss.SetLineWidth(3)
    pois.SetLineColor(BLUE)
    pois.SetLineWidth(3)
    gauss.Draw("l same")
    pois.Draw("l same")
    leg = ROOT.TLegend(0.42, 0.74, 0.96, 0.88)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextFont(FONT)
    leg.SetTextSize(19)
    leg.AddEntry(gauss, "as-is 1.00 #pm 4.00: Gaussian", "l")
    leg.AddEntry(pois, "capped 1.00 #pm 1.00: Poisson, N_{eff} = 1", "l")
    leg.Draw()
    lab2 = ROOT.TLatex()
    lab2.SetTextFont(FONT)
    lab2.SetTextSize(18)
    lab2.SetTextColor(RED)
    lab2.DrawLatex(-11.5, 1.12, "negative yield")
    lab2.DrawLatex(-11.5, 1.02, "allowed")
    pr.RedrawAxis()
    keep += [fr2, neg, gauss, pois, leg, lab2, header("#bf{Toy analysis} #it{fakes in b5, true yield 1.00}")]

    rootutil.save(c, "mccap")


@rootutil.isolated
def mccap_shapes():
    """Pre-fit and post-fit distributions for demo 16, straight from FitDiagnostics.

One column per version (as-is / capped / well-simulated reference).
Top: WZ + fakes pre-fit, data, the pre-fit background uncertainty band
(hatched) and the background-only post-fit band (blue outline).
Bottom: data / pre-fit background, with the pre-fit (hatched) and
background-only post-fit (blue) bands relative to the pre-fit background.

Usage: python3 plot_mccap_shapes.py  (after run_16) -> plots/mccap_shapes.*"""
    rootutil.setup(ticks=True)
    ROOT.gStyle.SetHatchesLineWidth(1)
    FONT = 43
    NB = 5
    ORANGE = ROOT.TColor.GetColor("#e8a33d")
    GREY = ROOT.TColor.GetColor("#8c8c8c")
    BLUE = ROOT.TColor.GetColor("#2c7bb6")
    RED = ROOT.TColor.GetColor("#c0392b")
    VERSIONS = [("as-is", "as-is: fakes b5 = 1.00 #pm 4.00"),
                ("capped", "capped: fakes b5 = 1.00 #pm 1.00"),
                ("goodmc", "reference: fakes b5 = 1.00 #pm 0.71")]


    def rebin(h, name):
        """FitDiagnostics stores shapes on a 0..NB axis already; copy to b1..b5 labels."""
        out = ROOT.TH1F(name, "", NB, 0, NB)
        for b in range(1, NB + 1):
            out.SetBinContent(b, h.GetBinContent(b))
            out.SetBinError(b, h.GetBinError(b))
        return out


    def style(h, ytitle, labels):
        for i in range(NB):
            h.GetXaxis().SetBinLabel(i + 1, "b%d" % (i + 1))
        for ax in [h.GetXaxis(), h.GetYaxis()]:
            ax.SetLabelFont(FONT)
            ax.SetLabelSize(21 if labels or ax == h.GetYaxis() else 0)
            ax.SetTitleFont(FONT)
            ax.SetTitleSize(21)
        h.GetYaxis().SetTitle(ytitle)
        h.GetYaxis().SetTitleOffset(1.6)
        h.GetYaxis().SetNdivisions(505)


    c = ROOT.TCanvas("c", "", 1800, 820)
    keep = []
    for k, (v, title) in enumerate(VERSIONS):
        f = ROOT.TFile.Open("mccap/fitDiagnostics.%s.root" % v)
        pre = "shapes_prefit/SR/"
        post = "shapes_fit_b/SR/"
        wz = rebin(f.Get(pre + "WZ"), "wz%d" % k)
        fk = rebin(f.Get(pre + "fakes"), "fk%d" % k)
        tot_pre = rebin(f.Get(pre + "total_background"), "tp%d" % k)
        tot_post = rebin(f.Get(post + "total_background"), "tb%d" % k)
        data = f.Get(pre + "data")                      # TGraphAsymmErrors
        x0, x1 = k / 3.0, (k + 1) / 3.0
        c.cd()
        top = ROOT.TPad("t%d" % k, "", x0, 0.33, x1, 1)
        bot = ROOT.TPad("b%d" % k, "", x0, 0, x1, 0.33)
        for p in (top, bot):
            p.SetLeftMargin(0.17)
            p.SetRightMargin(0.03)
            p.Draw()
        top.SetTopMargin(0.10)
        top.SetBottomMargin(0.02)
        bot.SetTopMargin(0.03)
        bot.SetBottomMargin(0.25)

        top.cd()
        top.SetLogy()
        fr = ROOT.TH1F("fr%d" % k, "", NB, 0, NB)
        fr.SetMinimum(0.5)
        fr.SetMaximum(3000)
        style(fr, "Events", False)
        fr.Draw("axis")
        stack = wz.Clone("st%d" % k)
        stack.Add(fk)
        for h, col in [(stack, ORANGE), (fk, GREY)]:
            h.SetFillColor(col)
            h.SetLineColor(ROOT.kBlack)
            h.Draw("hist same")
        band = tot_pre.Clone("band%d" % k)
        band.SetFillStyle(3354)
        band.SetFillColor(ROOT.kBlack)
        band.SetMarkerSize(0)
        band.Draw("e2 same")
        pb = tot_post.Clone("pb%d" % k)
        pb.SetFillStyle(0)
        pb.SetLineColor(BLUE)
        pb.SetLineWidth(2)
        pb.SetMarkerSize(0)
        pb.Draw("e2 same")
        data.SetMarkerStyle(20)
        data.SetMarkerSize(1.2)
        data.SetLineWidth(2)
        data.Draw("p same")
        leg = ROOT.TLegend(0.50, 0.58, 0.97, 0.87)
        leg.SetBorderSize(0)
        leg.SetFillStyle(0)
        leg.SetTextFont(FONT)
        leg.SetTextSize(17)
        leg.AddEntry(data, "Data", "pe")
        leg.AddEntry(stack, "WZ", "f")
        leg.AddEntry(fk, "Fakes", "f")
        leg.AddEntry(band, "Bkg. unc., pre-fit", "f")
        leg.AddEntry(pb, "Bkg. unc., post-fit (b-only)", "f")
        leg.Draw()
        t = ROOT.TLatex()
        t.SetNDC()
        t.SetTextFont(FONT)
        t.SetTextSize(19)
        t.DrawLatex(0.17, 0.92, "#bf{Toy} #it{%s}" % title)
        top.RedrawAxis()

        bot.cd()
        fr2 = ROOT.TH1F("fb%d" % k, "", NB, 0, NB)
        fr2.SetMinimum(0.0)
        fr2.SetMaximum(2.4)
        style(fr2, "Data / bkg.", True)
        fr2.GetXaxis().SetLabelSize(24)
        fr2.Draw("axis")
        # bands: background uncertainty relative to the pre-fit background, centred on 1
        r_pre = ROOT.TH1F("rp%d" % k, "", NB, 0, NB)
        r_post = ROOT.TH1F("rq%d" % k, "", NB, 0, NB)
        for b in range(1, NB + 1):
            n = tot_pre.GetBinContent(b)
            r_pre.SetBinContent(b, 1.0)
            r_pre.SetBinError(b, tot_pre.GetBinError(b) / n)
            r_post.SetBinContent(b, tot_post.GetBinContent(b) / n)
            r_post.SetBinError(b, tot_post.GetBinError(b) / n)
        r_pre.SetFillStyle(3354)
        r_pre.SetFillColor(ROOT.kBlack)
        r_pre.SetMarkerSize(0)
        r_pre.Draw("e2 same")
        r_post.SetFillStyle(0)
        r_post.SetLineColor(BLUE)
        r_post.SetLineWidth(2)
        r_post.SetMarkerSize(0)
        r_post.Draw("e2 same")
        one = ROOT.TLine(0, 1, NB, 1)
        one.SetLineStyle(2)
        one.Draw()
        gr = ROOT.TGraphAsymmErrors()
        for i in range(data.GetN()):
            x, y = data.GetPointX(i), data.GetPointY(i)
            n = tot_pre.GetBinContent(i + 1)
            gr.SetPoint(i, x, y / n)
            gr.SetPointError(i, 0, 0, data.GetErrorYlow(i) / n, data.GetErrorYhigh(i) / n)
        gr.SetMarkerStyle(20)
        gr.SetMarkerSize(1.2)
        gr.SetLineWidth(2)
        gr.Draw("p same")
        lab = ROOT.TLatex()
        lab.SetTextFont(FONT)
        lab.SetTextSize(18)
        lab.DrawLatex(3.35, 2.1, "b5 pre-fit unc. #pm%.0f%%" % (100 * r_pre.GetBinError(5)))
        bot.RedrawAxis()
        keep += [f, top, bot, fr, stack, fk, band, pb, data, leg, t, fr2, r_pre, r_post, one, gr, lab, wz, tot_pre, tot_post]
        print("%-7s b5 total bkg rel. unc.: pre-fit %.0f%%  post-fit %.0f%%"
              % (v, 100 * r_pre.GetBinError(5), 100 * tot_post.GetBinError(5) / tot_post.GetBinContent(5)))

    rootutil.save(c, "mccap_shapes")
