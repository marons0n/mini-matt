"""Theme configuration for the car dashboard"""

class Theme:
    """Theme configuration and dark mode support."""

    # -- Light Theme Colors --
    LIGHT_BACKGROUND = (1, 1, 1, 1)
    LIGHT_SIDEBAR = (0.95, 0.95, 0.95, 1)
    LIGHT_PRIMARY = (0.2, 0.2, 0.2, 1)
    LIGHT_SECONDARY = (0.5, 0.5, 0.5, 1)

    # -- Dark Theme Colors --
    DARK_BACKGROUND = (0.08, 0.08, 0.08, 1)
    DARK_SIDEBAR = (0.15, 0.15, 0.15, 1)
    DARK_PRIMARY = (0.9, 0.9, 0.9, 1)
    DARK_SECONDARY = (0.7, 0.7, 0.7, 1)

    ACCENT_COLOR = (0.0, 0.47, 0.84, 1)
    SUCCESS_COLOR = (0.2, 0.7, 0.3, 1)
    WARNING_COLOR = (0.9, 0.6, 0.1, 1)
    ERROR_COLOR = (0.8, 0.2, 0.2, 1)
    # Generic gray used for image placeholders
    PLACEHOLDER_COLOR = (0.5, 0.5, 0.5, 1)

    # Active palette (defaults to light)
    BACKGROUND_COLOR = LIGHT_BACKGROUND
    SIDEBAR_COLOR = LIGHT_SIDEBAR
    PRIMARY_COLOR = LIGHT_PRIMARY
    SECONDARY_COLOR = LIGHT_SECONDARY

    DARK_MODE = False

    # Sidebar
    SIDEBAR_WIDTH = 120
    SIDEBAR_SELECTED_COLOR = (0.9, 0.9, 0.9, 1)
    SIDEBAR_HOVER_COLOR = (0.92, 0.92, 0.92, 1)

    # Typography
    FONT_THIN = 'Roboto-Thin'
    FONT_LIGHT = 'Roboto-Light'
    FONT_REGULAR = 'Roboto-Regular'

    # Font Sizes
    FONT_SIZE_LARGE = '32sp'
    FONT_SIZE_MEDIUM = '24sp'
    FONT_SIZE_NORMAL = '18sp'
    FONT_SIZE_SMALL = '14sp'
    FONT_SIZE_ICON = '28sp'

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

    @classmethod
    def apply_dark_mode(cls, enabled: bool):
        """Switch between light and dark color palettes."""
        cls.DARK_MODE = enabled
        if enabled:
            cls.BACKGROUND_COLOR = cls.DARK_BACKGROUND
            cls.SIDEBAR_COLOR = cls.DARK_SIDEBAR
            cls.PRIMARY_COLOR = cls.DARK_PRIMARY
            cls.SECONDARY_COLOR = cls.DARK_SECONDARY
        else:
            cls.BACKGROUND_COLOR = cls.LIGHT_BACKGROUND
            cls.SIDEBAR_COLOR = cls.LIGHT_SIDEBAR
            cls.PRIMARY_COLOR = cls.LIGHT_PRIMARY
            cls.SECONDARY_COLOR = cls.LIGHT_SECONDARY

