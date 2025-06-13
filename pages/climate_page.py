from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

class ClimatePage(BoxLayout):
    """Placeholder climate control page."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(Label(text="Climate Page"))
