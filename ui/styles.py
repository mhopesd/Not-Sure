# --- THEME SYSTEM ---
# Supports both light and dark themes

# Light theme colors (from Figma design)
LIGHT_THEME = {
    "bg": "#f9fafb",              # Main background (gray-50)
    "bg_secondary": "#ffffff",     # Card backgrounds
    "card": "#ffffff",             # Card surface
    "card_hover": "#f3f4f6",       # Card hover state
    "border": "#e5e7eb",           # Border color (gray-200)
    "border_light": "#f3f4f6",     # Lighter border

    "primary": "#030213",          # Primary button background
    "primary_fg": "#ffffff",       # Primary button text
    "primary_hover": "#1f2937",    # Primary button hover

    "secondary": "#f3f4f6",        # Secondary button background
    "secondary_fg": "#374151",     # Secondary button text
    "secondary_hover": "#e5e7eb",  # Secondary button hover

    "destructive": "#dc2626",      # Red for stop/delete
    "destructive_fg": "#ffffff",
    "destructive_hover": "#b91c1c",

    "accent": "#3b82f6",           # Blue accent for AI features
    "accent_fg": "#ffffff",
    "accent_light": "#dbeafe",     # Light blue background

    "success": "#22c55e",          # Green for success states
    "success_light": "#dcfce7",

    "warning": "#f59e0b",          # Orange for warnings
    "warning_light": "#fef3c7",

    "text_primary": "#111827",     # Main text (gray-900)
    "text_secondary": "#6b7280",   # Secondary text (gray-500)
    "text_muted": "#9ca3af",       # Muted text (gray-400)
    "text_disabled": "#d1d5db",    # Disabled text

    "input_bg": "#f9fafb",         # Input background
    "input_border": "#d1d5db",     # Input border
    "input_focus": "#3b82f6",      # Input focus ring

    "tab_active": "#ffffff",       # Active tab background
    "tab_inactive": "#f3f4f6",     # Inactive tab background

    "recording_dot": "#dc2626",    # Recording indicator
    "recording_pulse": "#fecaca",  # Recording pulse effect
}

# Dark theme colors (based on original app)
DARK_THEME = {
    "bg": "#121212",               # Main background
    "bg_secondary": "#1a1a1a",     # Secondary background
    "card": "#1E1E1E",             # Card surface
    "card_hover": "#2a2a2a",       # Card hover state
    "border": "#2B2B2B",           # Border color
    "border_light": "#333333",     # Lighter border

    "primary": "#8A2BE2",          # Purple primary
    "primary_fg": "#ffffff",
    "primary_hover": "#7B1FA2",

    "secondary": "#2B2B2B",        # Secondary button
    "secondary_fg": "#E0E0E0",
    "secondary_hover": "#3a3a3a",

    "destructive": "#D32F2F",      # Red
    "destructive_fg": "#ffffff",
    "destructive_hover": "#B71C1C",

    "accent": "#4CAF50",           # Green accent
    "accent_fg": "#ffffff",
    "accent_light": "#1b5e20",

    "success": "#4CAF50",
    "success_light": "#1b5e20",

    "warning": "#FF9800",
    "warning_light": "#e65100",

    "text_primary": "#FFFFFF",
    "text_secondary": "#A0A0A0",
    "text_muted": "#707070",
    "text_disabled": "#505050",

    "input_bg": "#2B2B2B",
    "input_border": "#404040",
    "input_focus": "#8A2BE2",

    "tab_active": "#2B2B2B",
    "tab_inactive": "#1E1E1E",

    "recording_dot": "#D32F2F",
    "recording_pulse": "#5c1a1a",
}

# --- TYPOGRAPHY ---
FONTS = {
    "heading_xl": ("Arial", 28, "bold"),
    "heading_lg": ("Arial", 24, "bold"),
    "heading": ("Arial", 20, "bold"),
    "heading_sm": ("Arial", 18, "bold"),
    "subheading": ("Arial", 16, "bold"),
    "body": ("Arial", 14),
    "body_medium": ("Arial", 14, "bold"),
    "body_sm": ("Arial", 13),
    "caption": ("Arial", 12),
    "caption_sm": ("Arial", 11),
    "mono": ("Consolas", 13),
    "mono_sm": ("Consolas", 12),
}

# --- SPACING ---
SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 16,
    "lg": 24,
    "xl": 32,
    "xxl": 48,
}

# --- RADII ---
RADIUS = {
    "sm": 4,
    "md": 8,
    "lg": 12,
    "xl": 16,
    "full": 9999,
}


class ThemeManager:
    """Manages theme state and provides color access"""

    _current_theme = "light"
    _callbacks = []

    @classmethod
    def get_theme(cls) -> str:
        return cls._current_theme

    @classmethod
    def set_theme(cls, theme: str):
        if theme in ("light", "dark"):
            cls._current_theme = theme
            # Notify listeners
            for callback in cls._callbacks:
                try:
                    callback(theme)
                except:
                    pass

    @classmethod
    def toggle(cls):
        new_theme = "dark" if cls._current_theme == "light" else "light"
        cls.set_theme(new_theme)

    @classmethod
    def is_dark(cls) -> bool:
        return cls._current_theme == "dark"

    @classmethod
    def on_theme_change(cls, callback):
        """Register a callback to be called when theme changes"""
        cls._callbacks.append(callback)

    @classmethod
    def get_colors(cls) -> dict:
        """Get the current theme's color dictionary"""
        return DARK_THEME if cls._current_theme == "dark" else LIGHT_THEME

    @classmethod
    def get(cls, key: str) -> str:
        """Get a specific color from the current theme"""
        colors = cls.get_colors()
        return colors.get(key, "#000000")


# --- CONVENIENCE FUNCTIONS ---
def get_color(key: str) -> str:
    """Shorthand for ThemeManager.get()"""
    return ThemeManager.get(key)


def get_font(key: str) -> tuple:
    """Get a font tuple by key"""
    return FONTS.get(key, FONTS["body"])


# --- LEGACY COMPATIBILITY ---
# Keep old variable names for backwards compatibility during migration
C_BG_DARK = DARK_THEME["bg"]
C_SIDEBAR = DARK_THEME["card"]
C_CARD_BG = DARK_THEME["card"]
C_PURPLE = DARK_THEME["primary"]
C_PURPLE_HOVER = DARK_THEME["primary_hover"]
C_TEXT_MAIN = DARK_THEME["text_primary"]
C_TEXT_SUB = DARK_THEME["text_secondary"]
C_BORDER = DARK_THEME["border"]
