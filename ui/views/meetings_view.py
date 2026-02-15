"""Meetings history view - matches Figma design"""
import customtkinter as ctk
from ui.styles import ThemeManager, FONTS, RADIUS, SPACING
from ui.components.buttons import PrimaryButton, OutlineButton
from ui.components.inputs import StyledLabel
from ui.components.badges import Badge, SpeakerBadge
from ui.components.cards import Card


class MeetingsView(ctk.CTkFrame):
    """View for displaying meeting history with expandable cards"""

    def __init__(self, parent, meetings=None, on_analyze=None, on_click=None):
        colors = ThemeManager.get_colors()
        super().__init__(parent, fg_color=colors["bg"], corner_radius=0)

        self.meetings = meetings or []
        self.on_analyze = on_analyze
        self.on_click = on_click
        self.expanded_id = None

        self._build_ui()

    def _build_ui(self):
        """Build the meetings view"""
        colors = ThemeManager.get_colors()

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=SPACING["xl"], pady=(SPACING["xl"], SPACING["md"]))

        StyledLabel(
            header,
            text="Meeting History",
            variant="heading"
        ).pack(anchor="w")

        StyledLabel(
            header,
            text="View all your recorded meetings with speakers, timestamps, and AI-generated next steps",
            variant="caption"
        ).pack(anchor="w", pady=(SPACING["xs"], 0))

        # Scrollable meetings list
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=SPACING["xl"], pady=(0, SPACING["xl"]))

        self._render_meetings()

    def _render_meetings(self):
        """Render the meetings list"""
        colors = ThemeManager.get_colors()

        # Clear existing
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not self.meetings:
            # Empty state
            empty_card = ctk.CTkFrame(
                self.scroll_frame,
                fg_color=colors["card"],
                corner_radius=RADIUS["lg"],
                border_width=1,
                border_color=colors["border"]
            )
            empty_card.pack(fill="x", pady=SPACING["md"])

            StyledLabel(
                empty_card,
                text="No meetings recorded yet",
                variant="caption"
            ).pack(pady=SPACING["xl"])

            return

        # Render each meeting
        for meeting in self.meetings:
            self._create_meeting_card(meeting)

    def _create_meeting_card(self, meeting):
        """Create a meeting card"""
        colors = ThemeManager.get_colors()
        meeting_id = meeting.get("id", id(meeting))
        is_expanded = self.expanded_id == meeting_id

        # Card container
        card = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=colors["card"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=colors["border"]
        )
        card.pack(fill="x", pady=SPACING["xs"])

        # Main content
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=SPACING["lg"], pady=SPACING["lg"])

        # Header row
        header_row = ctk.CTkFrame(content, fg_color="transparent")
        header_row.pack(fill="x")

        # Title
        title = meeting.get("title", "Untitled Meeting")
        StyledLabel(
            header_row,
            text=title,
            variant="subheading"
        ).pack(side="left", fill="x", expand=True)

        # Expand/Collapse button
        expand_btn = OutlineButton(
            header_row,
            text="Collapse" if is_expanded else "Expand",
            width=80,
            height=28,
            command=lambda: self._toggle_expand(meeting_id)
        )
        expand_btn.pack(side="right")

        # Metadata row
        meta_row = ctk.CTkFrame(content, fg_color="transparent")
        meta_row.pack(fill="x", pady=(SPACING["sm"], 0))

        # Date
        date = meeting.get("date", "")
        if date:
            date_frame = ctk.CTkFrame(meta_row, fg_color="transparent")
            date_frame.pack(side="left", padx=(0, SPACING["md"]))
            ctk.CTkLabel(
                date_frame,
                text=f"📅 {date}",
                font=FONTS["caption"],
                text_color=colors["text_secondary"]
            ).pack()

        # Duration
        duration = meeting.get("duration", "")
        if duration:
            if isinstance(duration, int):
                minutes = duration // 60
                seconds = duration % 60
                duration = f"{minutes}m {seconds}s"

            duration_frame = ctk.CTkFrame(meta_row, fg_color="transparent")
            duration_frame.pack(side="left", padx=(0, SPACING["md"]))
            ctk.CTkLabel(
                duration_frame,
                text=f"⏱ {duration}",
                font=FONTS["caption"],
                text_color=colors["text_secondary"]
            ).pack()

        # Speakers
        speakers = meeting.get("speakers", [])
        if speakers and isinstance(speakers, list):
            speakers_frame = ctk.CTkFrame(meta_row, fg_color="transparent")
            speakers_frame.pack(side="left")

            speakers_text = ", ".join(speakers[:3])
            if len(speakers) > 3:
                speakers_text += f" +{len(speakers) - 3}"

            ctk.CTkLabel(
                speakers_frame,
                text=f"👥 {speakers_text}",
                font=FONTS["caption"],
                text_color=colors["text_secondary"]
            ).pack()

        # Speaker badges (optional)
        if speakers:
            badges_row = ctk.CTkFrame(content, fg_color="transparent")
            badges_row.pack(fill="x", pady=(SPACING["sm"], 0))

            for speaker in speakers[:5]:
                badge = Badge(badges_row, text=speaker, variant="outline")
                badge.pack(side="left", padx=(0, SPACING["xs"]))

        # Expanded content
        if is_expanded:
            self._render_expanded_content(content, meeting)

    def _render_expanded_content(self, parent, meeting):
        """Render the expanded meeting details"""
        colors = ThemeManager.get_colors()

        # Divider
        ctk.CTkFrame(
            parent,
            height=1,
            fg_color=colors["border"]
        ).pack(fill="x", pady=SPACING["md"])

        # Transcript section
        StyledLabel(
            parent,
            text="Transcript",
            variant="body_medium"
        ).pack(anchor="w")

        transcript = meeting.get("transcript", "No transcript available.")
        transcript_box = ctk.CTkTextbox(
            parent,
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
        next_steps_header = ctk.CTkFrame(parent, fg_color="transparent")
        next_steps_header.pack(fill="x", pady=(SPACING["md"], SPACING["xs"]))

        StyledLabel(
            next_steps_header,
            text="Next Steps & Action Items",
            variant="body_medium"
        ).pack(side="left")

        # AI analyze button
        next_steps = meeting.get("next_steps", "") or meeting.get("executive_summary", "")
        if not next_steps and self.on_analyze:
            analyze_btn = OutlineButton(
                next_steps_header,
                text="✨ Analyze with AI",
                command=lambda: self._analyze_meeting(meeting),
                height=32,
            )
            analyze_btn.pack(side="right")

        # Next steps content
        if next_steps:
            next_steps_frame = ctk.CTkFrame(
                parent,
                fg_color=colors["accent_light"],
                corner_radius=RADIUS["md"]
            )
            next_steps_frame.pack(fill="x", pady=SPACING["xs"])

            ctk.CTkLabel(
                next_steps_frame,
                text=next_steps,
                font=FONTS["body_sm"],
                text_color=colors["text_primary"],
                wraplength=700,
                justify="left",
                anchor="w"
            ).pack(padx=SPACING["md"], pady=SPACING["md"], fill="x")
        else:
            StyledLabel(
                parent,
                text="Click 'Analyze with AI' to generate action items and next steps",
                variant="caption"
            ).pack(anchor="w", pady=SPACING["xs"])

        # Tasks section (if available)
        tasks = meeting.get("tasks", [])
        if tasks and isinstance(tasks, list):
            ctk.CTkFrame(
                parent,
                height=1,
                fg_color=colors["border"]
            ).pack(fill="x", pady=SPACING["md"])

            StyledLabel(
                parent,
                text="Tasks",
                variant="body_medium"
            ).pack(anchor="w", pady=(0, SPACING["sm"]))

            for task in tasks:
                if isinstance(task, dict):
                    task_frame = ctk.CTkFrame(parent, fg_color="transparent")
                    task_frame.pack(fill="x", pady=SPACING["xs"])

                    ctk.CTkCheckBox(
                        task_frame,
                        text="",
                        width=20,
                        height=20,
                        checkbox_width=18,
                        checkbox_height=18,
                        fg_color=colors["accent"],
                        border_color=colors["border"]
                    ).pack(side="left", padx=(0, SPACING["sm"]))

                    task_text = task.get("description", str(task))
                    ctk.CTkLabel(
                        task_frame,
                        text=task_text,
                        font=FONTS["body"],
                        text_color=colors["text_primary"],
                        anchor="w"
                    ).pack(side="left", fill="x", expand=True)

                    assignee = task.get("assignee", "")
                    if assignee and assignee != "Unknown":
                        Badge(
                            task_frame,
                            text=f"👤 {assignee}",
                            variant="outline"
                        ).pack(side="right")

    def _toggle_expand(self, meeting_id):
        """Toggle expanded state of a meeting card"""
        if self.expanded_id == meeting_id:
            self.expanded_id = None
        else:
            self.expanded_id = meeting_id

        self._render_meetings()

    def _analyze_meeting(self, meeting):
        """Trigger AI analysis for a meeting"""
        if self.on_analyze:
            meeting_id = meeting.get("id", id(meeting))
            self.on_analyze(meeting_id)

    def update_meetings(self, meetings):
        """Update the meetings list"""
        self.meetings = meetings
        self._render_meetings()

    def refresh(self):
        """Refresh the view"""
        self._render_meetings()


class TasksView(ctk.CTkFrame):
    """View for displaying all tasks from meetings"""

    def __init__(self, parent, meetings=None):
        colors = ThemeManager.get_colors()
        super().__init__(parent, fg_color=colors["bg"], corner_radius=0)

        self.meetings = meetings or []
        self._build_ui()

    def _build_ui(self):
        """Build the tasks view"""
        colors = ThemeManager.get_colors()

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=SPACING["xl"], pady=(SPACING["xl"], SPACING["md"]))

        StyledLabel(
            header,
            text="Tasks",
            variant="heading"
        ).pack(anchor="w")

        StyledLabel(
            header,
            text="All action items from your meetings",
            variant="caption"
        ).pack(anchor="w", pady=(SPACING["xs"], 0))

        # Scrollable tasks list
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=SPACING["xl"], pady=(0, SPACING["xl"]))

        self._render_tasks()

    def _render_tasks(self):
        """Render all tasks"""
        colors = ThemeManager.get_colors()

        # Clear existing
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        # Collect all tasks
        all_tasks = []
        for meeting in self.meetings:
            tasks = meeting.get("tasks", [])
            source_title = meeting.get("title", "Unknown Meeting")
            if isinstance(tasks, list):
                for task in tasks:
                    if isinstance(task, dict):
                        task["source"] = source_title
                        all_tasks.append(task)

        if not all_tasks:
            # Empty state
            empty_card = ctk.CTkFrame(
                self.scroll_frame,
                fg_color=colors["card"],
                corner_radius=RADIUS["lg"],
                border_width=1,
                border_color=colors["border"]
            )
            empty_card.pack(fill="x", pady=SPACING["md"])

            StyledLabel(
                empty_card,
                text="No tasks yet. Tasks will appear here after you analyze meetings.",
                variant="caption"
            ).pack(pady=SPACING["xl"])

            return

        # Render each task
        for task in all_tasks:
            self._create_task_row(task)

    def _create_task_row(self, task):
        """Create a task row"""
        colors = ThemeManager.get_colors()

        row = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=colors["card"],
            corner_radius=0,
            border_width=0
        )
        row.pack(fill="x", pady=1)

        content = ctk.CTkFrame(row, fg_color="transparent")
        content.pack(fill="x", padx=SPACING["lg"], pady=SPACING["md"])

        # Checkbox
        ctk.CTkCheckBox(
            content,
            text="",
            width=20,
            height=20,
            checkbox_width=18,
            checkbox_height=18,
            fg_color=colors["accent"],
            border_color=colors["border"]
        ).pack(side="left", padx=(0, SPACING["md"]))

        # Task info
        info_frame = ctk.CTkFrame(content, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)

        # Description
        ctk.CTkLabel(
            info_frame,
            text=task.get("description", ""),
            font=FONTS["body"],
            text_color=colors["text_primary"],
            anchor="w"
        ).pack(fill="x")

        # Source meeting
        ctk.CTkLabel(
            info_frame,
            text=task.get("source", ""),
            font=FONTS["caption"],
            text_color=colors["text_muted"],
            anchor="w"
        ).pack(fill="x")

        # Assignee badge
        assignee = task.get("assignee", "")
        if assignee and assignee != "Unknown":
            Badge(
                content,
                text=f"👤 {assignee}",
                variant="outline"
            ).pack(side="right", padx=SPACING["sm"])

    def update_meetings(self, meetings):
        """Update the meetings data"""
        self.meetings = meetings
        self._render_tasks()
