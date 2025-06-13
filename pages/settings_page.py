from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

class SettingsPage(BoxLayout):
    """Placeholder settings page."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(Label(text="Settings Page"))
