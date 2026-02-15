"""
Main application using Figma-designed views.

This file uses the FigmaMainView and FigmaLoginView with your existing backend.
Tabs are fully connected to switch between Record, Meetings, Journal, and Settings.

Usage:
    python main_figma.py
"""
import customtkinter as ctk
import threading
import time

# Use centralized logging
from app_logging import logger, log_user_action, log_recording_start, log_recording_stop, log_error

from backend import EnhancedAudioApp
from ui.views.figma_main_view import FigmaMainView, FIGMA_COLORS, FIGMA_FONTS, TAB_ICONS
from ui.views.figma_login_view import FigmaLoginView

# Import existing views for tab navigation
try:
    from ui.views.meetings_view import MeetingsView
    from ui.views.journal_view import JournalView
    from ui.views.settings_view import SettingsView
    HAS_OTHER_VIEWS = True
except ImportError:
    HAS_OTHER_VIEWS = False
    logger.warning("Could not import MeetingsView, JournalView, or SettingsView")


class FigmaApp(ctk.CTk):
    """Application using Figma-designed UI with full tab navigation"""

    def __init__(self):
        super().__init__()
        self.title("Personal Assistant")
        self.geometry("1026x861")
        self.minsize(800, 600)

        # Set appearance
        ctk.set_appearance_mode("light")

        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Initialize state
        self.audio_app = None
        self.current_view = None
        self.current_tab = "record"
        self.is_recording = False
        self.tab_views = {}  # Cache for tab content views

        # UI components
        self.main_container = None
        self.tab_buttons = {}
        self.content_container = None

        # Start initialization
        self._initialize_backend()

    def _initialize_backend(self):
        """Initialize the audio backend"""
        try:
            self.audio_app = EnhancedAudioApp(
                status_callback=self._on_status_update,
                result_callback=self._on_recording_result,
                transcript_callback=self._on_transcript_update,
                level_callback=self._on_level_update
            )
            logger.info("Backend initialized successfully")

            # Check if logged in
            if self.audio_app.is_logged_in():
                self._show_main_interface()
            else:
                self._show_login_view()

        except Exception as e:
            logger.error(f"Backend initialization failed: {e}")
            self._show_main_interface()

    def _show_login_view(self):
        """Show the Figma login view"""
        self._clear_all()

        self.current_view = FigmaLoginView(
            self,
            on_login_success=self._on_login_success
        )
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def _show_main_interface(self):
        """Show the main interface with header, tabs, and content area"""
        self._clear_all()

        # Main container
        self.main_container = ctk.CTkFrame(self, fg_color=FIGMA_COLORS["bg"], corner_radius=0)
        self.main_container.grid(row=0, column=0, sticky="nsew")
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(2, weight=1)  # Content area expands

        # Build header
        self._build_header()

        # Build tab bar
        self._build_tab_bar()

        # Build content container
        self.content_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_container.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 24))
        self.content_container.grid_columnconfigure(0, weight=1)
        self.content_container.grid_rowconfigure(0, weight=1)

        # Show default tab (Record)
        self._switch_tab("record")

    def _build_header(self):
        """Build the Figma header"""
        header = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 32))

        ctk.CTkLabel(
            header,
            text="Personal Assistant",
            font=FIGMA_FONTS["heading_lg"],
            text_color=FIGMA_COLORS["text_primary"],
            anchor="w"
        ).pack(fill="x")

        ctk.CTkLabel(
            header,
            text="Record meetings, track your journey, and get AI-powered insights",
            font=FIGMA_FONTS["body"],
            text_color=FIGMA_COLORS["text_secondary"],
            anchor="w"
        ).pack(fill="x", pady=(8, 0))

    def _build_tab_bar(self):
        """Build the Figma tab bar"""
        tab_container = ctk.CTkFrame(
            self.main_container,
            fg_color=FIGMA_COLORS["tab_bg"],
            corner_radius=14,
            height=36
        )
        tab_container.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 32))
        tab_container.grid_propagate(False)

        tab_inner = ctk.CTkFrame(tab_container, fg_color="transparent")
        tab_inner.pack(fill="both", expand=True, padx=3, pady=3)

        for i in range(4):
            tab_inner.grid_columnconfigure(i, weight=1, uniform="tabs")
        tab_inner.grid_rowconfigure(0, weight=1)

        tabs_data = [
            ("record", TAB_ICONS["record"], "Record"),
            ("history", TAB_ICONS["history"], "Meetings"),
            ("journal", TAB_ICONS["journal"], "Journal"),
            ("settings", TAB_ICONS["settings"], "Settings"),
        ]

        for col, (key, icon, label) in enumerate(tabs_data):
            btn = ctk.CTkButton(
                tab_inner,
                text="",
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

        self._update_tab_styles()

    def _update_tab_styles(self):
        """Update tab button styles based on current selection"""
        for key, (btn, icon, label) in self.tab_buttons.items():
            if key == self.current_tab:
                btn.configure(
                    text=f"{icon}  {label}",
                    fg_color=FIGMA_COLORS["tab_active"],
                    hover_color=FIGMA_COLORS["tab_active"]
                )
            else:
                btn.configure(
                    text=icon,
                    fg_color="transparent",
                    hover_color=FIGMA_COLORS["card"]
                )

    def _switch_tab(self, tab_key):
        """Switch to a different tab"""
        # Prevent switching during recording
        if self.is_recording and tab_key != "record":
            logger.warning("Cannot switch tabs during recording")
            return

        self.current_tab = tab_key
        self._update_tab_styles()

        # Clear content container
        for widget in self.content_container.winfo_children():
            widget.grid_forget()

        # Show appropriate content
        if tab_key == "record":
            self._show_record_content()
        elif tab_key == "history":
            self._show_meetings_content()
        elif tab_key == "journal":
            self._show_journal_content()
        elif tab_key == "settings":
            self._show_settings_content()

    def _show_record_content(self):
        """Show the Record tab content"""
        if "record" not in self.tab_views:
            self.tab_views["record"] = RecordContent(
                self.content_container,
                on_start_recording=self._handle_start_recording,
                on_stop_recording=self._handle_stop_recording
            )

        self.current_view = self.tab_views["record"]
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def _show_meetings_content(self):
        """Show the Meetings tab content"""
        if HAS_OTHER_VIEWS and "history" not in self.tab_views:
            meetings = self.audio_app.chat_history if self.audio_app else []
            self.tab_views["history"] = MeetingsView(
                self.content_container,
                meetings=meetings,
                on_analyze=self._analyze_meeting,
                on_click=self._open_meeting_detail
            )
        elif "history" not in self.tab_views:
            # Placeholder if MeetingsView not available
            self.tab_views["history"] = PlaceholderContent(
                self.content_container,
                title="Meetings",
                message="View your recorded meetings here"
            )

        self.current_view = self.tab_views["history"]
        self.current_view.grid(row=0, column=0, sticky="nsew")

        # Refresh meetings data
        if HAS_OTHER_VIEWS and self.audio_app and hasattr(self.current_view, 'update_meetings'):
            self.current_view.update_meetings(self.audio_app.chat_history)

    def _show_journal_content(self):
        """Show the Journal tab content"""
        if HAS_OTHER_VIEWS and "journal" not in self.tab_views:
            entries = self.audio_app.get_journal_entries() if self.audio_app else []
            self.tab_views["journal"] = JournalView(
                self.content_container,
                entries=entries,
                on_create_entry=self._create_journal_entry,
                on_optimize_entry=self._optimize_journal_entry
            )
        elif "journal" not in self.tab_views:
            self.tab_views["journal"] = PlaceholderContent(
                self.content_container,
                title="Journal",
                message="Your personal journal entries"
            )

        self.current_view = self.tab_views["journal"]
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def _show_settings_content(self):
        """Show the Settings tab content"""
        if HAS_OTHER_VIEWS and "settings" not in self.tab_views:
            self.tab_views["settings"] = SettingsView(
                self.content_container,
                on_theme_change=self._handle_theme_change,
                on_logout=self._handle_logout,
                backend=self.audio_app
            )
        elif "settings" not in self.tab_views:
            self.tab_views["settings"] = PlaceholderContent(
                self.content_container,
                title="Settings",
                message="Configure your preferences"
            )

        self.current_view = self.tab_views["settings"]
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def _clear_all(self):
        """Clear all widgets"""
        for widget in self.winfo_children():
            widget.destroy()
        self.tab_views = {}
        self.tab_buttons = {}

    # Event handlers
    def _on_login_success(self, session_data):
        """Handle successful login"""
        logger.info(f"Login successful: {session_data}")
        if self.audio_app:
            self.audio_app.login(
                provider=session_data.get("provider", "email"),
                email=session_data.get("email")
            )
        self._show_main_interface()

    def _handle_start_recording(self):
        """Handle start recording"""
        logger.info("Start recording")
        self.is_recording = True
        if self.audio_app:
            self.audio_app.start_recording()

    def _handle_stop_recording(self):
        """Handle stop recording"""
        # Guard: only stop if we were recording
        if not self.is_recording:
            logger.warning("_handle_stop_recording called but not recording - ignoring")
            return

        logger.info("Stop recording")
        self.is_recording = False
        if self.audio_app:
            self.audio_app.stop_recording()

    def _on_status_update(self, message):
        """Handle status updates"""
        logger.info(f"Status: {message}")

    def _on_transcript_update(self, text):
        """Handle live transcript updates"""
        def safe_update():
            try:
                if self.current_view and hasattr(self.current_view, 'update_transcript'):
                    self.current_view.update_transcript(text)
            except Exception as e:
                logger.error(f"Error updating transcript: {e}")

        self.after(0, safe_update)

    def _on_recording_result(self, result):
        """Handle recording completion"""
        logger.info("Recording result received")
        self.is_recording = False

        def safe_complete():
            try:
                if self.current_view and hasattr(self.current_view, 'on_recording_complete'):
                    self.current_view.on_recording_complete(result)
            except Exception as e:
                logger.error(f"Error in on_recording_complete: {e}")

        def safe_update_summary():
            try:
                if result and isinstance(result, dict):
                    # Get the transcript to display
                    transcript = result.get('transcript', '')
                    if transcript and self.current_view and hasattr(self.current_view, 'update_transcript'):
                        self.current_view.update_transcript(transcript)
            except Exception as e:
                logger.error(f"Error updating summary: {e}")

        def safe_refresh_meetings():
            try:
                if "history" in self.tab_views and hasattr(self.tab_views["history"], 'update_meetings'):
                    if self.audio_app:
                        self.tab_views["history"].update_meetings(self.audio_app.chat_history)
            except Exception as e:
                logger.error(f"Error refreshing meetings: {e}")

        self.after(0, safe_complete)
        self.after(100, safe_update_summary)  # Slight delay to ensure UI is ready
        self.after(200, safe_refresh_meetings)

    def _on_level_update(self, level):
        """Handle audio level updates"""
        def safe_level():
            try:
                if self.current_view and hasattr(self.current_view, 'update_level'):
                    self.current_view.update_level(level)
            except Exception as e:
                pass  # Level updates are frequent, don't spam logs

        self.after(0, safe_level)

    def _analyze_meeting(self, meeting_id):
        """Analyze a meeting with AI"""
        logger.info(f"Analyzing meeting: {meeting_id}")

    def _open_meeting_detail(self, meeting):
        """Open meeting detail"""
        logger.info(f"Opening meeting: {meeting.get('id')}")

    def _create_journal_entry(self, text):
        """Create journal entry"""
        if self.audio_app:
            self.audio_app.create_journal_entry(text)

    def _optimize_journal_entry(self, entry_id):
        """Optimize journal entry"""
        if self.audio_app:
            self.audio_app.optimize_journal_entry(entry_id)

    def _handle_theme_change(self, theme):
        """Handle theme change"""
        logger.info(f"Theme changed to: {theme}")

    def _handle_logout(self):
        """Handle logout"""
        if self.audio_app:
            self.audio_app.logout()
        self._show_login_view()


class RecordContent(ctk.CTkFrame):
    """Record tab content - matching Figma design"""

    def __init__(self, parent, on_start_recording=None, on_stop_recording=None):
        super().__init__(parent, fg_color="transparent")

        self.on_start_recording = on_start_recording
        self.on_stop_recording = on_stop_recording
        self.is_recording = False
        self.speakers = []

        self._build_ui()

    def _build_ui(self):
        """Build the record content UI"""
        # Card container
        card = ctk.CTkFrame(
            self,
            fg_color=FIGMA_COLORS["card"],
            corner_radius=14,
            border_width=1,
            border_color=FIGMA_COLORS["card_border"]
        )
        card.pack(fill="both", expand=True)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=25, pady=25)

        # Record Meeting heading
        ctk.CTkLabel(
            content,
            text="Record Meeting",
            font=FIGMA_FONTS["heading_md"],
            text_color=FIGMA_COLORS["text_primary"],
            anchor="w"
        ).pack(fill="x", pady=(0, 16))

        # Start Recording button
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

        # Form fields
        form = ctk.CTkFrame(content, fg_color="transparent")
        form.pack(fill="x")

        # Meeting Title
        ctk.CTkLabel(
            form,
            text="Meeting Title (optional)",
            font=FIGMA_FONTS["body_medium"],
            text_color=FIGMA_COLORS["text_primary"],
            anchor="w"
        ).pack(fill="x", pady=(0, 8))

        self.title_entry = ctk.CTkEntry(
            form,
            placeholder_text="Enter meeting title",
            fg_color=FIGMA_COLORS["input_bg"],
            border_width=0,
            text_color=FIGMA_COLORS["text_primary"],
            placeholder_text_color=FIGMA_COLORS["text_placeholder"],
            font=FIGMA_FONTS["body_regular"],
            height=36,
            corner_radius=8
        )
        self.title_entry.pack(fill="x", pady=(0, 16))

        # Speakers
        ctk.CTkLabel(
            form,
            text="Speakers (optional)",
            font=FIGMA_FONTS["body_medium"],
            text_color=FIGMA_COLORS["text_primary"],
            anchor="w"
        ).pack(fill="x", pady=(0, 8))

        speaker_row = ctk.CTkFrame(form, fg_color="transparent")
        speaker_row.pack(fill="x", pady=(0, 16))

        self.speaker_entry = ctk.CTkEntry(
            speaker_row,
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

        self.add_speaker_btn = ctk.CTkButton(
            speaker_row,
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
        self.add_speaker_btn.pack(side="right")

        self.speakers_container = ctk.CTkFrame(form, fg_color="transparent")
        self.speakers_container.pack(fill="x", pady=(0, 16))

        # Transcript section
        ctk.CTkLabel(
            content,
            text="Transcript",
            font=FIGMA_FONTS["body_medium"],
            text_color=FIGMA_COLORS["text_primary"],
            anchor="w"
        ).pack(fill="x", pady=(16, 8))

        self.transcript_box = ctk.CTkTextbox(
            content,
            fg_color=FIGMA_COLORS["input_bg"],
            text_color=FIGMA_COLORS["text_primary"],
            font=FIGMA_FONTS["body_regular"],
            corner_radius=8,
            border_width=0,
            height=300
        )
        self.transcript_box.pack(fill="both", expand=True)
        self.transcript_box.configure(state="disabled")

    def _toggle_recording(self):
        if not self.is_recording:
            self._start_recording()
        else:
            self._stop_recording()

    def _start_recording(self):
        self.is_recording = True
        self.record_btn.configure(
            text="\u23F9  Stop Recording",
            fg_color="#dc2626",
            hover_color="#b91c1c"
        )
        self.title_entry.configure(state="disabled")
        self.speaker_entry.configure(state="disabled")
        self.add_speaker_btn.configure(state="disabled")

        # Clear transcript and show recording indicator
        self.transcript_box.configure(state="normal")
        self.transcript_box.delete("1.0", "end")
        self.transcript_box.insert("1.0", "Recording... Live transcript will appear here.")
        self.transcript_box.configure(state="disabled")

        if self.on_start_recording:
            self.on_start_recording()

    def _stop_recording(self):
        self.is_recording = False
        self.record_btn.configure(
            text=f"{TAB_ICONS['record']}  Start Recording",
            fg_color=FIGMA_COLORS["primary_btn"],
            hover_color=FIGMA_COLORS["primary_btn_hover"]
        )
        self.title_entry.configure(state="normal")
        self.speaker_entry.configure(state="normal")
        self.add_speaker_btn.configure(state="normal")

        if self.on_stop_recording:
            self.on_stop_recording()

    def _add_speaker(self):
        name = self.speaker_entry.get().strip()
        if name and name not in self.speakers:
            self.speakers.append(name)
            self.speaker_entry.delete(0, "end")
            self._refresh_speakers()

    def _refresh_speakers(self):
        for w in self.speakers_container.winfo_children():
            w.destroy()
        for name in self.speakers:
            badge = ctk.CTkFrame(self.speakers_container, fg_color=FIGMA_COLORS["input_bg"], corner_radius=12)
            badge.pack(side="left", padx=(0, 8), pady=4)
            ctk.CTkLabel(badge, text=name, font=FIGMA_FONTS["body_regular"]).pack(side="left", padx=(12, 4), pady=4)
            ctk.CTkButton(
                badge, text="\u2715", width=20, height=20,
                fg_color="transparent", hover_color="#e5e7eb",
                font=("Inter", 12), corner_radius=10,
                command=lambda n=name: self._remove_speaker(n)
            ).pack(side="right", padx=(0, 4), pady=4)

    def _remove_speaker(self, name):
        if name in self.speakers:
            self.speakers.remove(name)
            self._refresh_speakers()

    def update_transcript(self, text):
        """Update transcript display"""
        self.transcript_box.configure(state="normal")
        self.transcript_box.delete("1.0", "end")
        self.transcript_box.insert("1.0", text)
        self.transcript_box.see("end")
        self.transcript_box.configure(state="disabled")

    def update_level(self, level):
        """Update audio level (could add visual indicator)"""
        pass

    def on_recording_complete(self, result):
        """Handle recording completion - only update UI, don't trigger callback"""
        # Only update UI state, do NOT call on_stop_recording callback
        # (that would trigger another stop_recording() on the backend causing infinite loop)
        self.is_recording = False
        self.record_btn.configure(
            text=f"{TAB_ICONS['record']}  Start Recording",
            fg_color=FIGMA_COLORS["primary_btn"],
            hover_color=FIGMA_COLORS["primary_btn_hover"]
        )
        self.title_entry.configure(state="normal")
        self.speaker_entry.configure(state="normal")
        self.add_speaker_btn.configure(state="normal")


class PlaceholderContent(ctk.CTkFrame):
    """Placeholder content for tabs without existing views"""

    def __init__(self, parent, title="", message=""):
        super().__init__(parent, fg_color="transparent")

        card = ctk.CTkFrame(
            self,
            fg_color=FIGMA_COLORS["card"],
            corner_radius=14,
            border_width=1,
            border_color=FIGMA_COLORS["card_border"]
        )
        card.pack(fill="both", expand=True)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=25, pady=25)

        ctk.CTkLabel(
            content,
            text=title,
            font=FIGMA_FONTS["heading_md"],
            text_color=FIGMA_COLORS["text_primary"]
        ).pack(pady=(50, 16))

        ctk.CTkLabel(
            content,
            text=message,
            font=FIGMA_FONTS["body"],
            text_color=FIGMA_COLORS["text_secondary"]
        ).pack()


if __name__ == "__main__":
    app = FigmaApp()
    app.mainloop()
