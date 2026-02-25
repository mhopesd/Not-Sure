"""Live Meeting Coach alerts panel component"""
import customtkinter as ctk
from ui.styles import ThemeManager, FONTS, RADIUS, SPACING
from ui.components.inputs import StyledLabel


class CoachAlertsPanel(ctk.CTkFrame):
    """Side panel showing live meeting coach alerts and agenda progress."""

    TYPE_ICONS = {
        "off_topic": "!",
        "agenda_covered": "\u2713",
        "agenda_missing": "?",
        "suggestion": "\u2794",
        "context_ref": "\u2197",
        "time_warning": "\u23f0",
    }

    def __init__(self, parent):
        colors = ThemeManager.get_colors()
        super().__init__(
            parent,
            fg_color=colors["card"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=colors["border"]
        )
        self._build_ui()

    def _build_ui(self):
        colors = ThemeManager.get_colors()

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=SPACING["md"], pady=(SPACING["md"], SPACING["sm"]))

        StyledLabel(header, text="Meeting Coach", variant="subheading").pack(anchor="w")

        # Agenda progress section
        self.agenda_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.agenda_frame.pack(fill="x", padx=SPACING["md"], pady=(0, SPACING["sm"]))

        StyledLabel(self.agenda_frame, text="Agenda Progress", variant="caption").pack(anchor="w")
        self.agenda_items_frame = ctk.CTkFrame(self.agenda_frame, fg_color="transparent")
        self.agenda_items_frame.pack(fill="x")

        # Divider
        ctk.CTkFrame(self, height=1, fg_color=colors["border"]).pack(
            fill="x", padx=SPACING["md"]
        )

        # Alerts header
        StyledLabel(self, text="Alerts", variant="caption").pack(
            anchor="w", padx=SPACING["md"], pady=(SPACING["sm"], SPACING["xs"])
        )

        # Alerts list (scrollable)
        self.alerts_scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent", height=200
        )
        self.alerts_scroll.pack(fill="both", expand=True, padx=SPACING["xs"], pady=(0, SPACING["sm"]))

        # Empty state
        self.empty_label = StyledLabel(
            self.alerts_scroll,
            text="No alerts yet. The coach will analyze the conversation periodically.",
            variant="caption"
        )
        self.empty_label.pack(anchor="w", padx=SPACING["sm"], pady=SPACING["md"])

    def update_alerts(self, alerts, agenda):
        """Refresh the panel with new alerts and agenda status."""
        colors = ThemeManager.get_colors()

        # Rebuild agenda items
        for w in self.agenda_items_frame.winfo_children():
            w.destroy()

        for item in agenda:
            row = ctk.CTkFrame(self.agenda_items_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)

            icon_text = "\u2713" if item.get("covered") else "\u25cb"
            icon_color = colors["success"] if item.get("covered") else colors["text_muted"]

            ctk.CTkLabel(
                row,
                text=icon_text,
                font=FONTS["body"],
                text_color=icon_color,
                width=20
            ).pack(side="left")

            ctk.CTkLabel(
                row,
                text=item.get("text", ""),
                font=FONTS["body_sm"],
                text_color=colors["text_primary"] if item.get("covered") else colors["text_secondary"],
                anchor="w"
            ).pack(side="left", fill="x", expand=True, padx=(SPACING["xs"], 0))

            if item.get("time_mentioned"):
                ctk.CTkLabel(
                    row,
                    text=item["time_mentioned"],
                    font=FONTS["caption_sm"],
                    text_color=colors["text_muted"]
                ).pack(side="right")

        # Rebuild alerts
        for w in self.alerts_scroll.winfo_children():
            w.destroy()

        if not alerts:
            StyledLabel(
                self.alerts_scroll,
                text="No alerts yet. The coach will analyze the conversation periodically.",
                variant="caption"
            ).pack(anchor="w", padx=SPACING["sm"], pady=SPACING["md"])
            return

        for alert in reversed(alerts):  # Newest first
            self._render_alert(alert)

    def _render_alert(self, alert):
        """Render a single alert card."""
        colors = ThemeManager.get_colors()
        severity = alert.get("severity", "info")

        bg_map = {
            "info": colors.get("coach_info", colors["accent_light"]),
            "warning": colors.get("coach_warning", colors["warning_light"]),
            "critical": colors.get("coach_critical", "#fef2f2"),
        }
        border_map = {
            "info": colors.get("coach_info_border", colors["accent"]),
            "warning": colors.get("coach_warning_border", colors["warning"]),
            "critical": colors.get("coach_critical_border", colors["destructive"]),
        }

        frame = ctk.CTkFrame(
            self.alerts_scroll,
            fg_color=bg_map.get(severity, colors["card"]),
            corner_radius=RADIUS["md"],
            border_width=1,
            border_color=border_map.get(severity, colors["border"])
        )
        frame.pack(fill="x", pady=SPACING["xs"], padx=SPACING["xs"])

        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="x", padx=SPACING["sm"], pady=SPACING["sm"])

        # Top row: timestamp + type
        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x")

        timestamp = alert.get("timestamp", "")
        if timestamp:
            ctk.CTkLabel(
                top_row,
                text=timestamp,
                font=FONTS["mono_sm"],
                text_color=colors["text_muted"]
            ).pack(side="left")

        alert_type = alert.get("type", "")
        icon = self.TYPE_ICONS.get(alert_type, "")
        type_label = alert_type.replace("_", " ").title()

        ctk.CTkLabel(
            top_row,
            text=f"{icon} {type_label}",
            font=FONTS["caption"],
            text_color=border_map.get(severity, colors["text_secondary"])
        ).pack(side="left", padx=(SPACING["sm"], 0))

        # Message
        ctk.CTkLabel(
            inner,
            text=alert.get("message", ""),
            font=FONTS["body_sm"],
            text_color=colors["text_primary"],
            wraplength=250,
            anchor="w",
            justify="left"
        ).pack(fill="x", pady=(SPACING["xs"], 0))

        # Agenda item reference
        agenda_item = alert.get("agenda_item")
        if agenda_item:
            ctk.CTkLabel(
                inner,
                text=f"Re: {agenda_item}",
                font=FONTS["caption_sm"],
                text_color=colors["text_muted"],
                anchor="w"
            ).pack(fill="x", pady=(2, 0))
