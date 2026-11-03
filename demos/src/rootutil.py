"""Shared ROOT setup for the demo plots.

Every plot script calls setup() once, then uses the colours, FONT and save().
"""
import multiprocessing as mp
import os
import ROOT

# Copy of ROOT's style as it is at startup. setup() restores it, so plots
# that run in the same process do not share style settings.
_STARTUP_STYLE = ROOT.gStyle.Clone("startup_style")

FONT = 43
BLACK = ROOT.kBlack
GREEN = ROOT.TColor.GetColor("#4caf50")
YELLOW = ROOT.TColor.GetColor("#ffd54f")
BLUE = ROOT.TColor.GetColor("#1f5fa0")   # asymptotic
RED = ROOT.kRed + 1


def setup(ticks=False, end_error=None):
    """Batch mode, no stat box, histograms kept alive after their files close.

    ticks: tick marks on all four sides. end_error: error-bar cap size, if the
    plot draws error bars (ROOT default otherwise).
    """
    _STARTUP_STYLE.cd()   # undo the previous plot's style changes, if any
    ROOT.gROOT.SetBatch(True)
    ROOT.gStyle.SetOptStat(0)
    if ticks:
        ROOT.gStyle.SetPadTickX(1)
        ROOT.gStyle.SetPadTickY(1)
    if end_error is not None:
        ROOT.gStyle.SetEndErrorSize(end_error)
    ROOT.TH1.AddDirectory(False)


def axis_style(h, xtitle=None, ytitle=None, label_size=21, title_size=23):
    """Common axis fonts and sizes; titles are set only when given."""
    for ax in [h.GetXaxis(), h.GetYaxis()]:
        ax.SetLabelFont(FONT)
        ax.SetLabelSize(label_size)
        ax.SetTitleFont(FONT)
        ax.SetTitleSize(title_size)
    if xtitle is not None:
        h.GetXaxis().SetTitle(xtitle)
    if ytitle is not None:
        h.GetYaxis().SetTitle(ytitle)


def save(canvas, name):
    """Write plots/<name>.pdf and plots/<name>.png (plots/ relative to cwd)."""
    os.makedirs("plots", exist_ok=True)
    for ext in ["pdf", "png"]:
        canvas.SaveAs("plots/%s.%s" % (name, ext))


def isolated(fn):
    """Run a figure function in a forked child process.

    ROOT keeps global state (colours, style, open files) for the whole process,
    so a figure drawn after another one could differ from the same figure drawn
    alone. Each child starts from the same clean parent, like a separate run.
    """
    def wrapper(*args, **kwargs):
        child = mp.get_context("fork").Process(target=fn, args=args, kwargs=kwargs)
        child.start()
        child.join()
        if child.exitcode != 0:
            raise RuntimeError("%s failed (exit code %s)" % (fn.__name__, child.exitcode))
    wrapper.__name__ = fn.__name__
    wrapper.__doc__ = fn.__doc__
    return wrapper
