"""Styled button components"""
import customtkinter as ctk
from ui.styles import ThemeManager, FONTS, RADIUS


class PrimaryButton(ctk.CTkButton):
    """Primary action button (dark background, white text)"""

    def __init__(self, parent, text="", command=None, **kwargs):
        colors = ThemeManager.get_colors()
        defaults = {
            "text": text,
            "command": command,
            "fg_color": colors["primary"],
            "hover_color": colors["primary_hover"],
            "text_color": colors["primary_fg"],
            "font": FONTS["body_medium"],
            "height": 40,
            "corner_radius": RADIUS["md"],
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)


class SecondaryButton(ctk.CTkButton):
    """Secondary action button (light background)"""

    def __init__(self, parent, text="", command=None, **kwargs):
        colors = ThemeManager.get_colors()
        defaults = {
            "text": text,
            "command": command,
            "fg_color": colors["secondary"],
            "hover_color": colors["secondary_hover"],
            "text_color": colors["secondary_fg"],
            "font": FONTS["body_medium"],
            "height": 40,
            "corner_radius": RADIUS["md"],
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)


class DestructiveButton(ctk.CTkButton):
    """Destructive action button (red)"""

    def __init__(self, parent, text="", command=None, **kwargs):
        colors = ThemeManager.get_colors()
        defaults = {
            "text": text,
            "command": command,
            "fg_color": colors["destructive"],
            "hover_color": colors["destructive_hover"],
            "text_color": colors["destructive_fg"],
            "font": FONTS["body_medium"],
            "height": 40,
            "corner_radius": RADIUS["md"],
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)


class OutlineButton(ctk.CTkButton):
    """Outline/ghost button (transparent with border)"""

    def __init__(self, parent, text="", command=None, **kwargs):
        colors = ThemeManager.get_colors()
        defaults = {
            "text": text,
            "command": command,
            "fg_color": "transparent",
            "hover_color": colors["secondary"],
            "text_color": colors["text_primary"],
            "border_width": 1,
            "border_color": colors["border"],
            "font": FONTS["body_medium"],
            "height": 40,
            "corner_radius": RADIUS["md"],
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)


class IconButton(ctk.CTkButton):
    """Icon-only button (square, minimal)"""

    def __init__(self, parent, text="", command=None, size=36, **kwargs):
        colors = ThemeManager.get_colors()
        defaults = {
            "text": text,
            "command": command,
            "fg_color": "transparent",
            "hover_color": colors["secondary"],
            "text_color": colors["text_primary"],
            "font": FONTS["body"],
            "width": size,
            "height": size,
            "corner_radius": RADIUS["sm"],
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)


class AccentButton(ctk.CTkButton):
    """Accent button (blue, for AI features)"""

    def __init__(self, parent, text="", command=None, **kwargs):
        colors = ThemeManager.get_colors()
        defaults = {
            "text": text,
            "command": command,
            "fg_color": colors["accent"],
            "hover_color": "#2563eb",  # Slightly darker blue
            "text_color": colors["accent_fg"],
            "font": FONTS["body_medium"],
            "height": 40,
            "corner_radius": RADIUS["md"],
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)
