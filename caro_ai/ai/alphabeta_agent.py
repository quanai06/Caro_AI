import time
import random
from .base_agent import BaseAgent
from .evaluation import evaluate
from .move_ordering import order_moves_advanced, find_forced_move
from .zobrist import ZOBRIST, TranspositionTable
from ..game.rules import check_win

class AlphaBetaAgent(BaseAgent):
    def __init__(self, difficulty="medium"):
        super().__init__(difficulty)
        self.depth_map = {"easy": 2, "medium": 3, "hard": 4}
        self.branch_limit = {"easy": 8, "medium": 10, "hard": 12}
        self.random_chance = {"easy": 0.3, "medium": 0.1, "hard": 0.0}
        self.tt = TranspositionTable()

    def _stone_count(self, board):
        return sum(
            1
            for row in board.grid
            for cell in row
            if cell != '.'
        )

    def _candidate_radius(self, board):
        return 1 if self._stone_count(board) <= 4 else 2

    def _candidate_moves(self, board, player, depth):
        moves = board.get_valid_moves(radius=self._candidate_radius(board))
        moves = order_moves_advanced(board, moves, player, depth)
        limit = self.branch_limit.get(self.difficulty, 10)
        return moves[:limit]

    def get_move(self, board, depth=None, is_maximizing=True):
        if depth is None:
            depth = self.depth_map.get(self.difficulty, 3)
        ai_symbol = getattr(self, "ai_symbol", "O")
        opponent = 'O' if ai_symbol == 'X' else 'X'
        self.reset_stats()
        start = time.perf_counter()

        valid_moves = board.get_valid_moves(radius=2)  # radius=2 đủ để thấy nước chặn
        if not valid_moves:
            return None, 0

        forced_move, forced_value = find_forced_move(board, valid_moves, ai_symbol)
        if forced_move:
            self.time_taken = time.perf_counter() - start
            return forced_move, forced_value

        # 2. Easy mode: random
        if self.difficulty == "easy" and random.random() < self.random_chance["easy"]:
            move = random.choice(valid_moves)
            self.time_taken = time.perf_counter() - start
            return move, 0

        # 3. Sắp xếp nước đi bằng heuristic nâng cao
        ordered_moves = self._candidate_moves(board, ai_symbol, depth)

        best_move = None
        best_value = float('-inf')
        alpha = float('-inf')
        beta = float('inf')
        current_hash = ZOBRIST.hash_board(board)

        for move in ordered_moves:
            new_board = board.clone()
            new_board.place(move[0], move[1], ai_symbol)
            new_hash = ZOBRIST.update_hash(current_hash, move[0], move[1], '.', ai_symbol)
            value = self._alphabeta(
                new_board, depth - 1, False, alpha, beta, move, new_hash,
                ai_symbol, opponent)
            if value > best_value:
                best_value = value
                best_move = move
            alpha = max(alpha, value)
            if beta <= alpha:
                break

        self.time_taken = time.perf_counter() - start
        self.tt.store(current_hash, depth, best_value, 'exact', best_move)
        return best_move, best_value

    def _alphabeta(self, board, depth, is_maximizing, alpha, beta,
                   last_move, board_hash, ai_symbol, opponent):
        self.nodes_visited += 1

        # Terminal check
        if last_move:
            row, col = last_move
            if board.grid[row][col] == ai_symbol and check_win(board, row, col, ai_symbol):
                return 10_000_000
            if board.grid[row][col] == opponent and check_win(board, row, col, opponent):
                return -10_000_000
        if board.is_full():
            return 0

        # Transposition table lookup
        tt_val = self.tt.get(board_hash, depth, alpha, beta)
        if tt_val is not None:
            return tt_val

        if depth == 0:
            val = evaluate(board, ai_symbol, last_move=last_move)
            self.tt.store(board_hash, depth, val, 'exact')
            return val

        if is_maximizing:
            max_eval = float('-inf')
            moves = self._candidate_moves(board, ai_symbol, depth)
            for move in moves:
                new_board = board.clone()
                new_board.place(move[0], move[1], ai_symbol)
                new_hash = ZOBRIST.update_hash(board_hash, move[0], move[1], '.', ai_symbol)
                eval_val = self._alphabeta(
                    new_board, depth - 1, False, alpha, beta, move, new_hash,
                    ai_symbol, opponent)
                max_eval = max(max_eval, eval_val)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            flag = 'exact'
            if max_eval <= alpha: flag = 'upper'
            if max_eval >= beta: flag = 'lower'
            self.tt.store(board_hash, depth, max_eval, flag)
            return max_eval
        else:
            min_eval = float('inf')
            moves = self._candidate_moves(board, opponent, depth)
            for move in moves:
                new_board = board.clone()
                new_board.place(move[0], move[1], opponent)
                new_hash = ZOBRIST.update_hash(board_hash, move[0], move[1], '.', opponent)
                eval_val = self._alphabeta(
                    new_board, depth - 1, True, alpha, beta, move, new_hash,
                    ai_symbol, opponent)
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            flag = 'exact'
            if min_eval <= alpha: flag = 'upper'
            if min_eval >= beta: flag = 'lower'
            self.tt.store(board_hash, depth, min_eval, flag)
            return min_eval
