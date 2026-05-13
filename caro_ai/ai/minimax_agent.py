import time
from .base_agent import BaseAgent
from .evaluation import evaluate
from .move_ordering import order_moves_advanced, find_forced_move
from ..game.rules import check_win

class MinimaxAgent(BaseAgent):
    def __init__(self, difficulty="medium"):
        super().__init__(difficulty)
        self.depth_map = {"easy": 2, "medium": 3, "hard": 4}
        self.branch_limit = {"easy": 8, "medium": 10, "hard": 12}

    def _stone_count(self, board):
        return sum(
            1
            for row in board.grid
            for cell in row
            if cell != '.'
        )

    def _candidate_radius(self, board):
        # Early Minimax on a 15x15 board explodes if it considers radius=2.
        # Adjacent moves are enough for the first few turns and keep hard playable.
        return 1 if self._stone_count(board) <= 4 else 2

    def _candidate_moves(self, board, player, depth):
        moves = board.get_valid_moves(radius=self._candidate_radius(board))
        moves = order_moves_advanced(board, moves, player, depth)
        limit = self.branch_limit.get(self.difficulty, 10)
        return moves[:limit]

    def get_move(self, board, depth=None, is_maximizing=True):
        if depth is None:
            depth = self.depth_map.get(self.difficulty, 2)
        ai_symbol = getattr(self, "ai_symbol", "O")
        opponent = 'O' if ai_symbol == 'X' else 'X'
        self.reset_stats()
        start = time.perf_counter()
        best_move = None
        best_value = float('-inf')
        valid_moves = board.get_valid_moves(radius=2)
        if not valid_moves:
            return None, 0

        forced_move, forced_value = find_forced_move(board, valid_moves, ai_symbol)
        if forced_move:
            self.time_taken = time.perf_counter() - start
            return forced_move, forced_value

        valid_moves = self._candidate_moves(board, ai_symbol, depth)
        for move in valid_moves:
            new_board = board.clone()
            new_board.place(move[0], move[1], ai_symbol)
            value = self._minimax(new_board, depth-1, False, move, ai_symbol, opponent)
            if value > best_value:
                best_value = value
                best_move = move
        self.time_taken = time.perf_counter() - start
        return best_move, best_value

    def _minimax(self, board, depth, is_maximizing, last_move, ai_symbol, opponent):
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
        if depth == 0:
            return evaluate(board, ai_symbol)
        if is_maximizing:
            max_eval = float('-inf')
            moves = self._candidate_moves(board, ai_symbol, depth)
            for move in moves:
                new_board = board.clone()
                new_board.place(move[0], move[1], ai_symbol)
                eval = self._minimax(new_board, depth-1, False, move, ai_symbol, opponent)
                max_eval = max(max_eval, eval)
            return max_eval
        else:
            min_eval = float('inf')
            moves = self._candidate_moves(board, opponent, depth)
            for move in moves:
                new_board = board.clone()
                new_board.place(move[0], move[1], opponent)
                eval = self._minimax(new_board, depth-1, True, move, ai_symbol, opponent)
                min_eval = min(min_eval, eval)
            return min_eval
