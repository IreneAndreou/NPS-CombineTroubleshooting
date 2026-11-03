"""Reading and naming Combine outputs for the demo plots."""
import contextlib
import os
import re

import ROOT


def limit_file(tag, kind="exp", method="AsymptoticLimits"):
    """File written by run scripts with `-n .<tag>.<kind>`.

    kind is "exp" (Asimov, -t -1), "obs" (data), or any other name used in -n.
    """
    return "higgsCombine.%s.%s.%s.mH120.root" % (tag, kind, method)


def read_quantiles(fname):
    """{quantileExpected: limit}, e.g. {-1.0: observed, 0.5: median, ...}."""
    f = ROOT.TFile.Open(fname)
    out = {}
    for e in f.Get("limit"):
        out[round(e.quantileExpected, 3)] = e.limit
    f.Close()
    return out


def read_limit(fname, quantile):
    """(limit, limitErr) at one quantile, or None if the file has no such entry."""
    f = ROOT.TFile.Open(fname)
    out = None
    for e in f.Get("limit"):
        if abs(e.quantileExpected - quantile) < 1e-3:
            out = (e.limit, e.limitErr)
    f.Close()
    return out


@contextlib.contextmanager
def in_dir(path):
    """Work inside path (for the Combine steps and plots that read relative file names)."""
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


def first_value(path, pattern):
    """Last field of the first line of path that contains pattern, or "" if none."""
    for line in open(path, encoding="utf-8"):
        if pattern in line:
            return line.split()[-1]
    return ""


def count_nuisances(card, t2w_log):
    """(systematics + MC-stat parameters, MC-stat parameters), counted from text.

    Systematics: the rows of the card with type lnN or shape. MC-stat: the distinct
    prop_bin parameters that text2workspace reports in its log.
    """
    systs = len(re.findall(r"^[A-Za-z0-9_]+ +(lnN|shape)", open(card, encoding="utf-8").read(), flags=re.M))
    mc = len(set(re.findall(r"prop_bin[A-Za-z0-9]+_bin[0-9]+[A-Za-z0-9_]*",
                            open(t2w_log, encoding="utf-8").read())))
    return systs + mc, mc


def bin_treatment(log, bin_no, process):
    """How autoMCStats treated one process in one bin, from the text2workspace log.

    Returns the text after the first "=>" line for that bin and process that follows
    the bin's "total sum" line, or "" if there is none.
    """
    seen = False
    for line in open(log, encoding="utf-8"):
        fields = line.split()
        if fields and fields[0] == str(bin_no) and "total sum" in line:
            seen = True
        elif seen and "=>" in line and "_bin%d_%s" % (bin_no, process) in line:
            return line.split("=>", 1)[1].strip()
    return ""
