import pygame
import sys
import time
import math
import threading
import traceback
from ..game.caro import CaroGame
from ..ai.minimax_agent import MinimaxAgent
from ..ai.alphabeta_agent import AlphaBetaAgent
from .menu_overlay import MenuOverlay

# ── Palette (đồng bộ với main_menu) ─────────────────────────────────────────
_C = {
    "bg0":         ( 8,  10,  16),
    "bg1":         (14,  17,  26),
    "bg_board":    (20,  24,  36),
    "bg_panel":    (13,  15,  23),
    "grid":        (35,  42,  62),
    "grid_hi":     (50,  60,  88),
    "border":      (45,  55,  85),
    "border_hi":   (80, 105, 160),
    "amber":       (255, 190,  55),
    "amber_dim":   (180, 130,  25),
    "amber_pale":  (255, 220, 130),
    "teal":        ( 50, 215, 185),
    "teal_dim":    ( 30, 155, 135),
    "red":         (220,  75,  70),
    "red_dim":     (150,  48,  48),
    "green":       ( 55, 200, 120),
    "white":       (255, 255, 255),
    "txt_hi":      (230, 238, 255),
    "txt_mid":     (148, 160, 195),
    "txt_lo":      ( 80,  92, 130),
    "x_piece":     ( 88, 160, 255),   # xanh dương sáng
    "x_piece_dim": ( 50, 100, 200),
    "o_piece":     (255, 105,  95),   # đỏ cam
    "o_piece_dim": (180,  55,  50),
    "hover":       (255, 255, 255),
    "last_move":   ( 50, 215, 185),   # teal cho last move highlight
    "win_line":    (255, 215,   0),
}

# ── Font helper (tránh lỗi font không tồn tại) ───────────────────────────────
def _f(size, bold=False):
    for name in ["Segoe UI", "Calibri", "Arial"]:
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            pass
    return pygame.font.Font(None, size)

# ── Tiện ích vẽ ──────────────────────────────────────────────────────────────
def _rounded(surf, color, rect, r=10, alpha=255):
    s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(s, (*color[:3], alpha),
                     (0, 0, rect.width, rect.height),
                     border_radius=min(r, rect.width // 2, rect.height // 2))
    surf.blit(s, (rect.x, rect.y))

def _glow_circle(surf, color, center, radius, alpha=55):
    for r in range(radius, 0, -max(1, radius // 5)):
        a = int(alpha * (1 - r / radius) ** 1.6)
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color[:3], a), (r, r), r)
        surf.blit(s, (center[0] - r, center[1] - r))

def _icon_btn(surf, rect, symbol, bg, fg, hover=False, r=10):
    """Vẽ nút icon nhỏ vuông."""
    if hover:
        shadow = rect.move(0, 3)
        _rounded(surf, (0, 0, 0), shadow, r=r, alpha=80)
        # halo
        hr = rect.inflate(6, 6)
        _rounded(surf, bg, hr, r=r + 3, alpha=25)
    _rounded(surf, bg, rect, r=r, alpha=230)
    pygame.draw.rect(surf, _C["border_hi"] if hover else _C["border"],
                     rect, 1, border_radius=r)
    font = _f(15, bold=True)
    ts = font.render(symbol, True, fg)
    surf.blit(ts, ts.get_rect(center=rect.center))


# ── PygameUI ─────────────────────────────────────────────────────────────────
class PygameUI:
    def __init__(self, game, ai_agent, depth=3, board_size=15, cell_size=40):
        pygame.init()
        self.game          = game
        self.ai_agent      = ai_agent
        self.depth         = depth if depth is not None else 3
        self.board_size    = board_size
        self.cell_size     = cell_size
        self.state         = "playing"

        self.player_symbol      = game.player_symbol
        self.ai_symbol          = game.ai_player
        self.ai_agent.ai_symbol = self.ai_symbol
        self.first_player_mode  = 'ai' if game.current_player == game.ai_player else 'player'

        self.play_again_rect = None
        self.menu_rect       = None

        # Kích thước
        self.board_px  = board_size * cell_size          # chiều rộng bàn cờ
        self.panel_h   = 110                             # panel dưới
        self.width     = self.board_px
        self.height    = self.board_px + self.panel_h

        self.screen = pygame.display.set_mode(
            (self.width, self.height), pygame.DOUBLEBUF)
        pygame.display.set_caption("Caro")
        self.clock = pygame.time.Clock()

        # Fonts
        self.fnt_algo  = _f(15, bold=True)
        self.fnt_stats = _f(14)
        self.fnt_turn  = _f(20, bold=True)
        self.fnt_big   = _f(48, bold=True)
        self.fnt_med   = _f(22, bold=True)
        self.fnt_sm    = _f(14)

        # AI stats
        self.last_nodes    = 0
        self.last_time_ms  = 0.0
        self.last_value    = 0
        self.ai_thinking   = False
        self.hover_cell    = None
        self.last_ai_move  = None   # (col, row)
        self._ai_thread    = None
        self._ai_result    = None
        self._ai_error     = None
        self._ai_job_id    = 0

        # ── Panel buttons ──────────────────────────────────────────────────
        # 3 nút icon nhỏ canh phải panel
        btn_sz  = 38
        gap     = 10
        total_w = btn_sz * 3 + gap * 2
        bx      = self.width - total_w - 14
        by      = self.board_px + (self.panel_h - btn_sz) // 2

        self.restart_btn_rect = pygame.Rect(bx,                  by, btn_sz, btn_sz)
        self.home_btn_rect    = pygame.Rect(bx + btn_sz + gap,   by, btn_sz, btn_sz)
        self.menu_btn_rect    = pygame.Rect(bx + (btn_sz+gap)*2, by, btn_sz, btn_sz)

        self._hover_restart = False
        self._hover_home    = False
        self._hover_menu    = False

        # Menu overlay
        self.ai_agent_ref = [self.ai_agent]
        self.depth_ref    = [self.depth]
        self.menu = MenuOverlay(
            self.screen.get_rect(), self.game, self.ai_agent_ref, self.depth_ref,
            on_apply=self.apply_settings)

        # Pre-render nền bàn cờ
        self._board_bg  = self._make_board_bg()
        self._panel_bg  = self._make_panel_bg()

        # Pulse animation cho last move
        self._pulse_t = 0.0

    # ── Pre-render surfaces ──────────────────────────────────────────────────
    def _make_board_bg(self):
        s = pygame.Surface((self.board_px, self.board_px))
        # Gradient nhẹ
        for y in range(self.board_px):
            t   = y / self.board_px
            r   = int(_C["bg0"][0]*(1-t) + _C["bg_board"][0]*t)
            g   = int(_C["bg0"][1]*(1-t) + _C["bg_board"][1]*t)
            b   = int(_C["bg0"][2]*(1-t) + _C["bg_board"][2]*t)
            pygame.draw.line(s, (r, g, b), (0, y), (self.board_px, y))
        # Lưới
        cs = self.cell_size
        n  = self.board_size
        for i in range(n + 1):
            bright = (i == 0 or i == n)
            color  = _C["grid_hi"] if bright else _C["grid"]
            w      = 2 if bright else 1
            pygame.draw.line(s, color, (0, i*cs), (n*cs, i*cs), w)
            pygame.draw.line(s, color, (i*cs, 0), (i*cs, n*cs), w)
        # Dot trung tâm
        mid = n // 2
        pygame.draw.circle(s, _C["grid_hi"],
                           (mid*cs + cs//2, mid*cs + cs//2), 3)
        return s

    def _make_panel_bg(self):
        s = pygame.Surface((self.width, self.panel_h))
        # Gradient tối dần từ trên xuống
        for y in range(self.panel_h):
            t = y / self.panel_h
            r = int(_C["bg_panel"][0]*(1-t) + _C["bg0"][0]*t)
            g = int(_C["bg_panel"][1]*(1-t) + _C["bg0"][1]*t)
            b = int(_C["bg_panel"][2]*(1-t) + _C["bg0"][2]*t)
            pygame.draw.line(s, (r, g, b), (0, y), (self.width, y))
        return s

    # ── Vẽ quân cờ ──────────────────────────────────────────────────────────
    def draw_x(self, col, row, last=False):
        cs  = self.cell_size
        pad = cs // 5
        x1  = col * cs + pad
        y1  = row * cs + pad
        x2  = (col+1) * cs - pad
        y2  = (row+1) * cs - pad
        cx  = col * cs + cs // 2
        cy  = row * cs + cs // 2

        color = _C["amber"] if last else _C["x_piece"]
        dim   = _C["amber_dim"] if last else _C["x_piece_dim"]

        if last:
            _glow_circle(self.screen, color, (cx, cy), cs // 2, alpha=50)

        # Bóng mờ
        pygame.draw.line(self.screen, dim, (x1+2, y1+2), (x2+2, y2+2), 5)
        pygame.draw.line(self.screen, dim, (x2+2, y1+2), (x1+2, y2+2), 5)
        # Nét chính
        pygame.draw.line(self.screen, color, (x1, y1), (x2, y2), 4)
        pygame.draw.line(self.screen, color, (x2, y1), (x1, y2), 4)
        # Dot tâm
        pygame.draw.circle(self.screen, _C["white"], (cx, cy), 3)

    def draw_o(self, col, row, last=False):
        cs     = self.cell_size
        cx     = col * cs + cs // 2
        cy     = row * cs + cs // 2
        radius = cs // 2 - cs // 7

        color = _C["amber"] if last else _C["o_piece"]
        dim   = _C["amber_dim"] if last else _C["o_piece_dim"]

        if last:
            _glow_circle(self.screen, color, (cx, cy), cs // 2, alpha=50)

        # Bóng mờ
        pygame.draw.circle(self.screen, dim, (cx+2, cy+2), radius, 4)
        # Vòng ngoài
        pygame.draw.circle(self.screen, color, (cx, cy), radius, 4)
        # Dot tâm
        pygame.draw.circle(self.screen, color, (cx, cy), 3)

    # ── Vẽ bàn cờ ───────────────────────────────────────────────────────────
    def draw_board(self):
        self._pulse_t += 0.05

        # Nền bàn cờ
        self.screen.blit(self._board_bg, (0, 0))

        # Hover cell
        if (self.hover_cell and not self.game.game_over
                and self.game.current_player == self.player_symbol
                and not self.menu.visible):
            hx, hy = self.hover_cell
            cs = self.cell_size
            hover_s = pygame.Surface((cs, cs), pygame.SRCALPHA)
            hover_s.fill((*_C["hover"], 18))
            pygame.draw.rect(hover_s, (*_C["hover"], 55),
                             (0, 0, cs, cs), 1)
            self.screen.blit(hover_s, (hx * cs, hy * cs))

        # Last AI move pulse
        if self.last_ai_move:
            ax, ay = self.last_ai_move
            cs = self.cell_size
            pulse = 0.55 + 0.45 * math.sin(self._pulse_t)
            alpha = int(80 * pulse)
            lm_s  = pygame.Surface((cs, cs), pygame.SRCALPHA)
            pygame.draw.rect(lm_s, (*_C["last_move"], alpha),
                             (0, 0, cs, cs), border_radius=4)
            pygame.draw.rect(lm_s, (*_C["last_move"], int(180 * pulse)),
                             (0, 0, cs, cs), 2, border_radius=4)
            self.screen.blit(lm_s, (ax * cs, ay * cs))

        # Quân cờ
        for i in range(self.board_size):
            for j in range(self.board_size):
                piece = self.game.board.grid[i][j]
                is_last = self.last_ai_move == (j, i)
                if piece == 'X':
                    self.draw_x(j, i, last=is_last)
                elif piece == 'O':
                    self.draw_o(j, i, last=is_last)

    # ── Vẽ panel dưới ───────────────────────────────────────────────────────
    def draw_panel(self):
        py = self.board_px  # y bắt đầu panel

        # Nền panel
        self.screen.blit(self._panel_bg, (0, py))

        # Đường kẻ trên cùng panel
        sep_s = pygame.Surface((self.width, 1), pygame.SRCALPHA)
        for xi in range(self.width):
            t = abs(xi - self.width / 2) / (self.width / 2)
            a = int(160 * (1 - t ** 2))
            sep_s.set_at((xi, 0), (*_C["border_hi"], a))
        self.screen.blit(sep_s, (0, py))

        # ── Cột trái: algo + stats ─────────────────────────────────────────
        algo_name = self.ai_agent_ref[0].__class__.__name__.replace("Agent", "")
        algo_str  = f"{algo_name}  ·  depth {self.depth_ref[0]}"
        algo_surf = self.fnt_algo.render(algo_str, True, _C["amber"])
        self.screen.blit(algo_surf, (16, py + 12))

        stats = [
            f"nodes {self.last_nodes:,}",
            f"{self.last_time_ms:.1f} ms",
            f"eval {self.last_value:+,}",
        ]
        sx = 16
        for i, stat in enumerate(stats):
            ss = self.fnt_stats.render(stat, True, _C["txt_lo"])
            self.screen.blit(ss, (sx, py + 36 + i * 20))

        # ── Cột phải: turn indicator ───────────────────────────────────────
        if self.game.game_over:
            if self.game.winner == self.player_symbol:
                msg, col = "YOU WIN!", _C["amber"]
            elif self.game.winner == self.ai_symbol:
                msg, col = "AI WINS", _C["red"]
            else:
                msg, col = "DRAW", _C["txt_mid"]
        else:
            if self.ai_thinking:
                msg, col = "AI thinking...", _C["teal"]
            elif self.game.current_player == self.player_symbol:
                msg, col = "Your turn", _C["green"]
            else:
                msg, col = "AI turn", _C["txt_mid"]

        turn_surf = self.fnt_turn.render(msg, True, col)
        turn_rect = turn_surf.get_rect(
            right=self.restart_btn_rect.left - 18,
            centery=py + self.panel_h // 2)
        self.screen.blit(turn_surf, turn_rect)

        # ── Nút icon ──────────────────────────────────────────────────────
        _icon_btn(self.screen, self.restart_btn_rect,
                  "↺", _C["bg1"], _C["txt_mid"], hover=self._hover_restart)
        _icon_btn(self.screen, self.home_btn_rect,
                  "⌂", _C["bg1"], _C["txt_mid"], hover=self._hover_home)
        _icon_btn(self.screen, self.menu_btn_rect,
                  "⚙", _C["bg1"], _C["amber"] if self._hover_menu else _C["txt_mid"],
                  hover=self._hover_menu)

    # ── AI move ──────────────────────────────────────────────────────────────
    def ai_move(self):
        if (self.game.game_over
                or self.game.current_player != self.ai_symbol
                or self.menu.visible
                or self.ai_thinking):
            return

        self.ai_thinking = True
        self._ai_result = None
        self._ai_error = None
        self._ai_job_id += 1

        job_id = self._ai_job_id
        board_snapshot = self.game.board.clone()
        agent = self.ai_agent_ref[0]
        depth = self.depth_ref[0]

        def think():
            try:
                start = time.perf_counter()
                move, value = agent.get_move(
                    board_snapshot, depth, is_maximizing=True)
                elapsed = time.perf_counter() - start
                if job_id == self._ai_job_id:
                    self._ai_result = (
                        job_id, move, value, elapsed,
                        agent.nodes_visited)
            except Exception:
                if job_id == self._ai_job_id:
                    self._ai_error = (job_id, traceback.format_exc())

        self._ai_thread = threading.Thread(target=think, daemon=True)
        self._ai_thread.start()

    def finish_ai_move_if_ready(self):
        if not self.ai_thinking:
            return
        if self._ai_thread and self._ai_thread.is_alive():
            return

        if self._ai_error:
            job_id, err = self._ai_error
            if job_id == self._ai_job_id:
                print(err, file=sys.stderr)
            self.ai_thinking = False
            self._ai_thread = None
            self._ai_error = None
            return

        if not self._ai_result:
            self.ai_thinking = False
            self._ai_thread = None
            return

        job_id, move, value, elapsed, nodes = self._ai_result
        if job_id != self._ai_job_id:
            self._ai_result = None
            return

        self.last_nodes   = nodes
        self.last_time_ms = elapsed * 1000
        self.last_value   = value
        self.ai_thinking  = False
        self._ai_thread   = None
        self._ai_result   = None

        if move:
            if (not self.game.game_over
                    and self.game.current_player == self.ai_symbol):
                self.game.make_move(move[0], move[1], self.ai_symbol)
            try:
                self.last_ai_move = (move[1], move[0])
            except Exception:
                self.last_ai_move = None

    def _agent_algorithm(self):
        agent = self.ai_agent_ref[0]
        if isinstance(agent, MinimaxAgent):
            return "minimax"
        return "alphabeta"

    def _new_agent(self, algorithm, difficulty):
        if algorithm == "minimax":
            agent = MinimaxAgent(difficulty=difficulty)
        else:
            agent = AlphaBetaAgent(difficulty=difficulty)
        agent.ai_symbol = self.ai_symbol
        return agent

    def apply_settings(self, difficulty=None, algorithm=None,
                       board_size=None, player_symbol=None):
        if self.ai_thinking:
            return
        difficulty = difficulty or getattr(self.ai_agent_ref[0], "difficulty", "medium")
        algorithm = (algorithm or self._agent_algorithm()).lower()
        if algorithm in ("alpha-beta", "alpha_beta"):
            algorithm = "alphabeta"
        if algorithm not in ("alphabeta", "minimax"):
            algorithm = "alphabeta"

        board_size = int(board_size or self.board_size)
        player_symbol = player_symbol or self.player_symbol

        current_algorithm = self._agent_algorithm()
        if algorithm != current_algorithm:
            self.ai_agent = self._new_agent(algorithm, difficulty)
        else:
            self.ai_agent = self.ai_agent_ref[0]
            self.ai_agent.difficulty = difficulty
            self.ai_agent.ai_symbol = self.ai_symbol

        self.ai_agent_ref[0] = self.ai_agent
        self.depth = self.ai_agent.depth_map.get(difficulty, self.depth)
        self.depth_ref[0] = self.depth
        if hasattr(self.ai_agent, "tt"):
            self.ai_agent.tt.clear()

        needs_reset = board_size != self.board_size or player_symbol != self.player_symbol
        if needs_reset:
            self.board_size = board_size
            self.player_symbol = player_symbol
            self.ai_symbol = 'O' if player_symbol == 'X' else 'X'
            self.game = CaroGame(board_size=self.board_size, player_symbol=self.player_symbol)
            if self.first_player_mode == 'ai':
                self.game.current_player = self.game.ai_player
            else:
                self.game.current_player = self.game.player_symbol
            self.ai_agent.ai_symbol = self.ai_symbol
            self.last_ai_move = None
            self.hover_cell = None

        self.last_nodes = 0
        self.last_time_ms = 0.0
        self.last_value = 0
        self.ai_thinking = False
        self._ai_job_id += 1
        self._ai_thread = None
        self._ai_result = None
        self._ai_error = None
        self.state = "playing"
        self.menu.game = self.game

    # ── Game over screen ─────────────────────────────────────────────────────
    def draw_game_over_screen(self):
        # Overlay tối
        ov = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 185))
        self.screen.blit(ov, (0, 0))

        # Card giữa màn hình
        cw, ch = 320, 220
        cx, cy = self.width // 2, self.height // 2
        card = pygame.Rect(cx - cw//2, cy - ch//2, cw, ch)
        _rounded(self.screen, _C["bg1"], card, r=18, alpha=245)
        pygame.draw.rect(self.screen, _C["border_hi"],
                         card, 1, border_radius=18)

        if self.game.winner == self.player_symbol:
            msg, sub, col = "YOU WIN!", "Congratulations!", _C["amber"]
        elif self.game.winner == self.ai_symbol:
            msg, sub, col = "AI WINS", "Better luck next time.", _C["red"]
        else:
            msg, sub, col = "DRAW", "Well played!", _C["txt_mid"]

        # Glow dưới chữ thắng
        _glow_circle(self.screen, col, (cx, cy - 45), 60, alpha=30)

        big  = self.fnt_big.render(msg, True, col)
        self.screen.blit(big, big.get_rect(center=(cx, cy - 48)))

        small = self.fnt_sm.render(sub, True, _C["txt_mid"])
        self.screen.blit(small, small.get_rect(center=(cx, cy - 8)))

        # Nút Play Again
        btn_a = pygame.Rect(cx - 130, cy + 30, 120, 44)
        _rounded(self.screen, _C["amber_dim"], btn_a, r=10, alpha=230)
        pygame.draw.rect(self.screen, _C["amber"],
                         btn_a, 1, border_radius=10)
        ta = self.fnt_med.render("Play Again", True, _C["bg0"])
        self.screen.blit(ta, ta.get_rect(center=btn_a.center))
        self.play_again_rect = btn_a

        # Nút Main Menu
        btn_m = pygame.Rect(cx + 10, cy + 30, 120, 44)
        _rounded(self.screen, (30, 35, 52), btn_m, r=10, alpha=230)
        pygame.draw.rect(self.screen, _C["border_hi"],
                         btn_m, 1, border_radius=10)
        tm = self.fnt_med.render("Main Menu", True, _C["txt_hi"])
        self.screen.blit(tm, tm.get_rect(center=btn_m.center))
        self.menu_rect = btn_m

    # ── Reset ────────────────────────────────────────────────────────────────
    def reset_game(self):
        self._ai_job_id += 1
        self._ai_thread = None
        self._ai_result = None
        self._ai_error = None
        new_game = CaroGame(
            board_size=self.board_size,
            player_symbol=self.player_symbol)
        if self.first_player_mode == 'ai':
            new_game.current_player = new_game.ai_player
        else:
            new_game.current_player = new_game.player_symbol
        self.game         = new_game
        self.ai_symbol    = self.game.ai_player
        self.ai_agent_ref[0].ai_symbol = self.ai_symbol
        self.last_nodes   = 0
        self.last_time_ms = 0.0
        self.last_value   = 0
        self.ai_thinking  = False
        self.last_ai_move = None
        self.state        = "playing"
        # Regenerate board bg (board size có thể thay đổi từ menu)
        self._board_bg = self._make_board_bg()
        self.menu.game = new_game

    # ── Main loop ────────────────────────────────────────────────────────────
    def run(self):
        running = True

        self.draw_board()
        self.draw_panel()
        pygame.display.flip()

        if (not self.game.game_over
                and self.game.current_player == self.ai_symbol):
            self.ai_move()

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                # ── Update hover trên các nút panel ──────────────────────
                if event.type == pygame.MOUSEMOTION:
                    mp = event.pos
                    self._hover_restart = self.restart_btn_rect.collidepoint(mp)
                    self._hover_home    = self.home_btn_rect.collidepoint(mp)
                    self._hover_menu    = self.menu_btn_rect.collidepoint(mp)

                if self.state == "playing":
                    if event.type == pygame.MOUSEMOTION:
                        x, y = event.pos
                        if y < self.board_px and not self.menu.visible:
                            col = x // self.cell_size
                            row = y // self.cell_size
                            if (0 <= row < self.board_size
                                    and 0 <= col < self.board_size):
                                self.hover_cell = (col, row)
                            else:
                                self.hover_cell = None
                        else:
                            self.hover_cell = None

                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        x, y = event.pos
                        if self.ai_thinking and not self.menu.visible:
                            continue

                        # Nút settings
                        if self.menu_btn_rect.collidepoint(x, y) and not self.menu.visible:
                            self.menu.show()
                            continue

                        # Nút restart
                        if self.restart_btn_rect.collidepoint(x, y) and not self.menu.visible:
                            self.reset_game()
                            if self.game.current_player == self.ai_symbol:
                                self.ai_move()
                            continue

                        # Nút home
                        if self.home_btn_rect.collidepoint(x, y) and not self.menu.visible:
                            running = False
                            continue

                        # Nước đi người chơi
                        if (not self.menu.visible
                                and y < self.board_px
                                and not self.game.game_over
                                and self.game.current_player == self.player_symbol):
                            col = x // self.cell_size
                            row = y // self.cell_size
                            if self.game.make_move(row, col, self.player_symbol):
                                self.last_ai_move = None
                                self.ai_move()

                    self.menu.handle_event(event)

                    if self.game.game_over:
                        self.state = "gameover"

                elif self.state == "gameover":
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if (self.play_again_rect
                                and self.play_again_rect.collidepoint(event.pos)):
                            self.reset_game()
                            if self.game.current_player == self.ai_symbol:
                                self.ai_move()
                        elif (self.menu_rect
                                and self.menu_rect.collidepoint(event.pos)):
                            running = False

                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if self.menu.visible:
                        self.menu.hide()

            self.finish_ai_move_if_ready()
            if self.game.game_over and self.state == "playing":
                self.state = "gameover"

            # ── Render frame ─────────────────────────────────────────────
            self.draw_board()
            self.draw_panel()
            if self.state == "gameover":
                self.draw_game_over_screen()
            self.menu.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(60)

            # Tự động đi AI sau khi render
            if (not self.menu.visible
                    and not self.ai_thinking
                    and self.state == "playing"
                    and not self.game.game_over
                    and self.game.current_player == self.ai_symbol):
                self.ai_move()
