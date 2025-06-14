from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

from ui.theme import Theme


class MapsPage(BoxLayout):
    """Placeholder maps page with basic styling."""
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=Theme.PADDING_LARGE,
                         spacing=Theme.SPACING_LARGE, **kwargs)
        self.add_widget(Label(text="Maps Page", font_size=Theme.FONT_SIZE_LARGE,
                              color=Theme.PRIMARY_COLOR))

