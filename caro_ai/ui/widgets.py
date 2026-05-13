import pygame
from .asset_loader import AssetLoader

class Widget:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.visible = True
        self.enabled = True

    def handle_event(self, event):
        pass

    def draw(self, surface):
        pass

class Button(Widget):
    def __init__(self, x, y, width, height, text, 
                 image_key_normal=None, image_key_hover=None,
                 color=(100,100,120), hover_color=(70,70,90),
                 text_color=(255,255,255), font_size=18, corner_radius=10):
        super().__init__(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.font = pygame.font.SysFont("segoeui", font_size, bold=True)
        self.corner_radius = corner_radius
        self.is_hovered = False
        self.callback = None

        # Ảnh nền
        self.img_normal = AssetLoader.get_image(image_key_normal) if image_key_normal else None
        self.img_hover = AssetLoader.get_image(image_key_hover) if image_key_hover else None

    def draw(self, surface):
        if not self.visible:
            return
        # Chọn ảnh hoặc màu
        if self.img_normal and self.img_hover:
            img = self.img_hover if (self.is_hovered and self.enabled) else self.img_normal
            img = pygame.transform.scale(img, (self.rect.width, self.rect.height))
            surface.blit(img, self.rect.topleft)
        else:
            # Fallback vẽ rect như cũ
            color = self.hover_color if self.is_hovered and self.enabled else self.color
            pygame.draw.rect(surface, color, self.rect, border_radius=self.corner_radius)

        # Vẽ text (luôn có)
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        if not self.visible or not self.enabled:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered and self.callback:
                self.callback()
                return True
        return False
    # Note: the image-aware draw implementation above handles both image and fallback drawing.

class ToggleButton(Button):
    def __init__(self, x, y, width, height, text_on, text_off, color_on=(46, 204, 113),
                 color_off=(231, 76, 60), **kwargs):
        super().__init__(x, y, width, height, text_on, **kwargs)
        self.text_on = text_on
        self.text_off = text_off
        self.color_on = color_on
        self.color_off = color_off
        self.state = True  # True = on
        self.text = text_on
        self.color = color_on

    def handle_event(self, event):
        if super().handle_event(event):
            self.state = not self.state
            self.text = self.text_on if self.state else self.text_off
            self.color = self.color_on if self.state else self.color_off
            return True
        return False

class Slider(Widget):
    def __init__(self, x, y, width, min_val, max_val, default_val, label=""):
        super().__init__(x, y, width, 20)
        self.min_val = min_val
        self.max_val = max_val
        self.value = default_val
        self.label = label
        self.dragging = False
        self.font = pygame.font.SysFont("segoeui", 16)
        self.knob_radius = 10
        self.bar_color = (180, 180, 200)
        self.knob_color = (52, 152, 219)
        self.callback = None

    def handle_event(self, event):
        if not self.visible:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            knob_x = self.rect.x + int((self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width)
            if abs(event.pos[0] - knob_x) < self.knob_radius and abs(event.pos[1] - self.rect.centery) < self.knob_radius:
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.dragging and self.callback:
                self.callback()
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            rel_x = max(0, min(self.rect.width, event.pos[0] - self.rect.x))
            self.value = self.min_val + (rel_x / self.rect.width) * (self.max_val - self.min_val)
            if self.callback:
                self.callback()
            return True
        return False

    def draw(self, surface):
        if not self.visible:
            return
        # Draw label
        label_surf = self.font.render(f"{self.label}: {int(self.value)}", True, (50,50,70))
        surface.blit(label_surf, (self.rect.x, self.rect.y - 20))
        # Draw bar
        pygame.draw.rect(surface, self.bar_color, self.rect, border_radius=5)
        # Draw filled portion
        fill_width = int((self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width)
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
        pygame.draw.rect(surface, self.knob_color, fill_rect, border_radius=5)
        # Draw knob
        knob_x = self.rect.x + fill_width
        pygame.draw.circle(surface, self.knob_color, (knob_x, self.rect.centery), self.knob_radius)
        pygame.draw.circle(surface, (255,255,255), (knob_x, self.rect.centery), self.knob_radius-2)

class Panel(Widget):
    def __init__(self, x, y, width, height, color=(50,55,65, 220), corner_radius=15):
        super().__init__(x, y, width, height)
        self.color = color  # RGBA
        self.corner_radius = corner_radius
        self.children = []

    def add_child(self, widget):
        self.children.append(widget)

    def handle_event(self, event):
        if not self.visible:
            return False
        for child in self.children:
            child.handle_event(event)
        return False

    def draw(self, surface):
        if not self.visible:
            return
        # Semi-transparent background
        s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        s.fill(self.color)
        surface.blit(s, (self.rect.x, self.rect.y))
        # Border
        pygame.draw.rect(surface, (200,200,220), self.rect, width=2, border_radius=self.corner_radius)
        for child in self.children:
            child.draw(surface)