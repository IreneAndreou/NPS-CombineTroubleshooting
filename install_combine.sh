#!/bin/bash
# One-time install of Combine v11.1.0 in CMSSW_16_0_0 (lxplus, el9).
# Usage: bash install_combine.sh   (run from the directory you want CMSSW in)
set -e
source /cvmfs/cms.cern.ch/cmsset_default.sh

if [ ! -d CMSSW_16_0_0 ]; then
  cmsrel CMSSW_16_0_0
fi
cd CMSSW_16_0_0/src
eval "$(scramv1 runtime -sh)"   # = cmsenv

if [ ! -d HiggsAnalysis/CombinedLimit ]; then
  git -c advice.detachedHead=false clone --depth 1 --branch v11.1.0 \
    https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
fi
cd HiggsAnalysis/CombinedLimit
scramv1 b clean
scramv1 b -j"$(nproc --ignore=2)"

echo "Done. Each new session: cd $(pwd)/../.. && cmsenv"
