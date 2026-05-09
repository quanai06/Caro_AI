from .base_agent import BaseAgent

class AlphaBetaAgent(BaseAgent):
    def __init__(self, depth=4):
        self.depth = depth

    def choose_move(self, state):
        return None
