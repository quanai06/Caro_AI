import pygame

from ..ai.alphabeta_agent import AlphaBetaAgent
from ..ai.minimax_agent import MinimaxAgent


_C = {
    "backdrop": (3, 5, 10, 190),
    "panel": (16, 20, 31),
    "panel_2": (22, 27, 41),
    "border": (54, 66, 98),
    "border_hi": (90, 118, 170),
    "text": (235, 240, 255),
    "muted": (145, 157, 190),
    "low": (84, 96, 130),
    "amber": (255, 190, 55),
    "amber_dim": (178, 126, 28),
    "teal": (50, 215, 185),
    "teal_dim": (28, 145, 130),
    "green": (55, 200, 120),
    "green_dim": (32, 135, 85),
    "red": (220, 75, 70),
    "red_dim": (145, 48, 48),
    "button": (34, 42, 62),
    "button_hover": (46, 58, 84),
}


def _font(size, bold=False):
    for name in ("Segoe UI", "Calibri", "Arial"):
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            pass
    return pygame.font.Font(None, size)


def _rounded(surface, color, rect, radius=10, alpha=255):
    temp = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(
        temp,
        (*color[:3], alpha),
        (0, 0, rect.width, rect.height),
        border_radius=min(radius, rect.width // 2, rect.height // 2),
    )
    surface.blit(temp, rect.topleft)


class _Button:
    def __init__(self, rect, label, accent=None):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.accent = accent or _C["border_hi"]
        self.hovered = False
        self.font = _font(16, bold=True)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False

    def draw(self, surface):
        bg = _C["button_hover"] if self.hovered else _C["button"]
        if self.hovered:
            _rounded(surface, self.accent, self.rect.inflate(8, 8), 12, 22)
        _rounded(surface, bg, self.rect, 10, 245)
        pygame.draw.rect(surface, self.accent, self.rect, 1, border_radius=10)
        text = self.font.render(self.label, True, _C["text"])
        surface.blit(text, text.get_rect(center=self.rect.center))


class _SegmentedControl:
    def __init__(self, rect, options, selected):
        self.rect = pygame.Rect(rect)
        self.options = options
        self.selected = selected
        self.font = _font(15, bold=True)
        self.hovered = None
        self._option_rects = self._make_rects()

    def _make_rects(self):
        rects = {}
        count = len(self.options)
        gap = 8
        item_w = (self.rect.width - gap * (count - 1)) // count
        x = self.rect.x
        for _, key, _ in self.options:
            rects[key] = pygame.Rect(x, self.rect.y, item_w, self.rect.height)
            x += item_w + gap
        return rects

    def set_selected(self, selected):
        self.selected = selected

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = None
            for _, key, _ in self.options:
                if self._option_rects[key].collidepoint(event.pos):
                    self.hovered = key
                    break
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for _, key, _ in self.options:
                if self._option_rects[key].collidepoint(event.pos):
                    self.selected = key
                    return True
        return False

    def draw(self, surface):
        for label, key, color in self.options:
            rect = self._option_rects[key]
            active = key == self.selected
            hovered = key == self.hovered
            bg = color if active else (_C["button_hover"] if hovered else _C["button"])
            alpha = 240 if active else 210
            if active:
                _rounded(surface, color, rect.inflate(8, 8), 12, 26)
            _rounded(surface, bg, rect, 10, alpha)
            border = color if active or hovered else _C["border"]
            pygame.draw.rect(surface, border, rect, 2 if active else 1, border_radius=10)
            text_color = (8, 10, 16) if active else _C["muted"]
            text = self.font.render(label, True, text_color)
            surface.blit(text, text.get_rect(center=rect.center))


class MenuOverlay:
    def __init__(self, screen_rect, game_instance, ai_agent_ref,
                 depth_ref=None, on_apply=None):
        self.screen_rect = screen_rect
        self.game = game_instance
        self.ai_agent_ref = ai_agent_ref
        self.depth_ref = depth_ref
        self.on_apply = on_apply
        self.visible = False

        panel_w = min(500, int(screen_rect.width * 0.88))
        panel_h = 390
        self.panel = pygame.Rect(
            screen_rect.centerx - panel_w // 2,
            screen_rect.centery - panel_h // 2,
            panel_w,
            panel_h,
        )

        row_x = self.panel.x + 34
        row_w = self.panel.width - 68
        self.difficulty_ctrl = _SegmentedControl(
            (row_x, self.panel.y + 98, row_w, 42),
            [
                ("Easy", "easy", _C["green"]),
                ("Medium", "medium", _C["amber"]),
                ("Hard", "hard", _C["red"]),
            ],
            "medium",
        )
        self.algorithm_ctrl = _SegmentedControl(
            (row_x, self.panel.y + 182, row_w, 42),
            [
                ("Alpha-Beta", "alphabeta", _C["teal"]),
                ("Minimax", "minimax", _C["amber"]),
            ],
            "alphabeta",
        )
        self.symbol_ctrl = _SegmentedControl(
            (row_x, self.panel.y + 266, row_w, 42),
            [
                ("Play X", "X", _C["amber"]),
                ("Play O", "O", _C["teal"]),
            ],
            "X",
        )

        self.close_btn = _Button(
            (self.panel.right - 48, self.panel.y + 16, 32, 32),
            "x",
            _C["red"],
        )
        self.apply_btn = _Button(
            (self.panel.right - 154, self.panel.bottom - 56, 120, 40),
            "Apply",
            _C["teal"],
        )
        self.cancel_btn = _Button(
            (self.panel.right - 286, self.panel.bottom - 56, 120, 40),
            "Cancel",
            _C["border_hi"],
        )

        self._title_font = _font(26, bold=True)
        self._label_font = _font(14, bold=True)
        self._hint_font = _font(13)
        self._sync_from_live()

    def _current_algorithm(self):
        if isinstance(self.ai_agent_ref[0], MinimaxAgent):
            return "minimax"
        return "alphabeta"

    def _sync_from_live(self):
        agent = self.ai_agent_ref[0]
        self.difficulty_ctrl.set_selected(getattr(agent, "difficulty", "medium"))
        self.algorithm_ctrl.set_selected(self._current_algorithm())
        self.symbol_ctrl.set_selected(getattr(self.game, "player_symbol", "X"))

    def _fallback_apply(self, difficulty, algorithm):
        if algorithm == "minimax":
            self.ai_agent_ref[0] = MinimaxAgent(difficulty=difficulty)
        else:
            self.ai_agent_ref[0] = AlphaBetaAgent(difficulty=difficulty)
        self.ai_agent_ref[0].ai_symbol = getattr(self.game, "ai_player", "O")
        if self.depth_ref is not None:
            self.depth_ref[0] = self.ai_agent_ref[0].depth_map.get(difficulty, self.depth_ref[0])

    def apply_changes(self):
        difficulty = self.difficulty_ctrl.selected
        algorithm = self.algorithm_ctrl.selected
        player_symbol = self.symbol_ctrl.selected
        if self.on_apply:
            self.on_apply(
                difficulty=difficulty,
                algorithm=algorithm,
                player_symbol=player_symbol,
            )
        else:
            self._fallback_apply(difficulty, algorithm)
        self.hide()

    def show(self):
        self._sync_from_live()
        self.visible = True

    def hide(self):
        self.visible = False

    def handle_event(self, event):
        if not self.visible:
            return False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.hide()
            return True

        self.difficulty_ctrl.handle_event(event)
        self.algorithm_ctrl.handle_event(event)
        self.symbol_ctrl.handle_event(event)

        if self.close_btn.handle_event(event) or self.cancel_btn.handle_event(event):
            self.hide()
            return True
        if self.apply_btn.handle_event(event):
            self.apply_changes()
            return True
        return True

    def _draw_label(self, surface, text, y):
        label = self._label_font.render(text, True, _C["muted"])
        surface.blit(label, (self.panel.x + 36, y))

    def draw(self, surface):
        if not self.visible:
            return

        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill(_C["backdrop"])
        surface.blit(overlay, (0, 0))

        shadow = self.panel.move(0, 8)
        _rounded(surface, (0, 0, 0), shadow, 18, 120)
        _rounded(surface, _C["panel"], self.panel, 18, 248)
        inner = self.panel.inflate(-2, -2)
        pygame.draw.rect(surface, _C["border"], inner, 1, border_radius=17)

        header = pygame.Rect(self.panel.x, self.panel.y, self.panel.width, 72)
        _rounded(surface, _C["panel_2"], header, 18, 210)
        title = self._title_font.render("Settings", True, _C["text"])
        surface.blit(title, (self.panel.x + 34, self.panel.y + 22))
        subtitle = self._hint_font.render("Changes take effect after Apply.", True, _C["low"])
        surface.blit(subtitle, (self.panel.x + 34, self.panel.y + 52))

        self.close_btn.draw(surface)

        self._draw_label(surface, "Difficulty", self.panel.y + 76)
        self.difficulty_ctrl.draw(surface)

        self._draw_label(surface, "AI model", self.panel.y + 160)
        self.algorithm_ctrl.draw(surface)

        self._draw_label(surface, "Player mark", self.panel.y + 244)
        self.symbol_ctrl.draw(surface)

        note = self._hint_font.render("Changing player mark starts a fresh board.", True, _C["low"])
        surface.blit(note, (self.panel.x + 36, self.panel.y + 318))

        self.cancel_btn.draw(surface)
        self.apply_btn.draw(surface)
