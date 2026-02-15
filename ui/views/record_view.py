"""Recording interface view - matches Figma design"""
import customtkinter as ctk
from ui.styles import ThemeManager, FONTS, RADIUS, SPACING
from ui.components.buttons import PrimaryButton, DestructiveButton, OutlineButton
from ui.components.inputs import StyledEntry, StyledLabel, StyledTextbox
from ui.components.badges import SpeakerBadge, StatusBadge
from ui.components.cards import Card


class RecordView(ctk.CTkFrame):
    """Recording interface with mic button, title, speakers, and transcript"""

    def __init__(self, parent, on_save_recording=None, on_start_recording=None, on_stop_recording=None):
        colors = ThemeManager.get_colors()
        super().__init__(parent, fg_color=colors["bg"], corner_radius=0)

        self.on_save_recording = on_save_recording
        self.on_start_recording = on_start_recording
        self.on_stop_recording = on_stop_recording
        self.is_recording = False
        self.timer_seconds = 0
        self.timer_running = False
        self.speakers = []
        self.transcript = ""
        self.mic_error = None

        self._build_ui()

    def _build_ui(self):
        """Build the recording interface"""
        colors = ThemeManager.get_colors()

        # Main card container
        self.card = ctk.CTkFrame(
            self,
            fg_color=colors["card"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=colors["border"]
        )
        self.card.pack(fill="both", expand=True, padx=SPACING["xl"], pady=SPACING["xl"])

        # Content area
        content = ctk.CTkFrame(self.card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=SPACING["xl"], pady=SPACING["xl"])

        # Header
        StyledLabel(
            content,
            text="Record Meeting",
            variant="heading"
        ).pack(anchor="w", pady=(0, SPACING["lg"]))

        # Recording controls row
        controls_frame = ctk.CTkFrame(content, fg_color="transparent")
        controls_frame.pack(fill="x", pady=(0, SPACING["lg"]))

        # Record/Stop button
        self.record_btn = PrimaryButton(
            controls_frame,
            text="  Start Recording",
            command=self._toggle_recording,
            height=48,
            width=180,
        )
        self.record_btn.pack(side="left")

        # Recording indicator (timer + status)
        self.recording_indicator = ctk.CTkFrame(controls_frame, fg_color="transparent")

        # Recording dot and timer
        self.recording_dot = ctk.CTkFrame(
            self.recording_indicator,
            width=12,
            height=12,
            fg_color=colors["destructive"],
            corner_radius=RADIUS["full"]
        )
        self.recording_dot.pack(side="left", padx=(SPACING["md"], SPACING["xs"]))

        self.timer_label = ctk.CTkLabel(
            self.recording_indicator,
            text="0:00",
            font=FONTS["body_medium"],
            text_color=colors["text_primary"]
        )
        self.timer_label.pack(side="left")

        # Form fields
        form_frame = ctk.CTkFrame(content, fg_color="transparent")
        form_frame.pack(fill="x", pady=SPACING["md"])

        # Meeting title
        StyledLabel(
            form_frame,
            text="Meeting Title (optional)",
            variant="label"
        ).pack(anchor="w", pady=(0, SPACING["xs"]))

        self.title_entry = StyledEntry(
            form_frame,
            placeholder="Enter meeting title"
        )
        self.title_entry.pack(fill="x", pady=(0, SPACING["md"]))

        # Speakers
        StyledLabel(
            form_frame,
            text="Speakers (optional)",
            variant="label"
        ).pack(anchor="w", pady=(0, SPACING["xs"]))

        # Speaker input row
        speaker_input_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        speaker_input_frame.pack(fill="x", pady=(0, SPACING["sm"]))

        self.speaker_entry = StyledEntry(
            speaker_input_frame,
            placeholder="Add speaker name"
        )
        self.speaker_entry.pack(side="left", fill="x", expand=True, padx=(0, SPACING["sm"]))
        self.speaker_entry.bind("<Return>", lambda e: self._add_speaker())

        add_speaker_btn = OutlineButton(
            speaker_input_frame,
            text="Add",
            command=self._add_speaker,
            width=60,
            height=40
        )
        add_speaker_btn.pack(side="right")

        # Speaker badges container
        self.speakers_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        self.speakers_frame.pack(fill="x", pady=(0, SPACING["md"]))

        # Transcript section
        self.transcript_section = ctk.CTkFrame(content, fg_color="transparent")

        StyledLabel(
            self.transcript_section,
            text="Transcript",
            variant="label"
        ).pack(anchor="w", pady=(0, SPACING["xs"]))

        self.transcript_box = StyledTextbox(
            self.transcript_section,
            height=200
        )
        self.transcript_box.pack(fill="both", expand=True)
        self.transcript_box.configure(state="disabled")

        # Save button (shown after recording stops)
        self.save_btn = PrimaryButton(
            self.transcript_section,
            text="  Save Meeting",
            command=self._save_recording,
            height=44,
        )

        # Error banner
        self.error_frame = ctk.CTkFrame(
            content,
            fg_color=colors["warning_light"],
            corner_radius=RADIUS["md"],
            border_width=1,
            border_color=colors["warning"]
        )

        self.error_label = ctk.CTkLabel(
            self.error_frame,
            text="",
            font=FONTS["body_sm"],
            text_color=colors["text_primary"],
            wraplength=600
        )
        self.error_label.pack(padx=SPACING["md"], pady=SPACING["md"])

        # Audio level meter
        self.level_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.level_frame.pack(fill="x", pady=SPACING["md"])

        StyledLabel(
            self.level_frame,
            text="Audio Level",
            variant="caption"
        ).pack(anchor="w", pady=(0, SPACING["xs"]))

        self.level_bar = ctk.CTkProgressBar(
            self.level_frame,
            height=8,
            progress_color=colors["accent"],
            fg_color=colors["border"]
        )
        self.level_bar.pack(fill="x")
        self.level_bar.set(0)

    def _toggle_recording(self):
        """Toggle recording state"""
        if not self.is_recording:
            self._start_recording()
        else:
            self._stop_recording()

    def _start_recording(self):
        """Start recording"""
        colors = ThemeManager.get_colors()
        self.is_recording = True

        # Update button
        self.record_btn.configure(
            text="  Stop Recording",
            fg_color=colors["destructive"],
            hover_color=colors["destructive_hover"]
        )

        # Show recording indicator
        self.recording_indicator.pack(side="left")

        # Disable inputs during recording
        self.title_entry.configure(state="disabled")
        self.speaker_entry.configure(state="disabled")

        # Show transcript section
        self.transcript_section.pack(fill="both", expand=True, pady=SPACING["md"])

        # Start timer
        self.timer_seconds = 0
        self.timer_running = True
        self._tick()

        # Start pulse animation
        self._pulse_dot()

        # Clear transcript
        self.transcript_box.configure(state="normal")
        self.transcript_box.delete("1.0", "end")
        self.transcript_box.configure(state="disabled")

        # Hide error if visible
        self.error_frame.pack_forget()

        # Notify parent to start backend recording
        if self.on_start_recording:
            self.on_start_recording()

    def _stop_recording(self):
        """Stop recording"""
        colors = ThemeManager.get_colors()
        self.is_recording = False
        self.timer_running = False

        # Update button
        self.record_btn.configure(
            text="  Start Recording",
            fg_color=colors["primary"],
            hover_color=colors["primary_hover"]
        )

        # Hide recording indicator
        self.recording_indicator.pack_forget()

        # Enable inputs
        self.title_entry.configure(state="normal")
        self.speaker_entry.configure(state="normal")

        # Show save button if there's a transcript
        if self.transcript:
            self.save_btn.pack(anchor="e", pady=(SPACING["md"], 0))

        # Notify parent to stop backend recording
        if self.on_stop_recording:
            self.on_stop_recording()

    def _tick(self):
        """Update timer every second"""
        if not self.timer_running:
            return

        self.timer_seconds += 1
        minutes = self.timer_seconds // 60
        seconds = self.timer_seconds % 60
        self.timer_label.configure(text=f"{minutes}:{seconds:02d}")

        self.after(1000, self._tick)

    def _pulse_dot(self):
        """Animate the recording dot"""
        if not self.is_recording:
            return

        colors = ThemeManager.get_colors()
        current = self.recording_dot.cget("fg_color")

        if current == colors["destructive"]:
            self.recording_dot.configure(fg_color=colors["recording_pulse"])
        else:
            self.recording_dot.configure(fg_color=colors["destructive"])

        self.after(500, self._pulse_dot)

    def _add_speaker(self):
        """Add a speaker to the list"""
        name = self.speaker_entry.get().strip()
        if not name or name in self.speakers:
            return

        self.speakers.append(name)
        self.speaker_entry.delete(0, "end")
        self._refresh_speakers()

    def _remove_speaker(self, name):
        """Remove a speaker from the list"""
        if name in self.speakers:
            self.speakers.remove(name)
            self._refresh_speakers()

    def _refresh_speakers(self):
        """Refresh the speaker badges display"""
        # Clear existing badges
        for widget in self.speakers_frame.winfo_children():
            widget.destroy()

        # Add badges for each speaker
        for name in self.speakers:
            badge = SpeakerBadge(
                self.speakers_frame,
                name=name,
                on_remove=None if self.is_recording else self._remove_speaker
            )
            badge.pack(side="left", padx=(0, SPACING["xs"]), pady=SPACING["xs"])

    def _save_recording(self):
        """Save the recording"""
        if not self.transcript.strip():
            self.show_error("Please ensure there is a transcript to save.")
            return

        data = {
            "title": self.title_entry.get().strip() or "Untitled Meeting",
            "speakers": self.speakers.copy(),
            "transcript": self.transcript,
            "duration": self.timer_seconds,
        }

        if self.on_save_recording:
            self.on_save_recording(data)

        # Reset form
        self.reset()

    def reset(self):
        """Reset the form to initial state"""
        colors = ThemeManager.get_colors()

        self.is_recording = False
        self.timer_running = False
        self.timer_seconds = 0
        self.speakers = []
        self.transcript = ""

        # Reset UI
        self.title_entry.delete(0, "end")
        self.title_entry.configure(state="normal")
        self.speaker_entry.delete(0, "end")
        self.speaker_entry.configure(state="normal")

        self.timer_label.configure(text="0:00")
        self.recording_indicator.pack_forget()

        self.transcript_box.configure(state="normal")
        self.transcript_box.delete("1.0", "end")
        self.transcript_box.configure(state="disabled")

        self.transcript_section.pack_forget()
        self.save_btn.pack_forget()
        self.error_frame.pack_forget()

        self._refresh_speakers()

        self.record_btn.configure(
            text="  Start Recording",
            fg_color=colors["primary"],
            hover_color=colors["primary_hover"]
        )

        self.level_bar.set(0)

    def update_transcript(self, text):
        """Update the live transcript"""
        self.transcript = text
        self.transcript_box.configure(state="normal")
        self.transcript_box.delete("1.0", "end")
        self.transcript_box.insert("1.0", text)
        self.transcript_box.see("end")
        self.transcript_box.configure(state="disabled")

    def update_level(self, level):
        """Update the audio level meter"""
        # Boost visually since speech is often low RMS
        self.level_bar.set(min(level * 5, 1.0))

    def show_error(self, message):
        """Show an error message"""
        colors = ThemeManager.get_colors()
        self.error_label.configure(text=f"Error: {message}")
        self.error_frame.configure(
            fg_color=colors["warning_light"],
            border_color=colors["warning"]
        )
        self.error_frame.pack(fill="x", pady=SPACING["md"])

    def show_mic_error(self, message):
        """Show microphone error"""
        colors = ThemeManager.get_colors()
        self.mic_error = message
        self.error_label.configure(text=f"Microphone Error: {message}")
        self.error_frame.configure(
            fg_color="#fef2f2",  # Light red
            border_color=colors["destructive"]
        )
        self.error_frame.pack(fill="x", pady=SPACING["md"])

    def start_timer(self):
        """External method to start the timer"""
        self.timer_seconds = 0
        self.timer_running = True
        self._tick()

    def stop_timer(self):
        """External method to stop the timer"""
        self.timer_running = False
