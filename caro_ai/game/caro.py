# Core game state & flow for a single match loop

from .board import Board
from .rules import check_win

class CaroGame:
    def __init__(self, board_size=15, player_symbol='X'):
        self.board = Board(board_size)
        self.player_symbol = player_symbol
        self.current_player = player_symbol   # X or O
        self.ai_player = 'O' if player_symbol == 'X' else 'X'
        self.winner = None
        self.game_over = False
        self.last_move = None

    def make_move(self, row, col, player):
        if self.game_over or player != self.current_player or not self.board.is_valid_move(row, col):
            return False
        self.board.place(row, col, player)
        self.last_move = (row, col)
        if check_win(self.board, row, col, player):
            self.winner = player
            self.game_over = True
        elif self.board.is_full():
            self.game_over = True
        else:
            self.current_player = 'O' if self.current_player == 'X' else 'X'
        return True

    def get_state(self):
        return [row[:] for row in self.board.grid]