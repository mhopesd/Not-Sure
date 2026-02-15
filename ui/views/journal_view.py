"""Journal interface view - matches Figma design"""
import customtkinter as ctk
from ui.styles import ThemeManager, FONTS, RADIUS, SPACING
from ui.components.buttons import PrimaryButton, OutlineButton
from ui.components.inputs import StyledLabel, StyledTextbox
from ui.components.badges import Badge
from ui.components.cards import Card


class JournalView(ctk.CTkFrame):
    """Journal interface with entries and AI suggestions"""

    def __init__(self, parent, entries=None, on_create_entry=None, on_optimize_entry=None):
        colors = ThemeManager.get_colors()
        super().__init__(parent, fg_color=colors["bg"], corner_radius=0)

        self.entries = entries or []
        self.on_create_entry = on_create_entry
        self.on_optimize_entry = on_optimize_entry

        self._build_ui()

    def _build_ui(self):
        """Build the journal view"""
        colors = ThemeManager.get_colors()

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=SPACING["xl"], pady=(SPACING["xl"], SPACING["md"]))

        StyledLabel(
            header,
            text="Journal",
            variant="heading"
        ).pack(anchor="w")

        StyledLabel(
            header,
            text="Track your thoughts and get AI-powered insights",
            variant="caption"
        ).pack(anchor="w", pady=(SPACING["xs"], 0))

        # Main content area (scrollable)
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=SPACING["xl"], pady=(0, SPACING["xl"]))

        # New entry card
        self._create_new_entry_card()

        # Divider with label
        divider_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        divider_frame.pack(fill="x", pady=SPACING["lg"])

        ctk.CTkFrame(
            divider_frame,
            height=1,
            fg_color=colors["border"]
        ).pack(side="left", fill="x", expand=True, padx=(0, SPACING["md"]))

        StyledLabel(
            divider_frame,
            text="Past Entries",
            variant="caption"
        ).pack(side="left")

        ctk.CTkFrame(
            divider_frame,
            height=1,
            fg_color=colors["border"]
        ).pack(side="left", fill="x", expand=True, padx=(SPACING["md"], 0))

        # Entries list container
        self.entries_container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.entries_container.pack(fill="both", expand=True)

        self._render_entries()

    def _create_new_entry_card(self):
        """Create the new entry input card"""
        colors = ThemeManager.get_colors()

        card = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=colors["card"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=colors["border"]
        )
        card.pack(fill="x", pady=SPACING["xs"])

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=SPACING["lg"], pady=SPACING["lg"])

        StyledLabel(
            content,
            text="New Entry",
            variant="subheading"
        ).pack(anchor="w", pady=(0, SPACING["sm"]))

        # Text input
        self.entry_textbox = StyledTextbox(
            content,
            placeholder="What's on your mind today?",
            height=120
        )
        self.entry_textbox.pack(fill="x", pady=SPACING["xs"])

        # Save button
        self.save_btn = PrimaryButton(
            content,
            text="Save Entry",
            command=self._save_entry,
            height=40,
        )
        self.save_btn.pack(anchor="e", pady=(SPACING["sm"], 0))

    def _render_entries(self):
        """Render the journal entries list"""
        colors = ThemeManager.get_colors()

        # Clear existing
        for widget in self.entries_container.winfo_children():
            widget.destroy()

        if not self.entries:
            # Empty state
            empty_frame = ctk.CTkFrame(self.entries_container, fg_color="transparent")
            empty_frame.pack(pady=SPACING["xl"])

            StyledLabel(
                empty_frame,
                text="No journal entries yet. Start writing above!",
                variant="caption"
            ).pack()

            return

        # Render each entry
        for entry in self.entries:
            self._create_entry_card(entry)

    def _create_entry_card(self, entry):
        """Create a journal entry card"""
        colors = ThemeManager.get_colors()

        card = ctk.CTkFrame(
            self.entries_container,
            fg_color=colors["card"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=colors["border"]
        )
        card.pack(fill="x", pady=SPACING["xs"])

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=SPACING["lg"], pady=SPACING["lg"])

        # Date header
        date = entry.get("date", "")
        StyledLabel(
            content,
            text=date,
            variant="caption"
        ).pack(anchor="w")

        # Entry text
        entry_text = entry.get("entry", "")
        ctk.CTkLabel(
            content,
            text=entry_text,
            font=FONTS["body"],
            text_color=colors["text_primary"],
            wraplength=700,
            justify="left",
            anchor="w"
        ).pack(fill="x", pady=SPACING["sm"])

        # AI suggestions (if available)
        ai_suggestions = entry.get("ai_suggestions", "")
        if ai_suggestions:
            suggestions_frame = ctk.CTkFrame(
                content,
                fg_color=colors["accent_light"],
                corner_radius=RADIUS["md"]
            )
            suggestions_frame.pack(fill="x", pady=SPACING["sm"])

            header_row = ctk.CTkFrame(suggestions_frame, fg_color="transparent")
            header_row.pack(fill="x", padx=SPACING["md"], pady=(SPACING["sm"], 0))

            ctk.CTkLabel(
                header_row,
                text="✨ AI Suggestions",
                font=FONTS["caption"],
                text_color=colors["accent"]
            ).pack(side="left")

            ctk.CTkLabel(
                suggestions_frame,
                text=ai_suggestions,
                font=FONTS["body_sm"],
                text_color=colors["text_primary"],
                wraplength=680,
                justify="left",
                anchor="w"
            ).pack(fill="x", padx=SPACING["md"], pady=(SPACING["xs"], SPACING["sm"]))

        elif self.on_optimize_entry:
            # Show optimize button
            optimize_btn = OutlineButton(
                content,
                text="✨ Get AI Suggestions",
                command=lambda: self._optimize_entry(entry.get("id")),
                height=32,
            )
            optimize_btn.pack(anchor="w", pady=SPACING["xs"])

    def _save_entry(self):
        """Save a new journal entry"""
        entry_text = self.entry_textbox.get_value().strip()

        if not entry_text:
            from ui.components.toast import ToastManager
            ToastManager.warning("Please write something before saving.")
            return

        if self.on_create_entry:
            self.on_create_entry(entry_text)

        # Clear the textbox
        self.entry_textbox.delete("1.0", "end")
        self.entry_textbox._show_placeholder()

    def _optimize_entry(self, entry_id):
        """Request AI optimization for an entry"""
        if self.on_optimize_entry and entry_id:
            self.on_optimize_entry(entry_id)

    def update_entries(self, entries):
        """Update the entries list"""
        self.entries = entries
        self._render_entries()

    def add_entry(self, entry):
        """Add a new entry to the list"""
        self.entries.insert(0, entry)
        self._render_entries()

    def update_entry(self, entry_id, updated_entry):
        """Update a specific entry"""
        for i, entry in enumerate(self.entries):
            if entry.get("id") == entry_id:
                self.entries[i] = updated_entry
                break
        self._render_entries()

    def refresh(self):
        """Refresh the view"""
        self._render_entries()
