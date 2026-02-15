"""Figma Main Page - Exact replica of PAA Figma design"""
import customtkinter as ctk


# Figma design tokens (exact values from Figma)
FIGMA_COLORS = {
    "bg": "#f9fafb",
    "card": "#ffffff",
    "card_border": "#d4d4d4",  # rgba(0,0,0,0.1) approximation
    "primary_btn": "#030213",
    "primary_btn_hover": "#1a1a2e",
    "input_bg": "#f3f3f5",
    "tab_bg": "#ececf0",
    "tab_active": "#ffffff",
    "text_primary": "#0a0a0a",
    "text_secondary": "#4a5565",
    "text_placeholder": "#717182",
    "outline_btn_border": "#d4d4d4",
}

# Figma fonts - Inter with specific weights
# Note: Install Inter font on your system for exact match
FIGMA_FONTS = {
    "heading_lg": ("Inter Medium", 24),      # Personal Assistant title
    "heading_md": ("Inter Medium", 20),      # Record Meeting heading
    "body": ("Inter", 16),                   # Subtitle
    "body_medium": ("Inter Medium", 14),     # Labels, buttons
    "body_regular": ("Inter", 14),           # Input text
    "tab": ("Inter Medium", 14),             # Tab text
}

# Tab icons from Figma (Unicode approximations)
# For exact match, replace with PNG icons in /assets folder
TAB_ICONS = {
    "record": "\U0001F3A4",      # 🎤 Microphone
    "history": "\U0001F551",     # 🕑 Clock
    "journal": "\U0001F4D6",     # 📖 Open book
    "settings": "\u2699\uFE0F",  # ⚙️ Gear
}


class FigmaMainView(ctk.CTkFrame):
    """Main page matching Figma design exactly"""

    def __init__(self, parent, on_start_recording=None, on_stop_recording=None,
                 on_add_speaker=None, on_tab_change=None):
        super().__init__(parent, fg_color=FIGMA_COLORS["bg"], corner_radius=0)

        self.on_start_recording = on_start_recording
        self.on_stop_recording = on_stop_recording
        self.on_add_speaker = on_add_speaker
        self.on_tab_change = on_tab_change
        self.speakers = []
        self.is_recording = False
        self.transcript_text = ""

        self._build_ui()

    def _build_ui(self):
        """Build the exact Figma layout"""
        # Main container with padding
        self.main_container = ctk.CTkFrame(self, fg_color=FIGMA_COLORS["bg"])
        self.main_container.pack(fill="both", expand=True, padx=24, pady=24)

        # Header section
        self._build_header()

        # Tab list
        self._build_tab_list()

        # Content card
        self._build_content_card()

    def _build_header(self):
        """Build header with title and subtitle"""
        header = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 32))

        # Title: "Personal Assistant"
        ctk.CTkLabel(
            header,
            text="Personal Assistant",
            font=FIGMA_FONTS["heading_lg"],
            text_color=FIGMA_COLORS["text_primary"],
            anchor="w"
        ).pack(fill="x")

        # Subtitle
        ctk.CTkLabel(
            header,
            text="Record meetings, track your journey, and get AI-powered insights",
            font=FIGMA_FONTS["body"],
            text_color=FIGMA_COLORS["text_secondary"],
            anchor="w"
        ).pack(fill="x", pady=(8, 0))

    def _build_tab_list(self):
        """Build pill-shaped tab bar matching Figma exactly"""
        # Tab container with pill background
        tab_container = ctk.CTkFrame(
            self.main_container,
            fg_color=FIGMA_COLORS["tab_bg"],
            corner_radius=14,
            height=36
        )
        tab_container.pack(fill="x", pady=(0, 32))
        tab_container.pack_propagate(False)

        # Inner frame for tabs
        tab_inner = ctk.CTkFrame(tab_container, fg_color="transparent")
        tab_inner.pack(fill="both", expand=True, padx=3, pady=3)

        # Configure 4 equal columns
        for i in range(4):
            tab_inner.grid_columnconfigure(i, weight=1, uniform="tabs")
        tab_inner.grid_rowconfigure(0, weight=1)

        # Tab data from Figma: (key, icon, label)
        self.tabs_data = [
            ("record", TAB_ICONS["record"], "Record"),
            ("history", TAB_ICONS["history"], None),
            ("journal", TAB_ICONS["journal"], None),
            ("settings", TAB_ICONS["settings"], None),
        ]

        self.tab_buttons = {}
        self.current_tab = "record"

        for col, (key, icon, label) in enumerate(self.tabs_data):
            btn = ctk.CTkButton(
                tab_inner,
                text="",  # Set dynamically
                fg_color="transparent",
                hover_color=FIGMA_COLORS["card"],
                text_color=FIGMA_COLORS["text_primary"],
                font=FIGMA_FONTS["tab"],
                corner_radius=14,
                height=29,
                border_width=0,
                command=lambda k=key: self._switch_tab(k)
            )
            btn.grid(row=0, column=col, sticky="nsew", padx=1)
            self.tab_buttons[key] = (btn, icon, label)

        # Set initial active tab
        self._update_tab_styles()

    def _switch_tab(self, tab_key):
        """Switch to a different tab"""
        if tab_key == self.current_tab:
            return

        self.current_tab = tab_key
        self._update_tab_styles()

        # Notify callback if set
        if self.on_tab_change:
            self.on_tab_change(tab_key)

    def _update_tab_styles(self):
        """Update tab button styles based on current selection"""
        for key, (btn, icon, label) in self.tab_buttons.items():
            if key == self.current_tab:
                # Active tab: white background, icon + label (if has label)
                if label:
                    btn.configure(
                        text=f"{icon}  {label}",
                        fg_color=FIGMA_COLORS["tab_active"],
                        hover_color=FIGMA_COLORS["tab_active"]
                    )
                else:
                    btn.configure(
                        text=icon,
                        fg_color=FIGMA_COLORS["tab_active"],
                        hover_color=FIGMA_COLORS["tab_active"]
                    )
            else:
                # Inactive tab: transparent, icon only
                btn.configure(
                    text=icon,
                    fg_color="transparent",
                    hover_color=FIGMA_COLORS["card"]
                )

    def _build_content_card(self):
        """Build the main content card"""
        # Card container
        self.card = ctk.CTkFrame(
            self.main_container,
            fg_color=FIGMA_COLORS["card"],
            corner_radius=14,
            border_width=1,
            border_color=FIGMA_COLORS["card_border"]
        )
        self.card.pack(fill="both", expand=True)

        # Card content with padding
        content = ctk.CTkFrame(self.card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=25, pady=25)

        # "Record Meeting" heading
        ctk.CTkLabel(
            content,
            text="Record Meeting",
            font=FIGMA_FONTS["heading_md"],
            text_color=FIGMA_COLORS["text_primary"],
            anchor="w"
        ).pack(fill="x", pady=(0, 16))

        # Start Recording button (matches Figma exactly)
        self.record_btn = ctk.CTkButton(
            content,
            text=f"{TAB_ICONS['record']}  Start Recording",
            fg_color=FIGMA_COLORS["primary_btn"],
            hover_color=FIGMA_COLORS["primary_btn_hover"],
            text_color="#ffffff",
            font=FIGMA_FONTS["body_medium"],
            corner_radius=8,
            height=40,
            width=160,
            command=self._toggle_recording
        )
        self.record_btn.pack(anchor="w", pady=(0, 24))

        # Form fields container
        form_container = ctk.CTkFrame(content, fg_color="transparent")
        form_container.pack(fill="x")

        # Meeting Title field
        self._build_input_field(
            form_container,
            label="Meeting Title (optional)",
            placeholder="Enter meeting title",
            field_name="title"
        )

        # Speakers field with Add button
        self._build_speakers_field(form_container)

        # Transcript section (hidden initially, shown during/after recording)
        self.transcript_section = ctk.CTkFrame(content, fg_color="transparent")

        ctk.CTkLabel(
            self.transcript_section,
            text="Transcript",
            font=FIGMA_FONTS["body_medium"],
            text_color=FIGMA_COLORS["text_primary"],
            anchor="w"
        ).pack(fill="x", pady=(0, 8))

        self.transcript_box = ctk.CTkTextbox(
            self.transcript_section,
            fg_color=FIGMA_COLORS["input_bg"],
            text_color=FIGMA_COLORS["text_primary"],
            font=FIGMA_FONTS["body_regular"],
            corner_radius=8,
            border_width=0,
            height=350  # Larger transcript area
        )
        self.transcript_box.pack(fill="both", expand=True)
        self.transcript_box.configure(state="disabled")

        # Show transcript section by default (always visible)
        self.transcript_section.pack(fill="both", expand=True, pady=(24, 0))

    def _build_input_field(self, parent, label, placeholder, field_name):
        """Build a labeled input field matching Figma design"""
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", pady=(0, 16))

        # Label
        ctk.CTkLabel(
            container,
            text=label,
            font=FIGMA_FONTS["body_medium"],
            text_color=FIGMA_COLORS["text_primary"],
            anchor="w"
        ).pack(fill="x", pady=(0, 8))

        # Input field
        entry = ctk.CTkEntry(
            container,
            placeholder_text=placeholder,
            fg_color=FIGMA_COLORS["input_bg"],
            border_width=0,
            text_color=FIGMA_COLORS["text_primary"],
            placeholder_text_color=FIGMA_COLORS["text_placeholder"],
            font=FIGMA_FONTS["body_regular"],
            height=36,
            corner_radius=8
        )
        entry.pack(fill="x")

        # Store reference
        setattr(self, f"{field_name}_entry", entry)

    def _build_speakers_field(self, parent):
        """Build speakers field with Add button"""
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", pady=(0, 16))

        # Label
        ctk.CTkLabel(
            container,
            text="Speakers (optional)",
            font=FIGMA_FONTS["body_medium"],
            text_color=FIGMA_COLORS["text_primary"],
            anchor="w"
        ).pack(fill="x", pady=(0, 8))

        # Input row
        input_row = ctk.CTkFrame(container, fg_color="transparent")
        input_row.pack(fill="x")

        # Speaker entry
        self.speaker_entry = ctk.CTkEntry(
            input_row,
            placeholder_text="Add speaker name",
            fg_color=FIGMA_COLORS["input_bg"],
            border_width=0,
            text_color=FIGMA_COLORS["text_primary"],
            placeholder_text_color=FIGMA_COLORS["text_placeholder"],
            font=FIGMA_FONTS["body_regular"],
            height=36,
            corner_radius=8
        )
        self.speaker_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.speaker_entry.bind("<Return>", lambda e: self._add_speaker())

        # Add button
        add_btn = ctk.CTkButton(
            input_row,
            text="Add",
            fg_color=FIGMA_COLORS["card"],
            hover_color="#f5f5f5",
            text_color=FIGMA_COLORS["text_primary"],
            font=FIGMA_FONTS["body_medium"],
            corner_radius=8,
            height=36,
            width=60,
            border_width=1,
            border_color=FIGMA_COLORS["outline_btn_border"],
            command=self._add_speaker
        )
        add_btn.pack(side="right")

        # Speaker badges container
        self.speakers_container = ctk.CTkFrame(container, fg_color="transparent")
        self.speakers_container.pack(fill="x", pady=(8, 0))

    def _toggle_recording(self):
        """Toggle recording state"""
        if not self.is_recording:
            self._start_recording()
        else:
            self._stop_recording()

    def _start_recording(self):
        """Start recording"""
        self.is_recording = True
        self.record_btn.configure(
            text="\u23F9  Stop Recording",  # ⏹ Stop icon
            fg_color="#dc2626",
            hover_color="#b91c1c"
        )

        # Disable inputs during recording
        self.title_entry.configure(state="disabled")
        self.speaker_entry.configure(state="disabled")

        # Clear transcript for new recording
        self.transcript_box.configure(state="normal")
        self.transcript_box.delete("1.0", "end")
        self.transcript_box.configure(state="disabled")

        # Call external handler
        if self.on_start_recording:
            self.on_start_recording()

    def _stop_recording(self):
        """Stop recording"""
        self.is_recording = False
        self.record_btn.configure(
            text=f"{TAB_ICONS['record']}  Start Recording",
            fg_color=FIGMA_COLORS["primary_btn"],
            hover_color=FIGMA_COLORS["primary_btn_hover"]
        )

        # Re-enable inputs
        self.title_entry.configure(state="normal")
        self.speaker_entry.configure(state="normal")

        # Call external handler
        if self.on_stop_recording:
            self.on_stop_recording()

    def _add_speaker(self):
        """Add a speaker to the list"""
        name = self.speaker_entry.get().strip()
        if not name or name in self.speakers:
            return

        self.speakers.append(name)
        self.speaker_entry.delete(0, "end")
        self._refresh_speakers()

        if self.on_add_speaker:
            self.on_add_speaker(name)

    def _refresh_speakers(self):
        """Refresh speaker badges"""
        for widget in self.speakers_container.winfo_children():
            widget.destroy()

        for name in self.speakers:
            badge = ctk.CTkFrame(
                self.speakers_container,
                fg_color=FIGMA_COLORS["input_bg"],
                corner_radius=12
            )
            badge.pack(side="left", padx=(0, 8), pady=4)

            ctk.CTkLabel(
                badge,
                text=name,
                font=FIGMA_FONTS["body_regular"],
                text_color=FIGMA_COLORS["text_primary"]
            ).pack(side="left", padx=(12, 4), pady=4)

            remove_btn = ctk.CTkButton(
                badge,
                text="\u2715",
                width=20,
                height=20,
                fg_color="transparent",
                hover_color="#e5e7eb",
                text_color=FIGMA_COLORS["text_placeholder"],
                font=("Inter", 12),
                corner_radius=10,
                command=lambda n=name: self._remove_speaker(n)
            )
            remove_btn.pack(side="right", padx=(0, 4), pady=4)

    def _remove_speaker(self, name):
        """Remove a speaker"""
        if name in self.speakers:
            self.speakers.remove(name)
            self._refresh_speakers()

    # Public methods for external integration
    def start_recording(self):
        """External method to start recording"""
        if not self.is_recording:
            self._start_recording()

    def stop_recording(self):
        """External method to stop recording"""
        if self.is_recording:
            self._stop_recording()

    def update_transcript(self, text):
        """Update the transcript display with summarize_audio() output"""
        self.transcript_text = text
        self.transcript_box.configure(state="normal")
        self.transcript_box.delete("1.0", "end")
        self.transcript_box.insert("1.0", text)
        self.transcript_box.configure(state="disabled")

    def get_meeting_title(self):
        """Get the meeting title"""
        return self.title_entry.get().strip()

    def get_speakers(self):
        """Get list of speakers"""
        return self.speakers.copy()

    def get_metadata(self):
        """Get all recording metadata"""
        return {
            "title": self.get_meeting_title(),
            "speakers": self.get_speakers(),
            "transcript": self.transcript_text
        }

    def reset(self):
        """Reset the view to initial state"""
        self.is_recording = False
        self.speakers = []
        self.transcript_text = ""

        self.title_entry.configure(state="normal")
        self.title_entry.delete(0, "end")

        self.speaker_entry.configure(state="normal")
        self.speaker_entry.delete(0, "end")

        self._refresh_speakers()

        self.transcript_box.configure(state="normal")
        self.transcript_box.delete("1.0", "end")
        self.transcript_box.configure(state="disabled")

        # Keep transcript section visible (don't pack_forget)

        self.record_btn.configure(
            text=f"{TAB_ICONS['record']}  Start Recording",
            fg_color=FIGMA_COLORS["primary_btn"],
            hover_color=FIGMA_COLORS["primary_btn_hover"]
        )
