import json
import time
import csv
import os
import argparse
from ..game.board import Board
from ..ai.minimax_agent import MinimaxAgent
from ..ai.alphabeta_agent import AlphaBetaAgent

DIFFICULTY_DEPTHS = {"easy": 2, "medium": 3, "hard": 4}
AGENTS = [MinimaxAgent, AlphaBetaAgent]
DEFAULT_RESULTS_PATH = os.path.join(
    os.path.dirname(__file__), "results", "benchmark.csv")


def normalize_board_data(board_data):
    if not board_data:
        raise ValueError("board must not be empty")

    rows = []
    for row in board_data:
        if isinstance(row, str):
            parsed = list(row.strip())
        else:
            parsed = list(row)
        rows.append(parsed)

    size = len(rows)
    allowed = {'.', 'X', 'O'}
    for row_idx, row in enumerate(rows):
        if len(row) != size:
            raise ValueError(
                f"board row {row_idx} has length {len(row)}, expected {size}")
        invalid = set(row) - allowed
        if invalid:
            raise ValueError(f"board row {row_idx} has invalid cells: {invalid}")
    return rows


def load_board_from_json(board_data, size=None):
    rows = normalize_board_data(board_data)
    size = size or len(rows)
    board = Board(size)
    for i in range(size):
        for j in range(size):
            board.grid[i][j] = rows[i][j]
    return board


def _expected_hit(move, expected_moves):
    if not expected_moves or not move:
        return ""
    expected = {tuple(item) for item in expected_moves}
    return tuple(move) in expected


def _format_move(move):
    if not move:
        return "(-1,-1)"
    return f"({move[0]},{move[1]})"


def _build_comparison_rows(results):
    grouped = {}
    for item in results:
        key = (
            item["state_id"],
            item["state_name"],
            item["category"],
            item["turn"],
            item["difficulty"],
            item["depth"],
        )
        grouped.setdefault(key, {})[item["algorithm"]] = item

    rows = []
    metric_specs = [
        ("move", lambda r: _format_move((r["move_row"], r["move_col"]))),
        ("value", lambda r: str(r["value"])),
        ("nodes", lambda r: str(r["nodes"])),
        ("time_sec", lambda r: f"{r['time_sec']:.6f}"),
        ("expected_hit", lambda r: str(r["expected_hit"])),
    ]

    for key in sorted(grouped, key=lambda k: (k[0], int(k[5]))):
        state_id, state_name, category, turn, difficulty, depth = key
        minimax = grouped[key].get("MinimaxAgent")
        alphabeta = grouped[key].get("AlphaBetaAgent")
        if not minimax or not alphabeta:
            continue
        for metric, getter in metric_specs:
            rows.append({
                "state_id": state_id,
                "state_name": state_name,
                "category": category,
                "turn": turn,
                "difficulty": difficulty,
                "depth": depth,
                "metric": metric,
                "minimax": getter(minimax),
                "alphabeta": getter(alphabeta),
            })
        if alphabeta["nodes"]:
            node_ratio = minimax["nodes"] / alphabeta["nodes"]
            node_ratio_text = f"{node_ratio:.2f}"
        else:
            node_ratio_text = ""
        if alphabeta["time_sec"]:
            speedup = minimax["time_sec"] / alphabeta["time_sec"]
            speedup_text = f"{speedup:.2f}"
        else:
            speedup_text = ""
        rows.append({
            "state_id": state_id,
            "state_name": state_name,
            "category": category,
            "turn": turn,
            "difficulty": difficulty,
            "depth": depth,
            "metric": "node_ratio_minimax_over_alphabeta",
            "minimax": node_ratio_text,
            "alphabeta": "1.00" if node_ratio_text else "",
        })
        rows.append({
            "state_id": state_id,
            "state_name": state_name,
            "category": category,
            "turn": turn,
            "difficulty": difficulty,
            "depth": depth,
            "metric": "time_ratio_minimax_over_alphabeta",
            "minimax": speedup_text,
            "alphabeta": "1.00" if speedup_text else "",
        })
    return rows


def run_benchmark(config_path=None, depths=None, output_csv=None):
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "test_states.json")
    if depths is None:
        depths = list(DIFFICULTY_DEPTHS.values())
    if output_csv is None:
        output_csv = DEFAULT_RESULTS_PATH

    with open(config_path, 'r', encoding='utf-8') as f:
        states = json.load(f)

    results = []
    for state in states:
        print(f"Running: {state['name']} (id={state['id']})")
        board = load_board_from_json(state['board'])
        turn = state.get('turn', 'O')
        if turn not in ('X', 'O'):
            raise ValueError(f"state {state['id']} has invalid turn: {turn}")
        expected_moves = state.get("expected_moves", [])
        for depth in depths:
            difficulty = next(
                (name for name, mapped_depth in DIFFICULTY_DEPTHS.items()
                 if mapped_depth == depth),
                f"depth_{depth}",
            )
            for AgentClass in AGENTS:
                agent = AgentClass(difficulty=difficulty)
                if hasattr(agent, "random_chance"):
                    agent.random_chance = {
                        name: 0.0 for name in agent.random_chance
                    }
                agent.ai_symbol = turn
                start = time.perf_counter()
                move, value = agent.get_move(board, depth, is_maximizing=True)
                elapsed = time.perf_counter() - start
                expected_hit = _expected_hit(move, expected_moves)
                results.append({
                    "state_id": state["id"],
                    "state_name": state["name"],
                    "category": state.get("category", ""),
                    "turn": turn,
                    "difficulty": difficulty,
                    "depth": depth,
                    "algorithm": AgentClass.__name__,
                    "move_row": move[0] if move else -1,
                    "move_col": move[1] if move else -1,
                    "expected_hit": expected_hit,
                    "value": value,
                    "nodes": agent.nodes_visited,
                    "time_sec": elapsed
                })
                suffix = ""
                if expected_hit != "":
                    suffix = f", expected_hit={expected_hit}"
                print(
                    f"  {difficulty} depth={depth}, {AgentClass.__name__}: "
                    f"move={move}, nodes={agent.nodes_visited}, "
                    f"time={elapsed:.4f}s{suffix}")

    if not results:
        raise ValueError("benchmark produced no results")
    
    output_dir = os.path.dirname(output_csv)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    comparison_rows = _build_comparison_rows(results)
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=comparison_rows[0].keys())
        writer.writeheader()
        writer.writerows(comparison_rows)
    print(f"\nBenchmark done. Results saved to {output_csv}")
    return comparison_rows


def main():
    parser = argparse.ArgumentParser(description="Run Caro AI benchmark states.")
    parser.add_argument("--config", default=None, help="Path to benchmark JSON.")
    parser.add_argument("--output", default=None, help="Path to output CSV.")
    parser.add_argument(
        "--depths",
        nargs="+",
        type=int,
        default=None,
        help="Search depths to run. Default: 2 3 4.",
    )
    args = parser.parse_args()
    run_benchmark(config_path=args.config, depths=args.depths, output_csv=args.output)


if __name__ == "__main__":
    main()
