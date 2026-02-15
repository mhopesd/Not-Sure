"""Figma Login Page - Exact replica of PAA Figma design"""
import customtkinter as ctk


# Figma design tokens (exact values from Figma)
FIGMA_COLORS = {
    "bg": "#f9fafb",
    "card": "#ffffff",
    "card_border": "#d4d4d4",  # rgba(0,0,0,0.1) approximation
    "text_primary": "#0a0a0a",
    "text_secondary": "#4a5565",
    "text_muted": "#6a7282",
    "divider": "#d1d5dc",
    "btn_border": "#d4d4d4",
}

FIGMA_FONTS = {
    "heading": ("Inter", 24, "bold"),
    "body": ("Inter", 16),
    "button": ("Inter", 14, "bold"),
    "caption": ("Inter", 12),
}


class FigmaLoginView(ctk.CTkFrame):
    """Login page matching Figma design exactly"""

    def __init__(self, parent, on_login_success=None):
        super().__init__(parent, fg_color=FIGMA_COLORS["bg"], corner_radius=0)

        self.on_login_success = on_login_success
        self._build_ui()

    def _build_ui(self):
        """Build the exact Figma login layout"""
        # Center the card vertically and horizontally
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Card container (centered)
        self.card = ctk.CTkFrame(
            self,
            fg_color=FIGMA_COLORS["card"],
            corner_radius=14,
            border_width=1,
            border_color=FIGMA_COLORS["card_border"],
            width=448
        )
        self.card.grid(row=0, column=0)

        # Card content
        content = ctk.CTkFrame(self.card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=33, pady=33)

        # Header section
        self._build_header(content)

        # Login buttons section
        self._build_login_buttons(content)

        # Terms section
        self._build_terms(content)

    def _build_header(self, parent):
        """Build header with centered title and subtitle"""
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(0, 56))

        # Title: "Personal Assistant" (centered)
        ctk.CTkLabel(
            header,
            text="Personal Assistant",
            font=FIGMA_FONTS["heading"],
            text_color=FIGMA_COLORS["text_primary"],
            anchor="center"
        ).pack(fill="x")

        # Subtitle (centered, wrapping)
        ctk.CTkLabel(
            header,
            text="Sign in to access your meetings, journal, and AI insights",
            font=FIGMA_FONTS["body"],
            text_color=FIGMA_COLORS["text_secondary"],
            anchor="center",
            wraplength=342
        ).pack(fill="x", pady=(8, 0))

    def _build_login_buttons(self, parent):
        """Build login button options"""
        buttons_container = ctk.CTkFrame(parent, fg_color="transparent")
        buttons_container.pack(fill="x")

        # Google button
        self._create_login_button(
            buttons_container,
            icon="G",  # Placeholder for Google icon
            text="Continue with Google",
            command=lambda: self._handle_login("google")
        ).pack(fill="x", pady=(0, 16))

        # Microsoft button
        self._create_login_button(
            buttons_container,
            icon="\u229E",  # Placeholder for Microsoft icon (square with plus)
            text="Continue with Microsoft",
            command=lambda: self._handle_login("microsoft")
        ).pack(fill="x", pady=(0, 16))

        # SSO button
        self._create_login_button(
            buttons_container,
            icon="\U0001F512",  # Lock emoji as placeholder
            text="Continue with SSO",
            command=lambda: self._handle_login("sso")
        ).pack(fill="x", pady=(0, 24))

        # Divider with "Or"
        self._build_divider(buttons_container)

        # Email button
        self._create_login_button(
            buttons_container,
            icon="\u2709",  # Envelope emoji as placeholder
            text="Continue with Email",
            command=lambda: self._handle_login("email")
        ).pack(fill="x", pady=(24, 0))

    def _create_login_button(self, parent, icon, text, command):
        """Create a login button matching Figma style"""
        btn = ctk.CTkButton(
            parent,
            text=f"{icon}   {text}",
            fg_color=FIGMA_COLORS["card"],
            hover_color="#f5f5f5",
            text_color=FIGMA_COLORS["text_primary"],
            font=FIGMA_FONTS["button"],
            corner_radius=8,
            height=40,
            border_width=1,
            border_color=FIGMA_COLORS["btn_border"],
            command=command
        )
        return btn

    def _build_divider(self, parent):
        """Build the 'Or' divider"""
        divider_frame = ctk.CTkFrame(parent, fg_color="transparent", height=20)
        divider_frame.pack(fill="x")

        # Left line
        left_line = ctk.CTkFrame(
            divider_frame,
            height=1,
            fg_color=FIGMA_COLORS["divider"]
        )
        left_line.place(relx=0, rely=0.5, relwidth=0.45, anchor="w")

        # "Or" text
        or_label = ctk.CTkLabel(
            divider_frame,
            text="Or",
            font=("Inter", 14),
            text_color=FIGMA_COLORS["text_muted"],
            fg_color=FIGMA_COLORS["card"],
            width=32
        )
        or_label.place(relx=0.5, rely=0.5, anchor="center")

        # Right line
        right_line = ctk.CTkFrame(
            divider_frame,
            height=1,
            fg_color=FIGMA_COLORS["divider"]
        )
        right_line.place(relx=1, rely=0.5, relwidth=0.45, anchor="e")

    def _build_terms(self, parent):
        """Build terms of service text"""
        terms = ctk.CTkLabel(
            parent,
            text="By continuing, you agree to our Terms of Service and Privacy Policy",
            font=FIGMA_FONTS["caption"],
            text_color=FIGMA_COLORS["text_muted"],
            anchor="center"
        )
        terms.pack(fill="x", pady=(56, 0))

    def _handle_login(self, provider):
        """Handle login button click"""
        # Create session data
        session_data = {
            "provider": provider,
            "email": f"user@{provider}.com",
            "logged_in": True
        }

        # Notify parent
        if self.on_login_success:
            self.on_login_success(session_data)
