import os
import pygame


class AssetLoader:
    """Small asset loader that returns images or generated placeholders.

    Methods:
      - get_image(key, size=None) -> pygame.Surface or None
      - get_font(size, bold=False) -> pygame.font.Font
    """

    # Prefer a project-level `assets/` folder (at repo root). Fall back to
    # the package-local `caro_ai/assets/` folder so assets already committed
    # under `caro_ai/assets` are discovered.
    _HERE = os.path.dirname(__file__)
    _REPO_ROOT = os.path.abspath(os.path.join(_HERE, '..', '..'))
    ASSET_DIRS = [
        os.path.join(_REPO_ROOT, 'assets'),
        os.path.join(_HERE, '..', 'assets'),
    ]
    _cache = {}

    @classmethod
    def get_image(cls, key, size=None):
        if key is None:
            return None
        if key in cls._cache:
            surf = cls._cache[key]
        else:
            # look through candidate asset dirs and pick the first match
            path = None
            for d in cls.ASSET_DIRS:
                candidate = os.path.join(d, f"{key}.png")
                if os.path.exists(candidate):
                    path = candidate
                    break
            if path:
                surf = pygame.image.load(path).convert_alpha()
            else:
                surf = cls._make_placeholder(key)
            cls._cache[key] = surf

        if size and surf:
            return pygame.transform.smoothscale(surf, size)
        return surf

    @classmethod
    def get_font(cls, size, bold=False):
        # Try to load any .ttf font in assets/fonts/ first so bundled fonts
        # with proper glyph coverage are preferred. If none found, fall back
        # to a reasonable system font.
        fonts_dir_candidates = []
        # repo-level fonts folder
        repo_fonts = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')), 'assets', 'fonts')
        fonts_dir_candidates.append(repo_fonts)
        # package-local fonts folder
        pkg_fonts = os.path.join(os.path.dirname(__file__), '..', 'assets', 'fonts')
        fonts_dir_candidates.append(pkg_fonts)

        for fd in fonts_dir_candidates:
            try:
                if os.path.isdir(fd):
                    for fname in os.listdir(fd):
                        if fname.lower().endswith('.ttf'):
                            fpath = os.path.join(fd, fname)
                            try:
                                return pygame.font.Font(fpath, size)
                            except Exception:
                                # skip problematic font files
                                continue
            except Exception:
                continue

        # fallback system fonts (try multiple common names)
        for name in ('segoeui', 'arial', 'dejavusans', None):
            try:
                return pygame.font.SysFont(name, size, bold=bold)
            except Exception:
                continue
        # last resort
        return pygame.font.Font(None, size)

    @staticmethod
    def _make_placeholder(key, w=240, h=80):
        pygame.font.init()
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        hval = abs(hash(key)) % 200
        color = (50 + hval, 120, 180)
        surf.fill(color)
        font = pygame.font.SysFont('segoeui', 20, bold=True)
        txt = font.render(key.replace('_', ' ').upper(), True, (255, 255, 255))
        r = txt.get_rect(center=(w // 2, h // 2))
        surf.blit(txt, r)
        return surf