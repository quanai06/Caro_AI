"""Launches appropriate mode (human, benchmark).
"""

from . import modes


def run(mode: str, algorithm: str):
    print(f"Running Caro AI in mode={mode} with algorithm={algorithm}")
    # TODO: wire up to UI/benchmark runner
