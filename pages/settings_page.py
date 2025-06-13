from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.switch import Switch
from kivy.uix.anchorlayout import AnchorLayout
from kivy.core.window import Window

from ui.theme import Theme


class SettingsPage(BoxLayout):
    """Settings page with dark mode toggle."""
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=Theme.PADDING_LARGE,
                         spacing=Theme.SPACING_LARGE, **kwargs)
        header = Label(text="Settings", font_size=Theme.FONT_SIZE_LARGE,
                       color=Theme.PRIMARY_COLOR, size_hint_y=None,
                       height=Theme.HEADER_HEIGHT)
        self.add_widget(header)

        toggle_layout = AnchorLayout(anchor_x='left', anchor_y='top')
        self.switch = Switch(active=Theme.DARK_MODE)
        self.switch.bind(active=self.on_dark_mode_toggle)
        toggle_label = Label(text="Dark Mode", font_size=Theme.FONT_SIZE_NORMAL,
                             color=Theme.PRIMARY_COLOR)
        box = BoxLayout(size_hint_y=None, height=Theme.BUTTON_HEIGHT,
                        spacing=Theme.SPACING_MEDIUM)
        box.add_widget(toggle_label)
        box.add_widget(self.switch)
        toggle_layout.add_widget(box)
        self.add_widget(toggle_layout)

    def on_dark_mode_toggle(self, instance, value):
        Theme.apply_dark_mode(value)
        Window.clearcolor = Theme.BACKGROUND_COLOR

