#!/usr/bin/env python3
"""
Personal Assistant — macOS Menu Bar Companion

Lives in the menu bar and connects to the existing api_server.py backend.
Provides one-click recording, live status, and insight notifications.

Usage:
    python menubar_app.py

Requires:
    pip install rumps requests
"""

import rumps
import requests
import threading
import json
import time
import subprocess
import webbrowser

# Backend API base URL
API_BASE = "http://localhost:8000"


class PersonalAssistantMenuBar(rumps.App):
    def __init__(self):
        super().__init__(
            "🎙",
            title="🎙",
            quit_button=None,  # We'll add our own
        )

        # State
        self.is_recording = False
        self.duration = 0
        self.meeting_type = None
        self.topic = ""
        self.last_action_count = 0
        self.last_decision_count = 0
        self.backend_online = False

        # Build menu
        self.record_button = rumps.MenuItem("⏺  Start Recording", callback=self.toggle_recording)
        self.status_item = rumps.MenuItem("📊  Status: Checking...", callback=None)
        self.status_item.set_callback(None)  # Not clickable
        self.insights_item = rumps.MenuItem("💡  Latest Insights")
        self.audio_source_menu = rumps.MenuItem("🎤  Audio Source")
        self.open_dashboard = rumps.MenuItem("🖥  Open Dashboard", callback=self.open_app)
        self.quit_button = rumps.MenuItem("Quit", callback=self.quit_app)

        self.menu = [
            self.record_button,
            None,  # separator
            self.status_item,
            self.insights_item,
            None,  # separator
            self.audio_source_menu,
            self.open_dashboard,
            None,  # separator
            self.quit_button,
        ]

        # Polling thread
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()

        # Load audio sources on startup
        self._load_audio_sources()

    # ─── Recording Control ───────────────────────────────────────

    def toggle_recording(self, sender):
        if self.is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        try:
            resp = requests.post(f"{API_BASE}/api/recordings/start", json={}, timeout=5)
            if resp.ok:
                self.is_recording = True
                self.title = "🔴"
                self.record_button.title = "⏹  Stop Recording"
                self.last_action_count = 0
                self.last_decision_count = 0
                rumps.notification(
                    "Recording Started",
                    "Personal Assistant",
                    "Your meeting is being recorded and analyzed.",
                    sound=False,
                )
            else:
                rumps.notification("Error", "Failed to start", resp.text[:100], sound=True)
        except requests.ConnectionError:
            rumps.notification("Backend Offline", "Cannot start recording",
                             "Start the backend: python api_server.py", sound=True)
        except Exception as e:
            rumps.notification("Error", "Recording failed", str(e)[:100], sound=True)

    def _stop_recording(self):
        try:
            resp = requests.post(f"{API_BASE}/api/recordings/stop", timeout=30)
            self.is_recording = False
            self.title = "🎙"
            self.record_button.title = "⏺  Start Recording"
            self.meeting_type = None
            self.topic = ""
            self.status_item.title = "📊  Status: Idle"

            if resp.ok:
                rumps.notification(
                    "Recording Saved",
                    "Personal Assistant",
                    "Transcript and summary are being generated.",
                    sound=False,
                )
            else:
                rumps.notification("Warning", "Stop returned error", resp.text[:100], sound=True)
        except Exception as e:
            rumps.notification("Error", "Stop failed", str(e)[:100], sound=True)
            # Reset state anyway
            self.is_recording = False
            self.title = "🎙"
            self.record_button.title = "⏺  Start Recording"

    # ─── Audio Source Selection ───────────────────────────────────

    def _load_audio_sources(self):
        try:
            resp = requests.get(f"{API_BASE}/api/devices", timeout=3)
            if resp.ok:
                devices = resp.json().get("devices", [])
                self.audio_source_menu.clear()
                for device in devices:
                    name = device.get("name", "Unknown")
                    device_id = device.get("id", "")
                    item = rumps.MenuItem(name, callback=self._make_source_callback(device_id, name))
                    self.audio_source_menu.add(item)
        except Exception:
            self.audio_source_menu.clear()
            self.audio_source_menu.add(rumps.MenuItem("⚠ Backend offline"))

    def _make_source_callback(self, device_id, name):
        def callback(sender):
            try:
                requests.put(
                    f"{API_BASE}/api/settings",
                    json={"recording_mode": device_id},
                    timeout=3
                )
                rumps.notification("Audio Source", "Changed to", name, sound=False)
            except Exception:
                pass
        return callback

    # ─── Polling Loop ────────────────────────────────────────────

    def _poll_loop(self):
        """Polls backend for recording status and insights."""
        while True:
            try:
                self._poll_status()
                if self.is_recording:
                    self._poll_insights()
            except Exception:
                pass

            # Poll faster during recording
            interval = 3 if self.is_recording else 10
            time.sleep(interval)

    def _poll_status(self):
        try:
            resp = requests.get(f"{API_BASE}/api/recordings/status", timeout=3)
            if resp.ok:
                data = resp.json()
                was_online = self.backend_online
                self.backend_online = True

                if not was_online:
                    # Just came online
                    self._load_audio_sources()

                self.is_recording = data.get("is_recording", False)
                self.duration = data.get("duration", 0)
                self.meeting_type = data.get("meeting_type")
                self.topic = data.get("topic", "")

                if self.is_recording:
                    self.title = "🔴"
                    self.record_button.title = "⏹  Stop Recording"
                    mins = self.duration // 60
                    secs = self.duration % 60
                    status_parts = [f"{mins}:{secs:02d}"]
                    if self.meeting_type:
                        mt = self.meeting_type.replace("_", " ").title()
                        status_parts.append(mt)
                    if self.topic:
                        status_parts.append(self.topic)
                    self.status_item.title = f"📊  Recording {' | '.join(status_parts)}"
                else:
                    self.title = "🎙"
                    self.record_button.title = "⏺  Start Recording"
                    self.status_item.title = "📊  Status: Idle"
            else:
                self.backend_online = False
                self.status_item.title = "📊  Status: Backend error"
        except requests.ConnectionError:
            self.backend_online = False
            self.status_item.title = "📊  Status: Backend offline"
        except Exception:
            pass

    def _poll_insights(self):
        try:
            resp = requests.get(f"{API_BASE}/api/recordings/insights", timeout=3)
            if not resp.ok:
                return

            data = resp.json()

            # Update insights submenu
            self.insights_item.clear()
            key_points = data.get("key_points", [])
            for point in key_points[:5]:
                self.insights_item.add(rumps.MenuItem(f"• {point[:60]}"))

            actions = data.get("action_items", [])
            decisions = data.get("decisions", [])

            if actions:
                self.insights_item.add(None)  # separator
                self.insights_item.add(rumps.MenuItem("── Action Items ──"))
                for item in actions:
                    text = item.get("text", "")[:50]
                    assignee = item.get("assignee", "")
                    label = f"☐ {text}"
                    if assignee:
                        label += f" → {assignee}"
                    self.insights_item.add(rumps.MenuItem(label))

            if decisions:
                self.insights_item.add(None)  # separator
                self.insights_item.add(rumps.MenuItem("── Decisions ──"))
                for d in decisions:
                    self.insights_item.add(rumps.MenuItem(f"✓ {d[:60]}"))

            # Notify on NEW action items
            new_action_count = len(actions)
            if new_action_count > self.last_action_count and self.last_action_count > 0:
                new_items = actions[self.last_action_count:]
                for item in new_items:
                    text = item.get("text", "New action item")
                    assignee = item.get("assignee", "")
                    subtitle = f"Assigned to {assignee}" if assignee else "No assignee"
                    rumps.notification("📋 Action Item", subtitle, text, sound=False)
            self.last_action_count = new_action_count

            # Notify on NEW decisions
            new_decision_count = len(decisions)
            if new_decision_count > self.last_decision_count and self.last_decision_count > 0:
                new_decisions = decisions[self.last_decision_count:]
                for d in new_decisions:
                    rumps.notification("⚡ Decision Made", "Meeting Intelligence", d, sound=False)
            self.last_decision_count = new_decision_count

            # Notify once when meeting type is first detected
            mt = data.get("meeting_type")
            if mt and not self.meeting_type:
                confidence = data.get("confidence", 0)
                if confidence > 0.6:
                    mt_label = mt.replace("_", " ").title()
                    rumps.notification(
                        "Meeting Detected",
                        f"{mt_label}",
                        f"Topic: {data.get('topic', 'General discussion')}",
                        sound=False,
                    )

        except Exception:
            pass

    # ─── Utilities ───────────────────────────────────────────────

    def open_app(self, sender):
        """Open the dashboard in the default browser."""
        webbrowser.open("http://localhost:5173")

    def quit_app(self, sender):
        rumps.quit_application()


if __name__ == "__main__":
    PersonalAssistantMenuBar().run()
