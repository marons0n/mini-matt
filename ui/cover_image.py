from kivy.uix.image import AsyncImage
from kivy.graphics import Color, Rectangle

from .theme import Theme


class CoverImage(AsyncImage):
    """AsyncImage that shows a gray square when no image is available."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self._bg_color = Color(*Theme.PLACEHOLDER_COLOR)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg,
                   on_load=self._on_load, on_error=self._on_error)

    def _update_bg(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def _on_load(self, *args):
        # Hide placeholder when an image is successfully loaded
        if self.texture:
            self._bg_color.a = 0
        else:
            self._bg_color.a = 1

    def _on_error(self, *args):
        # Show gray placeholder on load failure
        self._bg_color.a = 1
        self.texture = None

    def set_source(self, src: str):
        """Set the image source and reset placeholder state."""
        if src:
            self._bg_color.a = 0
            self.source = src
            self.reload()
        else:
            self.source = ''
            self.texture = None
            self._bg_color.a = 1
