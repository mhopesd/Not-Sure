"""
Obsidian Vault Export — converts meeting summary data to Obsidian-flavored Markdown.
"""

import logging
import os
import re
from datetime import datetime

logger = logging.getLogger(__name__)


def _sanitize_filename(name: str) -> str:
    """Remove characters that are invalid in filenames / Obsidian titles."""
    name = re.sub(r'[\\/:*?"<>|]', "", name)
    name = name.strip(". ")
    return name or "Untitled Meeting"


def _format_duration(duration_val) -> str:
    """Convert duration (seconds int, or string like '5m 23s') to human-readable."""
    if isinstance(duration_val, str):
        return duration_val
    if isinstance(duration_val, (int, float)) and duration_val > 0:
        mins, secs = divmod(int(duration_val), 60)
        if mins:
            return f"{mins}m {secs}s"
        return f"{secs}s"
    return "Unknown"


def meeting_to_markdown(data: dict) -> str:
    """Render a meeting summary dict as Obsidian Markdown with YAML frontmatter."""

    title = data.get("title", "Untitled Meeting")
    date_raw = data.get("timestamp") or data.get("date") or str(datetime.now())
    duration = _format_duration(data.get("duration") or data.get("duration_seconds", 0))

    # Parse date for frontmatter
    try:
        dt = datetime.fromisoformat(str(date_raw).replace("Z", "+00:00"))
        date_str = dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        date_str = str(date_raw)

    # Speakers
    speaker_info = data.get("speaker_info", {})
    if isinstance(speaker_info, dict):
        speakers = speaker_info.get("list", [])
    elif isinstance(speaker_info, list):
        speakers = speaker_info
    else:
        speakers = []

    tags = data.get("tags", [])
    tag_list = ["meeting", "notsure"] + [t for t in tags if t not in ("meeting", "notsure")]

    # --- Build Markdown ---
    lines = []

    # YAML frontmatter
    lines.append("---")
    lines.append(f"title: \"{title}\"")
    lines.append(f"date: {date_str}")
    lines.append(f"duration: \"{duration}\"")
    if speakers:
        lines.append(f"speakers: [{', '.join(repr(s) for s in speakers)}]")
    lines.append(f"tags: [{', '.join(tag_list)}]")
    if data.get("start_time"):
        lines.append(f"start_time: \"{data['start_time']}\"")
    if data.get("end_time"):
        lines.append(f"end_time: \"{data['end_time']}\"")
    lines.append("---")
    lines.append("")

    # Title
    lines.append(f"# {title}")
    lines.append("")

    # Executive Summary
    summary = data.get("executive_summary", "")
    if summary:
        lines.append("## Summary")
        lines.append(summary)
        lines.append("")

    # Highlights
    highlights = data.get("highlights", [])
    if highlights:
        lines.append("## Highlights")
        for h in highlights:
            lines.append(f"- {h}")
        lines.append("")

    # Full Summary Sections
    sections = data.get("full_summary_sections", [])
    if sections:
        lines.append("## Detailed Notes")
        for section in sections:
            if isinstance(section, dict):
                heading = section.get("heading") or section.get("title", "")
                content = section.get("content") or section.get("body", "")
                if heading:
                    lines.append(f"### {heading}")
                if content:
                    lines.append(content)
                lines.append("")
            elif isinstance(section, str):
                lines.append(section)
                lines.append("")

    # Action Items / Tasks
    tasks = data.get("tasks", [])
    if tasks:
        lines.append("## Action Items")
        for task in tasks:
            if isinstance(task, dict):
                text = task.get("text") or task.get("task", "")
                assignee = task.get("assignee", "")
                if assignee:
                    lines.append(f"- [ ] {text} — *{assignee}*")
                else:
                    lines.append(f"- [ ] {text}")
            elif isinstance(task, str):
                lines.append(f"- [ ] {task}")
        lines.append("")

    # Transcript
    transcript = data.get("transcript", "")
    if transcript:
        lines.append("## Transcript")
        lines.append("")
        # Use diarized transcript if available
        diarized = data.get("diarized_transcript_text", "")
        if diarized:
            lines.append(diarized)
        else:
            lines.append(transcript)
        lines.append("")

    return "\n".join(lines)


def export_meeting_to_obsidian(meeting_data: dict, vault_path: str, folder: str = "Meetings") -> str:
    """
    Export a meeting as a Markdown note into the Obsidian vault.

    Returns the absolute path of the written file, or empty string on failure.
    """
    vault_path = os.path.expanduser(vault_path)
    target_dir = os.path.join(vault_path, folder)

    os.makedirs(target_dir, exist_ok=True)

    # Build filename: YYYY-MM-DD - Title.md
    title = meeting_data.get("title", "Untitled Meeting")
    date_raw = meeting_data.get("timestamp") or meeting_data.get("date") or str(datetime.now())
    try:
        dt = datetime.fromisoformat(str(date_raw).replace("Z", "+00:00"))
        date_prefix = dt.strftime("%Y-%m-%d")
    except Exception:
        date_prefix = datetime.now().strftime("%Y-%m-%d")

    safe_title = _sanitize_filename(title)
    base_name = f"{date_prefix} - {safe_title}"
    filename = f"{base_name}.md"
    filepath = os.path.join(target_dir, filename)

    # Handle duplicates
    counter = 1
    while os.path.exists(filepath):
        counter += 1
        filename = f"{base_name} ({counter}).md"
        filepath = os.path.join(target_dir, filename)

    markdown = meeting_to_markdown(meeting_data)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(markdown)

    logger.info(f"Exported meeting to Obsidian: {filepath}")
    return filepath
