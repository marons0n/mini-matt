from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

from ui.theme import Theme


class MiniMattPage(BoxLayout):
    """Placeholder page for future AI assistant functionality."""
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=Theme.PADDING_LARGE,
                         spacing=Theme.SPACING_LARGE, **kwargs)
        self.add_widget(Label(text="mini-matt", font_size=Theme.FONT_SIZE_LARGE,
                              color=Theme.PRIMARY_COLOR))


