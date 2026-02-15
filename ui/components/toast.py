"""Toast notification system"""
import customtkinter as ctk
from ui.styles import ThemeManager, FONTS, RADIUS, SPACING


class Toast(ctk.CTkFrame):
    """Individual toast notification"""

    def __init__(self, parent, message="", variant="info", duration=3000, on_dismiss=None, **kwargs):
        colors = ThemeManager.get_colors()

        # Variant styles
        variants = {
            "info": {
                "bg": colors["card"],
                "border": colors["border"],
                "icon": "ℹ️",
            },
            "success": {
                "bg": colors["success_light"],
                "border": colors["success"],
                "icon": "✓",
            },
            "warning": {
                "bg": colors["warning_light"],
                "border": colors["warning"],
                "icon": "⚠️",
            },
            "error": {
                "bg": colors["destructive"],
                "border": colors["destructive"],
                "icon": "✕",
            },
        }

        style = variants.get(variant, variants["info"])

        super().__init__(
            parent,
            fg_color=style["bg"],
            corner_radius=RADIUS["md"],
            border_width=1,
            border_color=style["border"],
            **kwargs
        )

        self.on_dismiss = on_dismiss
        self.duration = duration

        # Content container
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="x", padx=SPACING["md"], pady=SPACING["sm"])

        # Icon
        icon_color = colors["text_primary"] if variant != "error" else colors["destructive_fg"]
        ctk.CTkLabel(
            content,
            text=style["icon"],
            font=FONTS["body"],
            text_color=icon_color,
        ).pack(side="left", padx=(0, SPACING["sm"]))

        # Message
        msg_color = colors["text_primary"] if variant != "error" else colors["destructive_fg"]
        ctk.CTkLabel(
            content,
            text=message,
            font=FONTS["body"],
            text_color=msg_color,
        ).pack(side="left", fill="x", expand=True)

        # Dismiss button
        dismiss_color = colors["text_muted"] if variant != "error" else colors["destructive_fg"]
        dismiss_btn = ctk.CTkButton(
            content,
            text="×",
            width=24,
            height=24,
            fg_color="transparent",
            hover_color=colors["secondary"] if variant != "error" else colors["destructive_hover"],
            text_color=dismiss_color,
            font=FONTS["body_medium"],
            corner_radius=RADIUS["sm"],
            command=self._dismiss
        )
        dismiss_btn.pack(side="right")

        # Auto-dismiss after duration
        if duration > 0:
            self.after(duration, self._dismiss)

    def _dismiss(self):
        if self.on_dismiss:
            self.on_dismiss(self)
        self.destroy()


class ToastManager:
    """Manages toast notifications for the application"""

    _instance = None
    _parent = None
    _toasts = []
    _container = None

    @classmethod
    def initialize(cls, parent):
        """Initialize the toast manager with a parent window"""
        cls._parent = parent
        cls._toasts = []

    @classmethod
    def _ensure_container(cls):
        """Create or return the toast container"""
        if cls._container is None or not cls._container.winfo_exists():
            cls._container = ctk.CTkFrame(
                cls._parent,
                fg_color="transparent",
                width=350,
            )
            # Position at top-right of window
            cls._container.place(relx=1.0, rely=0, anchor="ne", x=-20, y=20)

        return cls._container

    @classmethod
    def show(cls, message, variant="info", duration=3000):
        """Show a toast notification"""
        if cls._parent is None:
            print(f"Toast: {message}")  # Fallback to console
            return

        container = cls._ensure_container()

        toast = Toast(
            container,
            message=message,
            variant=variant,
            duration=duration,
            on_dismiss=cls._on_toast_dismiss
        )
        toast.pack(fill="x", pady=(0, SPACING["xs"]))
        cls._toasts.append(toast)

        # Limit number of visible toasts
        while len(cls._toasts) > 5:
            old_toast = cls._toasts.pop(0)
            if old_toast.winfo_exists():
                old_toast.destroy()

    @classmethod
    def _on_toast_dismiss(cls, toast):
        """Handle toast dismissal"""
        if toast in cls._toasts:
            cls._toasts.remove(toast)

    @classmethod
    def success(cls, message, duration=3000):
        """Show a success toast"""
        cls.show(message, variant="success", duration=duration)

    @classmethod
    def error(cls, message, duration=5000):
        """Show an error toast"""
        cls.show(message, variant="error", duration=duration)

    @classmethod
    def warning(cls, message, duration=4000):
        """Show a warning toast"""
        cls.show(message, variant="warning", duration=duration)

    @classmethod
    def info(cls, message, duration=3000):
        """Show an info toast"""
        cls.show(message, variant="info", duration=duration)

    @classmethod
    def clear_all(cls):
        """Clear all toasts"""
        for toast in cls._toasts[:]:
            if toast.winfo_exists():
                toast.destroy()
        cls._toasts.clear()


# Convenience function
def show_toast(message, variant="info", duration=3000):
    """Convenience function to show a toast"""
    ToastManager.show(message, variant=variant, duration=duration)
