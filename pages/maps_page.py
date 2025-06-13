from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

class MapsPage(BoxLayout):
    """Placeholder maps page."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(Label(text="Maps Page"))
