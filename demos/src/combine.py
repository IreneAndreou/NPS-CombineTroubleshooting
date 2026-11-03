"""Run Combine tools from Python.

On lxplus the Combine tools are shell aliases that run inside a container
(see combine_env.sh). with_combine.sh exports the variables that define that
container command, and run() below builds the same command. Output goes to a
log file when one is given, otherwise to the terminal.
"""
import os
import shlex
import subprocess


def _container_prefix():
    return (["apptainer", "-s", "exec"]
            + shlex.split(os.environ.get("APPTAINER_OPTS", ""))
            + [os.environ["UNPACKED_IMAGE"],
               os.environ["SCRIPT_DIR"] + "/combine_alias/exec_script.sh"])


def run(tool, *args, log=None, cwd=None, append=False):
    """Run one Combine tool, e.g. run("combine", "-M", "AsymptoticLimits", "ws.root").

    log:    write stdout and stderr to this file (append=True adds to it).
    cwd:    run the tool in this directory (default: the current one).
    Raises CalledProcessError if the tool fails (the bash scripts used set -e).
    """
    cmd = _container_prefix() + [tool] + [str(a) for a in args]
    if log is None:
        subprocess.run(cmd, cwd=cwd, check=True)
    else:
        with open(log, "a" if append else "w", encoding="utf-8") as f:
            subprocess.run(cmd, cwd=cwd, stdout=f, stderr=subprocess.STDOUT, check=True)

def run_to_file(path, tool, *args, cwd=None):
    """Run one tool and write its standard output to path (e.g. combineCards.py)."""
    cmd = _container_prefix() + [tool] + [str(a) for a in args]
    with open(path, "w", encoding="utf-8") as f:
        subprocess.run(cmd, cwd=cwd, stdout=f, check=True)
