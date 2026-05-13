import pygame
from .game.caro import CaroGame
try:
    # production import (original)
    try:
        from .ui.main_menu import MainMenu
    except Exception:
        from .ui.main_menu_clean import MainMenu
except Exception:
    # fallback to clean replacement if the original module is broken
    from .ui.main_menu_clean import MainMenu
from .ui.pygame_ui import PygameUI
from .ai.alphabeta_agent import AlphaBetaAgent
from .ai.minimax_agent import MinimaxAgent

def start_game(first_player='player', difficulty='medium', board_size=15, algorithm='alphabeta'):
    player_symbol = 'X' if first_player == 'player' else 'O'
    game = CaroGame(board_size=board_size, player_symbol=player_symbol)
    game.ai_player = 'O' if player_symbol == 'X' else 'X'
    if first_player == 'ai':
        game.current_player = game.ai_player
    else:
        game.current_player = game.player_symbol

    if algorithm == 'minimax':
        agent = MinimaxAgent(difficulty=difficulty)
    else:
        agent = AlphaBetaAgent(difficulty=difficulty)
    agent.ai_symbol = game.ai_player

    depth = agent.depth_map.get(difficulty, 3)
    ui = PygameUI(game, agent, depth=depth, board_size=board_size, cell_size=45)
    ui.run()

def start_human_vs_ai(algorithm='alphabeta', depth=3, board_size=15, difficulty='medium'):
    # Giữ lại để tương thích cũ
    start_game(first_player='player', difficulty=difficulty, board_size=board_size, algorithm=algorithm)

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 700))
    pygame.display.set_caption("Caro AI")
    menu = MainMenu(screen)
    while True:
        result = menu.run()
        if len(result) == 3:
            action, difficulty, algorithm = result
        else:
            action, difficulty = result
            algorithm = 'alphabeta'
        if action == "player_first":
            start_game(first_player='player', difficulty=difficulty, algorithm=algorithm)
        elif action == "ai_first":
            start_game(first_player='ai', difficulty=difficulty, algorithm=algorithm)
        elif action == "quit":
            break
        # Sau khi start_game, khôi phục màn hình menu
        screen = pygame.display.set_mode((800, 700))
        menu = MainMenu(screen)  # tạo menu mới với kích thước đúng
    pygame.quit()

if __name__ == "__main__":
    main()


def start_demo_ui():
    """Start a small demo showing the image-based main menu and settings overlay.
    This is intended for a visual check; it creates a minimal pygame window and shows both screens.
    """
    import pygame
    # use the clean replacement for demo to avoid issues if main_menu.py is corrupted
    from .ui.main_menu_clean import MainMenu
    from .ui.menu_overlay import MenuOverlay
    from .game.caro import CaroGame
    from .ai.alphabeta_agent import AlphaBetaAgent

    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption('Caro AI - Demo')

    # create dummy game/agent for overlay
    game = CaroGame(board_size=9)
    agent = AlphaBetaAgent()

    menu = MainMenu(screen.get_rect(), on_start=lambda: None, on_quit=lambda: pygame.event.post(pygame.event.Event(pygame.QUIT)))
    overlay = MenuOverlay(screen.get_rect(), game, [agent], [3])

    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if menu.visible:
                if menu.handle_event(event):
                    # toggle to overlay on any click for demo
                    menu.visible = False
                    overlay.show()
            else:
                overlay.handle_event(event)

        if menu.visible:
            menu.draw(screen)
        else:
            screen.fill((20,20,24))
            overlay.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
