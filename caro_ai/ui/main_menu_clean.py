import sys
import os
import math
import pygame

try:
    from .asset_loader import AssetLoader
    _HAS_ASSET_LOADER = True
except ImportError:
    _HAS_ASSET_LOADER = False

# ── Palette ─────────────────────────────────────────────────────────────────
_C = {
    "bg0":        (8,   10,  16),
    "bg1":        (14,  17,  26),
    "bg2":        (22,  26,  40),
    "border":     (45,  55,  85),
    "border_hi":  (80, 105, 160),
    "amber":      (255, 190,  55),
    "amber_dim":  (190, 135,  30),
    "amber_pale": (255, 220, 130),
    "teal":       ( 50, 215, 185),
    "teal_dim":   ( 30, 155, 135),
    "red":        (220,  75,  70),
    "red_dim":    (160,  50,  50),
    "green":      ( 55, 200, 120),
    "green_dim":  ( 35, 145,  85),
    "white":      (255, 255, 255),
    "txt_hi":     (235, 240, 255),
    "txt_mid":    (150, 162, 195),
    "txt_lo":     ( 85,  95, 130),
    "overlay":    ( 10,  12,  20, 210),
}

def _font(size, bold=False):
    for name in ["Segoe UI", "Calibri", "Arial"]:
        try:
            f = pygame.font.SysFont(name, size, bold=bold)
            return f
        except Exception:
            pass
    return pygame.font.Font(None, size)

def _rounded_rect(surf, color, rect, r=12, alpha=255):
    s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(s, (*color[:3], alpha), (0, 0, rect.width, rect.height),
                     border_radius=min(r, rect.width // 2, rect.height // 2))
    surf.blit(s, (rect.x, rect.y))

def _draw_line_aa(surf, color, p1, p2, width=1):
    pygame.draw.line(surf, color, p1, p2, width)


# ── Decorative star-field background ────────────────────────────────────────
class _StarField:
    def __init__(self, w, h, n=80, seed=42):
        import random
        rng = random.Random(seed)
        self.stars = [
            (rng.randint(0, w), rng.randint(0, h),
             rng.uniform(0.4, 1.8), rng.uniform(0, math.pi * 2))
            for _ in range(n)
        ]
        self.w, self.h = w, h

    def draw(self, surf, t):
        for x, y, size, phase in self.stars:
            pulse = 0.55 + 0.45 * math.sin(t * 1.2 + phase)
            a = int(60 + 140 * pulse)
            r = max(1, int(size))
            s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (210, 220, 255, a), (r + 1, r + 1), r)
            surf.blit(s, (x - r, y - r))


# ── Animated ornament lines ──────────────────────────────────────────────────
def _draw_ornament(surf, cx, y, half_w, color, alpha=60):
    """Vẽ đường trang trí ngang với 2 đầu nhọn."""
    s = pygame.Surface((half_w * 2, 8), pygame.SRCALPHA)
    for xi in range(half_w * 2):
        t = abs(xi - half_w) / half_w      # 0 = giữa, 1 = đầu
        a = int(alpha * (1 - t ** 1.5))
        pygame.draw.line(s, (*color[:3], a), (xi, 3), (xi, 4))
    surf.blit(s, (cx - half_w, y - 4))


# ── Fancy Button ─────────────────────────────────────────────────────────────
class _FancyBtn:
    """Button tự vẽ với glow, shimmer, press effect."""

    SCHEMES = {
        "primary":  (_C["amber"],    _C["amber_pale"], _C["bg0"],    _C["amber_dim"]),
        "teal":     (_C["teal_dim"], _C["teal"],       _C["bg0"],    _C["teal_dim"]),
        "danger":   (_C["red_dim"],  _C["red"],        _C["white"],  _C["red_dim"]),
        "ghost":    (_C["bg2"],      (32, 38, 58),     _C["txt_mid"],_C["border"]),
    }

    def __init__(self, rect, label, scheme="ghost", font_size=20):
        self.rect   = pygame.Rect(rect)
        self.label  = label
        self.scheme = scheme
        self.font   = _font(font_size, bold=(scheme == "primary"))
        self.hovered  = False
        self.pressed  = False
        self.callback = None

    def hit(self, pos):
        return self.rect.collidepoint(pos)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.pressed and self.rect.collidepoint(event.pos):
                self.pressed = False
                if self.callback:
                    self.callback()
                return True
            self.pressed = False
        return False

    def draw(self, surf):
        bg_n, bg_h, txt_c, bdr = self.SCHEMES[self.scheme]
        bg = bg_h if self.hovered else bg_n
        r  = self.rect.copy()
        if self.pressed:
            r.inflate_ip(-4, -4)

        # Glow halo khi hover
        if self.hovered:
            glow_c = bg_h[:3]
            for g in (20, 12, 6):
                gr = r.inflate(g * 2, g * 2)
                _rounded_rect(surf, glow_c, gr, r=14 + g, alpha=max(0, 22 - g))

        # Shadow
        shadow = r.move(0, 4)
        _rounded_rect(surf, (0, 0, 0), shadow, r=13, alpha=90)

        # Body
        _rounded_rect(surf, bg, r, r=12, alpha=245)
        pygame.draw.rect(surf, bdr, r, 1, border_radius=12)

        # Shimmer cạnh trên
        if self.hovered:
            sx = r.x + 6
            ex = r.right - 6
            s2 = pygame.Surface((ex - sx, 2), pygame.SRCALPHA)
            for xi in range(ex - sx):
                t  = abs(xi - (ex - sx) / 2) / ((ex - sx) / 2 + 1)
                a2 = int(55 * (1 - t ** 2))
                s2.set_at((xi, 0), (255, 255, 255, a2))
            surf.blit(s2, (sx, r.y + 1))

        # Label
        ts = self.font.render(self.label, True, txt_c)
        surf.blit(ts, ts.get_rect(center=r.center))


# ── Difficulty pill selector ──────────────────────────────────────────────────
class _DiffPill:
    OPTS = [
        ("Easy",   _C["green"],   _C["green_dim"]),
        ("Medium", _C["amber"],   _C["amber_dim"]),
        ("Hard",   _C["red"],     _C["red_dim"]),
    ]

    def __init__(self, cx, y, btn_w=90, btn_h=34, gap=10):
        self.selected = "medium"
        self.font     = _font(15, bold=True)
        self.rects    = {}
        total = len(self.OPTS) * btn_w + (len(self.OPTS) - 1) * gap
        sx = cx - total // 2
        for label, _, _ in self.OPTS:
            self.rects[label.lower()] = pygame.Rect(sx, y, btn_w, btn_h)
            sx += btn_w + gap

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for label, _, _ in self.OPTS:
                key = label.lower()
                if self.rects[key].collidepoint(event.pos):
                    self.selected = key
                    return True
        return False

    def draw(self, surf):
        for label, col_on, col_off in self.OPTS:
            key  = label.lower()
            rect = self.rects[key]
            active = (key == self.selected)
            bg  = col_off if not active else col_on
            alpha = 240 if active else 120
            _rounded_rect(surf, bg, rect, r=rect.height // 2, alpha=alpha)
            border_c = col_on if active else _C["border"]
            pygame.draw.rect(surf, border_c, rect, 2 if active else 1,
                             border_radius=rect.height // 2)
            tc = _C["bg0"] if active else _C["txt_mid"]
            ts = self.font.render(label, True, tc)
            surf.blit(ts, ts.get_rect(center=rect.center))


class _AlgoPill:
    OPTS = [
        ("Alpha-Beta", "alphabeta", _C["teal"], _C["teal_dim"]),
        ("Minimax", "minimax", _C["amber"], _C["amber_dim"]),
    ]

    def __init__(self, cx, y, btn_w=126, btn_h=34, gap=12):
        self.selected = "alphabeta"
        self.font = _font(15, bold=True)
        self.rects = {}
        total = len(self.OPTS) * btn_w + (len(self.OPTS) - 1) * gap
        sx = cx - total // 2
        for _, key, _, _ in self.OPTS:
            self.rects[key] = pygame.Rect(sx, y, btn_w, btn_h)
            sx += btn_w + gap

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for _, key, _, _ in self.OPTS:
                if self.rects[key].collidepoint(event.pos):
                    self.selected = key
                    return True
        return False

    def draw(self, surf):
        for label, key, col_on, col_off in self.OPTS:
            rect = self.rects[key]
            active = key == self.selected
            bg = col_on if active else col_off
            alpha = 240 if active else 115
            _rounded_rect(surf, bg, rect, r=rect.height // 2, alpha=alpha)
            pygame.draw.rect(surf, col_on if active else _C["border"], rect,
                             2 if active else 1, border_radius=rect.height // 2)
            tc = _C["bg0"] if active else _C["txt_mid"]
            ts = self.font.render(label, True, tc)
            surf.blit(ts, ts.get_rect(center=rect.center))


# ── MainMenu ──────────────────────────────────────────────────────────────────
class MainMenu:
    """
    Menu chính đã làm đẹp lại:
    - Không hiển thị tên game (bỏ 'Caro AI')
    - Nút Player First / AI First / Quit kiểu game hiện đại
    - Difficulty pill selector
    - Nền animated starfield + ornament lines
    """

    def __init__(self, screen_or_rect, on_start=None, on_quit=None):
        if isinstance(screen_or_rect, pygame.Surface):
            self.surface     = screen_or_rect
            self.screen_rect = self.surface.get_rect()
        else:
            self.surface     = None
            self.screen_rect = screen_or_rect

        self.on_start  = on_start
        self.on_quit   = on_quit
        self.visible   = True
        self.difficulty = "medium"
        self.algorithm = "alphabeta"
        self._t        = 0.0

        W  = self.screen_rect.width
        H  = self.screen_rect.height
        cx = self.screen_rect.centerx

        # Starfield
        self._stars = _StarField(W, H)

        # Fonts
        self._f_title  = _font(52, bold=True)
        self._f_sub    = _font(14)
        self._f_label  = _font(13)

        # ── Buttons ──────────────────────────────────────────────────────────
        BW, BH = 280, 56
        bx = cx - BW // 2
        base_y = H // 2 - 88

        self._btn_player = _FancyBtn((bx, base_y,      BW, BH), "Player First", "primary", 19)
        self._btn_ai     = _FancyBtn((bx, base_y + 72, BW, BH), "AI First",     "teal",    19)
        self._btn_quit   = _FancyBtn((bx, base_y + 144,BW, BH), "Quit",          "danger",  18)

        self._btn_player.callback = lambda: None
        self._btn_ai.callback     = lambda: None
        self._btn_quit.callback   = lambda: None

        # ── Difficulty ───────────────────────────────────────────────────────
        self._diff = _DiffPill(cx, base_y + 218, btn_w=86, btn_h=34, gap=10)
        self._algo = _AlgoPill(cx, base_y + 272, btn_w=126, btn_h=34, gap=12)

        # ── Kết quả click ────────────────────────────────────────────────────
        self._action = None

        # Pre-render nền gradient (fallback khi không có ảnh)
        self._bg_surf = self._make_bg(W, H)

        # Ảnh nền tuỳ chọn — đặt tại assets/bg/main_menu_bg.png
        self._bg_img = None
        if _HAS_ASSET_LOADER:
            try:
                img = AssetLoader.get_image(os.path.join('bg', 'main_menu_bg'))
                if img:
                    self._bg_img = pygame.transform.smoothscale(img, (W, H))
            except Exception:
                pass

    # ── Nền gradient tĩnh ────────────────────────────────────────────────────
    @staticmethod
    def _make_bg(W, H):
        s = pygame.Surface((W, H))
        for y in range(H):
            t   = y / H
            r   = int(_C["bg0"][0] * (1 - t) + _C["bg1"][0] * t)
            g   = int(_C["bg0"][1] * (1 - t) + _C["bg1"][1] * t)
            b   = int(_C["bg0"][2] * (1 - t) + _C["bg1"][2] * t)
            pygame.draw.line(s, (r, g, b), (0, y), (W, y))
        return s

    # ── Event ─────────────────────────────────────────────────────────────────
    def handle_event(self, event):
        if not self.visible:
            return None

        self._diff.handle_event(event)
        self.difficulty = self._diff.selected
        self._algo.handle_event(event)
        self.algorithm = self._algo.selected

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self._btn_player.hit(pos):
                if callable(self.on_start):
                    self.on_start()
                return "player_first"
            if self._btn_ai.hit(pos):
                if callable(self.on_start):
                    self.on_start()
                return "ai_first"
            if self._btn_quit.hit(pos):
                if callable(self.on_quit):
                    self.on_quit()
                return "quit"

        self._btn_player.handle_event(event)
        self._btn_ai.handle_event(event)
        self._btn_quit.handle_event(event)
        return None

    # ── Draw ──────────────────────────────────────────────────────────────────
    def draw(self, surface):
        if not self.visible:
            return

        self._t += 0.016          # ~60fps
        W  = self.screen_rect.width
        H  = self.screen_rect.height
        cx = self.screen_rect.centerx
        ox = self.screen_rect.x
        oy = self.screen_rect.y

        # --- Nền ---
        if self._bg_img:
            # Có ảnh nền → blit ảnh, phủ overlay tối nhẹ để chữ/nút dễ đọc
            surface.blit(self._bg_img, (ox, oy))
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((8, 10, 16, 10))
            surface.blit(overlay, (ox, oy))
        else:
            # Fallback: gradient + starfield động
            surface.blit(self._bg_surf, (ox, oy))
            self._stars.draw(surface, self._t)

        # --- Đường trang trí trên & dưới title ---
        title_y = H // 2 - 185
        _draw_ornament(surface, cx, title_y + 45, 200, _C["amber"], alpha=55)

        # --- Icon / Symbol thay tên ---
        

        # --- Tagline kín đáo ---

        # --- Đường trang trí phía dưới subtitle ---
        _draw_ornament(surface, cx, title_y + 62, 120, _C["border_hi"], alpha=70)

        # --- Buttons ---
        self._btn_player.draw(surface)
        self._btn_ai.draw(surface)
        self._btn_quit.draw(surface)

        # --- Label "Difficulty" ---
        diff_y   = self._diff.rects["easy"].y
        lbl      = self._f_label.render("Difficulty", True, _C["txt_lo"])
        surface.blit(lbl, lbl.get_rect(center=(cx, diff_y - 18)))
        self._diff.draw(surface)

        algo_y = self._algo.rects["alphabeta"].y
        alg_lbl = self._f_label.render("AI Model", True, _C["txt_lo"])
        surface.blit(alg_lbl, alg_lbl.get_rect(center=(cx, algo_y - 18)))
        self._algo.draw(surface)

        # --- Footer ---
        footer = self._f_label.render("Press ESC to quit", True, _C["txt_lo"])
        surface.blit(footer, footer.get_rect(center=(cx, H - 22)))

    # ── run() blocking loop ───────────────────────────────────────────────────
    def run(self):
        surface = self.surface or pygame.display.get_surface()
        clock   = pygame.time.Clock()
        action  = None
        while action is None:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                result = self.handle_event(event)
                if result in ("player_first", "ai_first", "quit"):
                    action = result
                    break

            self.draw(surface)
            pygame.display.flip()
            clock.tick(60)

        return action, self.difficulty, self.algorithm
