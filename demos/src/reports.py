"""Text printouts from FitDiagnostics outputs, used by the run scripts."""
import ROOT


def fit_status(label, fname, pars, fits=("fit_s", "fit_b")):
    """Print fit health from a FitDiagnostics output: minimizer status, covariance
    quality, and chosen parameters with their correlation. fits picks the fits to print.

      status   0 = converged; anything else = the minimizer gave up
      covQual  3 = full, accurate covariance; 2 = forced positive-definite
               (Hesse failed, errors are not trustworthy); 0/1 = worse
    """
    ROOT.gROOT.SetBatch(True)
    f = ROOT.TFile.Open(fname)
    for fitname in fits:
        fr = f.Get(fitname)
        if not fr:
            print("%-34s %s: MISSING (fit did not run)" % (label, fitname))
            continue
        p = fr.floatParsFinal()
        txt = "  ".join("%s %.2f +- %.2f" % (n, p.find(n).getVal(), p.find(n).getError())
                        for n in pars if p.find(n))
        cor = ""
        if len(pars) == 2 and p.find(pars[0]) and p.find(pars[1]):
            cor = "  corr %+.2f" % fr.correlation(pars[0], pars[1])
        flag = "" if (fr.status() == 0 and fr.covQual() == 3) else "   <-- PROBLEM"
        print("%-34s %s: status %d  covQual %d  %s%s%s"
              % (label, fitname, fr.status(), fr.covQual(), txt, cor, flag))


def wz_norm_uncertainty(label, fname):
    """Print the post-fit relative uncertainty on the WZ normalisation, from a
    FitDiagnostics background-only fit (fit_b).

      constrained card: wz_xs (lnN 1.10, unit-Gaussian theta) -> 1.10**err - 1
      floating card:    wz_norm (rateParam, nominal 1)        -> err / 1
    """
    ROOT.gROOT.SetBatch(True)
    f = ROOT.TFile.Open(fname)
    fit = f.Get("fit_b")
    pars = fit.floatParsFinal()
    p = pars.find("wz_norm")
    if p:
        rel = p.getError() / p.getVal() if p.getVal() > 0 else float("nan")
        kind = "floating"
    else:
        p = pars.find("wz_xs")
        rel = 1.10 ** p.getError() - 1.0
        kind = "constrained"
    print("%-34s fit status %d   WZ norm post-fit uncertainty: %5.1f%%  (%s)"
          % (label, fit.status(), 100 * rel, kind))


def fit_error(label, fname, param):
    """Print the post-fit error of one parameter in the background-only fit (fit_b)."""
    ROOT.gROOT.SetBatch(True)
    f = ROOT.TFile.Open(fname)
    p = f.Get("fit_b").floatParsFinal().find(param)
    print("%-9s %.2f" % (label, p.getError()))
