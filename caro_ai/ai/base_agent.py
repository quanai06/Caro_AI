class BaseAgent:
    def __init__(self, difficulty="medium"):
        self.difficulty = difficulty  # "easy", "medium", "hard"
        self.nodes_visited = 0
        self.time_taken = 0.0

    def reset_stats(self):
        self.nodes_visited = 0
        self.time_taken = 0.0

    def get_move(self, board, depth, is_maximizing):
        raise NotImplementedError