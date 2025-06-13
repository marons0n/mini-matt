"""
Theme configuration for the car dashboard
Modern, clean design with thin fonts and white background
"""

class Theme:
    # Colors
    BACKGROUND_COLOR = (1, 1, 1, 1)  # Pure white
    SIDEBAR_COLOR = (0.95, 0.95, 0.95, 1)  # Light gray
    PRIMARY_COLOR = (0.2, 0.2, 0.2, 1)  # Dark gray for text
    SECONDARY_COLOR = (0.5, 0.5, 0.5, 1)  # Medium gray
    ACCENT_COLOR = (0.0, 0.47, 0.84, 1)  # Modern blue
    SUCCESS_COLOR = (0.2, 0.7, 0.3, 1)  # Green
    WARNING_COLOR = (0.9, 0.6, 0.1, 1)  # Orange
    ERROR_COLOR = (0.8, 0.2, 0.2, 1)  # Red
    
    # Sidebar
    SIDEBAR_WIDTH = 120
    SIDEBAR_SELECTED_COLOR = (0.9, 0.9, 0.9, 1)  # Slightly darker gray
    SIDEBAR_HOVER_COLOR = (0.92, 0.92, 0.92, 1)  # Light hover
    
    # Typography
    FONT_THIN = 'Roboto-Thin'  # Will fallback to default if not available
    FONT_LIGHT = 'Roboto-Light'
    FONT_REGULAR = 'Roboto-Regular'
    
    # Font Sizes
    FONT_SIZE_LARGE = '32sp'  # Page headers
    FONT_SIZE_MEDIUM = '24sp'  # Section headers
    FONT_SIZE_NORMAL = '18sp'  # Body text
    FONT_SIZE_SMALL = '14sp'  # Secondary text
    FONT_SIZE_ICON = '28sp'  # Sidebar icons
    
    # Spacing
    PADDING_LARGE = 24
    PADDING_MEDIUM = 16
    PADDING_SMALL = 8
    SPACING_LARGE = 20
    SPACING_MEDIUM = 12
    SPACING_SMALL = 6
    
    # Component Heights
    HEADER_HEIGHT = 80
    BUTTON_HEIGHT = 60
    LIST_ITEM_HEIGHT = 70
    
    # Animations
    TRANSITION_DURATION = 0.2