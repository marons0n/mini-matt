from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.clock import Clock

from ui.sidebar import SidebarNavigation
from pages.music_page import MusicPage
from pages.maps_page import MapsPage
from pages.climate_page import ClimatePage
from pages.settings_page import SettingsPage
from ui.theme import Theme

class CarDashboardApp(App):
    def build(self):
        # Configure window for car dashboard (vertical orientation)
        Window.size = (800, 1280)  # Portrait orientation
        Window.clearcolor = Theme.BACKGROUND_COLOR
        
        # Main layout
        self.main_layout = BoxLayout(orientation='horizontal')
        
        # Create sidebar navigation
        self.sidebar = SidebarNavigation()
        self.sidebar.bind_navigation(self.navigate_to_page)
        
        # Create pages
        self.pages = {
            'music': MusicPage(),
            'maps': MapsPage(),
            'climate': ClimatePage(),
            'settings': SettingsPage()
        }
        
        # Current page container
        self.content_area = BoxLayout()
        
        # Add components to main layout
        self.main_layout.add_widget(self.sidebar)
        self.main_layout.add_widget(self.content_area)
        
        # Start with music page
        self.current_page = None
        self.navigate_to_page('music')
        
        return self.main_layout
    
    def navigate_to_page(self, page_name):
        """Navigate to a specific page"""
        if page_name in self.pages:
            # Remove current page
            if self.current_page:
                self.content_area.remove_widget(self.current_page)
            
            # Add new page
            self.current_page = self.pages[page_name]
            self.content_area.add_widget(self.current_page)
            
            # Update sidebar selection
            self.sidebar.set_active_item(page_name)
            
            # Handle page-specific initialization
            if hasattr(self.current_page, 'on_page_enter'):
                self.current_page.on_page_enter()
    
    def on_stop(self):
        """Clean up when app closes"""
        for page in self.pages.values():
            if hasattr(page, 'on_page_exit'):
                page.on_page_exit()

if __name__ == '__main__':
    CarDashboardApp().run()