"""Card components for displaying content"""
import customtkinter as ctk
from ui.styles import ThemeManager, FONTS, RADIUS, SPACING


class Card(ctk.CTkFrame):
    """Base card component with consistent styling"""

    def __init__(self, parent, **kwargs):
        colors = ThemeManager.get_colors()
        defaults = {
            "fg_color": colors["card"],
            "corner_radius": RADIUS["lg"],
            "border_width": 1,
            "border_color": colors["border"],
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)


class MeetingCard(ctk.CTkFrame):
    """Card for displaying a meeting in history list"""

    def __init__(self, parent, meeting_data: dict, on_click=None, on_expand=None, **kwargs):
        colors = ThemeManager.get_colors()
        super().__init__(
            parent,
            fg_color=colors["card"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=colors["border"],
            **kwargs
        )

        self.meeting_data = meeting_data
        self.on_click = on_click
        self.is_expanded = False

        # Main content frame
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(fill="x", padx=SPACING["lg"], pady=SPACING["lg"])

        # Header row (title + expand button)
        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.pack(fill="x")

        # Title
        title = meeting_data.get("title", "Untitled Meeting")
        self.title_label = ctk.CTkLabel(
            header,
            text=title,
            font=FONTS["subheading"],
            text_color=colors["text_primary"],
            anchor="w"
        )
        self.title_label.pack(side="left", fill="x", expand=True)

        # Expand button
        self.expand_btn = ctk.CTkButton(
            header,
            text="Expand",
            width=70,
            height=28,
            fg_color="transparent",
            hover_color=colors["secondary"],
            text_color=colors["text_secondary"],
            border_width=1,
            border_color=colors["border"],
            font=FONTS["caption"],
            corner_radius=RADIUS["sm"],
            command=self._toggle_expand
        )
        self.expand_btn.pack(side="right")

        # Metadata row
        meta_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        meta_frame.pack(fill="x", pady=(SPACING["sm"], 0))

        # Date
        date = meeting_data.get("date", "")
        if date:
            ctk.CTkLabel(
                meta_frame,
                text=f"📅 {date}",
                font=FONTS["caption"],
                text_color=colors["text_secondary"]
            ).pack(side="left", padx=(0, SPACING["md"]))

        # Duration
        duration = meeting_data.get("duration", "")
        if duration:
            ctk.CTkLabel(
                meta_frame,
                text=f"⏱ {duration}",
                font=FONTS["caption"],
                text_color=colors["text_secondary"]
            ).pack(side="left", padx=(0, SPACING["md"]))

        # Speakers
        speakers = meeting_data.get("speakers", [])
        if speakers and isinstance(speakers, list):
            speakers_text = ", ".join(speakers[:3])
            if len(speakers) > 3:
                speakers_text += f" +{len(speakers) - 3}"
            ctk.CTkLabel(
                meta_frame,
                text=f"👥 {speakers_text}",
                font=FONTS["caption"],
                text_color=colors["text_secondary"]
            ).pack(side="left")

        # Expanded content (hidden by default)
        self.expanded_frame = None

        # Make card clickable
        if on_click:
            self.bind("<Button-1>", lambda e: on_click(meeting_data))
            self.content.bind("<Button-1>", lambda e: on_click(meeting_data))

    def _toggle_expand(self):
        colors = ThemeManager.get_colors()
        self.is_expanded = not self.is_expanded

        if self.is_expanded:
            self.expand_btn.configure(text="Collapse")
            self._show_expanded_content()
        else:
            self.expand_btn.configure(text="Expand")
            if self.expanded_frame:
                self.expanded_frame.destroy()
                self.expanded_frame = None

    def _show_expanded_content(self):
        colors = ThemeManager.get_colors()

        self.expanded_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.expanded_frame.pack(fill="x", padx=SPACING["lg"], pady=(0, SPACING["lg"]))

        # Divider
        ctk.CTkFrame(
            self.expanded_frame,
            height=1,
            fg_color=colors["border"]
        ).pack(fill="x", pady=SPACING["md"])

        # Transcript section
        ctk.CTkLabel(
            self.expanded_frame,
            text="Transcript",
            font=FONTS["body_medium"],
            text_color=colors["text_primary"],
            anchor="w"
        ).pack(fill="x")

        transcript = self.meeting_data.get("transcript", "No transcript available.")
        transcript_box = ctk.CTkTextbox(
            self.expanded_frame,
            height=150,
            font=FONTS["body_sm"],
            fg_color=colors["bg"],
            text_color=colors["text_secondary"],
            corner_radius=RADIUS["md"],
            border_width=1,
            border_color=colors["border"]
        )
        transcript_box.pack(fill="x", pady=SPACING["sm"])
        transcript_box.insert("1.0", transcript)
        transcript_box.configure(state="disabled")

        # Next steps section
        next_steps = self.meeting_data.get("next_steps", "")
        ctk.CTkLabel(
            self.expanded_frame,
            text="Next Steps & Action Items",
            font=FONTS["body_medium"],
            text_color=colors["text_primary"],
            anchor="w"
        ).pack(fill="x", pady=(SPACING["md"], 0))

        if next_steps:
            steps_frame = ctk.CTkFrame(
                self.expanded_frame,
                fg_color=colors["accent_light"],
                corner_radius=RADIUS["md"]
            )
            steps_frame.pack(fill="x", pady=SPACING["sm"])
            ctk.CTkLabel(
                steps_frame,
                text=next_steps,
                font=FONTS["body_sm"],
                text_color=colors["text_primary"],
                anchor="w",
                wraplength=600,
                justify="left"
            ).pack(padx=SPACING["md"], pady=SPACING["md"])
        else:
            ctk.CTkLabel(
                self.expanded_frame,
                text="Click 'Analyze with AI' to generate action items",
                font=FONTS["caption"],
                text_color=colors["text_muted"],
                anchor="w"
            ).pack(fill="x", pady=SPACING["xs"])


class JournalCard(ctk.CTkFrame):
    """Card for displaying a journal entry"""

    def __init__(self, parent, entry_data: dict, on_optimize=None, **kwargs):
        colors = ThemeManager.get_colors()
        super().__init__(
            parent,
            fg_color=colors["card"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=colors["border"],
            **kwargs
        )

        self.entry_data = entry_data
        self.on_optimize = on_optimize

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="x", padx=SPACING["lg"], pady=SPACING["lg"])

        # Date header
        date = entry_data.get("date", "")
        ctk.CTkLabel(
            content,
            text=date,
            font=FONTS["caption"],
            text_color=colors["text_secondary"],
            anchor="w"
        ).pack(fill="x")

        # Entry text
        entry_text = entry_data.get("entry", "")
        ctk.CTkLabel(
            content,
            text=entry_text,
            font=FONTS["body"],
            text_color=colors["text_primary"],
            anchor="w",
            wraplength=600,
            justify="left"
        ).pack(fill="x", pady=SPACING["sm"])

        # AI suggestions (if available)
        ai_suggestions = entry_data.get("ai_suggestions", "")
        if ai_suggestions:
            suggestions_frame = ctk.CTkFrame(
                content,
                fg_color=colors["accent_light"],
                corner_radius=RADIUS["md"]
            )
            suggestions_frame.pack(fill="x", pady=SPACING["sm"])

            ctk.CTkLabel(
                suggestions_frame,
                text="✨ AI Suggestions",
                font=FONTS["caption"],
                text_color=colors["accent"],
                anchor="w"
            ).pack(fill="x", padx=SPACING["md"], pady=(SPACING["sm"], 0))

            ctk.CTkLabel(
                suggestions_frame,
                text=ai_suggestions,
                font=FONTS["body_sm"],
                text_color=colors["text_primary"],
                anchor="w",
                wraplength=580,
                justify="left"
            ).pack(fill="x", padx=SPACING["md"], pady=(0, SPACING["sm"]))
        elif on_optimize:
            # Show optimize button if no suggestions yet
            from ui.components.buttons import OutlineButton
            optimize_btn = OutlineButton(
                content,
                text="✨ Get AI Suggestions",
                command=lambda: on_optimize(entry_data.get("id"))
            )
            optimize_btn.pack(anchor="w", pady=SPACING["sm"])
