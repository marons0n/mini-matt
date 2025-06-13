from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.modalview import ModalView
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.properties import BooleanProperty
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle
from gi.repository import GLib

from ui.theme import Theme
from bluetooth.controller import BluetoothController

class ModernButton(Button):
    """Modern styled button for the car dashboard"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)  # Transparent
        self.color = Theme.PRIMARY_COLOR
        
        with self.canvas.before:
            Color(*Theme.SIDEBAR_COLOR)
            self.bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[8]
            )
        
        self.bind(pos=self.update_bg, size=self.update_bg)
    
    def update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
    
    def on_press(self):
        # Highlight effect
        self.canvas.before.children[0].rgba = Theme.SIDEBAR_SELECTED_COLOR
    
    def on_release(self):
        self.canvas.before.children[0].rgba = Theme.SIDEBAR_COLOR

class DeviceRow(RecycleDataViewBehavior, BoxLayout):
    """Modern device row for the car interface"""
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.spacing = Theme.SPACING_MEDIUM
        self.padding = [Theme.PADDING_MEDIUM, Theme.PADDING_SMALL]
        self.size_hint_y = None
        self.height = Theme.LIST_ITEM_HEIGHT
        
        # Background
        with self.canvas.before:
            Color(*Theme.BACKGROUND_COLOR)
            self.bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[6]
            )
        
        self.bind(pos=self.update_bg, size=self.update_bg)
        
        # Device info
        info_layout = BoxLayout(orientation='vertical', spacing=4)
        
        self.name_label = Label(
            font_size=Theme.FONT_SIZE_NORMAL,
            color=Theme.PRIMARY_COLOR,
            text_size=(None, None),
            halign='left',
            valign='center'
        )
        
        self.status_label = Label(
            font_size=Theme.FONT_SIZE_SMALL,
            color=Theme.SECONDARY_COLOR,
            text_size=(None, None),
            halign='left',
            valign='center'
        )
        
        info_layout.add_widget(self.name_label)
        info_layout.add_widget(self.status_label)
        
        # Action button
        self.action_button = ModernButton(
            size_hint_x=None,
            width=120,
            font_size=Theme.FONT_SIZE_SMALL
        )
        self.action_button.bind(on_press=self.on_action)
        
        self.add_widget(info_layout)
        self.add_widget(self.action_button)
    
    def update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
    
    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        self.device_path = data.get('id', '')
        self.name_label.text = data.get('name', 'Unknown Device')
        
        paired = data.get('paired', False)
        connected = data.get('connected', False)
        
        if connected:
            self.status_label.text = "Connected"
            self.status_label.color = Theme.SUCCESS_COLOR
            self.action_button.text = "Disconnect"
        elif paired:
            self.status_label.text = "Paired"
            self.status_label.color = Theme.WARNING_COLOR
            self.action_button.text = "Connect"
        else:
            self.status_label.text = "Available"
            self.status_label.color = Theme.SECONDARY_COLOR
            self.action_button.text = "Pair"
        
        return super().refresh_view_attrs(rv, index, data)
    
    def on_action(self, instance):
        # Find parent music page and handle action
        parent = self.parent
        while parent and not hasattr(parent, 'handle_device_action'):
            parent = parent.parent
        if parent:
            parent.handle_device_action(self.device_path, instance.text)

class DeviceManagerModal(ModalView):
    """Modern device manager modal for car interface"""
    
    def __init__(self, music_page, **kwargs):
        super().__init__(**kwargs)
        self.music_page = music_page
        self.size_hint = (0.85, 0.8)
        self.auto_dismiss = False
        
        # Main layout
        layout = BoxLayout(
            orientation='vertical',
            padding=Theme.PADDING_LARGE,
            spacing=Theme.SPACING_LARGE
        )
        
        # Header
        header_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=60
        )
        
        header_label = Label(
            text="Bluetooth Devices",
            font_size=Theme.FONT_SIZE_LARGE,
            color=Theme.PRIMARY_COLOR,
            halign='left'
        )
        header_label.bind(size=header_label.setter('text_size'))
        
        close_button = ModernButton(
            text="✕",
            size_hint_x=None,
            width=60,
            font_size=Theme.FONT_SIZE_MEDIUM
        )
        close_button.bind(on_press=self.dismiss)
        
        header_layout.add_widget(header_label)
        header_layout.add_widget(close_button)
        layout.add_widget(header_layout)
        
        # Controls
        controls_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=Theme.BUTTON_HEIGHT,
            spacing=Theme.SPACING_MEDIUM
        )
        
        self.scan_button = ModernButton(
            text="Scan for Devices",
            font_size=Theme.FONT_SIZE_NORMAL
        )
        self.scan_button.bind(on_press=self.toggle_scan)
        
        controls_layout.add_widget(self.scan_button)
        layout.add_widget(controls_layout)
        
        # Device list
        self.device_list = RecycleView()
        self.device_list.viewclass = DeviceRow
        layout.add_widget(self.device_list)
        
        self.add_widget(layout)
        
        # Update timer
        Clock.schedule_interval(self.update_device_list, 1)
    
    def toggle_scan(self, instance):
        if self.music_page.bt_controller:
            GLib.idle_add(self.music_page.bt_controller.toggle_discovery)
    
    def update_device_list(self, dt):
        if not self.music_page.bt_controller:
            return
            
        devices = self.music_page.bt_controller.discovered_devices
        is_scanning = self.music_page.bt_controller.is_scanning
        
        self.scan_button.text = "Stop Scanning" if is_scanning else "Scan for Devices"
        
        self.device_list.data = [
            {
                'id': path,
                'name': data['name'],
                'paired': data['paired'],
                'connected': data['connected'],
                'height': Theme.LIST_ITEM_HEIGHT
            }
            for path, data in devices.items()
        ]
    
    def handle_device_action(self, device_path, action):
        if not self.music_page.bt_controller:
            return
            
        if action == "Disconnect":
            GLib.idle_add(self.music_page.bt_controller.disconnect_device, device_path)
        elif action == "Connect":
            GLib.idle_add(self.music_page.bt_controller.pair_and_connect_device, device_path)
        else:  # "Pair"
            GLib.idle_add(self.music_page.bt_controller.pair_and_connect_device, device_path)

class MusicPage(BoxLayout):
    """Main music page with modern car dashboard styling"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = Theme.PADDING_LARGE
        self.spacing = Theme.SPACING_LARGE
        
        self.bt_controller = None
        self.device_modal = None
        
        self.setup_ui()
        self.setup_bluetooth()
    
    def setup_ui(self):
        """Setup the music page UI"""
        # Header
        header = Label(
            text="Music Player",
            font_size=Theme.FONT_SIZE_LARGE,
            color=Theme.PRIMARY_COLOR,
            size_hint_y=None,
            height=Theme.HEADER_HEIGHT,
            halign='left'
        )
        header.bind(size=header.setter('text_size'))
        self.add_widget(header)
        
        # Connection status
        self.connection_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=100,
            spacing=Theme.SPACING_SMALL
        )
        
        self.status_label = Label(
            text="Bluetooth: Initializing...",
            font_size=Theme.FONT_SIZE_NORMAL,
            color=Theme.SECONDARY_COLOR,
            halign='left'
        )
        self.status_label.bind(size=self.status_label.setter('text_size'))
        
        self.device_label = Label(
            text="No device connected",
            font_size=Theme.FONT_SIZE_SMALL,
            color=Theme.SECONDARY_COLOR,
            halign='left'
        )
        self.device_label.bind(size=self.device_label.setter('text_size'))
        
        self.connection_layout.add_widget(self.status_label)
        self.connection_layout.add_widget(self.device_label)
        self.add_widget(self.connection_layout)
        
        # Now playing section
        self.now_playing_layout = BoxLayout(
            orientation='vertical',
            spacing=Theme.SPACING_MEDIUM,
            padding=[0, Theme.PADDING_LARGE, 0, Theme.PADDING_LARGE]
        )
        
        # Track info
        self.title_label = Label(
            text="No track playing",
            font_size=Theme.FONT_SIZE_LARGE,
            color=Theme.PRIMARY_COLOR,
            bold=True,
            halign='center'
        )
        self.title_label.bind(size=self.title_label.setter('text_size'))
        
        self.artist_label = Label(
            text="",
            font_size=Theme.FONT_SIZE_MEDIUM,
            color=Theme.SECONDARY_COLOR,
            halign='center'
        )
        self.artist_label.bind(size=self.artist_label.setter('text_size'))
        
        self.album_label = Label(
            text="",
            font_size=Theme.FONT_SIZE_NORMAL,
            color=Theme.SECONDARY_COLOR,
            halign='center'
        )
        self.album_label.bind(size=self.album_label.setter('text_size'))
        
        self.now_playing_layout.add_widget(self.title_label)
        self.now_playing_layout.add_widget(self.artist_label)
        self.now_playing_layout.add_widget(self.album_label)
        self.add_widget(self.now_playing_layout)
        
        # Spacer
        self.add_widget(BoxLayout())
        
        # Controls
        controls_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=Theme.BUTTON_HEIGHT,
            spacing=Theme.SPACING_MEDIUM
        )
        
        self.manage_button = ModernButton(
            text="Manage Devices",
            font_size=Theme.FONT_SIZE_NORMAL
        )
        self.manage_button.bind(on_press=self.open_device_manager)
        
        controls_layout.add_widget(self.manage_button)
        self.add_widget(controls_layout)
    
    def setup_bluetooth(self):
        """Initialize Bluetooth controller"""
        try:
            self.bt_controller = BluetoothController()
            self.bt_controller.start()
            Clock.schedule_interval(self.update_music_info, 0.5)
        except Exception as e:
            print(f"Failed to initialize Bluetooth: {e}")
            self.status_label.text = "Bluetooth: Error"
    
    def open_device_manager(self, instance):
        """Open device management modal"""
        if not self.device_modal:
            self.device_modal = DeviceManagerModal(self)
        self.device_modal.open()
    
    def handle_device_action(self, device_path, action):
        """Handle device actions from the modal"""
        if self.device_modal:
            self.device_modal.handle_device_action(device_path, action)
    
    def update_music_info(self, dt):
        """Update music information display"""
        if not self.bt_controller:
            return
        
        # Update connection status
        status = self.bt_controller.status
        if "Error" in status:
            self.status_label.color = Theme.ERROR_COLOR
        elif "Connected" in status:
            self.status_label.color = Theme.SUCCESS_COLOR
        else:
            self.status_label.color = Theme.SECONDARY_COLOR
        
        self.status_label.text = f"Bluetooth: {status}"
        
        # Update device info
        device = self.bt_controller.connected_device
        if device['name'] != 'None':
            self.device_label.text = f"Connected to: {device['name']}"
            self.device_label.color = Theme.SUCCESS_COLOR
        else:
            self.device_label.text = "No device connected"
            self.device_label.color = Theme.SECONDARY_COLOR
        
        # Update track info
        metadata = self.bt_controller.metadata
        title = metadata.get('Title', '')
        artist = metadata.get('Artist', '')
        album = metadata.get('Album', '')
        
        if title and title not in ['No Track', '---', '']:
            self.title_label.text = title
            self.artist_label.text = artist if artist and artist != '---' else ''
            self.album_label.text = album if album and album != '---' else ''
        else:
            self.title_label.text = "No track playing"
            self.artist_label.text = ""
            self.album_label.text = ""
    
    def on_page_enter(self):
        """Called when page becomes active"""
        pass
    
    def on_page_exit(self):
        """Called when leaving page"""
        if self.bt_controller and hasattr(self.bt_controller, 'mainloop'):
            if self.bt_controller.mainloop:
                self.bt_controller.mainloop.quit()
