"""Badge components for tags and status indicators"""
import customtkinter as ctk
from ui.styles import ThemeManager, FONTS, RADIUS, SPACING


class Badge(ctk.CTkFrame):
    """Base badge/pill component"""

    def __init__(self, parent, text="", variant="default", **kwargs):
        colors = ThemeManager.get_colors()

        # Variant styles
        variants = {
            "default": {
                "fg_color": colors["secondary"],
                "text_color": colors["text_primary"],
                "border_color": colors["border"],
            },
            "primary": {
                "fg_color": colors["primary"],
                "text_color": colors["primary_fg"],
                "border_color": colors["primary"],
            },
            "accent": {
                "fg_color": colors["accent_light"],
                "text_color": colors["accent"],
                "border_color": colors["accent"],
            },
            "success": {
                "fg_color": colors["success_light"],
                "text_color": colors["success"],
                "border_color": colors["success"],
            },
            "warning": {
                "fg_color": colors["warning_light"],
                "text_color": colors["warning"],
                "border_color": colors["warning"],
            },
            "destructive": {
                "fg_color": colors["destructive"],
                "text_color": colors["destructive_fg"],
                "border_color": colors["destructive"],
            },
            "outline": {
                "fg_color": "transparent",
                "text_color": colors["text_primary"],
                "border_color": colors["border"],
            },
        }

        style = variants.get(variant, variants["default"])

        defaults = {
            "fg_color": style["fg_color"],
            "corner_radius": RADIUS["full"],
            "border_width": 1,
            "border_color": style["border_color"],
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)

        # Badge text
        self.label = ctk.CTkLabel(
            self,
            text=text,
            font=FONTS["caption_sm"],
            text_color=style["text_color"],
        )
        self.label.pack(padx=SPACING["sm"], pady=SPACING["xs"])

    def set_text(self, text):
        self.label.configure(text=text)


class SpeakerBadge(ctk.CTkFrame):
    """Badge for displaying speaker names with optional remove button"""

    def __init__(self, parent, name="", on_remove=None, **kwargs):
        colors = ThemeManager.get_colors()
        super().__init__(
            parent,
            fg_color=colors["secondary"],
            corner_radius=RADIUS["full"],
            border_width=1,
            border_color=colors["border"],
            **kwargs
        )

        self.name = name
        self.on_remove = on_remove

        # Speaker icon and name
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(padx=SPACING["sm"], pady=SPACING["xs"])

        ctk.CTkLabel(
            content,
            text=f"👤 {name}",
            font=FONTS["caption"],
            text_color=colors["text_primary"],
        ).pack(side="left")

        # Remove button (if callback provided)
        if on_remove:
            remove_btn = ctk.CTkButton(
                content,
                text="×",
                width=18,
                height=18,
                fg_color="transparent",
                hover_color=colors["destructive"],
                text_color=colors["text_secondary"],
                font=FONTS["body_medium"],
                corner_radius=RADIUS["full"],
                command=lambda: on_remove(name)
            )
            remove_btn.pack(side="left", padx=(SPACING["xs"], 0))


class StatusBadge(ctk.CTkFrame):
    """Status indicator with dot and text"""

    def __init__(self, parent, text="", status="default", **kwargs):
        colors = ThemeManager.get_colors()
        super().__init__(parent, fg_color="transparent", **kwargs)

        # Status colors
        status_colors = {
            "default": colors["text_muted"],
            "active": colors["success"],
            "recording": colors["destructive"],
            "processing": colors["accent"],
            "warning": colors["warning"],
            "error": colors["destructive"],
        }

        dot_color = status_colors.get(status, status_colors["default"])

        # Status dot
        self.dot = ctk.CTkFrame(
            self,
            width=8,
            height=8,
            fg_color=dot_color,
            corner_radius=RADIUS["full"]
        )
        self.dot.pack(side="left", padx=(0, SPACING["xs"]))

        # Status text
        self.label = ctk.CTkLabel(
            self,
            text=text,
            font=FONTS["caption"],
            text_color=colors["text_secondary"],
        )
        self.label.pack(side="left")

        # For recording animation
        self._animate = status == "recording"
        if self._animate:
            self._pulse()

    def _pulse(self):
        """Animate the dot for recording status"""
        if not self._animate:
            return

        colors = ThemeManager.get_colors()
        current_color = self.dot.cget("fg_color")

        # Toggle between bright red and darker red
        if current_color == colors["destructive"]:
            self.dot.configure(fg_color=colors["recording_pulse"])
        else:
            self.dot.configure(fg_color=colors["destructive"])

        self.after(500, self._pulse)

    def set_status(self, text, status="default"):
        colors = ThemeManager.get_colors()
        status_colors = {
            "default": colors["text_muted"],
            "active": colors["success"],
            "recording": colors["destructive"],
            "processing": colors["accent"],
            "warning": colors["warning"],
            "error": colors["destructive"],
        }

        dot_color = status_colors.get(status, status_colors["default"])
        self.dot.configure(fg_color=dot_color)
        self.label.configure(text=text)

        # Update animation state
        self._animate = status == "recording"
        if self._animate:
            self._pulse()


class CountBadge(ctk.CTkFrame):
    """Small circular badge for showing counts"""

    def __init__(self, parent, count=0, **kwargs):
        colors = ThemeManager.get_colors()
        super().__init__(
            parent,
            width=20,
            height=20,
            fg_color=colors["destructive"],
            corner_radius=RADIUS["full"],
            **kwargs
        )

        self.label = ctk.CTkLabel(
            self,
            text=str(count) if count < 100 else "99+",
            font=FONTS["caption_sm"],
            text_color=colors["destructive_fg"],
        )
        self.label.place(relx=0.5, rely=0.5, anchor="center")

    def set_count(self, count):
        self.label.configure(text=str(count) if count < 100 else "99+")
