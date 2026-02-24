"""Modern GUI for Personal Assistant App - Redesigned with tab navigation"""
import customtkinter as ctk
import threading
import json
import os
import time
import logging

# Centralized logging is handled by app_logging.py (imported by backend).
# Do NOT configure the root logger here — it would duplicate handlers and
# set an overly verbose DEBUG level that could capture sensitive data.

from backend import EnhancedAudioApp
from ui.styles import ThemeManager, FONTS, RADIUS, SPACING
from ui.views.loading_view import LoadingView
from ui.views.login_view import LoginView
from ui.views.record_view import RecordView
from ui.views.meetings_view import MeetingsView, TasksView
from ui.views.journal_view import JournalView
from ui.views.settings_view import SettingsView
from ui.components.toast import ToastManager


class PersonalAssistantApp(ctk.CTk):
    """Main application with tab-based navigation and login flow"""

    def __init__(self):
        super().__init__()
        self.title("Personal Assistant")
        self.geometry("1200x800")
        self.minsize(900, 600)

        # Initialize theme
        colors = ThemeManager.get_colors()
        self.configure(fg_color=colors["bg"])

        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Initialize state
        self.audio_app = None
        self.current_tab = None
        self.views = {}
        self.is_recording = False

        # Show loading screen immediately
        self.loading_view = LoadingView(self)

        # Start background initialization
        threading.Thread(target=self._initialize_backend, daemon=True).start()

    def _initialize_backend(self):
        """Initialize backend in background thread"""
        try:
            self._update_loading_status("Initializing Audio Engine...")
            time.sleep(0.3)

            self.audio_app = EnhancedAudioApp(
                status_callback=self._update_status,
                result_callback=self._handle_recording_result,
                transcript_callback=self._update_transcript,
                level_callback=self._update_audio_level
            )

            self._update_loading_status("Loading AI Models...")
            time.sleep(0.8)

            self._update_loading_status("Ready!")
            time.sleep(0.3)

            # Check login status and show appropriate view
            self.after(0, self._check_login_status)

        except Exception as e:
            logging.error(f"Initialization failed: {e}")
            self._update_loading_status(f"Error: {e}")

    def _update_loading_status(self, text):
        """Update loading screen status"""
        self.after(0, lambda: self.loading_view.set_status(text))

    def _check_login_status(self):
        """Check if user is logged in and show appropriate view"""
        self.loading_view.destroy()

        if self.audio_app and self.audio_app.is_logged_in():
            self._show_main_interface()
        else:
            self._show_login()

    def _show_login(self):
        """Show login screen"""
        colors = ThemeManager.get_colors()
        self.configure(fg_color=colors["bg"])

        # Clear any existing views
        for widget in self.winfo_children():
            widget.destroy()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.login_view = LoginView(
            self,
            on_login_success=self._handle_login_success
        )
        self.login_view.grid(row=0, column=0, sticky="nsew")

    def _handle_login_success(self, session_data):
        """Handle successful login"""
        if self.audio_app:
            self.audio_app.login(
                provider=session_data.get("provider", "email"),
                email=session_data.get("email")
            )

        # Destroy login view and show main interface
        if hasattr(self, 'login_view'):
            self.login_view.destroy()

        self._show_main_interface()

    def _show_main_interface(self):
        """Show main application interface with tab navigation - matches Figma layout"""
        colors = ThemeManager.get_colors()
        self.configure(fg_color=colors["bg"])

        # Clear any existing views
        for widget in self.winfo_children():
            widget.destroy()

        # Configure grid for main layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)  # Single row, content handles everything

        # Main content wrapper (scrollable)
        main_wrapper = ctk.CTkFrame(self, fg_color=colors["bg"], corner_radius=0)
        main_wrapper.grid(row=0, column=0, sticky="nsew")
        main_wrapper.grid_columnconfigure(0, weight=1)
        main_wrapper.grid_rowconfigure(2, weight=1)

        # Create header section (title + subtitle)
        self._create_header_section(main_wrapper)

        # Create tab bar (centered pill tabs)
        self._create_tab_bar(main_wrapper)

        # Create main content container
        self.content_container = ctk.CTkFrame(
            main_wrapper,
            fg_color=colors["bg"],
            corner_radius=0
        )
        self.content_container.grid(row=2, column=0, sticky="nsew", padx=SPACING["xl"])
        self.content_container.grid_columnconfigure(0, weight=1)
        self.content_container.grid_rowconfigure(0, weight=1)

        # Initialize views
        self._create_views()

        # Show default tab
        self._show_tab("record")

        # Initialize toast manager
        ToastManager.initialize(self)

    def _create_header_section(self, parent):
        """Create header with title and subtitle - matches Figma design"""
        colors = ThemeManager.get_colors()

        # Header frame
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=SPACING["xl"], pady=(SPACING["xl"], SPACING["md"]))

        # Title
        ctk.CTkLabel(
            header,
            text="Personal Assistant",
            font=FONTS["heading"],
            text_color=colors["text_primary"]
        ).pack(anchor="w")

        # Subtitle
        ctk.CTkLabel(
            header,
            text="Record meetings, track your journey, and get AI-powered insights",
            font=FONTS["body"],
            text_color=colors["text_secondary"]
        ).pack(anchor="w", pady=(SPACING["xs"], 0))

    def _create_tab_bar(self, parent):
        """Create pill-shaped tab bar - matches Figma TabsList design"""
        colors = ThemeManager.get_colors()

        # Tab bar container (full width for centering)
        tab_bar_wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        tab_bar_wrapper.grid(row=1, column=0, sticky="ew", padx=SPACING["xl"], pady=(0, SPACING["lg"]))

        # Pill-shaped tab container - matches Figma TabsList
        tabs_container = ctk.CTkFrame(
            tab_bar_wrapper,
            fg_color=colors["secondary"],  # bg-muted equivalent
            corner_radius=RADIUS["xl"],
            height=44
        )
        tabs_container.pack(fill="x")

        # Inner frame for tabs with padding
        tabs_inner = ctk.CTkFrame(tabs_container, fg_color="transparent")
        tabs_inner.pack(fill="both", expand=True, padx=3, pady=3)

        # Configure equal columns for tabs
        tabs_inner.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="tabs")

        self.tab_buttons = {}
        self.tab_labels = {}

        # Tab data: (icon, text, key, column)
        tabs = [
            ("🎙", "Record", "record", 0),
            ("📋", "Meetings", "meetings", 1),
            ("📖", "Journal", "journal", 2),
            ("⚙", "Settings", "settings", 3)
        ]

        for icon, text, key, col in tabs:
            # Each tab is a button that shows icon always, text only when active
            btn = ctk.CTkButton(
                tabs_inner,
                text=icon,  # Will update with text when active
                fg_color="transparent",
                hover_color=colors["card"],
                text_color=colors["text_secondary"],
                font=FONTS["body_medium"],
                corner_radius=RADIUS["lg"],
                height=38,
                command=lambda k=key: self._show_tab(k)
            )
            btn.grid(row=0, column=col, sticky="ew", padx=1)
            self.tab_buttons[key] = btn
            self.tab_labels[key] = (icon, text)

    def _create_views(self):
        """Create all tab views"""
        # Record view
        self.views["record"] = RecordView(
            self.content_container,
            on_save_recording=self._save_meeting,
            on_start_recording=self._start_backend_recording,
            on_stop_recording=self._stop_backend_recording
        )

        # Meetings view
        self.views["meetings"] = MeetingsView(
            self.content_container,
            meetings=self.audio_app.chat_history if self.audio_app else [],
            on_analyze=self._analyze_meeting,
            on_click=self._open_meeting_detail
        )

        # Journal view
        self.views["journal"] = JournalView(
            self.content_container,
            entries=self.audio_app.get_journal_entries() if self.audio_app else [],
            on_create_entry=self._create_journal_entry,
            on_optimize_entry=self._optimize_journal_entry
        )

        # Settings view
        self.views["settings"] = SettingsView(
            self.content_container,
            on_theme_change=self._handle_theme_change,
            on_logout=self._handle_logout,
            backend=self.audio_app
        )

    def _show_tab(self, tab_name):
        """Show the specified tab with slider-style tab navigation"""
        # Warn if recording in progress and trying to leave
        if self.is_recording and tab_name != "record":
            ToastManager.warning("Recording in progress. Stop recording before switching tabs.")
            return

        colors = ThemeManager.get_colors()

        # Update tab button styles - active gets card bg and shows icon + text
        for key, btn in self.tab_buttons.items():
            icon, text = self.tab_labels[key]
            if key == tab_name:
                # Active tab: card/white background, icon + text (slider effect)
                btn.configure(
                    text=f"{icon}  {text}",
                    fg_color=colors["card"],
                    text_color=colors["text_primary"]
                )
            else:
                # Inactive tab: transparent background, icon only
                btn.configure(
                    text=icon,
                    fg_color="transparent",
                    text_color=colors["text_secondary"]
                )

        # Hide all views and show selected
        for key, view in self.views.items():
            view.grid_forget()

        if tab_name in self.views:
            self.views[tab_name].grid(row=0, column=0, sticky="nsew")
            self.current_tab = tab_name

            # Refresh view data when shown
            if tab_name == "meetings" and self.audio_app:
                self.views["meetings"].update_meetings(self.audio_app.chat_history)
            elif tab_name == "journal" and self.audio_app:
                self.views["journal"].update_entries(self.audio_app.get_journal_entries())

    def _start_backend_recording(self):
        """Start the backend audio recording"""
        if self.audio_app and not self.is_recording:
            self.is_recording = True
            self.audio_app.start_recording()
            ToastManager.info("Recording started...")

    def _stop_backend_recording(self):
        """Stop the backend audio recording"""
        if self.audio_app and self.is_recording:
            self.is_recording = False
            self.audio_app.stop_recording()

    def _save_meeting(self, data):
        """Save a completed meeting recording"""
        if self.audio_app:
            # Add to history
            meeting = {
                "id": str(time.time()),
                "title": data.get("title", "Untitled Meeting"),
                "date": time.strftime("%b %d, %Y at %I:%M %p"),
                "speakers": data.get("speakers", []),
                "transcript": data.get("transcript", ""),
                "duration": data.get("duration", 0),
                "next_steps": "",
                "tasks": []
            }

            self.audio_app.chat_history.insert(0, meeting)
            self.audio_app.save_history()

            ToastManager.success("Meeting saved successfully!")

            # Refresh meetings view
            if "meetings" in self.views:
                self.views["meetings"].update_meetings(self.audio_app.chat_history)

    def _analyze_meeting(self, meeting_id):
        """Analyze a meeting with AI"""
        if not self.audio_app:
            return

        # Find the meeting
        meeting = None
        for m in self.audio_app.chat_history:
            if str(m.get("id")) == str(meeting_id):
                meeting = m
                break

        if not meeting:
            ToastManager.error("Meeting not found")
            return

        ToastManager.info("Analyzing meeting with AI...")

        # Run analysis in background
        def analyze():
            try:
                transcript = meeting.get("transcript", "")
                if transcript:
                    summary = self.audio_app.generate_summary(transcript)
                    if summary and isinstance(summary, dict):
                        meeting["next_steps"] = summary.get("executive_summary", "")
                        meeting["tasks"] = summary.get("tasks", [])
                        self.audio_app.save_history()

                        self.after(0, lambda: self._on_analysis_complete(meeting_id))
            except Exception as e:
                logging.error(f"Analysis failed: {e}")
                self.after(0, lambda: ToastManager.error(f"Analysis failed: {str(e)}"))

        threading.Thread(target=analyze, daemon=True).start()

    def _on_analysis_complete(self, meeting_id):
        """Handle completed analysis"""
        ToastManager.success("AI analysis complete!")
        if "meetings" in self.views:
            self.views["meetings"].update_meetings(self.audio_app.chat_history)
            self.views["meetings"].refresh()

    def _open_meeting_detail(self, meeting):
        """Open meeting detail view"""
        # For now, just expand the meeting in the meetings view
        pass

    def _create_journal_entry(self, entry_text):
        """Create a new journal entry"""
        if self.audio_app:
            entry = self.audio_app.create_journal_entry(entry_text)
            if "journal" in self.views:
                self.views["journal"].add_entry(entry)
            ToastManager.success("Journal entry saved!")

    def _optimize_journal_entry(self, entry_id):
        """Get AI suggestions for a journal entry"""
        if not self.audio_app:
            return

        ToastManager.info("Getting AI suggestions...")

        def optimize():
            try:
                suggestions = self.audio_app.optimize_journal_entry(entry_id)
                if suggestions:
                    # Find and update the entry
                    entries = self.audio_app.get_journal_entries()
                    for entry in entries:
                        if entry.get("id") == entry_id:
                            self.after(0, lambda: self._on_journal_optimized(entry_id, entries))
                            break
            except Exception as e:
                logging.error(f"Journal optimization failed: {e}")
                self.after(0, lambda: ToastManager.error("Failed to get AI suggestions"))

        threading.Thread(target=optimize, daemon=True).start()

    def _on_journal_optimized(self, entry_id, entries):
        """Handle completed journal optimization"""
        ToastManager.success("AI suggestions added!")
        if "journal" in self.views:
            self.views["journal"].update_entries(entries)

    def _handle_theme_change(self, theme):
        """Handle theme change from settings"""
        # Save theme preference
        if self.audio_app and hasattr(self.audio_app, 'config'):
            if not self.audio_app.config.has_section('Settings'):
                self.audio_app.config.add_section('Settings')
            self.audio_app.config.set('Settings', 'theme', theme)

            config_path = getattr(self.audio_app, 'config_path', 'audio_config.ini')
            with open(config_path, 'w') as f:
                self.audio_app.config.write(f)

        # Rebuild the entire interface with new theme
        self._show_main_interface()

    def _handle_logout(self):
        """Handle logout from settings"""
        if self.audio_app:
            self.audio_app.logout()

        self._show_login()

    # Audio callback handlers
    def _update_status(self, message):
        """Update status (called from backend thread)"""
        self.after(0, lambda: self._safe_update_status(message))

    def _safe_update_status(self, message):
        """Thread-safe status update"""
        logging.info(f"Status: {message}")

    def _update_transcript(self, text):
        """Update live transcript (called from backend thread)"""
        self.after(0, lambda: self._safe_update_transcript(text))

    def _safe_update_transcript(self, text):
        """Thread-safe transcript update"""
        if "record" in self.views:
            self.views["record"].update_transcript(text)

    def _update_audio_level(self, level):
        """Update audio level (called from backend thread)"""
        self.after(0, lambda: self._safe_update_level(level))

    def _safe_update_level(self, level):
        """Thread-safe level update"""
        if "record" in self.views:
            self.views["record"].update_level(level)

    def _handle_recording_result(self, result):
        """Handle recording result (called from backend thread)"""
        self.after(0, lambda: self._safe_handle_result(result))

    def _safe_handle_result(self, result):
        """Thread-safe result handling"""
        self.is_recording = False

        if "record" in self.views:
            self.views["record"].reset()

        # Update meetings list
        if self.audio_app and "meetings" in self.views:
            self.views["meetings"].update_meetings(self.audio_app.chat_history)

        ToastManager.success("Recording processed successfully!")

    def start_recording(self):
        """Start audio recording"""
        if self.audio_app and not self.is_recording:
            self.is_recording = True
            self.audio_app.start_recording()

            if "record" in self.views:
                self.views["record"]._start_recording()

    def stop_recording(self):
        """Stop audio recording"""
        if self.audio_app and self.is_recording:
            self.is_recording = False
            self.audio_app.stop_recording()

            if "record" in self.views:
                self.views["record"]._stop_recording()


# Legacy alias for compatibility
JamieCloneApp = PersonalAssistantApp


if __name__ == "__main__":
    app = PersonalAssistantApp()
    app.mainloop()
