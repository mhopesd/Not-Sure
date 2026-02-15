"""Loading splash screen view"""
import customtkinter as ctk
from ui.styles import ThemeManager, FONTS, RADIUS, SPACING


class LoadingView(ctk.CTkFrame):
    """Loading screen shown during app initialization"""

    def __init__(self, parent):
        colors = ThemeManager.get_colors()
        super().__init__(parent, fg_color=colors["bg"], corner_radius=0)
        self.grid(row=0, column=0, sticky="nsew")

        # Center Container
        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Logo
        logo_frame = ctk.CTkFrame(
            self.center_frame,
            width=80,
            height=80,
            fg_color=colors["accent"],
            corner_radius=RADIUS["xl"]
        )
        logo_frame.pack(pady=(0, SPACING["lg"]))
        logo_frame.pack_propagate(False)

        ctk.CTkLabel(
            logo_frame,
            text="PA",
            font=("Arial", 32, "bold"),
            text_color="#ffffff"
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Title
        ctk.CTkLabel(
            self.center_frame,
            text="Personal Assistant",
            font=FONTS["heading_lg"],
            text_color=colors["text_primary"]
        ).pack(pady=(0, SPACING["xs"]))

        # Subtitle
        ctk.CTkLabel(
            self.center_frame,
            text="Your AI-powered meeting companion",
            font=FONTS["body"],
            text_color=colors["text_muted"]
        ).pack(pady=(0, SPACING["xl"]))

        # Loading Indicator
        self.status_label = ctk.CTkLabel(
            self.center_frame,
            text="Initializing...",
            font=FONTS["caption"],
            text_color=colors["text_secondary"]
        )
        self.status_label.pack()

        # Progress Bar
        self.progress = ctk.CTkProgressBar(
            self.center_frame,
            width=250,
            height=4,
            progress_color=colors["accent"],
            fg_color=colors["border"],
            corner_radius=2
        )
        self.progress.pack(pady=(SPACING["lg"], 0))
        self.progress.configure(mode="indeterminate")
        self.progress.start()

    def set_status(self, text):
        """Update the loading status text"""
        self.status_label.configure(text=text)
