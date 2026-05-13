# Board representation, move validation, board display

class Board:
    def __init__(self, size=15):
        self.size = size
        self.grid = [['.' for _ in range(size)] for _ in range(size)]

    def place(self, row, col, player):
        if self.is_valid_move(row, col):
            self.grid[row][col] = player
            return True
        return False

    def is_valid_move(self, row, col):
        return 0 <= row < self.size and 0 <= col < self.size and self.grid[row][col] == '.'

    def get_valid_moves(self, radius=2):
        if self.is_empty():
            return [(self.size//2, self.size//2)]
        moves = set()
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j] != '.':
                    for di in range(-radius, radius+1):
                        for dj in range(-radius, radius+1):
                            ni, nj = i+di, j+dj
                            if 0 <= ni < self.size and 0 <= nj < self.size and self.grid[ni][nj] == '.':
                                moves.add((ni, nj))
        return list(moves)

    def is_full(self):
        return all(self.grid[i][j] != '.' for i in range(self.size) for j in range(self.size))

    def is_empty(self):
        return all(self.grid[i][j] == '.' for i in range(self.size) for j in range(self.size))

    def clone(self):
        new_board = Board(self.size)
        new_board.grid = [row[:] for row in self.grid]
        return new_board

    def display(self):
        for row in self.grid:
            print(' '.join(row))