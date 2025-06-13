from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.animation import Animation
from ui.theme import Theme

class SidebarButton(Button):
    """Custom sidebar button with modern styling"""
    
    def __init__(self, icon_text, page_name, **kwargs):
        super().__init__(**kwargs)
        self.page_name = page_name
        self.icon_text = icon_text
        self.is_active = False
        
        # Styling
        self.background_color = (0, 0, 0, 0)  # Transparent
        self.color = Theme.SECONDARY_COLOR
        self.font_size = Theme.FONT_SIZE_ICON
        self.text = icon_text
        self.size_hint_y = None
        self.height = 100
        
        # Custom background
        with self.canvas.before:
            Color(*Theme.SIDEBAR_COLOR)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        
        self.bind(pos=self.update_bg, size=self.update_bg)
    
    def update_bg(self, *args):
        """Update background rectangle"""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
    
    def set_active(self, active):
        """Set button active state"""
        self.is_active = active
        if active:
            self.canvas.before.children[0].rgba = Theme.SIDEBAR_SELECTED_COLOR
            self.color = Theme.ACCENT_COLOR
        else:
            self.canvas.before.children[0].rgba = Theme.SIDEBAR_COLOR
            self.color = Theme.SECONDARY_COLOR
    
    def on_press(self):
        """Handle button press with animation"""
        # Brief highlight animation
        anim = Animation(color=Theme.ACCENT_COLOR, duration=0.1)
        anim.start(self)

class SidebarNavigation(BoxLayout):
    """Sidebar navigation component with modern car dashboard styling"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_x = None
        self.width = Theme.SIDEBAR_WIDTH
        
        # Navigation items configuration
        self.nav_items = [
            {'icon': '♪', 'page': 'music', 'label': 'Music'},
            {'icon': '🗺', 'page': 'maps', 'label': 'Maps'},
            {'icon': '❄', 'page': 'climate', 'label': 'Climate'},
            {'icon': '⚙', 'page': 'settings', 'label': 'Settings'}
        ]
        
        self.navigation_callback = None
        self.buttons = {}
        self.active_page = None
        
        self.setup_sidebar()
    
    def setup_sidebar(self):
        """Setup the sidebar layout and buttons"""
        # Background
        with self.canvas.before:
            Color(*Theme.SIDEBAR_COLOR)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        
        self.bind(pos=self.update_bg, size=self.update_bg)
        
        # Logo/Brand area
        logo_area = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=120,
            padding=[0, Theme.PADDING_MEDIUM, 0, 0]
        )
        
        logo_label = Label(
            text='CAR',
            font_size='24sp',
            color=Theme.PRIMARY_COLOR,
            bold=True
        )
        
        logo_area.add_widget(logo_label)
        self.add_widget(logo_area)
        
        # Navigation buttons
        nav_area = BoxLayout(orientation='vertical', spacing=Theme.SPACING_SMALL)
        
        for item in self.nav_items:
            button = SidebarButton(
                icon_text=item['icon'],
                page_name=item['page']
            )
            button.bind(on_press=lambda x, page=item['page']: self.navigate_to(page))
            
            # Button container with label
            button_container = BoxLayout(
                orientation='vertical',
                size_hint_y=None,
                height=100,
                spacing=2
            )
            
            button_container.add_widget(button)
            
            # Small label under icon
            label = Label(
                text=item['label'],
                font_size='10sp',
                color=Theme.SECONDARY_COLOR,
                size_hint_y=None,
                height=20
            )
            button_container.add_widget(label)
            
            nav_area.add_widget(button_container)
            self.buttons[item['page']] = (button, label)
        
        self.add_widget(nav_area)
        
        # Spacer to push everything to top
        self.add_widget(BoxLayout())
    
    def update_bg(self, *args):
        """Update background rectangle"""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
    
    def bind_navigation(self, callback):
        """Bind navigation callback"""
        self.navigation_callback = callback
    
    def navigate_to(self, page_name):
        """Handle navigation to a page"""
        if self.navigation_callback:
            self.navigation_callback(page_name)
    
    def set_active_item(self, page_name):
        """Set the active navigation item"""
        # Deactivate previous
        if self.active_page and self.active_page in self.buttons:
            button, label = self.buttons[self.active_page]
            button.set_active(False)
            label.color = Theme.SECONDARY_COLOR
        
        # Activate new
        if page_name in self.buttons:
            button, label = self.buttons[page_name]
            button.set_active(True)
            label.color = Theme.ACCENT_COLOR
            self.active_page = page_name