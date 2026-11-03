#!/bin/bash
# Run a demo with the Combine environment loaded.
# Usage (from anywhere): bash with_combine.sh demos/run_00_baseline.py
# The demo runs with the repo root as working directory. The variables
# exported here (set -a) are what demos/src/combine.py needs to call the tools.
set -e

if [ $# -ne 1 ]; then
  echo "Usage: bash with_combine.sh <demo .py or .sh>"
  exit 1
fi

root="$(cd "$(dirname "$0")" && pwd)"
case "$1" in
  *.py) runner="python3" ;;
  *)    runner="source" ;;
esac

exec bash -c "shopt -s expand_aliases
set -a
cd /cvmfs/cms.cern.ch/cat
source ./combine_env.sh > /dev/null
set +a
SCRIPT_DIR=/cvmfs/cms.cern.ch/cat; export SCRIPT_DIR
cd $root
$runner $1"
