import random

class Zobrist:
    def __init__(self, board_size=15):
        self.size = board_size
        # Bảng ngẫu nhiên cho mỗi ô và mỗi quân (0: rỗng, 1: X, 2: O)
        self.table = [[[random.getrandbits(64) for _ in range(3)] for _ in range(board_size)] for __ in range(board_size)]

    def hash_board(self, board):
        h = 0
        for i in range(self.size):
            for j in range(self.size):
                cell = board.grid[i][j]
                if cell == 'X':
                    h ^= self.table[i][j][1]
                elif cell == 'O':
                    h ^= self.table[i][j][2]
        return h

    def update_hash(self, old_hash, row, col, old_piece, new_piece):
        h = old_hash
        if old_piece != '.':
            idx = 1 if old_piece == 'X' else 2
            h ^= self.table[row][col][idx]
        if new_piece != '.':
            idx = 1 if new_piece == 'X' else 2
            h ^= self.table[row][col][idx]
        return h

class TranspositionTable:
    def __init__(self):
        self.table = {}

    def get(self, zobrist_hash, depth, alpha, beta):
        entry = self.table.get(zobrist_hash)
        if entry and entry['depth'] >= depth:
            if entry['flag'] == 'exact':
                return entry['value']
            elif entry['flag'] == 'lower' and entry['value'] >= beta:
                return beta
            elif entry['flag'] == 'upper' and entry['value'] <= alpha:
                return alpha
        return None

    def store(self, zobrist_hash, depth, value, flag, move=None):
        self.table[zobrist_hash] = {
            'depth': depth,
            'value': value,
            'flag': flag,
            'move': move
        }

    def clear(self):
        self.table.clear()

# Khởi tạo toàn cục cho toàn bộ game
ZOBRIST = Zobrist()