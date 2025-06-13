import threading
import dbus
import dbus.mainloop.glib
from gi.repository import GLib
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.modalview import ModalView
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.progressbar import ProgressBar
from kivy.properties import BooleanProperty
from kivy.clock import Clock
from kivy.core.window import Window
import time

# --- Improved UI Configuration ---
WINDOW_BACKGROUND_COLOR = (0.05, 0.05, 0.1, 1)  # Dark blue background
FONT_COLOR = (0.95, 0.95, 0.95, 1)  # Light text
STATUS_FONT_SIZE = '24sp'  # Larger fonts
METADATA_FONT_SIZE = '20sp'
DEVICE_NAME_FONT_SIZE = '18sp'
TITLE_FONT_SIZE = '28sp'  # Even larger for song title
CONNECT_BUTTON_COLOR = (0.2, 0.6, 0.9, 1)  # Brighter blue
DISCONNECT_BUTTON_COLOR = (0.9, 0.3, 0.2, 1)  # Brighter red
MANAGE_BUTTON_COLOR = (0.2, 0.8, 0.4, 1)  # Brighter green
PAIR_BUTTON_COLOR = (0.7, 0.5, 0.9, 1)  # Purple for pair

# --- D-Bus Constants ---
BLUEZ_SERVICE = 'org.bluez'
ADAPTER_INTERFACE = f'{BLUEZ_SERVICE}.Adapter1'
DEVICE_INTERFACE = f'{BLUEZ_SERVICE}.Device1'
MEDIA_PLAYER_INTERFACE = f'{BLUEZ_SERVICE}.MediaPlayer1'
DBUS_PROPERTIES_INTERFACE = 'org.freedesktop.DBus.Properties'
DBUS_OBJECT_MANAGER_INTERFACE = 'org.freedesktop.DBus.ObjectManager'

class BluetoothController(threading.Thread):
    """ Manages all Bluetooth communication in a separate thread. """
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.bus = None
        self.mainloop = None
        self.player_iface = None
        self.adapter = None
        self.adapter_props = None
        
        self.lock = threading.Lock()
        self._status = "Initializing..."
        self._metadata = {}
        self._connected_device = {"name": "None", "path": None}
        self._discovered_devices = {}
        self._is_scanning = False
        self._last_error = None

    # --- Thread-safe property accessors ---
    @property
    def status(self):
        with self.lock: 
            return self._status
    
    @property
    def metadata(self):
        with self.lock: 
            return self._metadata.copy()
    
    @property
    def connected_device(self):
        with self.lock: 
            return self._connected_device.copy()
    
    @property
    def discovered_devices(self):
        with self.lock: 
            return self._discovered_devices.copy()
    
    @property
    def is_scanning(self):
        with self.lock: 
            return self._is_scanning
    
    @property
    def last_error(self):
        with self.lock:
            return self._last_error

    def _update_status(self, new_status):
        with self.lock:
            if self._status != new_status:
                print(f"[BT_CTRL] Status -> {new_status}")
                self._status = new_status
    
    def _set_error(self, error_msg):
        with self.lock:
            self._last_error = error_msg
            print(f"[BT_CTRL] Error: {error_msg}")
    
    def run(self):
        """ The main loop for the D-Bus thread. """
        try:
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            self.bus = dbus.SystemBus()

            # Find and configure adapter
            adapter_path = self.find_adapter_path()
            if not adapter_path:
                self._update_status("Error: No Bluetooth Adapter Found")
                return

            self.adapter = dbus.Interface(
                self.bus.get_object(BLUEZ_SERVICE, adapter_path), 
                ADAPTER_INTERFACE
            )
            self.adapter_props = dbus.Interface(
                self.bus.get_object(BLUEZ_SERVICE, adapter_path),
                DBUS_PROPERTIES_INTERFACE
            )
            
            # Configure adapter for audio
            self.configure_adapter()
            
            # Set up signal receivers
            self.bus.add_signal_receiver(
                self.properties_changed,
                bus_name=BLUEZ_SERVICE,
                signal_name='PropertiesChanged',
                dbus_interface=DBUS_PROPERTIES_INTERFACE,
                path_keyword='path'
            )
            self.bus.add_signal_receiver(
                self.interfaces_added,
                bus_name=BLUEZ_SERVICE,
                signal_name='InterfacesAdded',
                dbus_interface=DBUS_OBJECT_MANAGER_INTERFACE
            )
            
            # Initial scans
            self.scan_existing_devices()
            
            # Set up periodic tasks
            GLib.timeout_add_seconds(2, self.periodic_check)
            
            self._update_status("Ready - No Device Connected")
            
            # Start main loop
            self.mainloop = GLib.MainLoop()
            self.mainloop.run()
            
        except Exception as e:
            self._set_error(f"Bluetooth initialization failed: {e}")
            self._update_status("Error: Bluetooth Failed")

    def configure_adapter(self):
        """ Configure the Bluetooth adapter for proper operation. """
        try:
            # Make sure adapter is powered on
            self.adapter_props.Set(ADAPTER_INTERFACE, "Powered", True)
            # Make adapter discoverable
            self.adapter_props.Set(ADAPTER_INTERFACE, "Discoverable", True)
            # Set discoverable timeout (0 = always discoverable)
            self.adapter_props.Set(ADAPTER_INTERFACE, "DiscoverableTimeout", dbus.UInt32(0))
            print("[BT_CTRL] Adapter configured successfully")
        except Exception as e:
            print(f"[BT_CTRL] Error configuring adapter: {e}")

    def scan_existing_devices(self):
        """ Scan for already paired/known devices. """
        try:
            manager = dbus.Interface(
                self.bus.get_object(BLUEZ_SERVICE, '/'),
                DBUS_OBJECT_MANAGER_INTERFACE
            )
            objects = manager.GetManagedObjects()
            
            with self.lock:
                for path, interfaces in objects.items():
                    if DEVICE_INTERFACE in interfaces:
                        props = interfaces[DEVICE_INTERFACE]
                        name = props.get("Name", "Unknown Device")
                        paired = props.get("Paired", False)
                        connected = props.get("Connected", False)
                        
                        self._discovered_devices[path] = {
                            "name": name,
                            "paired": paired,
                            "connected": connected
                        }
                        
                        if connected:
                            self._connected_device = {"name": name, "path": path}
                            print(f"[BT_CTRL] Found connected device: {name}")
                            
                    if MEDIA_PLAYER_INTERFACE in interfaces:
                        print(f"[BT_CTRL] Found media player at {path}")
                        GLib.idle_add(self.connect_to_player, path)
                        
        except Exception as e:
            print(f"[BT_CTRL] Error scanning existing devices: {e}")

    def periodic_check(self):
        """ Regular maintenance tasks. """
        if not self.player_iface:
            self.find_player()
        return True

    def find_adapter_path(self):
        """ Finds the path of the first Bluetooth adapter. """
        try:
            manager = dbus.Interface(
                self.bus.get_object(BLUEZ_SERVICE, '/'),
                DBUS_OBJECT_MANAGER_INTERFACE
            )
            objects = manager.GetManagedObjects()
            for path, interfaces in objects.items():
                if ADAPTER_INTERFACE in interfaces:
                    print(f"[BT_CTRL] Found adapter at {path}")
                    return path
        except Exception as e:
            print(f"[BT_CTRL] Error finding adapter: {e}")
        return None

    def toggle_discovery(self):
        """ Starts or stops scanning for devices. """
        if not self.adapter:
            return
            
        try:
            with self.lock:
                if self._is_scanning:
                    print("[BT_CTRL] Stopping discovery...")
                    self.adapter.StopDiscovery()
                    self._is_scanning = False
                else:
                    print("[BT_CTRL] Starting discovery...")
                    self.adapter.StartDiscovery()
                    self._is_scanning = True
        except Exception as e:
            print(f"[BT_CTRL] Discovery toggle error: {e}")
            with self.lock:
                self._is_scanning = False
    
    def pair_and_connect_device(self, device_path):
        """ Pair with a device and then connect to it. """
        try:
            device = dbus.Interface(
                self.bus.get_object(BLUEZ_SERVICE, device_path),
                DEVICE_INTERFACE
            )
            
            # Check if already paired
            device_props = dbus.Interface(
                self.bus.get_object(BLUEZ_SERVICE, device_path),
                DBUS_PROPERTIES_INTERFACE
            )
            
            is_paired = device_props.Get(DEVICE_INTERFACE, "Paired")
            
            if not is_paired:
                print(f"[BT_CTRL] Pairing with device at {device_path}")
                device.Pair()
                time.sleep(2)  # Give pairing time to complete
            
            print(f"[BT_CTRL] Connecting to device at {device_path}")
            device.Connect()
            
        except Exception as e:
            self._set_error(f"Failed to pair/connect: {e}")
    
    def disconnect_device(self, device_path):
        """ Disconnect from a device. """
        try:
            device = dbus.Interface(
                self.bus.get_object(BLUEZ_SERVICE, device_path),
                DEVICE_INTERFACE
            )
            print(f"[BT_CTRL] Disconnecting from {device_path}")
            device.Disconnect()
        except Exception as e:
            self._set_error(f"Failed to disconnect: {e}")

    def find_player(self):
        """ Finds any existing media player interface. """
        try:
            manager = dbus.Interface(
                self.bus.get_object(BLUEZ_SERVICE, '/'),
                DBUS_OBJECT_MANAGER_INTERFACE
            )
            objects = manager.GetManagedObjects()
            for path, interfaces in objects.items():
                if MEDIA_PLAYER_INTERFACE in interfaces:
                    self.connect_to_player(path)
                    return
        except Exception as e:
            print(f"[BT_CTRL] Error finding player: {e}")

    def connect_to_player(self, path):
        """ Establishes an interface with a media player. """
        try:
            self.player_iface = dbus.Interface(
                self.bus.get_object(BLUEZ_SERVICE, path),
                MEDIA_PLAYER_INTERFACE
            )
            print(f"[BT_CTRL] Connected to media player at {path}")
            self.get_player_properties()
        except Exception as e:
            print(f"[BT_CTRL] Failed to connect to player: {e}")
            self.player_iface = None

    def get_player_properties(self):
        """ Retrieves track info and status from the media player. """
        if not self.player_iface:
            return
            
        try:
            props_iface = dbus.Interface(
                self.player_iface.proxy_object,
                DBUS_PROPERTIES_INTERFACE
            )
            props = props_iface.GetAll(MEDIA_PLAYER_INTERFACE)
            
            with self.lock:
                self._status = props.get('Status', 'Connected')
                track_info = props.get('Track', {})
                self._metadata = {
                    "Title": str(track_info.get('Title', 'No Track')),
                    "Artist": str(track_info.get('Artist', 'Unknown Artist')),
                    "Album": str(track_info.get('Album', 'Unknown Album'))
                }
        except Exception as e:
            print(f"[BT_CTRL] Error getting player properties: {e}")
            self.player_iface = None
            with self.lock:
                self._status = "Connected - No Media Info"

    def properties_changed(self, interface, changed_properties, invalidated_properties, path):
        """ Handles property changes for devices and players. """
        if interface == DEVICE_INTERFACE:
            with self.lock:
                # Update device info
                if path not in self._discovered_devices:
                    self._discovered_devices[path] = {"name": "Unknown", "paired": False, "connected": False}
                
                if "Name" in changed_properties:
                    self._discovered_devices[path]["name"] = str(changed_properties["Name"])
                
                if "Paired" in changed_properties:
                    self._discovered_devices[path]["paired"] = bool(changed_properties["Paired"])
                
                if "Connected" in changed_properties:
                    is_connected = bool(changed_properties["Connected"])
                    self._discovered_devices[path]["connected"] = is_connected
                    
                    if is_connected:
                        name = self._discovered_devices[path]["name"]
                        print(f"[BT_CTRL] Device connected: {name}")
                        self._connected_device = {"name": name, "path": path}
                        self._status = "Connected"
                    else:
                        if self._connected_device and path == self._connected_device["path"]:
                            print(f"[BT_CTRL] Device disconnected: {self._connected_device['name']}")
                            self._connected_device = {"name": "None", "path": None}
                            self._status = "Ready - No Device Connected"
                            self._metadata = {}
                            self.player_iface = None
                            
        elif interface == MEDIA_PLAYER_INTERFACE:
            self.get_player_properties()

    def interfaces_added(self, path, interfaces):
        """ Handles newly discovered devices and players. """
        if DEVICE_INTERFACE in interfaces:
            props = interfaces[DEVICE_INTERFACE]
            name = str(props.get("Name", "Unknown Device"))
            paired = bool(props.get("Paired", False))
            connected = bool(props.get("Connected", False))
            
            print(f"[BT_CTRL] Discovered: {name} at {path}")
            with self.lock:
                self._discovered_devices[path] = {
                    "name": name,
                    "paired": paired,
                    "connected": connected
                }
        
        if MEDIA_PLAYER_INTERFACE in interfaces:
            print(f"[BT_CTRL] Media player interface added at {path}")
            GLib.idle_add(self.connect_to_player, path)

class DeviceRow(RecycleDataViewBehavior, BoxLayout):
    """ A row in the device list with improved styling. """
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.spacing = 15
        self.padding = [10, 5, 10, 5]
        
        # Device name label
        self.name_label = Label(
            font_size=DEVICE_NAME_FONT_SIZE,
            color=FONT_COLOR,
            text_size=(None, None),
            halign='left',
            valign='center'
        )
        
        # Status label
        self.status_label = Label(
            font_size='14sp',
            color=(0.7, 0.7, 0.7, 1),
            size_hint_x=0.3,
            text_size=(None, None),
            halign='center',
            valign='center'
        )
        
        # Action button
        self.action_button = Button(
            size_hint_x=0.3,
            height=40,
            font_size='16sp'
        )
        self.action_button.bind(on_press=self.on_action)
        
        self.add_widget(self.name_label)
        self.add_widget(self.status_label)
        self.add_widget(self.action_button)

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        self.device_path = data.get('id', '')
        self.name_label.text = data.get('name', 'Unknown')
        
        paired = data.get('paired', False)
        connected = data.get('connected', False)
        
        if connected:
            self.status_label.text = "Connected"
            self.status_label.color = (0.2, 0.8, 0.2, 1)  # Green
            self.action_button.text = "Disconnect"
            self.action_button.background_color = DISCONNECT_BUTTON_COLOR
        elif paired:
            self.status_label.text = "Paired"
            self.status_label.color = (0.8, 0.8, 0.2, 1)  # Yellow
            self.action_button.text = "Connect"
            self.action_button.background_color = CONNECT_BUTTON_COLOR
        else:
            self.status_label.text = "Available"
            self.status_label.color = (0.7, 0.7, 0.7, 1)  # Gray
            self.action_button.text = "Pair & Connect"
            self.action_button.background_color = PAIR_BUTTON_COLOR
        
        return super().refresh_view_attrs(rv, index, data)

    def on_action(self, instance):
        """ Handle button press based on device state. """
        popup = App.get_running_app().device_popup
        if popup:
            popup.handle_device_action(self.device_path, instance.text)

class DeviceManagementPopup(ModalView):
    """ Improved device management popup. """
    def __init__(self, bt_controller, **kwargs):
        super().__init__(**kwargs)
        self.bt_controller = bt_controller
        self.size_hint = (0.95, 0.9)
        self.auto_dismiss = False

        layout = BoxLayout(orientation='vertical', padding=15, spacing=15)
        
        # --- Header ---
        header = Label(
            text="Bluetooth Device Manager",
            font_size='28sp',
            color=FONT_COLOR,
            size_hint_y=None,
            height=50,
            bold=True
        )
        layout.add_widget(header)
        
        # --- Status bar ---
        self.status_bar = Label(
            text="Ready to scan for devices",
            font_size='16sp',
            color=(0.8, 0.8, 0.8, 1),
            size_hint_y=None,
            height=30
        )
        layout.add_widget(self.status_bar)
        
        # --- Control buttons ---
        button_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=60,
            spacing=10
        )
        
        self.scan_button = Button(
            text="Start Scanning",
            font_size='18sp',
            background_color=CONNECT_BUTTON_COLOR
        )
        self.scan_button.bind(on_press=self.toggle_scan)
        
        close_button = Button(
            text="Close",
            font_size='18sp',
            background_color=DISCONNECT_BUTTON_COLOR
        )
        close_button.bind(on_press=self.dismiss)
        
        button_layout.add_widget(self.scan_button)
        button_layout.add_widget(close_button)
        layout.add_widget(button_layout)

        # --- Device list ---
        list_header = Label(
            text="Available Devices:",
            font_size='20sp',
            color=FONT_COLOR,
            size_hint_y=None,
            height=40,
            halign='left'
        )
        list_header.bind(size=list_header.setter('text_size'))
        layout.add_widget(list_header)
        
        self.device_list_rv = RecycleView()
        self.device_list_rv.viewclass = DeviceRow
        layout.add_widget(self.device_list_rv)
        
        self.add_widget(layout)
        Clock.schedule_interval(self.update_device_list, 1)

    def toggle_scan(self, instance):
        # Run in D-Bus thread
        GLib.idle_add(self.bt_controller.toggle_discovery)

    def handle_device_action(self, device_path, action):
        """ Handle device actions based on current state. """
        if action == "Disconnect":
            GLib.idle_add(self.bt_controller.disconnect_device, device_path)
        else:  # "Connect" or "Pair & Connect"
            GLib.idle_add(self.bt_controller.pair_and_connect_device, device_path)

    def update_device_list(self, dt):
        devices = self.bt_controller.discovered_devices
        is_scanning = self.bt_controller.is_scanning
        
        # Update scan button
        self.scan_button.text = "Stop Scanning" if is_scanning else "Start Scanning"
        self.scan_button.background_color = DISCONNECT_BUTTON_COLOR if is_scanning else CONNECT_BUTTON_COLOR
        
        # Update status
        if is_scanning:
            self.status_bar.text = "Scanning for devices..."
        elif devices:
            self.status_bar.text = f"Found {len(devices)} device(s)"
        else:
            self.status_bar.text = "No devices found - try scanning"
        
        # Update device list
        self.device_list_rv.data = [
            {
                'id': path,
                'name': data['name'],
                'paired': data['paired'],
                'connected': data['connected'],
                'height': 50
            }
            for path, data in devices.items()
        ]

class MusicApp(App):
    def build(self):
        Window.clearcolor = WINDOW_BACKGROUND_COLOR
        self.device_popup = None
        
        # Main layout with better spacing
        self.layout = BoxLayout(
            orientation='vertical',
            padding=25,
            spacing=20
        )
        
        # --- Header ---
        header = Label(
            text="Bluetooth Music Player",
            font_size='32sp',
            color=FONT_COLOR,
            size_hint_y=None,
            height=60,
            bold=True
        )
        self.layout.add_widget(header)
        
        # --- Status section ---
        status_layout = BoxLayout(
            orientation='vertical',
            spacing=15,
            size_hint_y=None,
            height=120
        )
        
        self.status_label = Label(
            text="Initializing...",
            font_size=STATUS_FONT_SIZE,
            color=FONT_COLOR,
            bold=True
        )
        
        self.device_name_label = Label(
            text="Connected Device: None",
            font_size=DEVICE_NAME_FONT_SIZE,
            color=(0.8, 0.8, 0.8, 1)
        )
        
        status_layout.add_widget(self.status_label)
        status_layout.add_widget(self.device_name_label)
        self.layout.add_widget(status_layout)
        
        # --- Music info section ---
        music_layout = BoxLayout(
            orientation='vertical',
            spacing=10,
            padding=[0, 20, 0, 20]
        )
        
        self.title_label = Label(
            text="♪ No Track Playing",
            font_size=TITLE_FONT_SIZE,
            color=FONT_COLOR,
            bold=True
        )
        
        self.artist_label = Label(
            text="Artist: ---",
            font_size=METADATA_FONT_SIZE,
            color=(0.9, 0.9, 0.9, 1)
        )
        
        self.album_label = Label(
            text="Album: ---",
            font_size=METADATA_FONT_SIZE,
            color=(0.8, 0.8, 0.8, 1)
        )
        
        music_layout.add_widget(self.title_label)
        music_layout.add_widget(self.artist_label)
        music_layout.add_widget(self.album_label)
        self.layout.add_widget(music_layout)
        
        # --- Control button ---
        manage_button = Button(
            text="🔗 Manage Bluetooth Devices",
            font_size='20sp',
            size_hint_y=None,
            height=70,
            background_color=MANAGE_BUTTON_COLOR,
            bold=True
        )
        manage_button.bind(on_press=self.open_device_manager)
        self.layout.add_widget(manage_button)
        
        # Add some space at bottom
        spacer = Label(size_hint_y=0.2)
        self.layout.add_widget(spacer)

        # --- Start Bluetooth controller ---
        self.bt_controller = BluetoothController()
        self.bt_controller.start()

        Clock.schedule_interval(self.update_ui, 0.5)
        return self.layout

    def open_device_manager(self, instance):
        if not self.device_popup:
            self.device_popup = DeviceManagementPopup(bt_controller=self.bt_controller)
        self.device_popup.open()

    def update_ui(self, dt):
        # Update status
        status = self.bt_controller.status
        if "Error" in status:
            self.status_label.color = (0.9, 0.3, 0.3, 1)  # Red for errors
        elif "Connected" in status:
            self.status_label.color = (0.2, 0.9, 0.2, 1)  # Green for connected
        else:
            self.status_label.color = FONT_COLOR
        
        self.status_label.text = f"Status: {status}"
        
        # Update device name
        device_name = self.bt_controller.connected_device['name']
        self.device_name_label.text = f"Connected Device: {device_name}"
        
        # Update music info
        metadata = self.bt_controller.metadata
        title = metadata.get('Title', '')
        artist = metadata.get('Artist', '')
        album = metadata.get('Album', '')
        
        if title and title != 'No Track':
            self.title_label.text = f"♪ {title}"
            self.artist_label.text = f"Artist: {artist}"
            self.album_label.text = f"Album: {album}"
        else:
            self.title_label.text = "♪ No Track Playing"
            self.artist_label.text = "Artist: ---"
            self.album_label.text = "Album: ---"

    def on_stop(self):
        if hasattr(self, 'bt_controller') and self.bt_controller.mainloop:
            self.bt_controller.mainloop.quit()

if __name__ == '__main__':
    MusicApp().run()