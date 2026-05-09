"""Thin entry point for Caro AI.
Usage:
    python main.py --mode human --algorithm minimax
"""

import argparse

from caro_ai import app

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["human","benchmark"], default="human")
    parser.add_argument("--algorithm", choices=["minimax","alphabeta"], default="minimax")
    args = parser.parse_args()
    app.run(mode=args.mode, algorithm=args.algorithm)
