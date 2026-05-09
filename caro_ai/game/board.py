# Board representation, move validation, board display

class Board:
    def __init__(self, rows=6, cols=7):
        self.rows = rows
        self.cols = cols
        self.grid = [[None]*cols for _ in range(rows)]

    def __repr__(self):
        return f"Board({self.rows}x{self.cols})"
