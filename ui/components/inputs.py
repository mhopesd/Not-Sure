"""Styled input components"""
import customtkinter as ctk
from ui.styles import ThemeManager, FONTS, RADIUS, SPACING


class StyledLabel(ctk.CTkLabel):
    """Consistent label styling"""

    def __init__(self, parent, text="", variant="body", **kwargs):
        colors = ThemeManager.get_colors()

        # Determine font and color based on variant
        font_map = {
            "heading_xl": (FONTS["heading_xl"], colors["text_primary"]),
            "heading_lg": (FONTS["heading_lg"], colors["text_primary"]),
            "heading": (FONTS["heading"], colors["text_primary"]),
            "heading_sm": (FONTS["heading_sm"], colors["text_primary"]),
            "subheading": (FONTS["subheading"], colors["text_primary"]),
            "body": (FONTS["body"], colors["text_primary"]),
            "body_medium": (FONTS["body_medium"], colors["text_primary"]),
            "body_sm": (FONTS["body_sm"], colors["text_primary"]),
            "caption": (FONTS["caption"], colors["text_secondary"]),
            "muted": (FONTS["body"], colors["text_muted"]),
            "label": (FONTS["body_medium"], colors["text_primary"]),
        }

        font, text_color = font_map.get(variant, font_map["body"])

        defaults = {
            "text": text,
            "font": font,
            "text_color": text_color,
            "anchor": "w",
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)


class StyledEntry(ctk.CTkEntry):
    """Styled text entry field"""

    def __init__(self, parent, placeholder="", **kwargs):
        colors = ThemeManager.get_colors()
        defaults = {
            "placeholder_text": placeholder,
            "fg_color": colors["input_bg"],
            "border_color": colors["input_border"],
            "text_color": colors["text_primary"],
            "placeholder_text_color": colors["text_muted"],
            "font": FONTS["body"],
            "height": 40,
            "corner_radius": RADIUS["md"],
            "border_width": 1,
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)


class StyledTextbox(ctk.CTkTextbox):
    """Styled multi-line text area"""

    def __init__(self, parent, placeholder="", **kwargs):
        colors = ThemeManager.get_colors()
        defaults = {
            "fg_color": colors["input_bg"],
            "border_color": colors["input_border"],
            "text_color": colors["text_primary"],
            "font": FONTS["body"],
            "corner_radius": RADIUS["md"],
            "border_width": 1,
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)

        # Store placeholder for later use
        self._placeholder = placeholder
        self._showing_placeholder = False

        if placeholder:
            self._show_placeholder()
            self.bind("<FocusIn>", self._on_focus_in)
            self.bind("<FocusOut>", self._on_focus_out)

    def _show_placeholder(self):
        colors = ThemeManager.get_colors()
        if not self.get("1.0", "end-1c"):
            self._showing_placeholder = True
            self.insert("1.0", self._placeholder)
            self.configure(text_color=colors["text_muted"])

    def _on_focus_in(self, event):
        colors = ThemeManager.get_colors()
        if self._showing_placeholder:
            self.delete("1.0", "end")
            self.configure(text_color=colors["text_primary"])
            self._showing_placeholder = False

    def _on_focus_out(self, event):
        if not self.get("1.0", "end-1c").strip():
            self._show_placeholder()

    def get_value(self):
        """Get text content, excluding placeholder"""
        if self._showing_placeholder:
            return ""
        return self.get("1.0", "end-1c")


class PasswordEntry(ctk.CTkEntry):
    """Password entry with toggle visibility"""

    def __init__(self, parent, placeholder="Enter password", **kwargs):
        colors = ThemeManager.get_colors()
        self._show_password = False

        defaults = {
            "placeholder_text": placeholder,
            "fg_color": colors["input_bg"],
            "border_color": colors["input_border"],
            "text_color": colors["text_primary"],
            "placeholder_text_color": colors["text_muted"],
            "font": FONTS["body"],
            "height": 40,
            "corner_radius": RADIUS["md"],
            "border_width": 1,
            "show": "*",
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)

    def toggle_visibility(self):
        self._show_password = not self._show_password
        self.configure(show="" if self._show_password else "*")


class FormField(ctk.CTkFrame):
    """Form field with label and input"""

    def __init__(self, parent, label="", placeholder="", input_type="text", **kwargs):
        colors = ThemeManager.get_colors()
        super().__init__(parent, fg_color="transparent", **kwargs)

        # Label
        if label:
            StyledLabel(
                self,
                text=label,
                variant="label"
            ).pack(fill="x", pady=(0, SPACING["xs"]))

        # Input based on type
        if input_type == "password":
            self.input = PasswordEntry(self, placeholder=placeholder)
        elif input_type == "textarea":
            self.input = StyledTextbox(self, placeholder=placeholder, height=100)
        else:
            self.input = StyledEntry(self, placeholder=placeholder)

        self.input.pack(fill="x")

    def get(self):
        """Get the input value"""
        if isinstance(self.input, StyledTextbox):
            return self.input.get_value()
        return self.input.get()

    def set(self, value):
        """Set the input value"""
        if isinstance(self.input, StyledTextbox):
            self.input.delete("1.0", "end")
            self.input.insert("1.0", value)
        else:
            self.input.delete(0, "end")
            self.input.insert(0, value)
