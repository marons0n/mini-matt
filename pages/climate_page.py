from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button

from ui.theme import Theme

class TempControl(BoxLayout):
    """Temperature and fan speed controls for a single side."""
    def __init__(self, side_name: str, **kwargs):
        super().__init__(orientation='vertical', spacing=Theme.SPACING_MEDIUM, **kwargs)
        self.side_name = side_name
        self.temperature = 70
        self.fan_speed = 1

        self.title = Label(text=side_name, font_size=Theme.FONT_SIZE_MEDIUM,
                           color=Theme.PRIMARY_COLOR, size_hint_y=None,
                           height=Theme.HEADER_HEIGHT)
        self.add_widget(self.title)

        self.temp_label = Label(text=f"{self.temperature}°F", font_size=Theme.FONT_SIZE_LARGE,
                                color=Theme.ACCENT_COLOR)
        temp_controls = BoxLayout(size_hint_y=None, height=Theme.BUTTON_HEIGHT,
                                  spacing=Theme.SPACING_SMALL)
        btn_up = Button(text="＋")
        btn_down = Button(text="－")
        btn_up.bind(on_press=lambda *_: self.change_temp(1))
        btn_down.bind(on_press=lambda *_: self.change_temp(-1))
        temp_controls.add_widget(btn_down)
        temp_controls.add_widget(btn_up)

        self.add_widget(self.temp_label)
        self.add_widget(temp_controls)

        self.fan_label = Label(text=f"Fan {self.fan_speed}", font_size=Theme.FONT_SIZE_NORMAL,
                               color=Theme.PRIMARY_COLOR)
        fan_controls = BoxLayout(size_hint_y=None, height=Theme.BUTTON_HEIGHT,
                                 spacing=Theme.SPACING_SMALL)
        fan_up = Button(text="＋")
        fan_down = Button(text="－")
        fan_up.bind(on_press=lambda *_: self.change_fan(1))
        fan_down.bind(on_press=lambda *_: self.change_fan(-1))
        fan_controls.add_widget(fan_down)
        fan_controls.add_widget(fan_up)

        self.add_widget(self.fan_label)
        self.add_widget(fan_controls)

    def change_temp(self, delta):
        self.temperature = max(60, min(90, self.temperature + delta))
        self.temp_label.text = f"{self.temperature}°F"

    def change_fan(self, delta):
        self.fan_speed = max(0, min(5, self.fan_speed + delta))
        self.fan_label.text = f"Fan {self.fan_speed}"


class ClimatePage(BoxLayout):
    """Climate control page with left and right controls."""
    def __init__(self, **kwargs):
        super().__init__(orientation='horizontal', padding=Theme.PADDING_LARGE,
                         spacing=Theme.SPACING_LARGE, **kwargs)
        self.left = TempControl("Left")
        self.right = TempControl("Right")
        self.add_widget(self.left)
        self.add_widget(self.right)

