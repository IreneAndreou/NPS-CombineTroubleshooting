"""Demo 0: baseline. Builds workspaces for both versions of the toy and checks
they give the same limit (counting card vs. shape card are equivalent;
the shape card additionally has autoMCStats, so expect a small difference).

Run through the Combine environment:  bash with_combine.sh demos/run_00_baseline.py
"""
from src import cards, combine, plots


def main():
    cards.shapes_root()

    combine.run("text2workspace.py", "inputs/toy.txt", "-o", "toy.root")
    combine.run("text2workspace.py", "inputs/toy_shapes.txt", "-o", "toy_shapes.root_ws.root")

    print("=== Counting card: expected (Asimov) and observed ===")
    combine.run("combine", "-M", "AsymptoticLimits", "toy.root", "-t", "-1", "-n", ".toy.exp")
    combine.run("combine", "-M", "AsymptoticLimits", "toy.root", "-n", ".toy.obs")

    print("=== Shape card (with autoMCStats): expected and observed ===")
    combine.run("combine", "-M", "AsymptoticLimits", "toy_shapes.root_ws.root", "-t", "-1",
                "-n", ".shapes.exp")
    combine.run("combine", "-M", "AsymptoticLimits", "toy_shapes.root_ws.root", "-n", ".shapes.obs")

    print("=== Plots: pre-fit stack and baseline limits (plots/) ===")
    plots.prefit()
    plots.limit_table([("Counting card (toy.txt)", "toy", False),
                       ("Shape card + autoMCStats", "shapes", False)])


if __name__ == "__main__":
    main()
