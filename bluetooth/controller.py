import threading
import dbus
import dbus.mainloop.glib
from gi.repository import GLib
import time


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

